"""
Emerging DEX Pair Scanner Engine
Fetches newly boosted and trending token profiles from DexScreener & GeckoTerminal.
Applies quantitative pre-pump markers (Volume surge, aggressive buying, consolidation).
Dispatches alerts to Telegram while respecting cooldown windows.
"""

import urllib.request
import json
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import config
from notifier import send_telegram_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dex_scanner")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def fetch_json(url: str, retries: int = 3, delay: float = 1.5) -> Optional[Any]:
    req = urllib.request.Request(url, headers=HEADERS)
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay * 3)
            else:
                time.sleep(delay)
        except Exception:
            time.sleep(delay)
    return None

def evaluate_pair(pair: Dict[str, Any], min_liquidity: float) -> Optional[Dict[str, Any]]:
    token = pair.get("baseToken", {})
    sym = token.get("symbol", "UNKNOWN")
    addr = token.get("address", "")
    chain = (pair.get("chainId") or "").lower()
    dex = pair.get("dexId", "")
    
    # Check chain filter
    if config.TARGET_CHAINS and chain not in config.TARGET_CHAINS:
        return None
        
    liq_usd = float((pair.get("liquidity") or {}).get("usd") or 0)
    fdv = float(pair.get("fdv") or 0)
    price_usd = float(pair.get("priceUsd") or 0)
    
    if liq_usd < min_liquidity:
        return None
        
    vol = pair.get("volume") or {}
    v_1h = float(vol.get("h1") or 0)
    v_24h = float(vol.get("h24") or 0)
    
    # Baseline hourly volume
    v_baseline_1h = max((v_24h - v_1h) / 23.0, 1.0) if v_24h > v_1h else max(v_24h / 24.0, 1.0)
    vol_surge_ratio = v_1h / v_baseline_1h
    
    txns = pair.get("txns") or {}
    tx_1h = txns.get("h1") or {}
    buys_1h = int(tx_1h.get("buys") or 0)
    sells_1h = int(tx_1h.get("sells") or 0)
    total_tx_1h = buys_1h + sells_1h
    
    buy_ratio = (buys_1h / total_tx_1h) if total_tx_1h > 0 else 0.5
    
    price_chg = pair.get("priceChange") or {}
    chg_1h = float(price_chg.get("h1") or 0)
    
    liq_fdv_ratio = (liq_usd / fdv * 100) if fdv > 0 else 0.0
    
    signals = []
    score = 0
    
    # Marker 1: Volume Spike
    if vol_surge_ratio >= config.VOL_SURGE_THRESHOLD and v_1h >= 2500:
        signals.append(f"Volume Surge {vol_surge_ratio:.1f}x ($1h: ${v_1h:,.0f})")
        score += 35
    elif vol_surge_ratio >= 1.8 and v_1h >= 1000:
        signals.append(f"Mild Vol Expansion {vol_surge_ratio:.1f}x ($1h: ${v_1h:,.0f})")
        score += 15
        
    # Marker 2: Buy Side Accumulation
    if buy_ratio >= config.BUY_RATIO_THRESHOLD and buys_1h >= 10:
        signals.append(f"Aggressive Buying ({buy_ratio*100:.0f}% Buys, {buys_1h}B/{sells_1h}S)")
        score += 35
    elif buy_ratio >= 0.58 and buys_1h >= 5:
        signals.append(f"Net Buys ({buy_ratio*100:.0f}% Buys)")
        score += 15
        
    # Marker 3: Pre-Breakout Consolidation vs In-Flight
    if 0.5 <= chg_1h <= 20.0:
        signals.append(f"Pre-Breakout Base ({chg_1h:+.1f}% 1h)")
        score += 20
    elif -2.0 <= chg_1h < 0.5:
        signals.append(f"Tight Price Compression ({chg_1h:+.1f}% 1h)")
        score += 15
    elif chg_1h > 20.0:
        signals.append(f"In-Flight Spike (+{chg_1h:.1f}% 1h - Risk of Top)")
        score += 5
        
    # Marker 4: Springboard Float
    if 1.0 <= liq_fdv_ratio <= 15.0:
        signals.append(f"Tight Float (L/FDV: {liq_fdv_ratio:.1f}%)")
        score += 10
        
    return {
        "symbol": sym,
        "token_address": addr,
        "chain": chain,
        "dex": dex,
        "pair_url": f"https://dexscreener.com/{chain}/{pair.get('pairAddress')}",
        "price_usd": price_usd,
        "liquidity_usd": liq_usd,
        "fdv": fdv,
        "vol_1h": v_1h,
        "vol_24h": v_24h,
        "vol_surge_ratio": round(vol_surge_ratio, 2),
        "buys_1h": buys_1h,
        "sells_1h": sells_1h,
        "buy_pct": round(buy_ratio * 100, 1),
        "chg_1h": chg_1h,
        "score": score,
        "signals": signals
    }

class DexPumpScanner:
    def __init__(self):
        self.alert_history: Dict[str, float] = {} # token_address -> timestamp
        
    def get_candidate_tokens(self) -> List[str]:
        candidates = set()
        
        # 1. DexScreener Token Boosts (active discovery)
        boosts = fetch_json("https://api.dexscreener.com/token-boosts/latest/v1") or []
        for b in boosts:
            addr = b.get("tokenAddress")
            if addr:
                candidates.add(addr)
                
        # 2. DexScreener Latest Token Profiles
        profiles = fetch_json("https://api.dexscreener.com/token-profiles/latest/v1") or []
        for p in profiles:
            addr = p.get("tokenAddress")
            if addr:
                candidates.add(addr)
                
        return list(candidates)

    def scan_once(self):
        candidates = self.get_candidate_tokens()
        logger.info(f"Checking {len(candidates)} emerging candidate tokens...")
        
        now = time.time()
        for token_addr in candidates:
            # Check cooldown
            last_alerted = self.alert_history.get(token_addr, 0)
            if now - last_alerted < config.ALERT_COOLDOWN_MINUTES * 60:
                continue
                
            data = fetch_json(f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}")
            if not data or not data.get("pairs"):
                time.sleep(0.2)
                continue
                
            # Pick highest liquidity pair
            pairs = sorted(data["pairs"], key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0), reverse=True)
            best_pair = pairs[0]
            
            evaluation = evaluate_pair(best_pair, min_liquidity=config.MIN_LIQUIDITY_USD)
            if evaluation and evaluation["score"] >= config.MIN_SCORE_ALERT:
                logger.info(
                    f"🔥 PRE-PUMP SIGNAL: {evaluation['symbol']} ({evaluation['chain']}) "
                    f"[Score: {evaluation['score']}/100] Vol Surge: {evaluation['vol_surge_ratio']}x"
                )
                
                # Send Telegram alert
                sent = send_telegram_alert(
                    bot_token=config.TELEGRAM_BOT_TOKEN,
                    chat_id=config.TELEGRAM_CHAT_ID,
                    alert=evaluation
                )
                if sent or not config.TELEGRAM_BOT_TOKEN:
                    self.alert_history[token_addr] = now
                    
            time.sleep(0.25)

    def run_forever(self):
        logger.info("🚀 DEX Pre-Pump Scanner Started.")
        logger.info(f"Target Chains: {config.TARGET_CHAINS or 'ALL'}")
        logger.info(f"Min Liquidity: ${config.MIN_LIQUIDITY_USD:,.0f} | Min Score: {config.MIN_SCORE_ALERT}")
        
        while True:
            try:
                self.scan_once()
            except Exception as e:
                logger.error(f"Error in scan loop: {e}", exc_info=True)
                
            logger.info(f"Cycle complete. Sleeping {config.POLL_INTERVAL_SECONDS}s...")
            time.sleep(config.POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    scanner = DexPumpScanner()
    scanner.run_forever()
