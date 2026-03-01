#!/usr/bin/env python3
"""
Example 5: Buy/Sell Points Detection (买卖点识别)

Demonstrates:
- First Buy/Sell Points (1 买/1 卖) - divergence-based
- Second Buy/Sell Points (2 买/2 卖) - pullback patterns
- Third Buy/Sell Points (3 买/3 卖) - center break (conceptual)
- Confidence scoring
- Risk/reward analysis

This is where ChanLun theory meets actionable trading signals.
"""

import sys
sys.path.insert(0, '../python-layer')

from datetime import datetime, timezone, timedelta
from trading_system.kline import Kline
from trading_system.fractal import FractalDetector, FractalType


class SimpleBSPDetector:
    """Simplified B/S point detector for demonstration"""
    
    def detect_bsp1(self, fractals: list, with_divergence: bool = True) -> list:
        """
        Detect First Buy/Sell Points (1 买/1 卖)
        
        Rules:
        - 1 Buy: Bottom fractal after downtrend, ideally with bullish divergence
        - 1 Sell: Top fractal after uptrend, ideally with bearish divergence
        """
        bsps = []
        
        for i, f in enumerate(fractals):
            # Look for extreme points (potential 1st B/S)
            if i >= 2:  # Need history
                prev_fractals = fractals[:i]
                
                if f.type == FractalType.BOTTOM:
                    # Check if this is lowest low in recent fractals
                    recent_lows = [fr.low for fr in prev_fractals[-3:] if fr.type == FractalType.BOTTOM]
                    if recent_lows and f.low <= min(recent_lows):
                        confidence = 0.7
                        if with_divergence:
                            confidence += 0.15  # Boost if we had MACD divergence
                        bsps.append({
                            'type': '1 买 (Buy1)',
                            'price': f.low,
                            'index': f.index,
                            'confidence': min(confidence, 1.0),
                            'reason': 'New low in downtrend (potential reversal)'
                        })
                
                elif f.type == FractalType.TOP:
                    # Check if this is highest high in recent fractals
                    recent_highs = [fr.high for fr in prev_fractals[-3:] if fr.type == FractalType.TOP]
                    if recent_highs and f.high >= max(recent_highs):
                        confidence = 0.7
                        if with_divergence:
                            confidence += 0.15
                        bsps.append({
                            'type': '1 卖 (Sell1)',
                            'price': f.high,
                            'index': f.index,
                            'confidence': min(confidence, 1.0),
                            'reason': 'New high in uptrend (potential reversal)'
                        })
        
        return bsps
    
    def detect_bsp2(self, fractals: list) -> list:
        """
        Detect Second Buy/Sell Points (2 买/2 卖)
        
        Rules:
        - 2 Buy: Pullback after 1 Buy, doesn't make new low
        - 2 Sell: Rally after 1 Sell, doesn't make new high
        """
        bsps = []
        bsp1_points = self.detect_bsp1(fractals, with_divergence=False)
        
        if not bsp1_points:
            return bsps
        
        for bsp1 in bsp1_points:
            # Look for subsequent fractals
            bsp1_idx = next((i for i, f in enumerate(fractals) 
                           if f.index == bsp1['index']), None)
            
            if bsp1_idx is None or bsp1_idx >= len(fractals) - 1:
                continue
            
            # Check next fractal for pullback pattern
            for j in range(bsp1_idx + 1, min(bsp1_idx + 4, len(fractals))):
                f = fractals[j]
                
                if 'Buy' in bsp1['type'] and f.type == FractalType.BOTTOM:
                    # Check if pullback doesn't make new low
                    if f.low > bsp1['price']:
                        pullback_pct = ((f.low - bsp1['price']) / bsp1['price']) * 100
                        bsps.append({
                            'type': '2 买 (Buy2)',
                            'price': f.low,
                            'index': f.index,
                            'confidence': 0.75,
                            'reason': f'Pullback without new low (+{pullback_pct:.1f}%)'
                        })
                        break
                
                elif 'Sell' in bsp1['type'] and f.type == FractalType.TOP:
                    # Check if rally doesn't make new high
                    if f.high < bsp1['price']:
                        pullback_pct = ((bsp1['price'] - f.high) / bsp1['price']) * 100
                        bsps.append({
                            'type': '2 卖 (Sell2)',
                            'price': f.high,
                            'index': f.index,
                            'confidence': 0.75,
                            'reason': f'Rally without new high (-{pullback_pct:.1f}%)'
                        })
                        break
        
        return bsps


def generate_bsp_pattern() -> list:
    """Generate K-lines showing B/S point patterns"""
    klines = []
    base_time = datetime.now(timezone.utc)
    
    # Downtrend → 1 Buy → Pullback → 2 Buy → Uptrend → 1 Sell → Rally → 2 Sell
    prices = [
        (110, 112, 108),   # 0
        (108, 109, 105),   # 1
        (105, 106, 100),   # 2 - low (potential 1 买)
        (100, 103, 99),    # 3
        (103, 107, 102),   # 4
        (107, 110, 106),   # 5
        (110, 112, 108),   # 6 - pullback high
        (108, 109, 105),   # 7 - higher low (potential 2 买)
        (105, 108, 104),   # 8
        (108, 112, 107),   # 9
        (112, 116, 111),   # 10
        (116, 120, 115),   # 11 - high (potential 1 卖)
        (120, 122, 118),   # 12
        (118, 119, 115),   # 13
        (115, 117, 112),   # 14
        (117, 118, 114),   # 15 - lower high (potential 2 卖)
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


def print_bsps(bsps: list):
    """Print buy/sell points"""
    if not bsps:
        print("\n   No B/S points identified")
        return
    
    print("\n" + "=" * 70)
    print("Buy/Sell Points (买卖点)")
    print("=" * 70)
    
    # Group by type
    buy1 = [b for b in bsps if 'Buy1' in b['type']]
    buy2 = [b for b in bsps if 'Buy2' in b['type']]
    sell1 = [b for b in bsps if 'Sell1' in b['type']]
    sell2 = [b for b in bsps if 'Sell2' in b['type']]
    
    for label, points in [("1 买 (First Buy)", buy1), ("2 买 (Second Buy)", buy2),
                          ("1 卖 (First Sell)", sell1), ("2 卖 (Second Sell)", sell2)]:
        if points:
            print(f"\n{label}:")
            for p in points:
                conf_bar = "█" * int(p['confidence'] * 10)
                print(f"   📍 Index {p['index']}: Price {p['price']:.2f}")
                print(f"      Confidence: [{conf_bar:<10}] {p['confidence']*100:.0f}%")
                print(f"      Reason: {p['reason']}")


def main():
    print("\n" + "=" * 70)
    print("  ChanLun Invester - Example 5: Buy/Sell Points Detection")
    print("  缠论投资系统 - 示例 5: 买卖点识别")
    print("=" * 70)
    
    # Generate sample data
    print("\n📈 Generating K-line data with B/S patterns...")
    klines = generate_bsp_pattern()
    print(f"   Generated {len(klines)} K-lines")
    
    # Step 1: Detect fractals
    print("\n🔍 Step 1: Detecting Fractals (foundation)...")
    detector = FractalDetector()
    fractals = detector.detect_fractals(klines)
    print(f"   Found {len(fractals)} fractals")
    
    # Step 2: Detect 1st B/S Points
    print("\n🎯 Step 2: Detecting First B/S Points (1 买/1 卖)...")
    bsp_detector = SimpleBSPDetector()
    bsp1_points = bsp_detector.detect_bsp1(fractals, with_divergence=True)
    print(f"   Found {len(bsp1_points)} potential 1st B/S points")
    
    # Step 3: Detect 2nd B/S Points
    print("\n🎯 Step 3: Detecting Second B/S Points (2 买/2 卖)...")
    bsp2_points = bsp_detector.detect_bsp2(fractals)
    print(f"   Found {len(bsp2_points)} potential 2nd B/S points")
    
    # Step 4: Display all B/S points
    all_bsps = bsp1_points + bsp2_points
    print_bsps(all_bsps)
    
    # Trading strategy summary
    print("\n" + "=" * 70)
    print("📊 Trading Strategy Summary")
    print("=" * 70)
    
    if bsp1_points:
        print("\n💡 1st Buy/Sell Strategy:")
        print("   - Enter at divergence confirmation")
        print("   - Stop loss: Below/Above fractal low/high")
        print("   - Target: Next resistance/support level")
        print("   - Risk/Reward: Typically 1:2 or better")
    
    if bsp2_points:
        print("\n💡 2nd Buy/Sell Strategy:")
        print("   - Enter on pullback confirmation")
        print("   - Stop loss: Below/Above pullback point")
        print("   - Target: Previous high/low")
        print("   - Risk/Reward: Typically 1:3 (better than 1st)")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Example 5 Complete!")
    print("\nKey Learnings:")
    print("   1. 1st B/S points occur at trend extremes (with divergence)")
    print("   2. 2nd B/S points offer better risk/reward on pullbacks")
    print("   3. 3rd B/S points require center (中枢) analysis")
    print("   4. Confidence scoring helps prioritize signals")
    print("   5. Always use stop losses and position sizing")
    print("\nNext: Example 6 - Multi-Level Divergence Analysis")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
