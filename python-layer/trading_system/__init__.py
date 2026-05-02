"""
Trading System - Python Layer
Backup implementation and integration layer for Rust+Python hybrid trading system.

Features:
- 🐍 Python implementation for flexibility
- 🦀 Rust core integration (optional)
- 📊 Universal stock monitoring
- 🎯 Multi-level ChanLun analysis
"""

__version__ = "0.3.0"  # Added universal monitor
__author__ = "Weisen"

from .kline import Kline, KlineSeries, TimeFrame
from .fractal import Fractal, FractalDetector
from .pen import PenCalculator, Pen, PenDirection, PenConfig
from .segment import SegmentCalculator, Segment
from .center import Center, CenterDetector
from .indicators import MACD, MACDIndicator
from .monitor import ChanLunMonitor, MonitorConfig, AnalysisResult
from .backtest import BacktestEngine, BacktestConfig, BacktestResult, Trade
from .telegram_bot import ChanLunBot, send_alert, send_analysis_report
from .divergence import DivergenceDetector, DivergenceResult, ZeroPullbackResult, detect_divergence

__version__ = "0.5.0"  # Added divergence detection module

__all__ = [
    # Core
    "Kline",
    "KlineSeries",
    "TimeFrame",
    
    # Analysis
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
    
    # Monitor
    "ChanLunMonitor",
    "MonitorConfig",
    "AnalysisResult",
    
    # Backtest (New!)
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "Trade",
    
    # Telegram Bot (New!)
    "ChanLunBot",
    "send_alert",
    "send_analysis_report",

    # Divergence Detection (New!)
    "DivergenceDetector",
    "DivergenceResult",
    "ZeroPullbackResult",
    "detect_divergence",
]
