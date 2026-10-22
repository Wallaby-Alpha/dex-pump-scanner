# DEX Pre-Breakout & Pump Scanner 🚀

A real-time quantitative scanner reverse-engineered from empirical performance analysis across **197 live alerts** and **130 unique DEX tokens** on **Solana, Robinhood Chain, BSC, Base, and Ethereum**.

The scanner employs a **Dual-Profile Filter Architecture** designed to catch **+100% to +800% multi-baggers** while filtering out **>70% of false-positive noise and rugpull traps**.

---

## 📊 Empirical Performance & Key Discoveries

Across the historical dataset of live alerts, exactly **14 tokens achieved $\ge +100\%$ pumps (2x–9x)** from the alert moment:

### The 14 Verified Doublers
| Token | Chain | Peak Gain | Starting FDV | Starting Liq | Liq / FDV | 1h Chg at Alert | 1h Volume |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **W4WORK** | Robinhood | **+889.7%** | $185k | $121k | **65.4%** | +485% | $208k |
| **GLOAM** | Robinhood | **+324.5%** | $117k | $51k | **43.4%** | +25.6% | $29.5k |
| **Pokémon** | Solana | **+284.0%** | $390k | $67k | **17.2%** | +16.3% | $762k |
| **aDOGymous** | Solana | **+253.1%** | $264k | $43k | **16.4%** | +21.9% | $116k |
| **Wick** | BSC | **+207.8%** | $10.7k | $20.9k | **195.1%** | +4.9% | $300 |
| **.ai** | BSC | **+168.3%** | $72.2k | $24.6k | **34.1%** | +0.2% | $136k |
| **WORTHLESS**| Solana | **+143.5%** | $242k | $41.2k | **17.0%** | +352% | $355k |
| **WYRM** | Robinhood | **+138.0%** | $54.6k | $38.5k | **70.5%** | +391% | $45.7k |
| **SIGH** | BSC | **+110.7%** | $35.3k | $17.3k | **49.1%** | +3.3% | $3.3k |
| **DOLLARSE** | Solana | **+110.1%** | $137k | $16.7k | **12.2%** | +31.9% | $3.3k |
| **YILONGMA** | Ethereum | **+108.8%** | $57.0k | $21.0k | **36.8%** | -25.3% | $55.0k |
| **startupSI**| Solana | **+108.6%** | $11.4M | $335k | **2.9%** | -1.1% | $367k |
| **PIMP** | Robinhood | **+105.4%** | $13.7k | $10.1k | **73.6%** | +35.4% | $1.3k |
| **TORCHINU** | Robinhood | **+102.6%** | $16.2k | $12.5k | **77.0%** | +2.8% | $2.5k |

---

## 🔍 The Reverse-Engineered Architecture

Analysis of the winners revealed two fundamentally different market dynamics:

### 1. Profile A: Robinhood & BSC Deep-Float Accumulators
* **The Pattern:** On Robinhood and BSC, pools with **Liquidity $\ge$ 20% to 75% of FDV** cannot be dumped to zero by a single rogue seller. Slippage is low, enabling clean community accumulation and multi-hour runs.
* **Filter Conditions:**
  * Chain: `robinhood` or `bsc`
  * Float Backing: `Liquidity / FDV >= 20.0%`
  * Market Cap: `$10,000 <= FDV <= $350,000`
  * Net Buys: `Buy Ratio >= 55%`
* **Performance:** **57.1% win rate on BSC with +10.1% Expected Value per trade**.

### 2. Profile B: Solana High-Velocity Breakouts
* **The Pattern:** 54.6% of Solana tokens dump to zero within 2–4 hours due to sub-second MEV bundlers. The few that doubled had **huge institutional/retail volume ($100k–$750k/hr)** and **thousands of transactions**.
* **Filter Conditions:**
  * 1h Volume: `vol_1h >= $100,000`
  * Transaction Activity: `total_txns >= 2,500`
  * Buy Domination: `buys_pct >= 75.0%`
  * Float: `10.0% <= (Liquidity / FDV) <= 22.0%`
  * Pre-Alert Price Change: `<= +30.0%` (Rejects exhausted climax spikes)

### 3. Climax Top / Climax Pump Guard
* **The Rule:** Rejects any token up `> 35.0%` in the last hour **unless** its liquidity backing is extraordinarily deep (`Liq/FDV >= 60.0%`).
* **Impact:** Eliminates 85 out of 107 duds, reducing alert noise by **74%** while preserving **71.4% of all 2x+ winners**.

---

## 🛠 Local Setup

1. **Clone & Install Dependencies**:
   ```bash
   git clone https://github.com/Wallaby-Alpha/dex-pump-scanner.git
   cd dex-pump-scanner
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in your Telegram credentials:
   * `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/BotFather) on Telegram.
   * `TELEGRAM_CHAT_ID`: Your user or channel ID.

3. **Run Backtest Summary**:
   ```bash
   python backtest.py
   ```

4. **Start the Scanner**:
   ```bash
   python main.py
   ```

---

## ☁️ Deployment

### Using Docker Compose (Recommended)

1. **Start in Background**:
   ```bash
   docker-compose up -d --build
   ```

2. **Stream Logs**:
   ```bash
   docker-compose logs -f
   ```

### Using Systemd Service (Linux Droplet)

```bash
cat << 'EOF' > /etc/systemd/system/dex-scanner.service
[Unit]
Description=DEX Pre-Breakout Scanner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/dex-pump-scanner
ExecStart=/opt/dex-pump-scanner/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dex-scanner
systemctl start dex-scanner
```

---

## 📋 Recommended Trading Playbook

When an alert triggers, follow this rulebook derived from 4-hour trajectory analysis:

* **Robinhood & BSC Tokens:**
  * **Take Profit 1:** Sell 50% at **+30%**.
  * **Stop-to-Breakeven:** Move stop loss to **Breakeven (0% net risk)** immediately once +20% is reached.
  * **Take Profit 2:** Sell 30% at **+80% to +100%**.
  * **Moonbag:** Leave 20% trailing with a 25% trailing stop.
* **Solana Tokens:**
  * Solana runners peak fast (median: 120 minutes). Take 70% off at **+25% to +35%**.
  * Hard Stop Loss: **-15.0%**.
  * **Time Stop:** If not up $\ge$ +10% within **120 minutes**, exit immediately.
