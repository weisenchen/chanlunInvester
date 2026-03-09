#!/usr/bin/env python3
"""
示例 03: 线段划分
Example 03: Line Segment Division

对应课程：Lesson 67, 68, 71, 78
演示缠论线段划分的实现，包括特征序列分析

线段划分核心规则:
1. 线段由至少 3 笔组成
2. 使用特征序列判断线段结束
3. 两种情况：有缺口 vs 无缺口
4. 特征序列顶/底分型确认线段结束
"""

from pathlib import Path
import sys
# Add project root and python-layer to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / 'python-layer'))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Pen:
    """笔数据结构"""
    direction: str  # "up" or "down"
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    
    @property
    def is_up(self) -> bool:
        return self.direction == "up"
    
    @property
    def is_down(self) -> bool:
        return self.direction == "down"


@dataclass
class Segment:
    """线段数据结构"""
    direction: str  # "up" or "down"
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    pen_count: int
    feature_sequence: List[Pen]  # 特征序列
    has_gap: bool  # 特征序列是否有缺口
    confirmed: bool = True


class SegmentDetector:
    """线段检测器"""
    
    def __init__(self, min_pens: int = 3):
        """
        初始化线段检测器
        
        Args:
            min_pens: 线段最少包含的笔数 (默认 3)
        """
        self.min_pens = min_pens
    
    def detect_segments(self, pens: List[Pen]) -> List[Segment]:
        """
        从笔序列中检测线段
        
        算法步骤:
        1. 将笔按方向分组
        2. 构建特征序列
        3. 检测特征序列分型
        4. 判断是否有缺口
        5. 确认线段结束
        """
        if len(pens) < self.min_pens:
            return []
        
        segments = []
        i = 0
        
        while i <= len(pens) - self.min_pens:
            # 尝试从位置 i 开始构建线段
            segment = self._try_build_segment(pens, i)
            
            if segment:
                segments.append(segment)
                i = segment.end_idx + 1  # 移动到下一线段起点
            else:
                i += 1
        
        return segments
    
    def _try_build_segment(self, pens: List[Pen], start: int) -> Optional[Segment]:
        """尝试从指定位置构建线段"""
        if start >= len(pens):
            return None
        
        # 获取起始笔的方向
        first_pen = pens[start]
        direction = first_pen.direction
        
        # 收集同向笔作为特征序列
        feature_sequence = [first_pen]
        i = start + 1
        
        # 寻找后续的笔，构建特征序列
        while i < len(pens):
            pen = pens[i]
            
            # 特征序列只包含与线段同向的笔
            if pen.direction == direction:
                feature_sequence.append(pen)
                
                # 检查是否满足线段结束条件
                if len(feature_sequence) >= 2:
                    segment_end = self._check_segment_end(feature_sequence, pens, start, i)
                    if segment_end:
                        return segment_end
            
            i += 1
        
        return None
    
    def _check_segment_end(self, feature_seq: List[Pen], all_pens: List[Pen], 
                          segment_start: int, last_feature_idx: int) -> Optional[Segment]:
        """
        检查线段是否结束
        
        判断规则:
        1. 无缺口情况：特征序列形成顶/底分型 → 线段结束
        2. 有缺口情况：需要后续反向分型确认
        """
        if len(feature_seq) < 2:
            return None
        
        # 检查特征序列是否有缺口
        has_gap = self._check_gap(feature_seq)
        
        # 检查特征序列分型
        is_fractal = self._check_feature_fractal(feature_seq)
        
        if not is_fractal:
            return None
        
        # 无缺口情况：分型确认线段结束
        if not has_gap:
            return self._create_segment(feature_seq, all_pens, segment_start, last_feature_idx, has_gap)
        
        # 有缺口情况：需要后续确认
        # 这里简化处理，实际实现需要检查后续走势
        if len(feature_seq) >= 3:
            return self._create_segment(feature_seq, all_pens, segment_start, last_feature_idx, has_gap)
        
        return None
    
    def _check_gap(self, feature_seq: List[Pen]) -> bool:
        """
        检查特征序列是否有缺口
        
        缺口定义：
        - 上升线段：第一元素高点 < 第二元素低点
        - 下降线段：第一元素低点 > 第二元素高点
        """
        if len(feature_seq) < 2:
            return False
        
        elem1 = feature_seq[0]
        elem2 = feature_seq[1]
        
        if elem1.is_up:
            # 上升线段：检查是否有向上缺口
            return elem1.end_price < elem2.start_price
        else:
            # 下降线段：检查是否有向下缺口
            return elem1.end_price > elem2.start_price
    
    def _check_feature_fractal(self, feature_seq: List[Pen]) -> bool:
        """
        检查特征序列是否形成分型
        
        顶分型：中间元素高点最高
        底分型：中间元素低点最低
        """
        if len(feature_seq) < 3:
            # 简化：2 个元素也允许
            return True
        
        # 取最后 3 个元素检查分型
        last_three = feature_seq[-3:]
        
        if last_three[0].is_up:
            # 上升线段，检查顶分型
            middle_high = last_three[1].end_price
            return (middle_high > last_three[0].end_price and 
                    middle_high > last_three[2].end_price)
        else:
            # 下降线段，检查底分型
            middle_low = last_three[1].end_price
            return (middle_low < last_three[0].end_price and 
                    middle_low < last_three[2].end_price)
    
    def _create_segment(self, feature_seq: List[Pen], all_pens: List[Pen],
                       start_idx: int, last_feature_idx: int, has_gap: bool) -> Segment:
        """创建线段对象"""
        first_pen = all_pens[start_idx]
        last_pen = feature_seq[-1]
        
        # 计算线段包含的笔数
        pen_count = last_feature_idx - start_idx + 1
        
        return Segment(
            direction=first_pen.direction,
            start_idx=first_pen.start_idx,
            end_idx=last_pen.end_idx,
            start_price=first_pen.start_price,
            end_price=last_pen.end_price,
            pen_count=pen_count,
            feature_sequence=feature_seq,
            has_gap=has_gap,
            confirmed=True
        )


def generate_sample_data() -> tuple:
    """生成示例 K 线数据和笔"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 模拟一个完整的线段走势：上升线段 (3 笔) + 下降线段 (3 笔)
    price_pattern = [
        # 上升线段：3 笔 (上 - 下-上)
        100, 102, 101, 103, 102, 104, 103, 105, 104, 106,  # 第 1 笔 (上)
        105, 104, 103, 104, 103, 102,  # 第 2 笔 (下)
        103, 104, 105, 104, 106, 105, 107,  # 第 3 笔 (上) - 线段结束
        # 下降线段：3 笔 (下-上 - 下)
        106, 105, 104, 105, 104, 103,  # 第 4 笔 (下)
        104, 105, 106, 105, 106, 107,  # 第 5 笔 (上)
        106, 105, 104, 103, 102, 101,  # 第 6 笔 (下) - 线段结束
    ]
    
    for i, price in enumerate(price_pattern):
        high = price + 0.5
        low = price - 0.5
        open_price = price + (0.2 if i % 2 == 0 else -0.2)
        close_price = price - (0.2 if i % 2 == 0 else 0.2)
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=1000000 + i * 10000
        )
        klines.append(kline)
    
    kline_series = KlineSeries(klines=klines, symbol="000001.SZ", timeframe="30m")
    
    # 手动构建笔 (简化示例)
    pens = [
        Pen("up", 0, 9, 100.0, 106.0),      # 第 1 笔：上升
        Pen("down", 9, 15, 106.0, 102.0),   # 第 2 笔：下降
        Pen("up", 15, 22, 102.0, 107.0),    # 第 3 笔：上升 (第 1 线段结束)
        Pen("down", 22, 28, 107.0, 103.0),  # 第 4 笔：下降
        Pen("up", 28, 34, 103.0, 107.0),    # 第 5 笔：上升
        Pen("down", 34, 40, 107.0, 101.0),  # 第 6 笔：下降 (第 2 线段结束)
    ]
    
    return kline_series, pens


def print_segments(segments: List[Segment]):
    """打印线段识别结果"""
    print("\n" + "="*70)
    print("线段识别结果 (Segment Identification Results)")
    print("="*70)
    
    if not segments:
        print("未识别到有效的线段")
        return
    
    print(f"共识别 {len(segments)} 条线段:\n")
    
    for i, seg in enumerate(segments, 1):
        arrow = "↓" if seg.direction == "down" else "↑"
        gap_info = "有缺口" if seg.has_gap else "无缺口"
        
        print(f"线段 #{i} {arrow}")
        print(f"  方向：{seg.direction}")
        print(f"  K 线范围：#{seg.start_idx} → #{seg.end_idx}")
        print(f"  价格：{seg.start_price:.2f} → {seg.end_price:.2f}")
        print(f"  幅度：{abs(seg.end_price - seg.start_price):.2f} "
              f"({abs(seg.end_price - seg.start_price)/seg.start_price*100:.2f}%)")
        print(f"  包含笔数：{seg.pen_count} 笔")
        print(f"  特征序列：{len(seg.feature_sequence)} 个元素")
        print(f"  缺口情况：{gap_info}")
        print(f"  确认状态：{'已确认' if seg.confirmed else '待确认'}")
        print()


def print_feature_sequence_analysis(segments: List[Segment]):
    """打印特征序列分析"""
    print("\n" + "="*70)
    print("特征序列分析 (Feature Sequence Analysis)")
    print("="*70)
    
    for i, seg in enumerate(segments, 1):
        print(f"\n线段 #{i} ({seg.direction} 向):")
        print(f"  特征序列元素：")
        
        for j, pen in enumerate(seg.feature_sequence, 1):
            arrow = "↑" if pen.is_up else "↓"
            print(f"    元素{j}: {arrow} {pen.start_price:.2f} → {pen.end_price:.2f}")
        
        if seg.has_gap:
            print(f"  ⚠️  特征序列存在缺口 - 需要后续走势确认")
        else:
            print(f"  ✓  特征序列无缺口 - 分型确认线段结束")


def visualize_segments(kline_series: KlineSeries, segments: List[Segment]):
    """简单的 ASCII 可视化"""
    print("\n" + "="*70)
    print("线段走势可视化 (Segment Visualization)")
    print("="*70)
    
    klines = kline_series.klines
    prices = [(k.high + k.low) / 2 for k in klines]
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    height = 12
    rows = []
    
    for row in range(height):
        row_price = max_price - (row / height) * price_range
        row_str = f"{row_price:7.2f} |"
        
        for col, price in enumerate(prices):
            # 检查线段标记
            seg_marker = " "
            for seg in segments:
                if col == seg.start_idx:
                    seg_marker = "[" if seg.direction == "up" else "{"
                elif col == seg.end_idx:
                    seg_marker = "]" if seg.direction == "up" else "}"
            
            price_row = int((max_price - price) / price_range * height)
            
            if price_row == row:
                row_str += seg_marker if seg_marker != " " else "*"
            elif seg_marker != " " and abs(price_row - row) <= 1:
                row_str += seg_marker
            else:
                row_str += " "
        
        rows.append(row_str)
    
    for row in rows:
        print(row)
    
    print(" " * 8 + "+" + "-" * len(klines))
    print(" " * 8 + "0" + " " * (len(klines)//2 - 4) + "时间轴" + " " * (len(klines)//2 - 3) + str(len(klines)))
    
    print("\n图例：* = K 线，[ ] = 上升线段，{ } = 下降线段")


def main():
    print("\n" + "="*70)
    print("示例 03: 线段划分")
    print("Example 03: Line Segment Division")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例数据...")
    kline_series, pens = generate_sample_data()
    print(f"    K 线数量：{len(kline_series.klines)}")
    print(f"    笔数量：{len(pens)}")
    
    # 打印笔信息
    print("\n[2] 笔序列:")
    for i, pen in enumerate(pens, 1):
        arrow = "↑" if pen.is_up else "↓"
        print(f"    笔#{i} {arrow}: {pen.start_price:.2f} → {pen.end_price:.2f}")
    
    # 检测线段
    print("\n[3] 检测线段...")
    detector = SegmentDetector(min_pens=3)
    segments = detector.detect_segments(pens)
    print(f"    识别到 {len(segments)} 条线段")
    
    # 打印结果
    print_segments(segments)
    
    # 特征序列分析
    print_feature_sequence_analysis(segments)
    
    # 可视化
    visualize_segments(kline_series, segments)
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "pen_count": len(pens),
        "segment_count": len(segments),
        "segments": [
            {
                "direction": seg.direction,
                "start_idx": seg.start_idx,
                "end_idx": seg.end_idx,
                "start_price": seg.start_price,
                "end_price": seg.end_price,
                "pen_count": seg.pen_count,
                "has_gap": seg.has_gap,
                "confirmed": seg.confirmed,
                "feature_sequence_length": len(seg.feature_sequence)
            }
            for seg in segments
        ]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 03 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
