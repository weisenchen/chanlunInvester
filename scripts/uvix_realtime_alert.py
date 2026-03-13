#!/usr/bin/env python3
"""
UVIX Real-time Alert System
Sends immediate Telegram alerts when buy/sell points are detected
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from uvix_monitor import fetch_uvix_data, ChanLunAnalyzer


def send_telegram_alert(message: str) -> bool:
    """Send alert via OpenClaw message tool"""
    try:
        # Use message tool directly via subprocess with timeout
        result = subprocess.run([
            'openclaw', 'message', 'send',
            '-t', 'telegram',
            '-m', message
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ Alert sent successfully")
            return True
        else:
            print(f"✗ Alert failed: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ Alert timeout")
        return False
    except Exception as e:
        print(f"✗ Alert error: {e}")
        return False


def check_and_alert():
    """Check for buy/sell points and send alerts"""
    
    print(f"\n{'='*70}")
    print(f"UVIX Real-time Alert Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"{'='*70}\n")
    
    # Fetch data for all levels
    levels = ['day', '30m', '5m']
    alerts = []
    
    for level in levels:
        print(f"[{level}] Analyzing...")
        
        try:
            series = fetch_uvix_data('UVIX', count=200, timeframe=level)
            analyzer = ChanLunAnalyzer({'macd_params': {'fast': 12, 'slow': 26, 'signal': 9}})
            result = analyzer.analyze(series)
            
            # Check for buy/sell points
            bsp_list = result['analysis'].get('buy_sell_points', [])
            divergence = result['analysis'].get('divergence', {})
            
            if bsp_list or divergence.get('detected'):
                print(f"  🚨 SIGNAL DETECTED!")
                
                for bsp in bsp_list:
                    alert = format_alert(level, bsp, result['operation_suggestion'])
                    alerts.append(alert)
                    
                if divergence.get('detected') and not bsp_list:
                    alert = format_divergence_alert(level, divergence)
                    alerts.append(alert)
            else:
                print(f"  ✓ No signals")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Send alerts
    if alerts:
        print(f"\n🚨 Sending {len(alerts)} alert(s)...\n")
        
        for alert in alerts:
            send_telegram_alert(alert)
            
        # Log alerts
        log_alerts(alerts)
        
        return True
    else:
        print(f"\n✓ No buy/sell points detected")
        return False


def format_alert(level: str, bsp: dict, suggestion: dict) -> str:
    """Format buy/sell point alert"""
    
    emoji = "🟢" if 'buy' in bsp['type_en'].lower() else "🔴"
    action = suggestion['action']
    
    alert = f"""{emoji} *UVIX Buy/Sell Alert - {level.upper()}*

📊 *Type:* {bsp['type']}
💰 *Price:* ${bsp['price']:.2f}
📈 *Confidence:* {bsp['confidence']:.0%}
📝 *Signal:* {bsp['description']}

*Operation:* {action}
"""
    
    if action == 'BUY':
        alert += f"""
💵 *Entry:* ${suggestion.get('price', bsp['price']):.2f}
🛑 *Stop Loss:* ${suggestion.get('stop_loss', bsp['price'] * 0.95):.2f} (-5%)
🎯 *Target:* ${suggestion.get('target', bsp['price'] * 1.10):.2f} (+10%)
"""
    elif action == 'SELL':
        alert += f"""
💵 *Entry:* ${suggestion.get('price', bsp['price']):.2f}
🛑 *Stop Loss:* ${suggestion.get('stop_loss', bsp['price'] * 1.05):.2f} (+5%)
🎯 *Target:* ${suggestion.get('target', bsp['price'] * 0.90):.2f} (-10%)
"""
    
    alert += f"""
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST
📚 *Reference:* ChanLun Lesson 12, 24

⚠️ Disclaimer: For reference only, not investment advice"""
    
    return alert


def format_divergence_alert(level: str, divergence: dict) -> str:
    """Format divergence alert"""
    
    signal_type = "🟢 BUY" if divergence['signal'] == 'buy' else "🔴 SELL"
    div_type = "Bottom Divergence" if divergence['type'] == 'bottom_divergence' else "Top Divergence"
    
    alert = f"""🚨 *UVIX Divergence Alert - {level.upper()}*

📊 *Type:* {div_type}
💰 *Price:* ${divergence.get('price_high' if divergence['signal'] == 'sell' else 'price_low', 0):.2f}
📈 *Strength:* {divergence['strength']:.2f}
🎯 *Signal:* {signal_type}

⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST

⚠️ Monitor for potential buy/sell point formation"""
    
    return alert


def log_alerts(alerts: list):
    """Log alerts to file"""
    log_file = Path(__file__).parent.parent / 'logs' / 'realtime_alerts.log'
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"Alerts sent: {len(alerts)}\n")
        for alert in alerts:
            f.write(f"\n{alert}\n")


if __name__ == '__main__':
    has_signals = check_and_alert()
    sys.exit(0 if has_signals else 1)
