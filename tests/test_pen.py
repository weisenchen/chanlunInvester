#!/usr/bin/env python3
"""
Test Pen Detection Module
测试笔检测模块
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.pen import PenCalculator, PenConfig
from datetime import datetime, timedelta


def create_test_series(prices: list) -> KlineSeries:
    """Create test K-line series from price list"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    for i, price in enumerate(prices):
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=1000000
        )
        klines.append(kline)
    
    return KlineSeries(klines=klines, symbol="TEST", timeframe="30m")


def test_pen_creation():
    """Test basic pen creation"""
    print("Testing pen creation...")
    
    # Create pattern that should form at least one pen
    prices = [100, 102, 101, 99, 100, 103]
    series = create_test_series(prices)
    
    calculator = PenCalculator()
    pens = calculator.identify_pens(series)
    
    assert len(pens) >= 1, f"Expected at least 1 pen, got {len(pens)}"
    
    print(f"  ✓ Pen creation test passed ({len(pens)} pens)")
    return True


def test_new_definition():
    """Test new 3-K-line pen definition"""
    print("Testing new 3-K-line definition...")
    
    # Create pattern with clear fractals
    prices = [100, 101, 102, 101, 100, 99, 100, 101, 102]
    series = create_test_series(prices)
    
    config = PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    )
    calculator = PenCalculator(config)
    pens = calculator.identify_pens(series)
    
    # Should have pens with at least 3 K-lines each
    for pen in pens:
        assert pen.kline_count >= 3, \
            f"Pen should have at least 3 K-lines, got {pen.kline_count}"
    
    print(f"  ✓ New definition test passed ({len(pens)} valid pens)")
    return True


def test_pen_direction():
    """Test pen direction detection"""
    print("Testing pen direction...")
    
    # Create upward pattern
    prices = [100, 101, 102, 103, 104]
    series = create_test_series(prices)
    
    calculator = PenCalculator()
    pens = calculator.identify_pens(series)
    
    # Check that we have both up and down pens in a complete pattern
    prices_full = [100, 102, 101, 99, 100, 103, 102, 100]
    series_full = create_test_series(prices_full)
    pens_full = calculator.identify_pens(series_full)
    
    up_pens = [p for p in pens_full if p.is_up]
    down_pens = [p for p in pens_full if p.is_down]
    
    # Should have both directions in a complete pattern
    if len(pens_full) > 0:
        assert len(up_pens) + len(down_pens) == len(pens_full), \
            "All pens should have a direction"
    
    print(f"  ✓ Direction test passed (up: {len(up_pens)}, down: {len(down_pens)})")
    return True


def test_pen_magnitude():
    """Test pen magnitude calculation"""
    print("Testing pen magnitude...")
    
    prices = [100, 105, 104, 103, 102]
    series = create_test_series(prices)
    
    calculator = PenCalculator()
    pens = calculator.identify_pens(series)
    
    for pen in pens:
        # Magnitude should be positive
        assert pen.magnitude() >= 0, "Magnitude should be non-negative"
        # Magnitude should equal price difference
        expected_mag = abs(pen.end_price - pen.start_price)
        assert abs(pen.magnitude() - expected_mag) < 0.01, \
            f"Magnitude mismatch: {pen.magnitude()} vs {expected_mag}"
    
    print(f"  ✓ Magnitude test passed")
    return True


def test_strict_validation():
    """Test strict validation mode"""
    print("Testing strict validation...")
    
    prices = [100, 102, 101, 100, 99, 100]
    series = create_test_series(prices)
    
    # Strict mode
    config_strict = PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    )
    calc_strict = PenCalculator(config_strict)
    pens_strict = calc_strict.identify_pens(series)
    
    # Non-strict mode
    config_loose = PenConfig(
        use_new_definition=True,
        strict_validation=False,
        min_klines_between_turns=3
    )
    calc_loose = PenCalculator(config_loose)
    pens_loose = calc_loose.identify_pens(series)
    
    # Strict should have <= pens than non-strict
    assert len(pens_strict) <= len(pens_loose), \
        "Strict mode should have <= pens than non-strict"
    
    print(f"  ✓ Strict validation test passed (strict: {len(pens_strict)}, loose: {len(pens_loose)})")
    return True


def run_all_tests():
    """Run all pen tests"""
    print("\n" + "="*70)
    print("Pen Detection Module Tests")
    print("笔检测模块测试")
    print("="*70 + "\n")
    
    tests = [
        test_pen_creation,
        test_new_definition,
        test_pen_direction,
        test_pen_magnitude,
        test_strict_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
