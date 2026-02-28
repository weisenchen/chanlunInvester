"""
Trading System - Python Layer
Backup implementation and integration layer for Rust+Python hybrid trading system.
"""

__version__ = "0.1.0"
__author__ = "Weisen Chen"

# Python backup implementations
from .kline import Kline, KlineSeries, TimeFrame
from .fractal import FractalDetector, Fractal, FractalType

__all__ = [
    "Kline",
    "KlineSeries", 
    "TimeFrame",
    "FractalDetector",
    "Fractal",
    "FractalType",
]
