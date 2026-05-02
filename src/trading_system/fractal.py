"""
Fractal (分型) Detection
"""

from dataclasses import dataclass
from typing import List, Optional
from .kline import Kline, KlineSeries


@dataclass
class Fractal:
    """分型数据结构"""
    is_top: bool  # True=顶分型，False=底分型
    kline_index: int
    price: float  # 顶分型为 high, 底分型为 low
    confirmed: bool = True


class FractalDetector:
    """分型检测器"""
    
    def __init__(self, strict: bool = True):
        """
        初始化分型检测器
        
        Args:
            strict: 是否严格模式 (要求中间 K 线最高/最低)
        """
        self.strict = strict
    
    def detect_all(self, series: KlineSeries) -> List[Fractal]:
        """检测所有分型"""
        fractals = []
        klines = series.klines
        
        if len(klines) < 3:
            return fractals
        
        for i in range(1, len(klines) - 1):
            # 检查顶分型
            if self._is_top_fractal(klines, i):
                fractals.append(Fractal(
                    is_top=True,
                    kline_index=i,
                    price=klines[i].high,
                    confirmed=True
                ))
            # 检查底分型
            elif self._is_bottom_fractal(klines, i):
                fractals.append(Fractal(
                    is_top=False,
                    kline_index=i,
                    price=klines[i].low,
                    confirmed=True
                ))
        
        return fractals
    
    def _is_top_fractal(self, klines: List[Kline], idx: int) -> bool:
        """检查是否为顶分型"""
        if idx < 1 or idx >= len(klines) - 1:
            return False
        
        mid_high = klines[idx].high
        left_high = klines[idx - 1].high
        right_high = klines[idx + 1].high
        
        if self.strict:
            return mid_high > left_high and mid_high > right_high
        else:
            return mid_high >= left_high and mid_high >= right_high
    
    def _is_bottom_fractal(self, klines: List[Kline], idx: int) -> bool:
        """检查是否为底分型"""
        if idx < 1 or idx >= len(klines) - 1:
            return False
        
        mid_low = klines[idx].low
        left_low = klines[idx - 1].low
        right_low = klines[idx + 1].low
        
        if self.strict:
            return mid_low < left_low and mid_low < right_low
        else:
            return mid_low <= left_low and mid_low <= right_low
    
    def detect_tops(self, series: KlineSeries) -> List[Fractal]:
        """只检测顶分型"""
        all_fractals = self.detect_all(series)
        return [f for f in all_fractals if f.is_top]
    
    def detect_bottoms(self, series: KlineSeries) -> List[Fractal]:
        """只检测底分型"""
        all_fractals = self.detect_all(series)
        return [f for f in all_fractals if not f.is_top]
