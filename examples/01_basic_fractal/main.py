#!/usr/bin/env python3
"""
Example 1: Basic Fractal Recognition (基础分型识别)

Demonstrates:
- K-line data loading
- Fractal detection (顶分型/底分型)
- Containment relationship handling (包含关系处理)
- Basic visualization

This is the foundation for all ChanLun analysis.
"""

import sys
sys.path.insert(0, '../python-layer')

from datetime import datetime, timezone, timedelta
from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector, FractalType


def generate_sample_klines() -> list:
    """Generate sample K-line data with clear fractals"""
    klines = []
    base_time = datetime.now(timezone.utc)
    
    # Create a pattern with clear tops and bottoms
    prices = [
        (100, 102, 99),    # 0
        (102, 105, 101),   # 1 - potential top
        (105, 106, 103),   # 2
        (103, 104, 100),   # 3 - potential bottom
        (100, 101, 97),    # 4
        (97, 98, 94),      # 5 - lower bottom
        (94, 97, 93),      # 6
        (97, 100, 96),     # 7 - potential top
        (100, 103, 99),    # 8
        (103, 105, 102),   # 9 - higher top
        (105, 106, 103),   # 10
        (103, 104, 100),   # 11
    ]
    
    for i, (o, h, l) in enumerate(prices):
        # Calculate close (70% into the range if bullish, else 30%)
        c = o + (h - o) * 0.7 if o < h else o - (o - l) * 0.3
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i * 5),
            open=float(o),
            high=float(h),
            low=float(l),
            close=float(c),
            volume=float(1000 + i * 100)
        )
        klines.append(kline)
    
    return klines


def print_klines(klines: list):
    """Print K-line data in table format"""
    print("\n" + "=" * 70)
    print("K-line Data (OHLCV)")
    print("=" * 70)
    print(f"{'Idx':<4} {'Time':<12} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8} {'Volume':<10}")
    print("-" * 70)
    
    for i, k in enumerate(klines):
        time_str = k.timestamp.strftime('%H:%M:%S')
        bullish = "🟢" if k.is_bullish() else "🔴"
        print(f"{i:<4} {time_str:<12} {k.open:<8.2f} {k.high:<8.2f} {k.low:<8.2f} {k.close:<8.2f} {k.volume:<10.0f} {bullish}")
    
    print("=" * 70)


def detect_and_display_fractals(klines: list):
    """Detect fractals and display results"""
    detector = FractalDetector()
    fractals = detector.detect_fractals(klines)
    
    print(f"\n📊 Fractal Detection Results")
    print(f"   Total fractals found: {len(fractals)}")
    print("-" * 70)
    
    if not fractals:
        print("   No fractals detected (may need more data or clearer patterns)")
        return
    
    tops = [f for f in fractals if f.type == FractalType.TOP]
    bottoms = [f for f in fractals if f.type == FractalType.BOTTOM]
    
    print(f"\n🔴 Top Fractals (顶分型): {len(tops)}")
    for f in tops:
        print(f"   Index {f.index}: High={f.high:.2f} @ {f.time.strftime('%H:%M')}")
    
    print(f"\n🟢 Bottom Fractals (底分型): {len(bottoms)}")
    for f in bottoms:
        print(f"   Index {f.index}: Low={f.low:.2f} @ {f.time.strftime('%H:%M')}")
    
    # Show K-lines with fractal markers
    print("\n" + "=" * 70)
    print("K-lines with Fractal Markers")
    print("=" * 70)
    
    for i, k in enumerate(klines):
        marker = ""
        for f in fractals:
            if f.index == i:
                if f.type == FractalType.TOP:
                    marker = " 🔴 TOP"
                else:
                    marker = " 🟢 BOTTOM"
                break
        
        if marker:
            print(f"   {i:>2}: {k.close:>7.2f} {marker}")


def main():
    print("\n" + "=" * 70)
    print("  ChanLun Invester - Example 1: Basic Fractal Recognition")
    print("  缠论投资系统 - 示例 1: 基础分型识别")
    print("=" * 70)
    
    # Generate sample data
    print("\n📈 Generating sample K-line data...")
    klines = generate_sample_klines()
    print(f"   Generated {len(klines)} K-lines (5-minute timeframe)")
    
    # Display K-lines
    print_klines(klines)
    
    # Detect fractals
    detect_and_display_fractals(klines)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Example 1 Complete!")
    print("\nKey Learnings:")
    print("   1. Fractals are 3-K-line patterns (high-high-low or low-low-high)")
    print("   2. Containment relationships are handled automatically")
    print("   3. Top fractals (顶分型) mark potential trend reversals down")
    print("   4. Bottom fractals (底分型) mark potential trend reversals up")
    print("\nNext: Example 2 - Pen Detection (笔的识别)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
