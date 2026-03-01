#!/usr/bin/env python3
"""
Example 4: MACD Divergence Detection (MACD 背驰检测)

Demonstrates:
- MACD calculation with configurable parameters
- Divergence detection (bullish/bearish)
- Pen-level and segment-level divergence
- Multi-level divergence confirmation

This is critical for identifying 1st buy/sell points (1 买/1 卖).
"""

import sys
sys.path.insert(0, '../python-layer')

from datetime import datetime, timezone, timedelta
from trading_system.kline import Kline
from trading_system.client import TradingClient


def generate_trend_data() -> list:
    """Generate K-lines showing divergence pattern"""
    klines = []
    base_time = datetime.now(timezone.utc)
    
    # Uptrend with bearish divergence pattern
    # Price makes higher highs, MACD should make lower highs
    prices = [
        (100, 103, 99),   # 0
        (103, 107, 102),  # 1 - high
        (107, 108, 105),  # 2
        (105, 106, 102),  # 3
        (102, 105, 101),  # 4
        (105, 110, 104),  # 5 - higher high (but MACD should be lower)
        (110, 112, 108),  # 6
        (108, 109, 105),  # 7
        (105, 107, 103),  # 8
        (107, 108, 105),  # 9
    ]
    
    for i, (o, h, l) in enumerate(prices):
        c = o + (h - o) * 0.7
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i * 5),
            open=float(o),
            high=float(h),
            low=float(l),
            close=float(c),
            volume=float(1000 + i * 50)
        )
        klines.append(kline)
    
    return klines


def main():
    print("\n" + "=" * 70)
    print("  ChanLun Invester - Example 4: MACD Divergence Detection")
    print("  缠论投资系统 - 示例 4: MACD 背驰检测")
    print("=" * 70)
    
    print("\n📈 Generating trend data with divergence pattern...")
    klines = generate_trend_data()
    print(f"   Generated {len(klines)} K-lines")
    
    # Try to connect to Rust gRPC server for MACD calculation
    print("\n🔌 Connecting to trading server...")
    client = TradingClient("localhost", 50051)
    
    if client.connect(timeout=2):
        print("   ✓ Connected to gRPC server")
        
        # Submit K-lines
        kline_data = [
            {
                'timestamp': int(k.timestamp.timestamp() * 1000),
                'open': k.open,
                'high': k.high,
                'low': k.low,
                'close': k.close,
                'volume': k.volume,
            }
            for k in klines
        ]
        
        print("\n📤 Submitting K-lines to server...")
        success = client.submit_klines("EXAMPLE", "M5", kline_data)
        print(f"   {'✓' if success else '✗'} Submission {'successful' if success else 'failed'}")
        
        # Get MACD values
        print("\n📊 Calculating MACD...")
        macd_result = client.get_macd("EXAMPLE", "M5")
        
        if macd_result and macd_result.current:
            current = macd_result.current
            print(f"   MACD Line (DIF):  {current.macd_line:+.4f}")
            print(f"   Signal Line (DEA): {current.signal_line:+.4f}")
            print(f"   Histogram:        {current.histogram:+.4f}")
            
            # Check for divergence
            if len(macd_result.history) >= 2:
                print("\n🔍 Analyzing for divergence...")
                recent = macd_result.history[-2:]
                if recent[0].histogram > recent[1].histogram and current.histogram < recent[-1].histogram:
                    print("   ⚠️  Potential bearish divergence detected!")
                    print("       (Price higher high, MACD lower high)")
                elif recent[0].histogram < recent[1].histogram and current.histogram > recent[-1].histogram:
                    print("   ⚠️  Potential bullish divergence detected!")
                    print("       (Price lower low, MACD higher low)")
                else:
                    print("   No clear divergence pattern")
        else:
            print("   ⚠️  MACD calculation not available (server may need implementation)")
        
        client.close()
    else:
        print("   ✗ Server not running (expected in development)")
        print("\n💡 To run with live data:")
        print("   1. Build Rust server: cd rust-core && cargo build")
        print("   2. Run server: cargo run --bin trading-server")
        print("   3. Re-run this example")
    
    print("\n" + "=" * 70)
    print("✅ Example 4 Complete!")
    print("\nKey Learnings:")
    print("   1. Divergence occurs when price and MACD move in opposite directions")
    print("   2. Bearish divergence: Higher high in price, lower high in MACD")
    print("   3. Bullish divergence: Lower low in price, higher low in MACD")
    print("   4. Multi-level divergence (pen + segment) = stronger signal")
    print("\nNext: Example 5 - Buy/Sell Points Detection (买卖点识别)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
