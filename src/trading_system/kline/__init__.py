"""
K-line Data Structures
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List
from enum import Enum


class TimeFrame(Enum):
    """时间周期"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY = "day"
    WEEK = "week"


@dataclass
class Kline:
    """K-line (蜡烛图) 数据结构"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def is_bullish(self) -> bool:
        """是否阳线"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """是否阴线"""
        return self.close < self.open
    
    @property
    def body(self) -> float:
        """实体大小"""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """上影线"""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """下影线"""
        return min(self.open, self.close) - self.low


@dataclass
class KlineSeries:
    """K 线序列"""
    klines: List[Kline]
    symbol: str = ""
    timeframe: str = ""
    
    def __len__(self) -> int:
        return len(self.klines)
    
    def __getitem__(self, idx: int) -> Kline:
        return self.klines[idx]
    
    @property
    def highs(self) -> List[float]:
        return [k.high for k in self.klines]
    
    @property
    def lows(self) -> List[float]:
        return [k.low for k in self.klines]
    
    @property
    def closes(self) -> List[float]:
        return [k.close for k in self.klines]
    
    @property
    def opens(self) -> List[float]:
        return [k.open for k in self.klines]
