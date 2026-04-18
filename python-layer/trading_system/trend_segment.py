"""
趋势段识别模块 - Trend Segment Identification
缠论 v7.0 核心模块

功能:
1. 将线段序列划分为不同的趋势段
2. 识别趋势逆转点
3. 确定趋势段的起点和终点
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class TrendSegment:
    """趋势段数据结构"""
    index: int  # 趋势段序号
    trend: str  # 'up', 'down', 'sideways'
    segments: List = field(default_factory=list)  # 包含的线段
    start_date: datetime = None
    end_date: datetime = None
    start_price: float = 0.0
    end_price: float = 0.0
    center_count: int = 0  # 中枢数量
    stage: str = 'unknown'  # 诞生期/成长期/成熟期/衰退期
    
    @property
    def duration(self):
        """趋势段持续时间"""
        if self.start_date and self.end_date:
            return self.end_date - self.start_date
        return None
    
    @property
    def price_change(self):
        """价格变化"""
        return self.end_price - self.start_price
    
    @property
    def price_change_percent(self):
        """价格变化百分比"""
        if self.start_price > 0:
            return (self.end_price - self.start_price) / self.start_price * 100
        return 0.0


class TrendSegmentIdentifier:
    """
    趋势段识别器
    
    核心逻辑:
    1. 遍历线段序列
    2. 检测趋势方向变化
    3. 识别关键位置突破
    4. 划分趋势段
    """
    
    def __init__(self):
        """初始化识别器"""
        # 趋势逆转判断参数
        self.REVERSAL_THRESHOLD = 0.05  # 5% 突破阈值
        self.MIN_SEGMENTS_FOR_TREND = 2  # 最少线段数形成趋势
    
    def identify(self, segments: List) -> List[TrendSegment]:
        """
        识别趋势段
        
        Args:
            segments: 线段列表
        
        Returns:
            趋势段列表
        """
        if not segments or len(segments) < self.MIN_SEGMENTS_FOR_TREND:
            return []
        
        trend_segments = []
        current_trend = None
        current_segments = []
        trend_index = 0
        
        for seg in segments:
            if current_trend is None:
                # 第一个线段，确定初始趋势
                current_trend = seg['direction']
                current_segments = [seg]
            elif seg['direction'] == current_trend:
                # 同向线段，延续当前趋势
                current_segments.append(seg)
            else:
                # 反向线段，检查是否趋势逆转
                if self._is_trend_reversal(current_segments, seg):
                    # 趋势逆转，保存当前趋势段
                    trend_index += 1
                    trend_seg = self._create_trend_segment(
                        trend_index, current_trend, current_segments
                    )
                    trend_segments.append(trend_seg)
                    
                    # 开始新趋势段
                    current_trend = seg['direction']
                    current_segments = [seg]
                else:
                    # 只是回调/反弹，延续当前趋势
                    current_segments.append(seg)
        
        # 保存最后一个趋势段
        if current_segments:
            trend_index += 1
            trend_seg = self._create_trend_segment(
                trend_index, current_trend, current_segments
            )
            trend_segments.append(trend_seg)
        
        return trend_segments
    
    def _is_trend_reversal(self, segments: List, new_seg) -> bool:
        """
        判断是否趋势逆转
        
        条件:
        1. 跌破/突破关键位置 (中枢边界)
        2. 力度明显减弱
        3. 连续反向线段
        """
        if len(segments) < self.MIN_SEGMENTS_FOR_TREND:
            return False
        
        # 获取最后一个中枢 (如果有)
        from .center import CenterDetector
        from .segment import Segment
        
        # 转换为 Segment 对象
        seg_objects = []
        for s in segments:
            seg_objects.append(Segment(
                direction=s['direction'],
                start_idx=s['start_idx'],
                end_idx=s['end_idx'],
                start_price=s['start_price'],
                end_price=s['end_price'],
                pen_count=2,
                feature_sequence=[],
                has_gap=False,
                confirmed=True
            ))
        
        center_det = CenterDetector(min_segments=2)
        centers = center_det.detect_centers(seg_objects)
        
        if centers:
            last_center = centers[-1]
            
            # 上涨趋势逆转判断 (跌破中枢下沿)
            if segments[0]['direction'] == 'up':
                if new_seg['end_price'] < last_center.zd * (1 - self.REVERSAL_THRESHOLD):
                    return True
            
            # 下跌趋势逆转判断 (突破中枢上沿)
            elif segments[0]['direction'] == 'down':
                if new_seg['end_price'] > last_center.zg * (1 + self.REVERSAL_THRESHOLD):
                    return True
        
        # 没有中枢，检查价格突破
        if segments[0]['direction'] == 'up':
            # 跌破起点
            min_price = min(s['start_price'] for s in segments)
            if new_seg['end_price'] < min_price * (1 - self.REVERSAL_THRESHOLD):
                return True
        elif segments[0]['direction'] == 'down':
            # 突破起点
            max_price = max(s['start_price'] for s in segments)
            if new_seg['end_price'] > max_price * (1 + self.REVERSAL_THRESHOLD):
                return True
        
        return False
    
    def _create_trend_segment(self, index: int, trend: str, segments: List) -> TrendSegment:
        """创建趋势段对象"""
        start_date = segments[0]['start_date'] if 'start_date' in segments[0] else None
        end_date = segments[-1]['end_date'] if 'end_date' in segments[-1] else None
        start_price = segments[0]['start_price']
        end_price = segments[-1]['end_price']
        
        # 检测中枢数量
        from .center import CenterDetector
        from .segment import Segment
        
        seg_objects = []
        for s in segments:
            seg_objects.append(Segment(
                direction=s['direction'],
                start_idx=s['start_idx'],
                end_idx=s['end_idx'],
                start_price=s['start_price'],
                end_price=s['end_price'],
                pen_count=2,
                feature_sequence=[],
                has_gap=False,
                confirmed=True
            ))
        
        center_det = CenterDetector(min_segments=2)
        centers = center_det.detect_centers(seg_objects)
        center_count = len(centers)
        
        # 确定趋势阶段
        if center_count == 0:
            stage = '形成期'
        elif center_count == 1:
            stage = '诞生期'
        elif center_count == 2:
            stage = '成长期'
        elif center_count == 3:
            stage = '成熟期'
        else:
            stage = '衰退期'
        
        return TrendSegment(
            index=index,
            trend=trend,
            segments=segments,
            start_date=start_date,
            end_date=end_date,
            start_price=start_price,
            end_price=end_price,
            center_count=center_count,
            stage=stage
        )


def identify_trend_segments(segments: List) -> List[TrendSegment]:
    """便捷函数：识别趋势段"""
    identifier = TrendSegmentIdentifier()
    return identifier.identify(segments)


# 测试函数
def test_trend_segment_identifier():
    """测试趋势段识别"""
    print("=" * 70)
    print("趋势段识别器 - 测试")
    print("=" * 70)
    print()
    
    # 模拟线段数据
    test_segments = [
        {'direction': 'up', 'start_idx': 0, 'end_idx': 2, 'start_price': 100, 'end_price': 110, 'start_date': datetime(2025, 1, 1), 'end_date': datetime(2025, 1, 3)},
        {'direction': 'up', 'start_idx': 2, 'end_idx': 4, 'start_price': 110, 'end_price': 120, 'start_date': datetime(2025, 1, 3), 'end_date': datetime(2025, 1, 5)},
        {'direction': 'down', 'start_idx': 4, 'end_idx': 6, 'start_price': 120, 'end_price': 115, 'start_date': datetime(2025, 1, 5), 'end_date': datetime(2025, 1, 7)},
        {'direction': 'down', 'start_idx': 6, 'end_idx': 8, 'start_price': 115, 'end_price': 105, 'start_date': datetime(2025, 1, 7), 'end_date': datetime(2025, 1, 9)},
        {'direction': 'down', 'start_idx': 8, 'end_idx': 10, 'start_price': 105, 'end_price': 95, 'start_date': datetime(2025, 1, 9), 'end_date': datetime(2025, 1, 11)},
    ]
    
    # 识别趋势段
    identifier = TrendSegmentIdentifier()
    trend_segments = identifier.identify(test_segments)
    
    print(f"输入线段数：{len(test_segments)}")
    print(f"输出趋势段数：{len(trend_segments)}")
    print()
    
    for ts in trend_segments:
        print(f"趋势段 {ts.index}:")
        print(f"  方向：{ts.trend}")
        print(f"  线段数：{len(ts.segments)}")
        print(f"  中枢数：{ts.center_count}")
        print(f"  阶段：{ts.stage}")
        print(f"  起点：${ts.start_price:.2f} ({ts.start_date})")
        print(f"  终点：${ts.end_price:.2f} ({ts.end_date})")
        print(f"  变化：${ts.price_change:.2f} ({ts.price_change_percent:+.1f}%)")
        print()
    
    return trend_segments


if __name__ == "__main__":
    print("趋势段识别模块已加载 ✅")
    print("使用示例:")
    print("  from trading_system.trend_segment import identify_trend_segments")
    print("  trend_segments = identify_trend_segments(segments)")
