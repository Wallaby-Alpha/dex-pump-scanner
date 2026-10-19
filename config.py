import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Base Scanner Thresholds
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "10000.0"))
MIN_LIQUIDITY_SOLANA_USD = float(os.getenv("MIN_LIQUIDITY_SOLANA_USD", "25000.0"))
MIN_SCORE_ALERT = int(os.getenv("MIN_SCORE_ALERT", "60"))
VOL_SURGE_THRESHOLD = float(os.getenv("VOL_SURGE_THRESHOLD", "2.5"))
BUY_RATIO_THRESHOLD = float(os.getenv("BUY_RATIO_THRESHOLD", "0.65"))

# Maximum allowed price expansion to prevent chasing in-flight tops
MAX_ALLOWED_1H_CHANGE_PCT = float(os.getenv("MAX_ALLOWED_1H_CHANGE_PCT", "25.0"))
MAX_ALLOWED_5M_CHANGE_PCT = float(os.getenv("MAX_ALLOWED_5M_CHANGE_PCT", "15.0"))

# Target Chains (leave empty to scan ALL chains)
TARGET_CHAINS = [c.strip().lower() for c in os.getenv("TARGET_CHAINS", "solana,robinhood,base,bsc,ethereum").split(",") if c.strip()]

# Poll interval in seconds
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))

# Cooldown period (in minutes) so the same token isn't spammed
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "120"))
