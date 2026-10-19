# DEX Pump Precursor Scanner 🚀

A real-time quantitative scanner designed to monitor emerging DEX pairs across **Solana, Robinhood Chain, Base, BSC, Ethereum, and Arbitrum** to catch pre-pump markers and send alerts directly to **Telegram**.

---

## 🔍 How It Detects Pre-Pumps

The scanner evaluates on-chain liquidity pools and pairs against 4 primary markers:

1. **Volume Surge Multiplier ($V_{\text{ratio}} = \frac{V_{1h}}{\text{Baseline}}$)**: Flags volume expanding $>2.5\times - 3.0\times$ above the recent hourly baseline.
2. **Aggressive Buy-Side Ratio**: Detects when buys outnumber sells by $>65\%-75\%$ with strong buyer transaction counts.
3. **Pre-Breakout Consolidation**: Identifies price bases $(-2.0\% \text{ to } +15\%)$ before the public vertical spike occurs, filtering out already-exhausted pumps.
4. **Springboard Float Ratio ($L / \text{FDV}$)**: Flags tight circulating floats $(1\% - 15\%)$ where incoming order flow causes rapid price appreciation.

---

## 🛠 Local Setup

1. **Clone & Install Dependencies**:
   ```bash
   git clone <repo_url>
   cd dex-pump-scanner
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in your Telegram credentials:
   - `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/BotFather) on Telegram.
   - `TELEGRAM_CHAT_ID`: Your user ID or group/channel ID (get it via [@userinfobot](https://t.me/userinfobot) or [@RawDataBot](https://t.me/RawDataBot)).

3. **Run Locally**:
   ```bash
   python main.py
   ```

---

## ☁️ DigitalOcean Droplet Deployment

### Option A: Using Docker & Docker Compose (Recommended)

1. **SSH into your DigitalOcean Droplet**:
   ```bash
   ssh root@<YOUR_DROPLET_IP>
   ```

2. **Install Docker & Git** (if not already installed):
   ```bash
   apt-get update && apt-get install -y docker.io docker-compose git
   ```

3. **Clone the Repository**:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd dex-pump-scanner
   ```

4. **Create `.env`**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *(Paste your Telegram Bot Token & Chat ID, then save with `Ctrl+O`, `Enter`, `Ctrl+X`)*

5. **Start Scanner in Background**:
   ```bash
   docker-compose up -d --build
   ```

6. **Check Logs**:
   ```bash
   docker-compose logs -f
   ```

---

### Option B: Using Systemd Service (Native Python)

If you prefer running directly without Docker:

1. **Install Python & Virtualenv**:
   ```bash
   apt-get update && apt-get install -y python3 python3-pip python3-venv git
   git clone <YOUR_GITHUB_REPO_URL> /opt/dex-pump-scanner
   cd /opt/dex-pump-scanner
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env
   ```

2. **Create Systemd Service**:
   ```bash
   cat << 'EOF' > /etc/systemd/system/dex-scanner.service
   [Unit]
   Description=DEX Pump Precursor Scanner
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/dex-pump-scanner
   ExecStart=/opt/dex-pump-scanner/venv/bin/python -u /opt/dex-pump-scanner/main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

3. **Enable & Start Service**:
   ```bash
   systemctl daemon-reload
   systemctl enable dex-scanner
   systemctl start dex-scanner
   ```

4. **Monitor Real-time Logs**:
   ```bash
   journalctl -u dex-scanner -f
   ```
