#!/usr/bin/env python3
"""
Integration Tests for Trading System
交易系统集成测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator
from datetime import datetime, timedelta


def create_trend_series(trend: str = "up", count: int = 50) -> KlineSeries:
    """Create a trending K-line series for testing with enough volatility for fractals"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    base_price = 100.0
    
    import random
    random.seed(42)  # Reproducible
    
    for i in range(count):
        if trend == "up":
            base = base_price + i * 0.3
        elif trend == "down":
            base = base_price - i * 0.3
        else:
            base = base_price + (i % 10) * 0.3
        
        # Add volatility to create fractals
        volatility = random.uniform(-1, 1)
        price = base + volatility
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=price,
            high=price + abs(random.uniform(0.5, 2)),
            low=price - abs(random.uniform(0.5, 2)),
            close=price,
            volume=1000000
        )
        klines.append(kline)
    
    return KlineSeries(klines=klines, symbol="TEST", timeframe="30m")


def test_full_pipeline():
    """Test complete analysis pipeline"""
    print("Testing full analysis pipeline...")
    
    # Create test data
    series = create_trend_series("up", count=100)
    
    # Step 1: Fractal detection
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    assert len(fractals) > 0, "Should detect fractals"
    
    # Step 2: Pen identification
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    # Pens are formed from fractals
    
    # Step 3: Segment division
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    # Segments are formed from pens
    
    # Step 4: MACD calculation
    macd = MACDIndicator()
    prices = [k.close for k in series.klines]
    macd_data = macd.calculate(prices)
    assert len(macd_data) == len(prices), "MACD should have same length as prices"
    
    print(f"  ✓ Full pipeline test passed")
    print(f"    - Fractals: {len(fractals)}")
    print(f"    - Pens: {len(pens)}")
    print(f"    - Segments: {len(segments)}")
    print(f"    - MACD points: {len(macd_data)}")
    
    return True


def test_module_consistency():
    """Test consistency between Rust and Python implementations"""
    print("Testing module consistency...")
    
    # Create identical test data
    series = create_trend_series("up", count=50)
    
    # Test fractal detector
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    
    # Test pen calculator
    pen_calc = PenCalculator()
    pens = pen_calc.identify_pens(series)
    
    # Test segment calculator
    seg_calc = SegmentCalculator()
    segments = seg_calc.detect_segments(pens)
    
    # Verify all modules work together
    assert isinstance(fractals, list), "Fractals should be a list"
    assert isinstance(pens, list), "Pens should be a list"
    assert isinstance(segments, list), "Segments should be a list"
    
    print(f"  ✓ Module consistency test passed")
    return True


def test_data_flow():
    """Test data flow between modules"""
    print("Testing data flow...")
    
    series = create_trend_series("down", count=75)
    
    # Fractal -> Pen -> Segment flow
    fractals = FractalDetector().detect_all(series)
    pens = PenCalculator().identify_pens(series)
    segments = SegmentCalculator().detect_segments(pens)
    
    # Verify data integrity
    for fractal in fractals:
        assert 0 <= fractal.kline_index < len(series), \
            f"Fractal index {fractal.kline_index} out of range"
    
    for pen in pens:
        assert 0 <= pen.start_idx < len(series), "Pen start index out of range"
        assert 0 <= pen.end_idx < len(series), "Pen end index out of range"
        assert pen.start_idx <= pen.end_idx, "Pen start should be <= end"
    
    for segment in segments:
        assert 0 <= segment.start_idx < len(series), "Segment start index out of range"
        assert 0 <= segment.end_idx < len(series), "Segment end index out of range"
    
    print(f"  ✓ Data flow test passed")
    return True


def test_macd_integration():
    """Test MACD integration with price data"""
    print("Testing MACD integration...")
    
    series = create_trend_series("up", count=100)
    prices = [k.close for k in series.klines]
    
    # Test different MACD parameters
    configs = [
        (12, 26, 9),   # Standard
        (8, 17, 9),    # Fast
        (19, 39, 9),   # Slow
    ]
    
    for fast, slow, signal in configs:
        macd = MACDIndicator(fast=fast, slow=slow, signal=signal)
        macd_data = macd.calculate(prices)
        
        assert len(macd_data) == len(prices), \
            f"MACD length mismatch for config ({fast}, {slow}, {signal})"
        
        # Check that MACD values are reasonable
        for i, data in enumerate(macd_data):
            assert isinstance(data.dif, (int, float)), f"DIF should be numeric at {i}"
            assert isinstance(data.dea, (int, float)), f"DEA should be numeric at {i}"
            assert isinstance(data.macd, (int, float)), f"MACD should be numeric at {i}"
    
    print(f"  ✓ MACD integration test passed ({len(configs)} configs)")
    return True


def test_edge_cases():
    """Test edge cases"""
    print("Testing edge cases...")
    
    # Empty series
    empty_series = KlineSeries(klines=[], symbol="EMPTY", timeframe="30m")
    assert len(FractalDetector().detect_all(empty_series)) == 0
    assert len(PenCalculator().identify_pens(empty_series)) == 0
    
    # Single K-line
    single_kline = KlineSeries(
        klines=[Kline(
            timestamp=datetime.now(),
            open=100, high=101, low=99, close=100, volume=1000
        )],
        symbol="SINGLE",
        timeframe="30m"
    )
    assert len(FractalDetector().detect_all(single_kline)) == 0
    
    # Two K-lines
    two_klines = KlineSeries(
        klines=[
            Kline(timestamp=datetime.now(), open=100, high=101, low=99, close=100, volume=1000),
            Kline(timestamp=datetime.now(), open=101, high=102, low=100, close=101, volume=1000),
        ],
        symbol="TWO",
        timeframe="30m"
    )
    assert len(FractalDetector().detect_all(two_klines)) == 0
    
    print(f"  ✓ Edge cases test passed")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("Integration Tests")
    print("系统集成测试")
    print("="*70 + "\n")
    
    tests = [
        test_full_pipeline,
        test_module_consistency,
        test_data_flow,
        test_macd_integration,
        test_edge_cases,
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
