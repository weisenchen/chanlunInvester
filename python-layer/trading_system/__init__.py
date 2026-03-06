"""
Trading System - Python Layer
Backup implementation and integration layer for Rust+Python hybrid trading system.
"""

__version__ = "0.2.0"  # Updated with center module
__author__ = "Weisen"

from .kline import Kline, KlineSeries, TimeFrame
from .fractal import Fractal, FractalDetector
from .pen import PenCalculator, Pen, PenDirection, PenConfig
from .segment import SegmentCalculator, Segment
from .center import Center, CenterDetector
from .indicators import MACD, MACDIndicator

__all__ = [
    "Kline",
    "KlineSeries",
    "TimeFrame",
    "Fractal",
    "FractalDetector",
    "PenCalculator",
    "Pen",
    "PenDirection",
    "PenConfig",
    "SegmentCalculator",
    "Segment",
    "Center",
    "CenterDetector",
    "MACD",
    "MACDIndicator",
]
