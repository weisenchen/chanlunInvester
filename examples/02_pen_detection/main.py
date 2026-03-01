#!/usr/bin/env python3
"""
Example 2: Pen Detection (笔的识别)

Demonstrates:
- Connecting fractals to form pens
- New 3-K-line definition (新笔)
- Minimum K-line requirements
- Pen validation rules

This builds on Example 1 (Fractals) to form the next level of ChanLun structure.
"""

import sys
sys.path.insert(0, '../python-layer')

from datetime import datetime, timezone, timedelta
from trading_system.kline import Kline
from trading_system.fractal import FractalDetector, FractalType


def generate_pen_pattern() -> list:
    """Generate K-lines showing clear pen formation"""
    klines = []
    base_time = datetime.now(timezone.utc)
    
    # Pattern: Bottom fractal → Up pen → Top fractal → Down pen → Bottom fractal
    prices = [
        (100, 101, 98),    # 0 - start
        (98, 99, 95),      # 1 - bottom forming
        (95, 96, 92),      # 2 - BOTTOM FRACTAL (low point)
        (92, 95, 91),      # 3
        (95, 98, 94),      # 4
        (98, 102, 97),     # 5
        (102, 106, 101),   # 6 - TOP FRACTAL (high point)
        (106, 107, 103),   # 7
        (103, 104, 100),   # 8
        (100, 101, 97),    # 9
        (97, 98, 94),      # 10 - BOTTOM FRACTAL
        (94, 97, 93),      # 11
        (97, 100, 96),     # 12
        (100, 103, 99),    # 13
        (103, 105, 102),   # 14 - TOP FRACTAL
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


def identify_pens_from_fractals(klines: list, fractals: list) -> list:
    """
    Identify pens by connecting alternating fractals
    
    Pen rules (新笔 - New Definition):
    1. Must connect top fractal to bottom fractal (or vice versa)
    2. Minimum 3 K-lines between fractal points
    3. No overlapping price ranges (strict validation)
    """
    pens = []
    
    if len(fractals) < 2:
        return pens
    
    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]
        
        # Check minimum K-line separation (at least 3)
        kline_gap = abs(f2.index - f1.index)
        if kline_gap < 3:
            print(f"   ⚠️  Skipping: Only {kline_gap} K-lines between fractals (need ≥3)")
            continue
        
        # Check alternating types (top→bottom or bottom→top)
        if f1.type == f2.type:
            print(f"   ⚠️  Skipping: Same fractal types (need alternating)")
            continue
        
        # Valid pen found!
        pen_type = "UP" if f1.type == FractalType.BOTTOM else "DOWN"
        price_change = f2.high - f1.low if pen_type == "UP" else f2.low - f1.high
        
        pens.append({
            'type': pen_type,
            'start_fractal': f1,
            'end_fractal': f2,
            'start_price': f1.low if pen_type == "UP" else f1.high,
            'end_price': f2.high if pen_type == "UP" else f2.low,
            'kline_count': kline_gap + 1,
            'price_change': price_change,
        })
    
    return pens


def print_pens(pens: list):
    """Print identified pens"""
    if not pens:
        print("\n   No valid pens identified")
        return
    
    print("\n" + "=" * 70)
    print("Identified Pens (笔)")
    print("=" * 70)
    
    for i, pen in enumerate(pens, 1):
        direction = "📈" if pen['type'] == "UP" else "📉"
        change_pct = (pen['price_change'] / pen['start_price']) * 100
        
        print(f"\n{direction} Pen #{i} ({pen['type']})")
        print(f"   Start: Price {pen['start_price']:.2f} @ Index {pen['start_fractal'].index}")
        print(f"   End:   Price {pen['end_price']:.2f} @ Index {pen['end_fractal'].index}")
        print(f"   K-lines: {pen['kline_count']} (gap: {pen['kline_count'] - 1})")
        print(f"   Change: {pen['price_change']:+.2f} ({change_pct:+.1f}%)")


def main():
    print("\n" + "=" * 70)
    print("  ChanLun Invester - Example 2: Pen Detection")
    print("  缠论投资系统 - 示例 2: 笔的识别")
    print("=" * 70)
    
    # Generate sample data
    print("\n📈 Generating K-line data with pen patterns...")
    klines = generate_pen_pattern()
    print(f"   Generated {len(klines)} K-lines")
    
    # Step 1: Detect fractals
    print("\n🔍 Step 1: Detecting Fractals...")
    detector = FractalDetector()
    fractals = detector.detect_fractals(klines)
    
    print(f"   Found {len(fractals)} fractals:")
    tops = [f for f in fractals if f.type == FractalType.TOP]
    bottoms = [f for f in fractals if f.type == FractalType.BOTTOM]
    print(f"      🔴 Top fractals: {len(tops)}")
    print(f"      🟢 Bottom fractals: {len(bottoms)}")
    
    for f in fractals:
        marker = "🔴 TOP" if f.type == FractalType.TOP else "🟢 BOTTOM"
        price = f.high if f.type == FractalType.TOP else f.low
        print(f"      Index {f.index}: {price:.2f} {marker}")
    
    # Step 2: Form pens from fractals
    print("\n🔗 Step 2: Connecting Fractals to Form Pens...")
    print("   Rules (新笔 - New Definition):")
    print("      ✓ Alternating top/bottom fractals")
    print("      ✓ Minimum 3 K-lines between points")
    print("      ✓ No overlapping price ranges")
    
    pens = identify_pens_from_fractals(klines, fractals)
    
    # Step 3: Display results
    print_pens(pens)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Example 2 Complete!")
    print("\nKey Learnings:")
    print("   1. Pens connect alternating fractals (top↔bottom)")
    print("   2. New definition requires minimum 3 K-lines (Lesson 65)")
    print("   3. Up pen: Bottom fractal → Top fractal (low to high)")
    print("   4. Down pen: Top fractal → Bottom fractal (high to low)")
    print("   5. Pens are the building blocks for segments (线段)")
    print("\nNext: Example 3 - Segment Division (线段的划分)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
