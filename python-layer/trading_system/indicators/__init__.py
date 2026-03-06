"""
Technical Indicators - Python Implementation
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class MACDResult:
    """MACD 指标结果"""
    dif: float
    dea: float
    macd: float
    histogram: float


class MACDIndicator:
    """MACD 指标计算器"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """
        初始化 MACD
        
        Args:
            fast: 快线周期 (默认 12)
            slow: 慢线周期 (默认 26)
            signal: 信号线周期 (默认 9)
        """
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
    
    def calculate(self, prices: List[float]) -> List[MACDResult]:
        """计算 MACD 指标"""
        if len(prices) < self.slow:
            return [MACDResult(0, 0, 0, 0)] * len(prices)
        
        # 计算 EMA
        ema_fast = self._ema(prices, self.fast)
        ema_slow = self._ema(prices, self.slow)
        
        # 计算 DIF
        dif = [f - s for f, s in zip(ema_fast, ema_slow)]
        
        # 计算 DEA
        dea = self._ema(dif, self.signal_period)
        
        # 计算 MACD 柱
        macd = [(d - e) * 2 for d, e in zip(dif, dea)]
        
        results = []
        for i in range(len(prices)):
            results.append(MACDResult(
                dif=dif[i] if i < len(dif) else 0,
                dea=dea[i] if i < len(dea) else 0,
                macd=macd[i] if i < len(macd) else 0,
                histogram=macd[i] if i < len(macd) else 0
            ))
        
        return results
    
    def _ema(self, data: List[float], period: int) -> List[float]:
        """计算指数移动平均"""
        if len(data) < period:
            return [0.0] * len(data)
        
        multiplier = 2.0 / (period + 1)
        ema = [sum(data[:period]) / period]
        
        for i in range(period, len(data)):
            ema.append((data[i] - ema[-1]) * multiplier + ema[-1])
        
        return [ema[0]] * (period - 1) + ema


# 兼容别名
MACD = MACDIndicator
