import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("telegram_notifier")

def send_telegram_alert(bot_token: str, chat_id: str, alert: Dict[str, Any]) -> bool:
    """
    Sends a formatted Markdown alert to a Telegram channel or group.
    """
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token or Chat ID not configured. Skipping alert dispatch.")
        return False
        
    score = alert.get("score", 0)
    tag = "🚨 *HIGH PROBABILITY PRE-PUMP ALERT*" if score >= 60 else "⚡ *PRE-PUMP WATCHLIST*"
    
    signals_formatted = "\n".join([f"  • {s}" for s in alert.get("signals", [])])
    
    msg = (
        f"{tag} [{score}/100]\n\n"
        f"🪙 *Token:* `{alert.get('symbol')}` ({alert.get('chain', '').upper()})\n"
        f"💵 *Price:* `${alert.get('price_usd')}`\n"
        f"💧 *Liquidity:* `${alert.get('liquidity_usd', 0):,.0f}`\n"
        f"📊 *FDV:* `${alert.get('fdv', 0):,.0f}`\n\n"
        f"📈 *1h Volume Surge:* `{alert.get('vol_surge_ratio')}x` ($1h: `${alert.get('vol_1h', 0):,.0f}`)\n"
        f"🛒 *1h Buys:* `{alert.get('buy_pct')}%` ({alert.get('buys_1h')} Buys / {alert.get('sells_1h')} Sells)\n"
        f"🕒 *1h Price Change:* `{alert.get('chg_1h'):+.1f}%`\n\n"
        f"🎯 *Key Trigger Signals:*\n{signals_formatted}\n\n"
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
                logger.info(f"Telegram alert sent successfully for {alert.get('symbol')}")
                return True
            else:
                logger.error(f"Telegram API responded with error: {res_data}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False
