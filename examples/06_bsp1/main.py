#!/usr/bin/env python3
"""
示例 06: 第一类买卖点详解
Example 06: Type 1 Buy/Sell Points (Trend Divergence Points)

对应课程：Lesson 12, 21, 24, 27
深入演示第一类买卖点的识别和确认

第一类买卖点定义:
- 第一类买点：下降趋势背驰后的最低点 (风险最大，收益最大)
- 第一类卖点：上升趋势背驰后的最高点

确认条件:
1. 明确的趋势 (至少 2 个同向线段)
2. 背驰确认 (价格创新低/高，MACD 不创新低/高)
3. 背驰强度足够 (>0.3)
"""

import sys
sys.path.insert(0, '/home/wei/.openclaw/workspace/trading-system/python-layer')

from trading_system.kline import Kline, KlineSeries
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math


@dataclass
class Segment:
    """线段数据结构"""
    direction: str
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float


@dataclass
class BSP1:
    """第一类买卖点"""
    type: str  # "buy1" or "sell1"
    idx: int
    price: float
    segment_idx: int  # 所属线段索引
    divergence_strength: float
    confidence: float
    description: str
    risk_reward_ratio: float


class BSP1Detector:
    """第一类买卖点检测器"""
    
    def __init__(self, min_segments: int = 2, divergence_threshold: float = 0.3):
        """
        初始化检测器
        
        Args:
            min_segments: 最小线段数 (形成趋势)
            divergence_threshold: 背驰强度阈值
        """
        self.min_segments = min_segments
        self.divergence_threshold = divergence_threshold
    
    def detect(self, kline_series: KlineSeries, 
               segments: List[Segment]) -> List[BSP1]:
        """
        检测第一类买卖点
        
        算法步骤:
        1. 寻找连续同向线段 (形成趋势)
        2. 计算相邻线段的背驰
        3. 确认背驰强度
        4. 定位买卖点
        """
        if len(segments) < self.min_segments:
            return []
        
        bsp1_list = []
        klines = kline_series.klines
        
        # 计算 MACD
        prices = [(k.high + k.low) / 2 for k in klines]
        macd_data = self._calculate_macd(prices)
        
        # 寻找趋势背驰
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]
            
            # 必须是同向线段
            if seg1.direction != seg2.direction:
                continue
            
            # 获取 MACD 值
            macd1 = macd_data[seg1.end_idx]['histogram']
            macd2 = macd_data[seg2.end_idx]['histogram']
            
            bsp1 = None
            
            if seg1.direction == "down":
                # 下降趋势：检查底背驰 (买点 1)
                if seg2.end_price < seg1.end_price:  # 价格创新低
                    if macd2 > macd1:  # MACD 未创新低 (底背驰)
                        strength = abs(macd1 - macd2) / max(abs(macd1), 0.001)
                        
                        if strength >= self.divergence_threshold:
                            # 计算风险收益比
                            rr_ratio = self._calculate_rr_ratio(segments, i + 1, "buy")
                            
                            bsp1 = BSP1(
                                type="buy1",
                                idx=seg2.end_idx,
                                price=seg2.end_price,
                                segment_idx=i + 1,
                                divergence_strength=strength,
                                confidence=min(strength, 0.9),
                                description=f"第一类买点：{seg2.end_price:.2f}, 背驰强度{strength:.2f}",
                                risk_reward_ratio=rr_ratio
                            )
            
            elif seg1.direction == "up":
                # 上升趋势：检查顶背驰 (卖点 1)
                if seg2.end_price > seg1.end_price:  # 价格创新高
                    if macd2 < macd1:  # MACD 未创新高 (顶背驰)
                        strength = abs(macd1 - macd2) / max(abs(macd1), 0.001)
                        
                        if strength >= self.divergence_threshold:
                            rr_ratio = self._calculate_rr_ratio(segments, i + 1, "sell")
                            
                            bsp1 = BSP1(
                                type="sell1",
                                idx=seg2.end_idx,
                                price=seg2.end_price,
                                segment_idx=i + 1,
                                divergence_strength=strength,
                                confidence=min(strength, 0.9),
                                description=f"第一类卖点：{seg2.end_price:.2f}, 背驰强度{strength:.2f}",
                                risk_reward_ratio=rr_ratio
                            )
            
            if bsp1:
                bsp1_list.append(bsp1)
        
        return bsp1_list
    
    def _calculate_macd(self, prices: List[float]) -> List[dict]:
        """计算 MACD 指标"""
        if len(prices) < 26:
            return [{'histogram': 0}] * len(prices)
        
        # 简化 MACD 计算
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        dif = [e1 - e2 for e1, e2 in zip(ema12, ema26)]
        dea = self._ema(dif, 9)
        macd = [(d - e) * 2 for d, e in zip(dif, dea)]
        
        return [{'histogram': m} for m in macd]
    
    def _ema(self, data: List[float], period: int) -> List[float]:
        """计算 EMA"""
        if len(data) < period:
            return [0] * len(data)
        
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]
        
        for i in range(period, len(data)):
            ema.append((data[i] - ema[-1]) * multiplier + ema[-1])
        
        return [ema[0]] * (period - 1) + ema
    
    def _calculate_rr_ratio(self, segments: List[Segment], 
                           seg_idx: int, direction: str) -> float:
        """
        计算风险收益比
        
        买点：止损 = 前低 -2%, 目标 = 前高
        卖点：止损 = 前高 +2%, 目标 = 前低
        """
        if seg_idx >= len(segments):
            return 0.0
        
        current_seg = segments[seg_idx]
        
        if direction == "buy":
            # 找前一个高点作为目标
            if seg_idx >= 1:
                prev_high = segments[seg_idx - 1].start_price
                stop_loss = current_seg.end_price * 0.98
                reward = prev_high - current_seg.end_price
                risk = current_seg.end_price - stop_loss
                return reward / risk if risk > 0 else 0.0
        else:
            # 找前一个低点作为目标
            if seg_idx >= 1:
                prev_low = segments[seg_idx - 1].start_price
                stop_loss = current_seg.end_price * 1.02
                reward = current_seg.end_price - prev_low
                risk = stop_loss - current_seg.end_price
                return reward / risk if risk > 0 else 0.0
        
        return 0.0


def generate_sample_data() -> tuple:
    """生成第一类买卖点示例数据"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 模拟一个完整的下降趋势 + 底背驰走势
    # 用于演示第一类买点
    price_pattern = [
        # 第一段下降
        100, 98, 96, 94, 92, 90, 88,
        # 反弹
        89, 91, 93, 92, 91,
        # 第二段下降 (创新低，力度减弱 - 背驰)
        90, 88, 86, 84, 83, 82, 81,  # 创新低 81
        # 确认上升
        82, 84, 86, 88, 90, 92, 94, 96
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
    
    # 定义线段
    segments = [
        Segment("down", 0, 6, 100.0, 88.0),   # 下降段 1
        Segment("up", 6, 11, 88.0, 93.0),     # 反弹段
        Segment("down", 11, 18, 93.0, 81.0),  # 下降段 2 (背驰段，买点 1)
        Segment("up", 18, 25, 81.0, 96.0),    # 上升段
    ]
    
    return kline_series, segments


def print_bsp1_detail(bsp1: BSP1, kline_series: KlineSeries):
    """打印第一类买卖点详情"""
    klines = kline_series.klines
    
    print("\n" + "="*70)
    if bsp1.type == "buy1":
        print("🟢 第一类买点详情 (Type 1 Buy Point)")
    else:
        print("🔴 第一类卖点详情 (Type 1 Sell Point)")
    print("="*70)
    
    print(f"\n位置信息:")
    print(f"  K 线索引：#{bsp1.idx}")
    print(f"  时间：{klines[bsp1.idx].timestamp}")
    print(f"  价格：{bsp1.price:.2f}")
    
    print(f"\n背驰分析:")
    print(f"  所属线段：#{bsp1.segment_idx}")
    print(f"  背驰强度：{bsp1.divergence_strength:.2f} "
          f"({'强' if bsp1.divergence_strength > 0.5 else '中' if bsp1.divergence_strength > 0.3 else '弱'})")
    print(f"  置信度：{bsp1.confidence:.0%}")
    
    print(f"\n风险评估:")
    print(f"  风险收益比：1:{bsp1.risk_reward_ratio:.2f}")
    if bsp1.risk_reward_ratio >= 3:
        print(f"  评级：⭐⭐⭐⭐⭐ 优秀 (RR >= 3)")
    elif bsp1.risk_reward_ratio >= 2:
        print(f"  评级：⭐⭐⭐⭐ 良好 (RR >= 2)")
    elif bsp1.risk_reward_ratio >= 1:
        print(f"  评级：⭐⭐⭐ 一般 (RR >= 1)")
    else:
        print(f"  评级：⭐⭐ 较差 (RR < 1)")
    
    print(f"\n操作建议:")
    print(f"  {bsp1.description}")
    
    if bsp1.type == "buy1":
        stop_loss = bsp1.price * 0.98
        target1 = bsp1.price * 1.05
        target2 = bsp1.price * 1.10
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (-2%)")
        print(f"  目标 1: {target1:.2f} (+5%)")
        print(f"  目标 2: {target2:.2f} (+10%)")
    else:
        stop_loss = bsp1.price * 1.02
        target1 = bsp1.price * 0.95
        target2 = bsp1.price * 0.90
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (+2%)")
        print(f"  目标 1: {target1:.2f} (-5%)")
        print(f"  目标 2: {target2:.2f} (-10%)")


def print_trend_analysis(segments: List[Segment]):
    """打印趋势分析"""
    print("\n" + "="*70)
    print("趋势分析 (Trend Analysis)")
    print("="*70)
    
    print(f"\n共 {len(segments)} 个线段:")
    
    for i, seg in enumerate(segments):
        arrow = "↓" if seg.direction == "down" else "↑"
        change = seg.end_price - seg.start_price
        pct = change / seg.start_price * 100
        
        print(f"\n线段 #{i} {arrow}")
        print(f"  方向：{seg.direction}")
        print(f"  范围：K 线 #{seg.start_idx} → #{seg.end_idx}")
        print(f"  价格：{seg.start_price:.2f} → {seg.end_price:.2f}")
        print(f"  变化：{change:+.2f} ({pct:+.2f}%)")


def visualize_bsp1(kline_series: KlineSeries, bsp1_list: List[BSP1], segments: List[Segment]):
    """可视化第一类买卖点"""
    print("\n" + "="*70)
    print("第一类买卖点可视化")
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
            marker = " "
            
            # 买卖点标记
            for bsp in bsp1_list:
                if bsp.idx == col:
                    marker = "B" if bsp.type == "buy1" else "S"
            
            # 线段端点标记
            for seg in segments:
                if col == seg.start_idx:
                    marker = marker if marker != " " else "("
                elif col == seg.end_idx:
                    marker = marker if marker != " " else ")"
            
            price_row = int((max_price - price) / price_range * height)
            
            if price_row == row:
                row_str += marker if marker != " " else "*"
            elif marker != " " and abs(price_row - row) <= 1:
                row_str += marker
            else:
                row_str += " "
        
        rows.append(row_str)
    
    for row in rows:
        print(row)
    
    print(" " * 8 + "+" + "-" * len(klines))
    
    print("\n图例：* = K 线，B = 买点 1, S = 卖点 1, ( ) = 线段端点")


def main():
    print("\n" + "="*70)
    print("示例 06: 第一类买卖点详解")
    print("Example 06: Type 1 Buy/Sell Points (Trend Divergence)")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例数据...")
    kline_series, segments = generate_sample_data()
    print(f"    K 线数量：{len(kline_series.klines)}")
    print(f"    线段数量：{len(segments)}")
    
    # 趋势分析
    print("\n[2] 趋势分析...")
    print_trend_analysis(segments)
    
    # 检测第一类买卖点
    print("\n[3] 检测第一类买卖点...")
    detector = BSP1Detector(min_segments=2, divergence_threshold=0.3)
    bsp1_list = detector.detect(kline_series, segments)
    print(f"    检测到 {len(bsp1_list)} 个第一类买卖点")
    
    # 打印详情
    for bsp1 in bsp1_list:
        print_bsp1_detail(bsp1, kline_series)
    
    # 可视化
    visualize_bsp1(kline_series, bsp1_list, segments)
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "bsp1_count": len(bsp1_list),
        "buy_sell_points": [
            {
                "type": bsp1.type,
                "idx": bsp1.idx,
                "price": bsp1.price,
                "segment_idx": bsp1.segment_idx,
                "divergence_strength": bsp1.divergence_strength,
                "confidence": bsp1.confidence,
                "risk_reward_ratio": bsp1.risk_reward_ratio,
                "description": bsp1.description
            }
            for bsp1 in bsp1_list
        ]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 06 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
