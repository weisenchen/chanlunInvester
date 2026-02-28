"""
Trading System - Python Layer
Backup implementation and integration layer for Rust+Python hybrid trading system.
"""

__version__ = "0.1.0"
__author__ = "Weisen"

from .kline import Kline, KlineSeries, TimeFrame
from .pen import PenCalculator, Pen, PenDirection
from .segment import SegmentCalculator
from .indicators import MACD

__all__ = [
    "Kline",
    "KlineSeries",
    "TimeFrame",
    "PenCalculator",
    "Pen",
    "PenDirection",
    "SegmentCalculator",
    "MACD",
]
