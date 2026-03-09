#!/usr/bin/env python3
"""
示例 08: 第三类买卖点详解
Example 08: Type 3 Buy/Sell Points (Center Breakout Confirmation)

对应课程：Lesson 20, 53
演示第三类买卖点的识别和确认

第三类买卖点定义:
- 第三类买点：向上突破中枢后，回踩不进入中枢
- 第三类卖点：向下跌破中枢后，反弹不进入中枢

特点:
- 趋势延续确认点
- 风险适中，收益可观
- 需要中枢作为参考
"""

from pathlib import Path
import sys
# Add project root and python-layer to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / 'python-layer'))

from trading_system.kline import Kline, KlineSeries
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Center:
    """中枢数据结构"""
    start_idx: int
    end_idx: int
    high: float  # 中枢上沿 (ZG)
    low: float   # 中枢下沿 (ZD)
    name: str = ""


@dataclass
class BSP3:
    """第三类买卖点"""
    type: str  # "buy3" or "sell3"
    idx: int
    price: float
    center_reference: Center
    breakout_idx: int
    breakout_price: float
    pullback_depth: float  # 回踩/反弹深度
    confidence: float
    description: str
    is_confirmed: bool


class BSP3Detector:
    """第三类买卖点检测器"""
    
    def __init__(self, max_retrace: float = 0.1, min_confidence: float = 0.65):
        """
        初始化检测器
        
        Args:
            max_retrace: 最大回踩/反弹深度 (相对于中枢边界)
            min_confidence: 最小置信度
        """
        self.max_retrace = max_retrace
        self.min_confidence = min_confidence
    
    def detect(self, kline_series: KlineSeries,
               centers: List[Center]) -> List[BSP3]:
        """
        检测第三类买卖点
        
        算法步骤:
        1. 从中枢结束后开始搜索
        2. 寻找突破 (向上/向下)
        3. 等待回踩/反弹
        4. 确认不进入中枢
        """
        if not centers:
            return []
        
        bsp3_list = []
        klines = kline_series.klines
        
        for center in centers:
            # 从中枢结束后开始搜索
            start_search = center.end_idx + 1
            
            # 寻找买点 3
            bsp3_buy = self._find_bsp3_buy(klines, start_search, center)
            if bsp3_buy:
                bsp3_list.append(bsp3_buy)
            
            # 寻找卖点 3
            bsp3_sell = self._find_bsp3_sell(klines, start_search, center)
            if bsp3_sell:
                bsp3_list.append(bsp3_sell)
        
        return bsp3_list
    
    def _find_bsp3_buy(self, klines: List[Kline],
                       start: int, center: Center) -> Optional[BSP3]:
        """
        寻找第三类买点
        
        条件:
        1. 向上突破中枢 (价格 > ZG)
        2. 回踩不破中枢上沿 (ZG)
        """
        zg = center.high  # 中枢上沿
        breakout_idx = None
        breakout_price = None
        
        # 寻找突破点
        for i in range(start, min(start + 30, len(klines))):
            high = klines[i].high
            
            if high > zg:
                breakout_idx = i
                breakout_price = high
                break
        
        if not breakout_idx:
            return None
        
        # 寻找回踩
        pullback_low = breakout_price
        pullback_idx = breakout_idx
        
        for i in range(breakout_idx + 1, min(breakout_idx + 20, len(klines))):
            low = klines[i].low
            
            # 检查是否进入中枢
            if low < zg * (1 - self.max_retrace):
                # 回踩过深，进入中枢，失效
                return None
            
            if low < pullback_low:
                pullback_low = low
                pullback_idx = i
        
        # 确认回踩后上升
        if pullback_idx < len(klines) - 3:
            after_pullback = klines[pullback_idx + 3].high
            
            if after_pullback > klines[pullback_idx].high:
                # 计算回踩深度 (相对于中枢上沿)
                pullback_depth = (zg - pullback_low) / zg
                
                # 计算置信度
                confidence = self._calculate_confidence(pullback_depth, True)
                
                if confidence >= self.min_confidence:
                    return BSP3(
                        type="buy3",
                        idx=pullback_idx,
                        price=pullback_low,
                        center_reference=center,
                        breakout_idx=breakout_idx,
                        breakout_price=breakout_price,
                        pullback_depth=pullback_depth,
                        confidence=confidence,
                        description=f"第三类买点：突破{breakout_price:.2f} 后回踩{pullback_low:.2f} 不破中枢{zg:.2f}",
                        is_confirmed=True
                    )
        
        return None
    
    def _find_bsp3_sell(self, klines: List[Kline],
                        start: int, center: Center) -> Optional[BSP3]:
        """
        寻找第三类卖点
        
        条件:
        1. 向下跌破中枢 (价格 < ZD)
        2. 反弹不破中枢下沿 (ZD)
        """
        zd = center.low  # 中枢下沿
        breakout_idx = None
        breakout_price = None
        
        # 寻找跌破点
        for i in range(start, min(start + 30, len(klines))):
            low = klines[i].low
            
            if low < zd:
                breakout_idx = i
                breakout_price = low
                break
        
        if not breakout_idx:
            return None
        
        # 寻找反弹
        pullback_high = breakout_price
        pullback_idx = breakout_idx
        
        for i in range(breakout_idx + 1, min(breakout_idx + 20, len(klines))):
            high = klines[i].high
            
            # 检查是否进入中枢
            if high > zd * (1 + self.max_retrace):
                # 反弹过高，进入中枢，失效
                return None
            
            if high > pullback_high:
                pullback_high = high
                pullback_idx = i
        
        # 确认反弹后下降
        if pullback_idx < len(klines) - 3:
            after_pullback = klines[pullback_idx + 3].low
            
            if after_pullback < klines[pullback_idx].low:
                # 计算反弹深度 (相对于中枢下沿)
                pullback_depth = (pullback_high - zd) / zd
                
                # 计算置信度
                confidence = self._calculate_confidence(pullback_depth, False)
                
                if confidence >= self.min_confidence:
                    return BSP3(
                        type="sell3",
                        idx=pullback_idx,
                        price=pullback_high,
                        center_reference=center,
                        breakout_idx=breakout_idx,
                        breakout_price=breakout_price,
                        pullback_depth=pullback_depth,
                        confidence=confidence,
                        description=f"第三类卖点：跌破{breakout_price:.2f} 后反弹{pullback_high:.2f} 不破中枢{zd:.2f}",
                        is_confirmed=True
                    )
        
        return None
    
    def _calculate_confidence(self, pullback_depth: float, is_buy: bool) -> float:
        """
        计算第三类买卖点置信度
        
        因素:
        - 回踩/反弹深度适中
        - 突破力度
        """
        # 理想深度：10%-30%
        ideal_depth = 0.2
        depth_score = 1 - abs(pullback_depth - ideal_depth) / ideal_depth
        
        # 基础置信度
        base_confidence = 0.75
        
        confidence = base_confidence * 0.7 + depth_score * 0.3
        return min(max(confidence, 0), 1)


def generate_sample_data() -> tuple:
    """生成第三类买卖点示例数据"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 模拟中枢 + 突破 + 回踩走势
    price_pattern = [
        # 中枢形成 (90-95 区间)
        92, 93, 91, 94, 92, 93, 91, 95, 92, 94,
        # 向上突破
        96, 98, 100,
        # 回踩 (不破 95)
        99, 98, 97, 96,  # 回踩低点
        # 确认上升
        97, 99, 101, 103, 105
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
    
    # 定义中枢 (K 线 0-9, 区间 90-95)
    center = Center(
        start_idx=0,
        end_idx=9,
        high=95.0,  # ZG
        low=90.0,   # ZD
        name="中枢 A"
    )
    
    return kline_series, [center]


def print_bsp3_detail(bsp3: BSP3, kline_series: KlineSeries):
    """打印第三类买卖点详情"""
    klines = kline_series.klines
    center = bsp3.center_reference
    
    print("\n" + "="*70)
    if bsp3.type == "buy3":
        print("🟢 第三类买点详情 (Type 3 Buy Point)")
    else:
        print("🔴 第三类卖点详情 (Type 3 Sell Point)")
    print("="*70)
    
    print(f"\n位置信息:")
    print(f"  K 线索引：#{bsp3.idx}")
    print(f"  时间：{klines[bsp3.idx].timestamp}")
    print(f"  价格：{bsp3.price:.2f}")
    
    print(f"\n中枢参考:")
    print(f"  中枢名称：{center.name}")
    print(f"  中枢区间：{center.low:.2f} - {center.high:.2f}")
    print(f"  中枢 K 线：#{center.start_idx} → #{center.end_idx}")
    
    print(f"\n突破分析:")
    print(f"  突破位置：K 线 #{bsp3.breakout_idx}")
    print(f"  突破价格：{bsp3.breakout_price:.2f}")
    if bsp3.type == "buy3":
        print(f"  突破方向：向上突破中枢上沿 ({center.high:.2f})")
    else:
        print(f"  突破方向：向下跌破中枢下沿 ({center.low:.2f})")
    
    print(f"\n回踩分析:")
    print(f"  回踩深度：{bsp3.pullback_depth:.1%}")
    if bsp3.pullback_depth < 0.1:
        print(f"  评价：回踩很浅，强势确认")
    elif bsp3.pullback_depth < 0.3:
        print(f"  评价：回踩适中，理想买点")
    else:
        print(f"  评价：回踩较深，注意风险")
    
    print(f"\n置信度评估:")
    print(f"  置信度：{bsp3.confidence:.0%}")
    print(f"  确认状态：{'✓ 已确认' if bsp3.is_confirmed else '⏳ 待确认'}")
    
    print(f"\n操作建议:")
    print(f"  {bsp3.description}")
    
    if bsp3.type == "buy3":
        stop_loss = center.high * 0.98  # 中枢上沿下方
        target1 = bsp3.price * 1.05
        target2 = bsp3.price * 1.10
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (中枢上沿下方 2%)")
        print(f"  目标 1: {target1:.2f} (+5%)")
        print(f"  目标 2: {target2:.2f} (+10%)")
    else:
        stop_loss = center.low * 1.02  # 中枢下沿上方
        target1 = bsp3.price * 0.95
        target2 = bsp3.price * 0.90
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (中枢下沿上方 2%)")
        print(f"  目标 1: {target1:.2f} (-5%)")
        print(f"  目标 2: {target2:.2f} (-10%)")


def compare_all_bsp(bsp1_price: float, bsp2_price: float, bsp3_price: float):
    """对比三类买卖点"""
    print("\n" + "="*70)
    print("三类买卖点对比分析")
    print("="*70)
    
    print(f"\n{'指标':<15} | {'BSP1':<15} | {'BSP2':<15} | {'BSP3':<15}")
    print("-" * 65)
    print(f"{'价格':<15} | {bsp1_price:>15.2f} | {bsp2_price:>15.2f} | {bsp3_price:>15.2f}")
    print(f"{'风险':<15} | {'高':>15} | {'中':>15} | {'中低':>15}")
    print(f"{'收益潜力':<15} | {'⭐⭐⭐⭐⭐':>15} | {'⭐⭐⭐⭐':>15} | {'⭐⭐⭐':>15}")
    print(f"{'确认性':<15} | {'⭐⭐':>15} | {'⭐⭐⭐⭐':>15} | {'⭐⭐⭐⭐⭐':>15}")
    print(f"{'推荐仓位':<15} | {'30%':>15} | {'50%':>15} | {'70%':>15}")
    
    print(f"\n策略建议:")
    print(f"  • BSP1: 左侧交易，适合激进型，博取最大收益")
    print(f"  • BSP2: 确认交易，适合稳健型，平衡风险收益")
    print(f"  • BSP3: 右侧交易，适合保守型，趋势延续确认")
    print(f"  • 理想策略：BSP1(30%) → BSP2(50%) → BSP3(70%) 分批建仓")


def visualize_bsp3(kline_series: KlineSeries, center: Center, bsp3: BSP3):
    """可视化第三类买卖点"""
    print("\n" + "="*70)
    print("第三类买卖点可视化")
    print("="*70)
    
    klines = kline_series.klines
    prices = [(k.high + k.low) / 2 for k in klines]
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    # 中枢边界
    zg = center.high
    zd = center.low
    
    height = 12
    rows = []
    
    for row in range(height):
        row_price = max_price - (row / height) * price_range
        row_str = f"{row_price:7.2f} |"
        
        # 标记中枢边界
        is_zg = abs(row_price - zg) / price_range < 1/height
        is_zd = abs(row_price - zd) / price_range < 1/height
        
        for col, price in enumerate(prices):
            marker = " "
            
            # 中枢区域
            if center.start_idx <= col <= center.end_idx:
                if is_zg or is_zd:
                    marker = "="
                elif zd <= price <= zg:
                    marker = "•"
            
            # BSP3 标记
            if col == bsp3.idx:
                marker = "3"
            elif col == bsp3.breakout_idx:
                marker = "B"  # Breakout
            
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
    
    print("\n图例：* = K 线，• = 中枢区域，= = 中枢边界，B = 突破点，3 = BSP3")
    print(f"\n中枢区间：{zd:.2f} - {zg:.2f}")


def main():
    print("\n" + "="*70)
    print("示例 08: 第三类买卖点详解")
    print("Example 08: Type 3 Buy/Sell Points (Center Breakout)")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例数据...")
    kline_series, centers = generate_sample_data()
    print(f"    K 线数量：{len(kline_series.klines)}")
    print(f"    中枢数量：{len(centers)}")
    for c in centers:
        print(f"      {c.name}: {c.low:.2f} - {c.high:.2f} (K 线 #{c.start_idx}-#{c.end_idx})")
    
    # 检测第三类买卖点
    print("\n[2] 检测第三类买卖点...")
    detector = BSP3Detector(max_retrace=0.1, min_confidence=0.65)
    bsp3_list = detector.detect(kline_series, centers)
    print(f"    检测到 {len(bsp3_list)} 个第三类买卖点")
    
    # 打印详情
    for bsp3 in bsp3_list:
        print_bsp3_detail(bsp3, kline_series)
    
    # 对比分析
    if bsp3_list:
        # 假设 BSP1 和 BSP2 价格 (示例)
        bsp1_price = centers[0].low * 0.95
        bsp2_price = centers[0].low * 0.98
        bsp3_price = bsp3_list[0].price
        compare_all_bsp(bsp1_price, bsp2_price, bsp3_price)
    
    # 可视化
    if bsp3_list:
        visualize_bsp3(kline_series, centers[0], bsp3_list[0])
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "centers": [
            {
                "name": c.name,
                "start_idx": c.start_idx,
                "end_idx": c.end_idx,
                "high": c.high,
                "low": c.low
            }
            for c in centers
        ],
        "bsp3_count": len(bsp3_list),
        "buy_sell_points": [
            {
                "type": bsp3.type,
                "idx": bsp3.idx,
                "price": bsp3.price,
                "center": {
                    "name": bsp3.center_reference.name,
                    "high": bsp3.center_reference.high,
                    "low": bsp3.center_reference.low
                },
                "breakout_idx": bsp3.breakout_idx,
                "breakout_price": bsp3.breakout_price,
                "pullback_depth": bsp3.pullback_depth,
                "confidence": bsp3.confidence,
                "description": bsp3.description
            }
            for bsp3 in bsp3_list
        ]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 08 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
