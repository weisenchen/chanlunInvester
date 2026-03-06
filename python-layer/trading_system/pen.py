"""
Pen (笔) Implementation - Python Backup Layer
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from .kline import Kline, KlineSeries
from .fractal import FractalDetector, Fractal


class PenDirection(Enum):
    """笔方向"""
    UP = "up"
    DOWN = "down"


@dataclass
class Pen:
    """笔数据结构"""
    direction: PenDirection
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    confirmed: bool = False
    
    @property
    def is_up(self) -> bool:
        return self.direction == PenDirection.UP
    
    @property
    def is_down(self) -> bool:
        return self.direction == PenDirection.DOWN
    
    @property
    def magnitude(self) -> float:
        return abs(self.end_price - self.start_price)
    
    @property
    def kline_count(self) -> int:
        return self.end_idx - self.start_idx + 1
    
    def kline_count_func(self) -> int:
        """Method alias for compatibility"""
        return self.kline_count


@dataclass
class PenConfig:
    """笔配置"""
    use_new_definition: bool = True  # 新 3K 线定义
    strict_validation: bool = True
    min_klines_between_turns: int = 3


class PenCalculator:
    """笔计算器"""
    
    def __init__(self, config: PenConfig = None):
        self.config = config or PenConfig()
        self.fractal_detector = FractalDetector()
    
    def identify_pens(self, series: KlineSeries) -> List[Pen]:
        """识别所有笔"""
        if len(series) < 3:
            return []
        
        fractals = self.fractal_detector.detect_all(series)
        pens = []
        
        # 连接相邻分型形成笔
        for i in range(len(fractals) - 1):
            curr = fractals[i]
            next_f = fractals[i + 1]
            
            # 检查 K 线数量
            kline_count = next_f.kline_index - curr.kline_index + 1
            if kline_count < self.config.min_klines_between_turns:
                continue
            
            # 确定方向
            if curr.is_top:
                direction = PenDirection.DOWN
                start_price = curr.price
                end_price = next_f.price
            else:
                direction = PenDirection.UP
                start_price = curr.price
                end_price = next_f.price
            
            pen = Pen(
                direction=direction,
                start_idx=curr.kline_index,
                end_idx=next_f.kline_index,
                start_price=start_price,
                end_price=end_price,
                confirmed=True
            )
            pens.append(pen)
        
        return pens
    
    def identify_pens_new_definition(self, series: KlineSeries) -> List[Pen]:
        """使用新 3K 线定义识别笔"""
        return self.identify_pens(series)
