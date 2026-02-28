"""
K-line Data Structures - Python Implementation
Backup layer for Rust engine
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class TimeFrame(Enum):
    """Timeframe enumeration"""
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN = "1M"


@dataclass
class Kline:
    """K-line (candlestick) data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    turnover: Optional[float] = None

    def is_bullish(self) -> bool:
        """Check if candle is bullish (close > open)"""
        return self.close > self.open

    def is_bearish(self) -> bool:
        """Check if candle is bearish (close < open)"""
        return self.close < self.open

    def range(self) -> float:
        """Calculate candle range (high - low)"""
        return self.high - self.low

    def body_size(self) -> float:
        """Calculate body size (abs(close - open))"""
        return abs(self.close - self.open)


class KlineSeries:
    """K-line series (ordered collection)"""
    
    def __init__(self, symbol: str, timeframe: TimeFrame):
        self.symbol = symbol
        self.timeframe = timeframe
        self.klines: List[Kline] = []

    def push(self, kline: Kline):
        """Add a K-line"""
        self.klines.append(kline)

    def latest(self) -> Optional[Kline]:
        """Get the latest K-line"""
        return self.klines[-1] if self.klines else None

    def get(self, index: int) -> Optional[Kline]:
        """Get K-line at index (negative for from end)"""
        return self.klines[index] if index < len(self.klines) else None

    def __len__(self) -> int:
        return len(self.klines)

    def __iter__(self):
        return iter(self.klines)
