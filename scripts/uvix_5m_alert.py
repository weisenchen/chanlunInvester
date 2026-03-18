#!/usr/bin/env python3
"""
UVIX 5-Minute Buy/Sell Price Alert
Real-time analysis with specific price levels
"""

import yfinance as yf
from datetime import datetime

def get_uvix_5m_data():
    """Fetch UVIX 5-minute data from Yahoo Finance"""
    uvix = yf.Ticker('UVIX')
    history = uvix.history(period='5d', interval='5m')
    return history

def analyze_levels(history):
    """Calculate key price levels"""
    
    # Current price
    current_price = float(history['Close'].iloc[-1])
    
    # Recent support/resistance
    recent_high = float(history['High'].tail(20).max())
    recent_low = float(history['Low'].tail(20).min())
    
    # Moving averages
    ma_20 = float(history['Close'].tail(20).mean())
    ma_50 = float(history['Close'].tail(50).mean())
    
    # Fibonacci levels (from recent swing)
    swing_high = recent_high
    swing_low = recent_low
    diff = swing_high - swing_low
    
    fib_236 = swing_high - (diff * 0.236)
    fib_382 = swing_high - (diff * 0.382)
    fib_500 = swing_high - (diff * 0.500)
    fib_618 = swing_high - (diff * 0.618)
    
    return {
        'current': current_price,
        'resistance': [recent_high, fib_236, fib_382],
        'support': [fib_618, fib_500, recent_low],
        'ma_20': ma_20,
        'ma_50': ma_50
    }

def generate_alerts(levels):
    """Generate buy/sell alerts based on levels"""
    
    current = levels['current']
    
    print("\n" + "="*70)
    print("🚨 UVIX 5-Minute Price Alert System")
    print("="*70)
    print(f"\n📊 Current Price: ${current:.2f}")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    
    print(f"\n{'='*70}")
    print("📈 SELL ZONES (Resistance)")
    print(f"{'='*70}")
    for i, level in enumerate(levels['resistance'], 1):
        distance = ((level - current) / current) * 100
        if current >= level * 0.98:
            print(f"🔴 SELL Zone {i}: ${level:.2f} (+{distance:.1f}%) ⚠️ NEAR!")
        else:
            print(f"   Resistance {i}: ${level:.2f} (+{distance:.1f}%)")
    
    print(f"\n{'='*70}")
    print("📉 BUY ZONES (Support)")
    print(f"{'='*70}")
    for i, level in enumerate(levels['support'], 1):
        distance = ((current - level) / current) * 100
        if current <= level * 1.02:
            print(f"🟢 BUY Zone {i}: ${level:.2f} (+{distance:.1f}%) ⚠️ NEAR!")
        else:
            print(f"   Support {i}: ${level:.2f} (+{distance:.1f}%)")
    
    print(f"\n{'='*70}")
    print("📊 Key Levels")
    print(f"{'='*70}")
    print(f"  MA20: ${levels['ma_20']:.2f}")
    print(f"  MA50: ${levels['ma_50']:.2f}")
    
    # Trading signals
    print(f"\n{'='*70}")
    print("🎯 Trading Signals")
    print(f"{'='*70}")
    
    if current <= levels['support'][0] * 1.01:
        print("  🟢 STRONG BUY - At key support level")
        print(f"     Entry: ${current:.2f}")
        print(f"     Stop:  ${levels['support'][0] * 0.97:.2f} (-3%)")
        print(f"     Target: ${levels['resistance'][0]:.2f} (+{(levels['resistance'][0]/current-1)*100:.1f}%)")
    elif current >= levels['resistance'][0] * 0.99:
        print("  🔴 STRONG SELL - At key resistance")
        print(f"     Entry: ${current:.2f}")
        print(f"     Stop:  ${levels['resistance'][0] * 1.03:.2f} (+3%)")
        print(f"     Target: ${levels['support'][0]:.2f} (-{(1-levels['support'][0]/current)*100:.1f}%)")
    elif current > levels['ma_20']:
        print("  🟢 BULLISH - Above MA20")
        print(f"     Watch for pullback to ${levels['ma_20']:.2f} for entry")
    elif current < levels['ma_20']:
        print("  🔴 BEARISH - Below MA20")
        print(f"     Watch for rally to ${levels['ma_20']:.2f} for exit")
    else:
        print("  ⚪ NEUTRAL - Wait for clearer signal")
    
    print(f"\n{'='*70}")
    print("⚠️  Risk Management")
    print(f"{'='*70}")
    print("  • Never risk more than 2% per trade")
    print("  • Always use stop loss")
    print("  • UVIX is highly volatile - use smaller position sizes")
    print("  • This is NOT financial advice - do your own research")
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    try:
        history = get_uvix_5m_data()
        levels = analyze_levels(history)
        generate_alerts(levels)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Please check internet connection and try again")
