#!/usr/bin/env python3
"""
Test Segment Detection Module
测试线段检测模块
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.pen import Pen, PenDirection
from trading_system.segment import SegmentCalculator
from datetime import datetime, timedelta


def create_test_series(count=50) -> KlineSeries:
    """Create test K-line series"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    import random
    random.seed(42)
    
    base_price = 100.0
    for i in range(count):
        volatility = random.uniform(-1, 1)
        price = base_price + volatility
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=price,
            high=price + abs(random.uniform(0.5, 2)),
            low=price - abs(random.uniform(0.5, 2)),
            close=price,
            volume=1000000
        )
        klines.append(kline)
        base_price = price
    
    return KlineSeries(klines=klines, symbol="TEST", timeframe="30m")


def create_test_pens() -> list:
    """Create test pen series"""
    from trading_system.pen import Pen, PenDirection
    
    pens = [
        Pen(PenDirection.UP, 0, 10, 100.0, 105.0, True),
        Pen(PenDirection.DOWN, 10, 20, 105.0, 102.0, True),
        Pen(PenDirection.UP, 20, 30, 102.0, 107.0, True),
        Pen(PenDirection.DOWN, 30, 40, 107.0, 104.0, True),
        Pen(PenDirection.UP, 40, 50, 104.0, 109.0, True),
    ]
    return pens


def test_segment_creation():
    """Test basic segment creation"""
    print("Testing segment creation...")
    
    pens = create_test_pens()
    calc = SegmentCalculator(min_pens=3)
    segments = calc.detect_segments(pens)
    
    assert len(segments) >= 1, f"Expected at least 1 segment, got {len(segments)}"
    
    print(f"  ✓ Segment creation test passed ({len(segments)} segments)")
    return True


def test_min_pens_requirement():
    """Test minimum pens requirement"""
    print("Testing minimum pens requirement...")
    
    # Create only 2 pens (should not form a segment)
    pens = [
        Pen(PenDirection.UP, 0, 10, 100.0, 105.0, True),
        Pen(PenDirection.DOWN, 10, 20, 105.0, 102.0, True),
    ]
    
    calc = SegmentCalculator(min_pens=3)
    segments = calc.detect_segments(pens)
    
    assert len(segments) == 0, f"Expected 0 segments with only 2 pens, got {len(segments)}"
    
    print(f"  ✓ Minimum pens requirement test passed")
    return True


def test_segment_direction():
    """Test segment direction detection"""
    print("Testing segment direction...")
    
    pens = create_test_pens()
    calc = SegmentCalculator(min_pens=3)
    segments = calc.detect_segments(pens)
    
    for seg in segments:
        assert seg.direction in ['up', 'down'], f"Invalid segment direction: {seg.direction}"
        
        if seg.direction == 'up':
            assert seg.end_price > seg.start_price, "Up segment should end higher than start"
        else:
            assert seg.end_price < seg.start_price, "Down segment should end lower than start"
    
    print(f"  ✓ Segment direction test passed")
    return True


def test_segment_with_real_data():
    """Test with realistic pen series"""
    print("Testing with realistic pen series...")
    
    series = create_test_series(100)
    
    # First detect pens
    from trading_system.fractal import FractalDetector
    from trading_system.pen import PenCalculator, PenConfig
    
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    
    # Then detect segments
    calc = SegmentCalculator(min_pens=3)
    segments = calc.detect_segments(pens)
    
    print(f"  ✓ Realistic data test passed")
    print(f"    Pens: {len(pens)}, Segments: {len(segments)}")
    return True


def test_segment_properties():
    """Test segment properties"""
    print("Testing segment properties...")
    
    pens = create_test_pens()
    calc = SegmentCalculator(min_pens=3)
    segments = calc.detect_segments(pens)
    
    for seg in segments:
        # Test basic properties
        assert hasattr(seg, 'direction'), "Segment should have direction"
        assert hasattr(seg, 'start_idx'), "Segment should have start_idx"
        assert hasattr(seg, 'end_idx'), "Segment should have end_idx"
        assert hasattr(seg, 'start_price'), "Segment should have start_price"
        assert hasattr(seg, 'end_price'), "Segment should have end_price"
        assert hasattr(seg, 'pen_count'), "Segment should have pen_count"
        
        # Test magnitude
        magnitude = abs(seg.end_price - seg.start_price)
        assert magnitude > 0, "Segment magnitude should be positive"
        
        # Test pen count
        assert seg.pen_count >= 3, f"Segment should have at least 3 pens, got {seg.pen_count}"
    
    print(f"  ✓ Segment properties test passed")
    return True


def run_all_tests():
    """Run all segment tests"""
    print("\n" + "="*70)
    print("Segment Detection Module Tests")
    print("线段检测模块测试")
    print("="*70 + "\n")
    
    tests = [
        test_segment_creation,
        test_min_pens_requirement,
        test_segment_direction,
        test_segment_with_real_data,
        test_segment_properties,
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
