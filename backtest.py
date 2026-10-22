"""
Historical Performance & Strategy Backtest Engine
Evaluates DEX scanner Telegram alerts against on-chain outcomes,
identifies 100%+ pumpers, and evaluates positive EV trading strategies.
"""

import os
import re
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any

def load_and_parse_alerts(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    messages = data.get('messages', []) if isinstance(data, dict) else data
    alerts = []
    
    for msg in messages:
        text = ''
        if isinstance(msg.get('text'), list):
            for part in msg['text']:
                if isinstance(part, str): text += part
                elif isinstance(part, dict) and 'text' in part: text += part['text']
        elif isinstance(msg.get('text'), str):
            text = msg['text']
            
        if 'ALERT' not in text and 'WATCHLIST' not in text:
            continue
            
        # Regex parsers
        score_m = re.search(r'(?:ALERT|WATCHLIST)\s+(\d+)/100', text)
        token_m = re.search(r'Token:\s*([^\n\r\(]+)\s*\(([^\)]+)\)', text)
        price_m = re.search(r'Price:\s*\$([0-9\.eE\-]+)', text)
        liq_m = re.search(r'Liquidity:\s*\$([0-9,]+)', text)
        fdv_m = re.search(r'FDV:\s*\$([0-9,]+)', text)
        vol_m = re.search(r'1h Volume Surge:\s*([0-9\.]+)x\s*\(\$1h:\s*\$([0-9,]+)\)', text)
        buys_m = re.search(r'1h Buys:\s*([0-9\.]+)%\s*\((\d+)\s*Buys\s*/\s*(\d+)\s*Sells\)', text)
        chg_m = re.search(r'1h Price Change:\s*([+\-0-9\.]+)%', text)
        contract_m = re.search(r'Contract:\s*([a-zA-Z0-9_]+)', text)
        
        fdv = float(fdv_m.group(1).replace(',', '')) if fdv_m else 0.0
        liq = float(liq_m.group(1).replace(',', '')) if liq_m else 0.0
        liq_fdv = (liq / fdv * 100.0) if fdv > 0 else 0.0
        
        alerts.append({
            'id': msg.get('id'),
            'date': msg.get('date'),
            'date_unix': int(msg.get('date_unixtime', 0)),
            'token': token_m.group(1).strip() if token_m else 'UNKNOWN',
            'chain': token_m.group(2).strip().lower() if token_m else 'unknown',
            'score': int(score_m.group(1)) if score_m else 50,
            'price': float(price_m.group(1)) if price_m else 0.0,
            'liq': liq,
            'fdv': fdv,
            'liq_fdv': liq_fdv,
            'vol_surge': float(vol_m.group(1)) if vol_m else 0.0,
            'vol_1h': float(vol_m.group(2).replace(',', '')) if vol_m else 0.0,
            'buys_pct': float(buys_m.group(1)) if buys_m else 0.0,
            'buys_count': int(buys_m.group(2)) if buys_m else 0,
            'sells_count': int(buys_m.group(3)) if buys_m else 0,
            'chg_1h': float(chg_m.group(1)) if chg_m else 0.0,
            'contract': contract_m.group(1).strip() if contract_m else ''
        })
        
    return alerts

def main():
    print("=" * 65)
    print("      DEX PUMP SCANNER QUANTITATIVE BACKTEST SUMMARY")
    print("=" * 65)
    
    # Check if pre-parsed data exists
    if os.path.exists('parsed_alerts.json') and os.path.exists('live_pairs.json'):
        with open('parsed_alerts.json', 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        with open('live_pairs.json', 'r', encoding='utf-8') as f:
            live = json.load(f)
    else:
        print("Pre-calculated alerts or live pair data not found. Run scanner or provide dataset.")
        return

    trajs = {}
    if os.path.exists('trajectories.json'):
        with open('trajectories.json', 'r', encoding='utf-8') as f:
            trajs = {t['token']: t for t in json.load(f)}

    rows = []
    for a in alerts:
        c = a['contract']
        p = live.get(c)
        if not p:
            for k, v in live.items():
                if k.lower() == c.lower(): p = v; break
                
        p_now = float(p.get('priceUsd') or 0.0) if p else 0.0
        ret_now = ((p_now - a['price']) / a['price'] * 100.0) if a['price'] > 0 and p_now > 0 else -100.0
        t = trajs.get(a['token'])
        max_g = t['max_gain_pct'] if t else max(0.0, ret_now)
        
        created_at = p.get('pairCreatedAt') if p else None
        age_h = (a['date_unix'] - (created_at / 1000.0)) / 3600.0 if created_at else None
        
        rows.append({
            'token': a['token'],
            'chain': a['chain'].lower(),
            'score': a['score'],
            'price': a['price'],
            'fdv': a['fdv'],
            'liq': a['liq'],
            'liq_fdv': a['liq'] / a['fdv'] * 100.0 if a['fdv'] > 0 else 0.0,
            'vol_1h': a['vol_1h'],
            'vol_surge': a['vol_surge'],
            'buys_pct': a['buys_pct'],
            'chg_1h': a['chg_1h'],
            'age_hours': age_h,
            'ret_now': ret_now,
            'max_gain': max_g,
            'is_100': max_g >= 100.0,
            'is_50': max_g >= 50.0,
            'is_rug': (ret_now <= -80.0) or ((p.get('liquidity') or {}).get('usd', 0) < 3500) if p else True
        })
        
    df = pd.DataFrame(rows)
    tokens_df = df.sort_values('max_gain', ascending=False).drop_duplicates('token')
    
    print(f"\nTotal Alerts Analyzed: {len(df)}")
    print(f"Total Unique Tokens:   {len(tokens_df)}")
    print(f"Tokens >= +100% Gain:  {tokens_df['is_100'].sum()} ({tokens_df['is_100'].mean()*100:.1f}%)")
    print(f"Tokens >= +50% Gain:   {tokens_df['is_50'].sum()} ({tokens_df['is_50'].mean()*100:.1f}%)")
    print(f"Tokens Rugged / Dead:  {tokens_df['is_rug'].sum()} ({tokens_df['is_rug'].mean()*100:.1f}%)")
    
    print("\n--- Key Metrics by Chain ---")
    chain_summary = tokens_df.groupby('chain').agg(
        tokens=('token', 'count'),
        doublers=('is_100', 'sum'),
        rug_rate=('is_rug', lambda x: f"{x.mean()*100:.1f}%"),
        med_return=('ret_now', lambda x: f"{x.median():+.1f}%")
    )
    print(chain_summary)
    
if __name__ == '__main__':
    main()
