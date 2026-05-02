"""
Segment (线段) Implementation - Python Backup Layer
"""

from dataclasses import dataclass
from typing import List, Optional
from .kline import KlineSeries
from .pen import Pen, PenDirection


@dataclass
class Segment:
    """线段数据结构"""
    direction: str  # "up" or "down"
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    pen_count: int = 0
    feature_sequence: List[Pen] = None
    has_gap: bool = False
    confirmed: bool = True
    
    def __post_init__(self):
        if self.feature_sequence is None:
            self.feature_sequence = []
    
    @property
    def is_up(self) -> bool:
        return self.direction == "up"
    
    @property
    def is_down(self) -> bool:
        return self.direction == "down"
    
    @property
    def magnitude(self) -> float:
        return abs(self.end_price - self.start_price)


class SegmentCalculator:
    """线段计算器"""
    
    def __init__(self, min_pens: int = 3):
        """
        初始化线段计算器
        
        Args:
            min_pens: 线段最少包含的笔数
        """
        self.min_pens = min_pens
    
    def detect_segments(self, pens: List[Pen]) -> List[Segment]:
        """从笔序列检测线段"""
        if len(pens) < self.min_pens:
            return []
        
        segments = []
        i = 0
        
        while i <= len(pens) - self.min_pens:
            segment = self._try_build_segment(pens, i)
            
            if segment:
                segments.append(segment)
                i = segment.end_idx + 1
            else:
                i += 1
        
        return segments
    
    def _try_build_segment(self, pens: List[Pen], start: int) -> Optional[Segment]:
        """尝试构建线段"""
        if start >= len(pens):
            return None
        
        first_pen = pens[start]
        direction = first_pen.direction.value if isinstance(first_pen.direction, PenDirection) else first_pen.direction
        
        # 收集特征序列
        feature_sequence = [first_pen]
        
        for i in range(start + 1, len(pens)):
            pen = pens[i]
            pen_dir = pen.direction.value if isinstance(pen.direction, PenDirection) else pen.direction
            
            if pen_dir == direction:
                feature_sequence.append(pen)
                
                # 检查线段结束
                if len(feature_sequence) >= 2:
                    has_gap = self._check_gap(feature_sequence)
                    is_fractal = self._check_feature_fractal(feature_sequence)
                    
                    if is_fractal:
                        last_pen = feature_sequence[-1]
                        last_idx = i
                        
                        return Segment(
                            direction=direction,
                            start_idx=first_pen.start_idx,
                            end_idx=last_pen.end_idx,
                            start_price=first_pen.start_price,
                            end_price=last_pen.end_price,
                            pen_count=last_idx - start + 1,
                            feature_sequence=feature_sequence,
                            has_gap=has_gap,
                            confirmed=True
                        )
        
        return None
    
    def _check_gap(self, feature_seq: List[Pen]) -> bool:
        """检查特征序列是否有缺口"""
        if len(feature_seq) < 2:
            return False
        
        elem1 = feature_seq[0]
        elem2 = feature_seq[1]
        
        dir1 = elem1.direction.value if isinstance(elem1.direction, PenDirection) else elem1.direction
        
        if dir1 == "up":
            return elem1.end_price < elem2.start_price
        else:
            return elem1.end_price > elem2.start_price
    
    def _check_feature_fractal(self, feature_seq: List[Pen]) -> bool:
        """检查特征序列分型"""
        if len(feature_seq) < 2:
            return True
        
        if len(feature_seq) >= 3:
            last_three = feature_seq[-3:]
            dir1 = last_three[0].direction.value if isinstance(last_three[0].direction, PenDirection) else last_three[0].direction
            
            if dir1 == "up":
                middle_high = last_three[1].end_price
                return middle_high > last_three[0].end_price and middle_high > last_three[2].end_price
            else:
                middle_low = last_three[1].end_price
                return middle_low < last_three[0].end_price and middle_low < last_three[2].end_price
        
        return True
