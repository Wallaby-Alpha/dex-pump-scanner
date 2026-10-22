import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("telegram_notifier")

def send_telegram_alert(bot_token: str, chat_id: str, alert: Dict[str, Any]) -> bool:
    """
    Sends an empirical, high-conviction Markdown alert to Telegram.
    Includes execution playbook, float backing, and setup classification.
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token or Chat ID not configured. Skipping alert dispatch.")
        return False
        
    score = alert.get("score", 0)
    setup = alert.get("setup_profile", "PRE-BREAKOUT BASE")
    liq_usd = alert.get("liquidity_usd", 0)
    fdv = alert.get("fdv", 0)
    liq_fdv = (liq_usd / fdv * 100.0) if fdv > 0 else 0.0
    chain = alert.get("chain", "").lower()
    
    # Float Badge
    if liq_fdv >= 30.0:
        float_badge = f"🟢 Deep Float ({liq_fdv:.1f}%)"
    elif liq_fdv >= 15.0:
        float_badge = f"🟡 Tight Float ({liq_fdv:.1f}%)"
    else:
        float_badge = f"🔴 Thin Float ({liq_fdv:.1f}%)"
        
    # Suggested Trade Playbook
    if chain in ['robinhood', 'bsc']:
        tp_text = "TP1: +30% (Move SL to BE) | TP2: +80% | Moonbag: 20% trail"
        time_exit = "4.0 hours"
    else:
        tp_text = "TP1: +25% (Move SL to BE) | TP2: +60% | Moonbag: 15% trail"
        time_exit = "120 minutes (Solana runners peak at ~2h)"
        
    signals_formatted = "\n".join([f"  • {s}" for s in alert.get("signals", [])])
    
    msg = (
        f"🚨 *PRE-PUMP ALERT* [{score}/100]\n"
        f"🎯 *Setup:* `{setup}`\n\n"
        f"🪙 *Token:* `{alert.get('symbol')}` ({chain.upper()})\n"
        f"💵 *Price:* `${alert.get('price_usd')}`\n"
        f"💧 *Liquidity:* `${liq_usd:,.0f}`\n"
        f"📊 *FDV:* `${fdv:,.0f}` ({float_badge})\n\n"
        f"📈 *1h Volume:* `${alert.get('vol_1h', 0):,.0f}` (`{alert.get('vol_surge_ratio')}x` surge)\n"
        f"🛒 *1h Buys:* `{alert.get('buy_pct')}%` ({alert.get('buys_1h')}B / {alert.get('sells_1h')}S)\n"
        f"🕒 *1h Price Change:* `{alert.get('chg_1h'):+.1f}%`\n\n"
        f"🎯 *Key Trigger Signals:*\n{signals_formatted}\n\n"
        f"📋 *Trade Playbook:*\n"
        f"  • Targets: `{tp_text}`\n"
        f"  • Stop Loss: `-20.0%`\n"
        f"  • Time Stop: `{time_exit}`\n\n"
        f"🔗 [View on DexScreener]({alert.get('pair_url')})\n"
        f"📋 *Contract:* `{alert.get('token_address')}`"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if res_data.get("ok"):
                logger.info(f"Telegram alert dispatched for {alert.get('symbol')}")
                return True
            else:
                logger.error(f"Telegram API responded with error: {res_data}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
