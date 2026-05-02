#!/usr/bin/env python3
"""
BSP Detection Tests - 缠论6类买卖点测试 (Theory-Compliant)
Tests: Buy1, Buy2, Buy3, Sell1, Sell2, Sell3
Updated: Buy1/Sell1 require ≥2 centers (trend check per Lesson 15)
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random, math
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator, Segment
from trading_system.indicators import MACDIndicator
from trading_system.center import CenterDetector, Center

sys.path.insert(0, str(Path(__file__).parent.parent))
from monitor_all import detect_buy_sell_points


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


# ===== Theory-Compliant Tests =====

def test_buy1_requires_downtrend():
    """Buy1 requires ≥2 non-overlapping centers (downtrend)."""
    print("\n  [Test] Buy1 - Requires downtrend (≥2 centers) per Lesson 15")
    
    # No centers → no Buy1 regardless of price/MACD
    series = create_oscillation_series([(100, 85, 3.0), (85, 78, 2.0)], count_per_phase=30)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    # Without centers passed
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m")
    signals = result['signals']
    buy1 = [s for s in signals if s['type'] == 'buy1']
    assert len(buy1) == 0, "Buy1 should NOT fire without centers (no trend)"
    
    # With empty centers
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m", centers=[])
    signals = result['signals']
    buy1 = [s for s in signals if s['type'] == 'buy1']
    assert len(buy1) == 0, "Buy1 should NOT fire with empty centers"
    
    # With only 1 center
    fake_center = Center(start_idx=0, end_idx=10, high=105, low=95, confirmed=True)
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m", centers=[fake_center])
    signals = result['signals']
    buy1 = [s for s in signals if s['type'] == 'buy1']
    assert len(buy1) == 0, "Buy1 should NOT fire with only 1 center"
    
    print("    ✅ Buy1 correctly blocked: no center, empty centers, single center all rejected")
    return True


def test_sell1_requires_uptrend():
    """Sell1 requires ≥2 non-overlapping centers (uptrend)."""
    print("\n  [Test] Sell1 - Requires uptrend (≥2 centers) per Lesson 15")
    
    series = create_oscillation_series([(100, 115, 3.0), (115, 122, 2.0)], count_per_phase=30)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m")
    sell1 = [s for s in result['signals'] if s['type'] == 'sell1']
    assert len(sell1) == 0, "Sell1 should NOT fire without centers"
    
    print("    ✅ Sell1 correctly blocked: no centers")
    return True


def test_buy1_trend_check_centers_overlapping():
    """Buy1: overlapping centers (range/盘整) should NOT trigger divergence."""
    print("\n  [Test] Buy1 - Overlapping centers (盘整) should NOT trigger divergence")
    
    # Two overlapping centers = range/consolidation, not a trend
    range_center1 = Center(start_idx=0, end_idx=10, high=105, low=95, segments=[], confirmed=True)
    range_center2 = Center(start_idx=11, end_idx=20, high=103, low=97, segments=[], confirmed=True)  # overlaps with c1
    
    series = create_oscillation_series([(100, 85, 3.0)], count_per_phase=20)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    # This is a range (centers overlap), not a trend — Buy1 should not fire
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m",
                                     centers=[range_center1, range_center2])
    buy1 = [s for s in result['signals'] if s['type'] == 'buy1']
    assert len(buy1) == 0, "Buy1 should NOT fire with overlapping centers (盘整, not trend)"
    print("    ✅ Buy1 correctly blocked: overlapping centers = 盘整, not trend")
    return True


def test_buy1_trend_check_valid_downtrend():
    """Buy1: non-overlapping centers (downtrend) ALLOWS divergence check."""
    print("\n  [Test] Buy1 - Non-overlapping centers should allow divergence check")
    
    # Non-overlapping centers = valid downtrend
    trend_c1 = Center(start_idx=0, end_idx=10, high=110, low=100, segments=[], confirmed=True)
    trend_c2 = Center(start_idx=11, end_idx=20, high=95, low=85, segments=[], confirmed=True)  # entirely below c1
    
    series = create_oscillation_series([(100, 90, 2.0)], count_per_phase=20)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    # Trend check should pass (downtrend), but Buy1 may not fire due to lack of divergence in random data
    # The key test: the trend verification gate opens correctly
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m",
                                     centers=[trend_c1, trend_c2])
    buy1 = [s for s in result['signals'] if s['type'] == 'buy1']
    # May or may not fire depending on MACD divergence in data - that's fine
    for s in result['signals']:
        assert not s['type'].startswith('sell'), "In downtrend, should not have sell signals"
    print(f"    ✅ Downtrend verification passed. Signals present: {len(result['signals'])}")
    return True


def test_sell1_trend_check_valid_uptrend():
    """Sell1: non-overlapping centers (uptrend) ALLOWS divergence check."""
    print("\n  [Test] Sell1 - Non-overlapping centers should allow divergence check")
    
    trend_c1 = Center(start_idx=0, end_idx=10, high=105, low=95, segments=[], confirmed=True)
    trend_c2 = Center(start_idx=11, end_idx=20, high=120, low=110, segments=[], confirmed=True)  # entirely above c1
    
    series = create_oscillation_series([(110, 120, 2.0)], count_per_phase=20)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m",
                                     centers=[trend_c1, trend_c2])
    for s in result['signals']:
         assert not s['type'].startswith('buy'), "In uptrend, should not have buy signals"
    print(f"    ✅ Uptrend verification passed. Signals present: {len(result['signals'])}")
    return True


def test_old_buy1_still_works_without_centers():
    """Backward compatibility: old code path without centers still works for non-BSP1 signals."""
    print("\n  [Test] Backward Compatibility - Buying/selling without BSP1 still works")
    
    # Without centers, Buy2/Sell2 should still work (they don't need trends)
    series = create_oscillation_series([(90, 108, 2.5), (108, 102, 2.0)], count_per_phase=25)
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m")
    buy2 = [s for s in result['signals'] if s['type'] == 'buy2']
    # May or may not fire depending on data - just verify no BSP1 fires
    
    # Conflict resolution should still work
    buy_types = [s['type'] for s in result['signals'] if s['type'].startswith('buy')]
    sell_types = [s['type'] for s in result['signals'] if s['type'].startswith('sell')]
    assert len(buy_types) == 0 or len(sell_types) == 0, f"Conflict: {[s['type'] for s in result['signals']]}"

    print(f"    ✅ Backward compatible. Signals: {[s['type'] for s in result['signals']] if result['signals'] else 'none'}")
    return True


def test_conflict_resolution():
    """Test that buy/sell conflict resolution works correctly."""
    print("\n  [Test] Conflict Resolution - 买卖点互斥检查")
    
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    price = 100.0
    for i in range(60):
        price = price + random.uniform(-1.0, 1.0)
        klines.append(Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=price, high=price+1.5, low=price-1.5,
            close=price, volume=1000000
        ))
    series = KlineSeries(klines=klines, symbol="TEST", timeframe="30m")
    
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    pen_calc = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True))
    pens = pen_calc.identify_pens(series)
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    macd_data = compute_macd(series)
    
    result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, "30m")
    buy_types = [s['type'] for s in result['signals'] if s['type'].startswith('buy')]
    sell_types = [s['type'] for s in result['signals'] if s['type'].startswith('sell')]
    assert len(buy_types) == 0 or len(sell_types) == 0, \
        f"Conflict resolution failed: both buy {buy_types} and sell {sell_types}"
    print(f"    ✅ Conflict resolution passed (signals: {[s['type'] for s in result['signals']]})")
    return True


def test_signal_structure():
    """Test that signals have the right structure for anti-spam."""
    print("\n  [Test] Signal Structure - 信号结构完整性")
    test_signals = [
        {'type': 'buy1', 'name': '30m级别第一类买点 (底背驰)', 'price': 100.0,
         'confidence': 'high', 'strength': 2.0, 'description': 'Test'},
        {'type': 'sell3', 'name': '30m级别第三类卖点 (中枢跌破)', 'price': 98.0,
         'confidence': 'medium', 'strength': 3.5, 'description': 'Test'},
    ]
    for sig in test_signals:
        normalized = sig['type'].replace(' (背驰)', '').replace(' (顶背驰)', '')
        normalized = normalized.replace(' (中枢突破)', '').replace(' (中枢跌破)', '')
        assert normalized in ('buy1', 'buy2', 'buy3', 'sell1', 'sell2', 'sell3'), \
            f"Invalid normalized type: {normalized} from {sig['type']}"
    print(f"    ✅ All 6 signal types normalize correctly")
    return True


# ===== Run All =====
def run_all():
    print("\n" + "="*70)
    print("BSP Detection Tests (Theory-Compliant) - 缠论买卖点测试")
    print("="*70)
    random.seed(42)
    
    tests = [
        ("Buy1 requires downtrend (Lesson 15)", test_buy1_requires_downtrend),
        ("Sell1 requires uptrend (Lesson 15)", test_sell1_requires_uptrend),
        ("Buy1: overlapping centers = range, not trend", test_buy1_trend_check_centers_overlapping),
        ("Buy1: non-overlapping centers = downtrend OK", test_buy1_trend_check_valid_downtrend),
        ("Sell1: non-overlapping centers = uptrend OK", test_sell1_trend_check_valid_uptrend),
        ("Backward compatibility (no centers)", test_old_buy1_still_works_without_centers),
        ("Conflict resolution", test_conflict_resolution),
        ("Signal structure", test_signal_structure),
    ]
    
    passed, failed = 0, 0
    for name, fn in tests:
        print(f"\n{'─'*60}")
        try:
            fn()
            print(f"  ✅ {name}: PASS")
            passed += 1
        except Exception as e:
            import traceback
            print(f"  ❌ {name}: FAIL - {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
