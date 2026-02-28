"""
Fractal Detection - Python Implementation
Backup layer for Rust engine
"""

from typing import List, Optional, Tuple
from enum import Enum
from .kline import Kline


class FractalType(Enum):
    """Fractal type"""
    TOP = "top"      # 顶分型
    BOTTOM = "bottom" # 底分型


class Fractal:
    """Fractal structure"""
    
    def __init__(self, ftype: FractalType, index: int, klines: List[Kline]):
        self.type = ftype
        self.index = index
        self.high = klines[1].high if ftype == FractalType.TOP else max(k[1].high for k in [klines])
        self.low = klines[1].low if ftype == FractalType.BOTTOM else min(k[1].low for k in [klines])
        self.time = klines[1].timestamp

    def __repr__(self):
        return f"Fractal({self.type.value} @ {self.time}, price={self.high if self.type == FractalType.TOP else self.low})"


class FractalDetector:
    """Fractal detector with containment handling"""
    
    def __init__(self):
        pass

    def detect_fractals(self, klines: List[Kline]) -> List[Fractal]:
        """Detect all fractals in K-line series"""
        if len(klines) < 3:
            return []

        # First, handle containment relationships
        processed = self._process_containment(klines)
        
        fractals = []
        for i in range(1, len(processed) - 1):
            if self._is_top_fractal(processed, i):
                fractals.append(Fractal(FractalType.TOP, i, processed[i-1:i+2]))
            elif self._is_bottom_fractal(processed, i):
                fractals.append(Fractal(FractalType.BOTTOM, i, processed[i-1:i+2]))
        
        return fractals

    def _process_containment(self, klines: List[Kline]) -> List[Kline]:
        """Process containment relationships (包含关系处理)"""
        if not klines:
            return []

        result = [klines[0]]
        
        for i in range(1, len(klines)):
            prev = result[-1]
            curr = klines[i]
            
            # Check for containment
            if (curr.high <= prev.high and curr.low >= prev.low) or \
               (curr.high >= prev.high and curr.low <= prev.low):
                # Merge: determine direction from previous trend
                if len(result) > 1:
                    direction = 1 if result[-1].high > result[-2].high else -1
                else:
                    direction = 1
                
                if direction > 0:  # Upward
                    # 高高 + 低高
                    merged_high = max(prev.high, curr.high)
                    merged_low = max(prev.low, curr.low)
                else:  # Downward
                    # 低低 + 高低
                    merged_high = min(prev.high, curr.high)
                    merged_low = min(prev.low, curr.low)
                
                # Create merged K-line
                merged = Kline(
                    timestamp=curr.timestamp,
                    open=curr.open,
                    high=merged_high,
                    low=merged_low,
                    close=curr.close,
                    volume=prev.volume + curr.volume
                )
                result[-1] = merged
            else:
                result.append(curr)
        
        return result

    def _is_top_fractal(self, klines: List[Kline], index: int) -> bool:
        """Check if index is a top fractal (顶分型)"""
        if index < 1 or index >= len(klines) - 1:
            return False
        
        return (klines[index].high > klines[index-1].high and 
                klines[index].high > klines[index+1].high and
                klines[index].low > klines[index-1].low and
                klines[index].low > klines[index+1].low)

    def _is_bottom_fractal(self, klines: List[Kline], index: int) -> bool:
        """Check if index is a bottom fractal (底分型)"""
        if index < 1 or index >= len(klines) - 1:
            return False
        
        return (klines[index].low < klines[index-1].low and 
                klines[index].low < klines[index+1].low and
                klines[index].high < klines[index-1].high and
                klines[index].high < klines[index+1].high)
