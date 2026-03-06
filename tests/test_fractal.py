#!/usr/bin/env python3
"""
Test Fractal Detection Module
测试分型检测模块
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
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


def test_top_fractal():
    """Test top fractal detection"""
    print("Testing top fractal detection...")
    
    # Create pattern: low, high, low (top fractal)
    prices = [100, 102, 101]
    series = create_test_series(prices)
    
    detector = FractalDetector()
    fractals = detector.detect_all(series)
    top_fractals = [f for f in fractals if f.is_top]
    
    assert len(top_fractals) == 1, f"Expected 1 top fractal, got {len(top_fractals)}"
    assert top_fractals[0].kline_index == 1, f"Expected index 1, got {top_fractals[0].kline_index}"
    assert top_fractals[0].price == 103, f"Expected price 103, got {top_fractals[0].price}"
    
    print("  ✓ Top fractal detection passed")
    return True


def test_bottom_fractal():
    """Test bottom fractal detection"""
    print("Testing bottom fractal detection...")
    
    # Create pattern: high, low, high (bottom fractal)
    prices = [100, 98, 99]
    series = create_test_series(prices)
    
    detector = FractalDetector()
    fractals = detector.detect_all(series)
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    assert len(bottom_fractals) == 1, f"Expected 1 bottom fractal, got {len(bottom_fractals)}"
    assert bottom_fractals[0].kline_index == 1, f"Expected index 1, got {bottom_fractals[0].kline_index}"
    assert bottom_fractals[0].price == 97, f"Expected price 97, got {bottom_fractals[0].price}"
    
    print("  ✓ Bottom fractal detection passed")
    return True


def test_multiple_fractals():
    """Test multiple fractals in a series"""
    print("Testing multiple fractals...")
    
    # Create pattern with multiple fractals
    prices = [100, 102, 101, 99, 100, 102, 101]
    series = create_test_series(prices)
    
    detector = FractalDetector()
    fractals = detector.detect_all(series)
    
    assert len(fractals) >= 2, f"Expected at least 2 fractals, got {len(fractals)}"
    
    print(f"  ✓ Multiple fractals detection passed ({len(fractals)} fractals)")
    return True


def test_strict_mode():
    """Test strict vs non-strict mode"""
    print("Testing strict mode...")
    
    # Create pattern with equal highs
    prices = [100, 102, 102, 101]
    series = create_test_series(prices)
    
    # Strict mode (default)
    detector_strict = FractalDetector(strict=True)
    fractals_strict = detector_strict.detect_all(series)
    
    # Non-strict mode
    detector_loose = FractalDetector(strict=False)
    fractals_loose = detector_loose.detect_all(series)
    
    # Non-strict should detect more or equal fractals
    assert len(fractals_loose) >= len(fractals_strict), \
        f"Non-strict should detect >= fractals than strict"
    
    print(f"  ✓ Strict mode test passed (strict: {len(fractals_strict)}, loose: {len(fractals_loose)})")
    return True


def test_insufficient_data():
    """Test with insufficient data"""
    print("Testing insufficient data...")
    
    # Less than 3 K-lines
    prices = [100, 101]
    series = create_test_series(prices)
    
    detector = FractalDetector()
    fractals = detector.detect_all(series)
    
    assert len(fractals) == 0, f"Expected 0 fractals for insufficient data, got {len(fractals)}"
    
    print("  ✓ Insufficient data test passed")
    return True


def run_all_tests():
    """Run all fractal tests"""
    print("\n" + "="*70)
    print("Fractal Detection Module Tests")
    print("分型检测模块测试")
    print("="*70 + "\n")
    
    tests = [
        test_top_fractal,
        test_bottom_fractal,
        test_multiple_fractals,
        test_strict_mode,
        test_insufficient_data,
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
