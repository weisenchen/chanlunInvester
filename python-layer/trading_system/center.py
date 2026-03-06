"""
Center (中枢) Detection Module
中枢检测模块 - 基于缠论第 18, 20, 63 课
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .kline import KlineSeries
from .segment import Segment


@dataclass
class Center:
    """中枢数据结构"""
    start_idx: int
    end_idx: int
    high: float  # 中枢上沿 (ZG)
    low: float   # 中枢下沿 (ZD)
    segments: List[Segment] = field(default_factory=list)
    level: str = "unknown"  # 中枢级别
    confirmed: bool = True
    
    @property
    def zg(self) -> float:
        """中枢上沿 (ZG)"""
        return self.high
    
    @property
    def zd(self) -> float:
        """中枢下沿 (ZD)"""
        return self.low
    
    @property
    def gg(self) -> float:
        """中枢最高点 (GG)"""
        return max(seg.end_price for seg in self.segments) if self.segments else self.high
    
    @property
    def dd(self) -> float:
        """中枢最低点 (DD)"""
        return min(seg.start_price for seg in self.segments) if self.segments else self.low
    
    @property
    def range(self) -> float:
        """中枢区间大小"""
        return self.high - self.low
    
    def contains(self, price: float) -> bool:
        """检查价格是否在中枢区间内"""
        return self.low <= price <= self.high


class CenterDetector:
    """
    中枢检测器
    
    中枢定义 (第 18 课):
    某级别走势类型中，被至少三个连续次级别走势类型所重叠的部分
    
    识别方法:
    1. 找到至少 3 个连续线段
    2. 计算重叠区间
    3. 确认中枢形成
    """
    
    def __init__(self, min_segments: int = 3):
        """
        初始化中枢检测器
        
        Args:
            min_segments: 形成中枢所需的最少线段数 (默认 3)
        """
        self.min_segments = min_segments
    
    def detect_centers(self, segments: List[Segment]) -> List[Center]:
        """
        从线段序列中检测中枢
        
        Args:
            segments: 线段列表
        
        Returns:
            中枢列表
        """
        if len(segments) < self.min_segments:
            return []
        
        centers = []
        i = 0
        
        while i <= len(segments) - self.min_segments:
            # 尝试从位置 i 开始构建中枢
            center = self._try_build_center(segments, i)
            
            if center:
                centers.append(center)
                # 移动到中枢结束后
                i = center.end_idx + 1
            else:
                i += 1
        
        return centers
    
    def _try_build_center(self, segments: List[Segment], start: int) -> Optional[Center]:
        """
        尝试从指定位置构建中枢
        
        中枢形成条件:
        1. 至少 3 个连续线段
        2. 线段之间有重叠区间
        3. 重叠区间稳定
        """
        if start >= len(segments):
            return None
        
        # 收集连续的线段
        center_segments = [segments[start]]
        i = start + 1
        
        while i < len(segments):
            seg = segments[i]
            
            # 检查是否与前一个线段有重叠
            if self._has_overlap(center_segments[-1], seg):
                center_segments.append(seg)
                
                # 检查是否满足中枢条件
                if len(center_segments) >= self.min_segments:
                    center = self._create_center(center_segments, start, i)
                    if center:
                        return center
            else:
                # 无重叠，重新开始
                if len(center_segments) >= self.min_segments:
                    center = self._create_center(center_segments, start, i - 1)
                    if center:
                        return center
                else:
                    center_segments = [seg]
            
            i += 1
        
        # 检查最后的线段组合
        if len(center_segments) >= self.min_segments:
            return self._create_center(center_segments, start, len(segments) - 1)
        
        return None
    
    def _has_overlap(self, seg1: Segment, seg2: Segment) -> bool:
        """
        检查两个线段是否有重叠
        
        重叠定义:
        两个线段的价格区间有交集
        """
        # 获取线段的价格区间
        seg1_low = min(seg1.start_price, seg1.end_price)
        seg1_high = max(seg1.start_price, seg1.end_price)
        
        seg2_low = min(seg2.start_price, seg2.end_price)
        seg2_high = max(seg2.start_price, seg2.end_price)
        
        # 检查是否有重叠
        return seg1_high >= seg2_low and seg2_high >= seg1_low
    
    def _calculate_overlap(self, segments: List[Segment]) -> Optional[Tuple[float, float]]:
        """
        计算多个线段的重叠区间
        
        Returns:
            (high, low) 重叠区间，如果无重叠则返回 None
        """
        if not segments:
            return None
        
        # 初始化重叠区间为第一个线段的区间
        overlap_high = max(segments[0].start_price, segments[0].end_price)
        overlap_low = min(segments[0].start_price, segments[0].end_price)
        
        # 依次与其他线段求交集
        for seg in segments[1:]:
            seg_high = max(seg.start_price, seg.end_price)
            seg_low = min(seg.start_price, seg.end_price)
            
            # 更新重叠区间
            overlap_high = min(overlap_high, seg_high)
            overlap_low = max(overlap_low, seg_low)
            
            # 如果无重叠，返回 None
            if overlap_high < overlap_low:
                return None
        
        return (overlap_high, overlap_low)
    
    def _create_center(self, segments: List[Segment], start_idx: int, 
                      end_idx: int) -> Optional[Center]:
        """
        创建中枢对象
        
        Args:
            segments: 构成中枢的线段列表
            start_idx: 中枢起始索引
            end_idx: 中枢结束索引
        
        Returns:
            Center 对象，如果无法形成中枢则返回 None
        """
        # 计算重叠区间
        overlap = self._calculate_overlap(segments)
        
        if not overlap:
            return None
        
        overlap_high, overlap_low = overlap
        
        # 检查重叠区间是否有效
        if overlap_high <= overlap_low:
            return None
        
        return Center(
            start_idx=start_idx,
            end_idx=end_idx,
            high=overlap_high,
            low=overlap_low,
            segments=segments.copy(),
            level="unknown",
            confirmed=True
        )
    
    def detect_center_extension(self, centers: List[Center]) -> List[Center]:
        """
        检测中枢延伸和扩张
        
        中枢延伸 (第 20 课):
        中枢形成后，后续走势继续在中枢区间内震荡
        
        中枢扩张:
        中枢延伸超过 9 段，级别扩张
        """
        extended_centers = []
        
        for center in centers:
            # 检查中枢段数
            if len(center.segments) >= 9:
                # 中枢扩张，级别升级
                extended_center = Center(
                    start_idx=center.start_idx,
                    end_idx=center.end_idx,
                    high=center.high,
                    low=center.low,
                    segments=center.segments.copy(),
                    level="expanded",  # 扩张级别
                    confirmed=True
                )
                extended_centers.append(extended_center)
            else:
                extended_centers.append(center)
        
        return extended_centers
    
    def detect_center_entry_exit(self, center: Center, 
                                segments: List[Segment]) -> dict:
        """
        检测中枢的进入段和离开段
        
        Returns:
            {
                'entry_segment': 进入段,
                'exit_segment': 离开段,
                'entry_price': 进入价格,
                'exit_price': 离开价格
            }
        """
        result = {
            'entry_segment': None,
            'exit_segment': None,
            'entry_price': None,
            'exit_price': None
        }
        
        # 找进入段 (中枢前的线段)
        if center.start_idx > 0:
            result['entry_segment'] = segments[center.start_idx - 1]
            result['entry_price'] = segments[center.start_idx - 1].end_price
        
        # 找离开段 (中枢后的线段)
        if center.end_idx < len(segments) - 1:
            result['exit_segment'] = segments[center.end_idx + 1]
            result['exit_price'] = segments[center.end_idx + 1].start_price
        
        return result


def test_center_detection():
    """测试中枢检测功能"""
    print("Testing center detection...")
    
    # 创建测试线段
    seg1 = Segment("up", 0, 10, 100.0, 105.0, 105.0 - 100.0, [], False, True)
    seg2 = Segment("down", 10, 20, 105.0, 102.0, 105.0 - 102.0, [], False, True)
    seg3 = Segment("up", 20, 30, 102.0, 104.0, 104.0 - 102.0, [], False, True)
    seg4 = Segment("down", 30, 40, 104.0, 103.0, 104.0 - 103.0, [], False, True)
    
    segments = [seg1, seg2, seg3, seg4]
    
    # 检测中枢
    detector = CenterDetector(min_segments=3)
    centers = detector.detect_centers(segments)
    
    print(f"  Segments: {len(segments)}")
    print(f"  Centers detected: {len(centers)}")
    
    if centers:
        for i, center in enumerate(centers):
            print(f"    Center {i+1}: ZG={center.high:.2f}, ZD={center.low:.2f}, Range={center.range:.2f}")
    
    return True


if __name__ == "__main__":
    test_center_detection()
