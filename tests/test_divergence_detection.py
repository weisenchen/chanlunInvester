#!/usr/bin/env python3
"""
Divergence Detection Tests - 缠论背驰多方法检测测试
Tests: Point method, Area method, DIF method, zero-pullback check, segment divergence
"""
import sys
import os
import math
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector, Fractal
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator, Segment
from trading_system.indicators import MACDIndicator
from trading_system.center import CenterDetector, Center
from trading_system.divergence import DivergenceDetector, DivergenceResult, ZeroPullbackResult


def create_oscillation_series(phases=None, timeframe="30m", count_per_phase=20):
    """Create structured price data with clear peaks/valleys for fractal detection."""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    if phases is None:
        phases = [(100, 100, 3.0)]
    idx = 0
    for start_p, end_p, vol in phases:
        for i in range(count_per_phase):
            t = i / count_per_phase
            base = start_p + (end_p - start_p) * t
            wave1 = math.sin(t * 4 * math.pi) * vol * 0.3
            wave2 = math.sin(t * 2 * math.pi + 0.5) * vol * 0.15
            mid = base + wave1 + wave2
            body = abs(random.uniform(0.1, 0.5))
            upper_shadow = random.uniform(0.0, 0.8)
            lower_shadow = random.uniform(0.0, 0.8)
            o = mid - body / 2 + random.uniform(-0.1, 0.1)
            c = mid + body / 2 + random.uniform(-0.1, 0.1)
            h = max(o, c) + upper_shadow
            l = min(o, c) - lower_shadow
            klines.append(Kline(
                timestamp=base_time + timedelta(minutes=idx*30 if timeframe == "30m" else idx*5),
                open=round(o, 2), high=round(h, 2), low=round(l, 2),
                close=round(c, 2), volume=int(random.uniform(500000, 2000000))
            ))
            idx += 1
    return KlineSeries(klines=klines, symbol="TEST", timeframe=timeframe)


def compute_macd(series):
    prices = [k.close for k in series.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    return macd.calculate(prices)


def create_clear_divergence_data(bullish=True):
    """
    Create synthetic data with a clear divergence pattern.
    
    For bullish divergence:
    Phase 1: Downtrend (price drops)
    Phase 2: Pullback (price rises slightly)
    Phase 3: Second downtrend (price drops further BUT MACD diverges)
    
    For bearish divergence:
    Phase 1: Uptrend (price rises)
    Phase 2: Pullback (price drops slightly)
    Phase 3: Second uptrend (price rises further BUT MACD diverges)
    """
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    random.seed(42)

    if bullish:
        # Bullish divergence: lower lows, higher MACD
        # Phase 1: Drop from 100 to 80 (first low)
        # Phase 2: Bounce to 90
        # Phase 3: Drop from 90 to 75 (lower low)
        phases_prices = [
            (100, 80, 30),  # First drop
            (80, 90, 15),   # Bounce
            (90, 75, 30),   # Second drop (lower low)
        ]
    else:
        # Bearish divergence: higher highs, lower MACD
        # Phase 1: Rise from 80 to 100 (first high)
        # Phase 2: Pullback to 90
        # Phase 3: Rise from 90 to 105 (higher high)
        phases_prices = [
            (80, 100, 30),  # First rise
            (100, 90, 15),  # Pullback
            (90, 105, 30),  # Second rise (higher high)
        ]

    idx = 0
    for start_p, end_p, count in phases_prices:
        for i in range(count):
            t = i / count
            base = start_p + (end_p - start_p) * t
            # Add controlled noise for realistic MACD behavior
            noise = random.uniform(-0.3, 0.3)
            mid = base + noise
            o = mid - 0.2
            c = mid + 0.2
            h = max(o, c) + random.uniform(0, 0.5)
            l = min(o, c) - random.uniform(0, 0.5)
            klines.append(Kline(
                timestamp=base_time + timedelta(minutes=idx * 30),
                open=round(o, 2), high=round(h, 2), low=round(l, 2),
                close=round(c, 2), volume=int(random.uniform(500000, 2000000))
            ))
            idx += 1

    return KlineSeries(klines=klines, symbol="TEST", timeframe="30m")


def create_clear_zero_pullback_data():
    """
    Create data where DIF clearly pulls back to 0.
    
    Pattern:
    1. Price drops → DIF goes negative
    2. Price bounces → DIF rises toward 0 (pullback)
    3. Price drops again → DIF diverges
    """
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    random.seed(42)

    # Start at 100, drop to 80, bounce to 90, drop to 75
    prices = []
    # Drop phase: 100 → 80
    for i in range(25):
        prices.append(100 - (i / 25) * 20 + random.uniform(-0.5, 0.5))
    # Bounce phase: 80 → 90
    for i in range(15):
        prices.append(80 + (i / 15) * 10 + random.uniform(-0.5, 0.5))
    # Drop again: 90 → 75
    for i in range(25):
        prices.append(90 - (i / 25) * 15 + random.uniform(-0.5, 0.5))

    for i, p in enumerate(prices):
        o = p - 0.2
        c = p + 0.2
        h = max(o, c) + random.uniform(0, 0.5)
        l = min(o, c) - random.uniform(0, 0.5)
        klines.append(Kline(
            timestamp=base_time + timedelta(minutes=i * 30),
            open=round(o, 2), high=round(h, 2), low=round(l, 2),
            close=round(c, 2), volume=int(random.uniform(500000, 2000000))
        ))

    return KlineSeries(klines=klines, symbol="TEST", timeframe="30m")


# ===== Tests =====

def test_point_method_bullish():
    """Test basic point-based bullish divergence detection."""
    print("\n  [Test] Point Method - Bullish Divergence")
    detector = DivergenceDetector()
    
    # Create synthetic MACD data where price goes lower but MACD goes higher
    macd_data = []
    for i in range(10):
        # At idx=2: price low, MACD = -3.0 (very negative)
        # At idx=7: price lower, MACD = -1.0 (less negative = divergence)
        if i == 2:
            macd_data.append(type('M', (), {'histogram': -3.0, 'dif': -2.5, 'dea': -2.7})())
        elif i == 7:
            macd_data.append(type('M', (), {'histogram': -1.0, 'dif': -0.5, 'dea': -0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    score = detector._point_method_bullish(macd_data, 7, 2)
    assert score > 0, f"Should detect bullish divergence, got score={score}"
    print(f"    ✅ Bullish divergence detected: score={score:.2f}")
    return True


def test_point_method_bearish():
    """Test basic point-based bearish divergence detection."""
    print("\n  [Test] Point Method - Bearish Divergence")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(10):
        if i == 2:
            macd_data.append(type('M', (), {'histogram': 3.0, 'dif': 2.5, 'dea': 2.7})())
        elif i == 7:
            macd_data.append(type('M', (), {'histogram': 1.0, 'dif': 0.5, 'dea': 0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    score = detector._point_method_bearish(macd_data, 7, 2)
    assert score > 0, f"Should detect bearish divergence, got score={score}"
    print(f"    ✅ Bearish divergence detected: score={score:.2f}")
    return True


def test_dif_method_bullish():
    """Test DIF 黄白线 bullish divergence detection."""
    print("\n  [Test] DIF Method - Bullish Divergence")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(10):
        if i == 2:
            macd_data.append(type('M', (), {'histogram': -3.0, 'dif': -2.5, 'dea': -2.7})())
        elif i == 7:
            macd_data.append(type('M', (), {'histogram': -1.0, 'dif': -0.5, 'dea': -0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    score = detector._dif_method_bullish(macd_data, 7, 2)
    assert score > 0, f"Should detect DIF bullish divergence, got score={score}"
    print(f"    ✅ DIF bullish divergence detected: score={score:.2f}")
    return True


def test_dif_method_bearish():
    """Test DIF 黄白线 bearish divergence detection."""
    print("\n  [Test] DIF Method - Bearish Divergence")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(10):
        if i == 2:
            macd_data.append(type('M', (), {'histogram': 3.0, 'dif': 2.5, 'dea': 2.7})())
        elif i == 7:
            macd_data.append(type('M', (), {'histogram': 1.0, 'dif': 0.5, 'dea': 0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    score = detector._dif_method_bearish(macd_data, 7, 2)
    assert score > 0, f"Should detect DIF bearish divergence, got score={score}"
    print(f"    ✅ DIF bearish divergence detected: score={score:.2f}")
    return True


def test_no_divergence_when_no_price_extremes():
    """Test that no divergence is detected when price isn't making extremes."""
    print("\n  [Test] No divergence when price doesn't make new extremes")
    detector = DivergenceDetector()
    
    # Manually create bottom fractals at the SAME price level
    # This simulates a range-bound market with no clear trend
    f1 = type('F', (), {'price': 100.0, 'kline_index': 2})()
    f2 = type('F', (), {'price': 100.0, 'kline_index': 7})()
    
    macd_data = []
    for i in range(10):
        macd_data.append(type('M', (), {'histogram': float(i * 0.5), 'dif': float(i * 0.3), 'dea': float(i * 0.2)})())

    # Price NOT making new low (both at 100) → no divergence
    series = create_oscillation_series([(100, 100, 2.0)], count_per_phase=10)
    
    result = detector.detect_bullish_divergence(
        series, macd_data, [], [f1, f2], []
    )
    assert not result.has_divergence, f"Should not detect bullish divergence without price extremes, got score={result.score}"
    
    # Same for bearish - price NOT making new high
    result = detector.detect_bearish_divergence(
        series, macd_data, [], [f1, f2], []
    )
    assert not result.has_divergence, f"Should not detect bearish divergence without price extremes, got score={result.score}"
    
    print("    ✅ No false divergence detected on equal prices")
    return True


def test_zero_pullback_detection():
    """Test 黄白线回拉0轴 detection with clear pullback data."""
    print("\n  [Test] 黄白线回拉0轴 Detection")
    detector = DivergenceDetector()
    
    # Create MACD data where DIF clearly pulls back to ~0
    macd_data = []
    # Phase 1: DIF goes deeply negative (first drop)
    for i in range(10):
        macd_data.append(type('M', (), {'dif': -2.0 + i * 0.2, 'histogram': -1.5, 'dea': -1.5})())
    # Phase 2: DIF rises to near 0 (pullback during center formation)
    for i in range(10):
        macd_data.append(type('M', (), {'dif': -0.2 + i * 0.1, 'histogram': 0.3, 'dea': 0.2})())
    # Phase 3: DIF diverges (second drop, DIF less negative)
    for i in range(10):
        macd_data.append(type('M', (), {'dif': -0.5 + i * 0.1, 'histogram': -0.3, 'dea': -0.3})())

    # Create a center spanning phase 2
    center = Center(start_idx=10, end_idx=19, high=95, low=85, segments=[], confirmed=True)
    
    result = detector.check_zero_pullback(macd_data, [center])
    print(f"    has_pullback={result.has_pullback}, pullback_level={result.pullback_level:.3f}, "
          f"dif_min={result.dif_min:.2f}, dif_max={result.dif_max:.2f}")
    
    assert result.has_pullback, "Should detect DIF pullback to near 0"
    print("    ✅ Zero pullback detected")
    return True


def test_no_pullback_when_dif_stays_negative():
    """Test that no pullback is detected when DIF stays far from 0."""
    print("\n  [Test] No pullback when DIF stays far from 0")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(30):
        macd_data.append(type('M', (), {'dif': -5.0 + i * 0.05, 'histogram': -2.0, 'dea': -3.0})())
    
    center = Center(start_idx=10, end_idx=19, high=95, low=85, segments=[], confirmed=True)
    result = detector.check_zero_pullback(macd_data, [center])
    
    print(f"    has_pullback={result.has_pullback}, pullback_level={result.pullback_level:.3f}")
    assert not result.has_pullback, "Should NOT detect pullback when DIF stays far from 0"
    print("    ✅ No false pullback detected")
    return True


def test_combined_divergence_with_real_data():
    """Test combined divergence detection on synthetic real-like data."""
    print("\n  [Test] Combined Divergence - Full Pipeline")
    
    series = create_clear_divergence_data(bullish=True)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    macd_data = compute_macd(series)
    
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    center_det = CenterDetector(min_segments=3)
    centers = center_det.detect_centers(segments)
    
    detector = DivergenceDetector()
    
    # Test bullish divergence
    bottom_fractals = [f for f in fractals if not f.is_top]
    print(f"    Bottom fractals: {len(bottom_fractals)}")
    
    if len(bottom_fractals) >= 2:
        result = detector.detect_bullish_divergence(
            series, macd_data, segments, bottom_fractals, centers
        )
        print(f"    Bullish: has_divergence={result.has_divergence}, score={result.score:.2f}")
        print(f"      Details: {result.details}")
        
        # At minimum, the zone should be valid
        assert result.score >= 0, "Score should not be negative"
    
    print("    ✅ Full pipeline completed")
    return True


def test_area_method_between_segments():
    """Test area-based divergence between two same-direction segments."""
    print("\n  [Test] Area Method - Segment-based divergence")
    detector = DivergenceDetector()
    
    # Create MACD data
    macd_data = []
    for i in range(50):
        # Segment 1 (indices 5-15): strongly negative values (big downward momentum)
        # Segment 2 (indices 30-40): less negative values (smaller downward momentum = divergence)
        if 5 <= i <= 15:
            macd_data.append(type('M', (), {'histogram': -3.0, 'dif': -2.5, 'dea': -2.7})())
        elif 30 <= i <= 40:
            macd_data.append(type('M', (), {'histogram': -1.0, 'dif': -0.5, 'dea': -0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    # Two down segments
    seg1 = Segment(direction='down', start_idx=5, end_idx=15, start_price=100, end_price=85,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)
    seg2 = Segment(direction='down', start_idx=30, end_idx=40, start_price=90, end_price=78,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)

    score = detector._area_method_bullish(macd_data, None, [seg1, seg2], 40, 15,
                                          type('F', (), {'price': 78})(), type('F', (), {'price': 85})())
    print(f"    Area method score: {score:.2f}")
    assert score > 0, f"Should detect area divergence, got score={score}"
    print("    ✅ Area divergence detected")
    return True


def test_segment_divergence():
    """Test segment-level divergence (区间套)."""
    print("\n  [Test] Segment Divergence (区间套 - Lesson 27)")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(50):
        if 5 <= i <= 15:
            macd_data.append(type('M', (), {'histogram': -3.0, 'dif': -2.5, 'dea': -2.7})())
        elif 30 <= i <= 40:
            macd_data.append(type('M', (), {'histogram': -1.0, 'dif': -0.5, 'dea': -0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    seg1 = Segment(direction='down', start_idx=5, end_idx=15, start_price=100, end_price=85,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)
    seg2 = Segment(direction='down', start_idx=30, end_idx=40, start_price=90, end_price=78,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)
    seg3 = Segment(direction='up', start_idx=15, end_idx=25, start_price=85, end_price=92,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)

    result = detector.check_segment_fractal_divergence(
        None, macd_data, [seg1, seg3, seg2]
    )

    if result:
        print(f"    has_divergence={result.has_divergence}, score={result.score:.2f}, "
              f"direction={result.details.get('direction', 'N/A')}")
        assert result.details.get('direction') == 'bullish', "Should detect bullish segment divergence"
    else:
        print("    (No segment-level divergence found - may need more data)")
    
    print("    ✅ Segment divergence check completed")
    return True


def test_bearish_area_method():
    """Test area-based bearish divergence."""
    print("\n  [Test] Area Method - Bearish Divergence")
    detector = DivergenceDetector()
    
    macd_data = []
    for i in range(50):
        if 5 <= i <= 15:
            macd_data.append(type('M', (), {'histogram': 3.0, 'dif': 2.5, 'dea': 2.7})())
        elif 30 <= i <= 40:
            macd_data.append(type('M', (), {'histogram': 1.0, 'dif': 0.5, 'dea': 0.8})())
        else:
            macd_data.append(type('M', (), {'histogram': 0.0, 'dif': 0.0, 'dea': 0.0})())

    seg1 = Segment(direction='up', start_idx=5, end_idx=15, start_price=80, end_price=100,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)
    seg2 = Segment(direction='up', start_idx=30, end_idx=40, start_price=90, end_price=105,
                   pen_count=3, feature_sequence=[], has_gap=False, confirmed=True)

    score = detector._area_method_bearish(macd_data, None, [seg1, seg2], 40, 15,
                                          type('F', (), {'price': 105})(), type('F', (), {'price': 100})())
    print(f"    Bearish area score: {score:.2f}")
    assert score > 0, f"Should detect bearish area divergence, got score={score}"
    print("    ✅ Bearish area divergence detected")
    return True


# ===== Run All =====
def run_all():
    print("\n" + "=" * 70)
    print("Divergence Detection Tests (Phase 2) - 缠论背驰多方法检测")
    print("=" * 70)
    random.seed(42)

    tests = [
        ("Point method bullish", test_point_method_bullish),
        ("Point method bearish", test_point_method_bearish),
        ("DIF method bullish", test_dif_method_bullish),
        ("DIF method bearish", test_dif_method_bearish),
        ("No false divergence", test_no_divergence_when_no_price_extremes),
        ("Zero pullback detection", test_zero_pullback_detection),
        ("No false pullback", test_no_pullback_when_dif_stays_negative),
        ("Area divergence between segments", test_area_method_between_segments),
        ("Bearish area divergence", test_bearish_area_method),
        ("Segment divergence (区间套)", test_segment_divergence),
        ("Combined full pipeline", test_combined_divergence_with_real_data),
    ]

    passed, failed = 0, 0
    for name, fn in tests:
        print(f"\n{'─' * 60}")
        try:
            fn()
            print(f"  ✅ {name}: PASS")
            passed += 1
        except Exception as e:
            import traceback
            print(f"  ❌ {name}: FAIL - {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 70}")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
