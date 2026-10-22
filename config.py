import os
from dotenv import load_dotenv

load_dotenv()

# 1. Telegram Dispatch Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 2. Chains to Monitor (comma-separated: solana, robinhood, bsc, base, ethereum)
TARGET_CHAINS = [
    c.strip().lower() 
    for c in os.getenv("TARGET_CHAINS", "solana,robinhood,bsc,base,ethereum").split(",") 
    if c.strip()
]

# 3. Base Scanner Timing & Cooldown
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
ALERT_COOLDOWN_MINUTES = int(os.getenv("ALERT_COOLDOWN_MINUTES", "120"))
MIN_SCORE_ALERT = int(os.getenv("MIN_SCORE_ALERT", "60"))

# 4. Climax Top / Exhaustion Guard
# Rejects in-flight parabolic spikes unless backed by extremely deep float (>= 60%)
MAX_ALLOWED_1H_CHANGE_PCT = float(os.getenv("MAX_ALLOWED_1H_CHANGE_PCT", "35.0"))
CLIMAX_EXCEPTION_FLOAT_RATIO = float(os.getenv("CLIMAX_EXCEPTION_FLOAT_RATIO", "60.0"))
MAX_ALLOWED_5M_CHANGE_PCT = float(os.getenv("MAX_ALLOWED_5M_CHANGE_PCT", "15.0"))

# 5. Profile A: Robinhood / BSC Deep-Float Accumulation (High Multi-Bagger Rate)
# Targets sticky pools where liquidity backing protects against dev dumps
MIN_FLOAT_RATIO_EVM = float(os.getenv("MIN_FLOAT_RATIO_EVM", "20.0"))
MAX_FDV_EVM = float(os.getenv("MAX_FDV_EVM", "350000.0"))
MIN_BUY_RATIO_EVM = float(os.getenv("MIN_BUY_RATIO_EVM", "0.55"))
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", "10000.0"))

# 6. Profile B: Solana High-Velocity Frenzy (Institutional/Retail Momentum)
# Filters out 90%+ of dead pump.fun launches and sniper wash-trading
MIN_VOL_1H_SOLANA = float(os.getenv("MIN_VOL_1H_SOLANA", "100000.0"))
MIN_TXNS_SOLANA = int(os.getenv("MIN_TXNS_SOLANA", "2500"))
MIN_BUY_RATIO_SOLANA = float(os.getenv("MIN_BUY_RATIO_SOLANA", "0.75"))
MIN_FLOAT_RATIO_SOLANA = float(os.getenv("MIN_FLOAT_RATIO_SOLANA", "10.0"))
MAX_FLOAT_RATIO_SOLANA = float(os.getenv("MAX_FLOAT_RATIO_SOLANA", "22.0"))
MIN_FDV_SOLANA = float(os.getenv("MIN_FDV_SOLANA", "100000.0"))
MAX_FDV_SOLANA = float(os.getenv("MAX_FDV_SOLANA", "500000.0"))
MIN_LIQUIDITY_SOLANA_USD = float(os.getenv("MIN_LIQUIDITY_SOLANA_USD", "30000.0"))
