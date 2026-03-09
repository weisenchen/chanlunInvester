#!/usr/bin/env python3
"""
示例 07: 第二类买卖点详解
Example 07: Type 2 Buy/Sell Points (Pullback Confirmation)

对应课程：Lesson 12, 21
演示第二类买卖点的识别和确认

第二类买卖点定义:
- 第二类买点：第一类买点后的次级别回踩，不破前低
- 第二类卖点：第一类卖点后的次级别反弹，不破前高

特点:
- 风险较第一类小
- 确认性更强
- 收益可能略低于第一类
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
class BSP1:
    """第一类买卖点引用"""
    type: str
    idx: int
    price: float


@dataclass
class BSP2:
    """第二类买卖点"""
    type: str  # "buy2" or "sell2"
    idx: int
    price: float
    bsp1_reference: BSP1
    pullback_depth: float  # 回踩深度 (%)
    confidence: float
    description: str
    is_confirmed: bool


class BSP2Detector:
    """第二类买卖点检测器"""
    
    def __init__(self, max_pullback: float = 0.5, min_confidence: float = 0.6):
        """
        初始化检测器
        
        Args:
            max_pullback: 最大回踩深度 (相对于 BSP1)
            min_confidence: 最小置信度
        """
        self.max_pullback = max_pullback
        self.min_confidence = min_confidence
    
    def detect(self, kline_series: KlineSeries,
               bsp1_list: List[BSP1]) -> List[BSP2]:
        """
        检测第二类买卖点
        
        算法步骤:
        1. 从 BSP1 位置开始搜索
        2. 寻找次级别回踩/反弹
        3. 确认不破 BSP1 价格
        4. 计算置信度
        """
        if not bsp1_list:
            return []
        
        bsp2_list = []
        klines = kline_series.klines
        
        for bsp1 in bsp1_list:
            # 从 BSP1 后开始搜索
            start_search = bsp1.idx + 1
            
            if bsp1.type == "buy1":
                # 寻找买点 2：回踩不破前低
                bsp2 = self._find_bsp2_buy(klines, start_search, bsp1)
                if bsp2:
                    bsp2_list.append(bsp2)
            
            elif bsp1.type == "sell1":
                # 寻找卖点 2：反弹不破前高
                bsp2 = self._find_bsp2_sell(klines, start_search, bsp1)
                if bsp2:
                    bsp2_list.append(bsp2)
        
        return bsp2_list
    
    def _find_bsp2_buy(self, klines: List[Kline], 
                       start: int, bsp1: BSP1) -> Optional[BSP2]:
        """寻找第二类买点"""
        bsp1_price = bsp1.price
        min_price = bsp1_price
        min_idx = start
        
        # 搜索回踩 (最多 20 根 K 线)
        search_end = min(start + 20, len(klines))
        
        for i in range(start, search_end):
            low = klines[i].low
            
            # 检查是否破前低
            if low < bsp1_price * (1 - self.max_pullback):
                # 回踩过深，失效
                return None
            
            # 记录最低点
            if low < min_price:
                min_price = low
                min_idx = i
        
        # 确认回踩后上升
        if min_idx < search_end - 3:
            # 检查后续是否有上升
            after_low = klines[min_idx + 3].high if min_idx + 3 < len(klines) else 0
            
            if after_low > klines[min_idx].high:
                # 计算回踩深度
                pullback_depth = (bsp1_price - min_price) / bsp1_price
                
                # 计算置信度
                confidence = self._calculate_confidence(pullback_depth, bsp1)
                
                if confidence >= self.min_confidence:
                    return BSP2(
                        type="buy2",
                        idx=min_idx,
                        price=min_price,
                        bsp1_reference=bsp1,
                        pullback_depth=pullback_depth,
                        confidence=confidence,
                        description=f"第二类买点：回踩{pullback_depth:.1%} 不破前低{bsp1_price:.2f}",
                        is_confirmed=True
                    )
        
        return None
    
    def _find_bsp2_sell(self, klines: List[Kline],
                        start: int, bsp1: BSP1) -> Optional[BSP2]:
        """寻找第二类卖点"""
        bsp1_price = bsp1.price
        max_price = bsp1_price
        max_idx = start
        
        # 搜索反弹 (最多 20 根 K 线)
        search_end = min(start + 20, len(klines))
        
        for i in range(start, search_end):
            high = klines[i].high
            
            # 检查是否破前高
            if high > bsp1_price * (1 + self.max_pullback):
                # 反弹过高，失效
                return None
            
            # 记录最高点
            if high > max_price:
                max_price = high
                max_idx = i
        
        # 确认反弹后下降
        if max_idx < search_end - 3:
            after_high = klines[max_idx + 3].low if max_idx + 3 < len(klines) else float('inf')
            
            if after_high < klines[max_idx].low:
                # 计算反弹深度
                pullback_depth = (max_price - bsp1_price) / bsp1_price
                
                # 计算置信度
                confidence = self._calculate_confidence(pullback_depth, bsp1)
                
                if confidence >= self.min_confidence:
                    return BSP2(
                        type="sell2",
                        idx=max_idx,
                        price=max_price,
                        bsp1_reference=bsp1,
                        pullback_depth=pullback_depth,
                        confidence=confidence,
                        description=f"第二类卖点：反弹{pullback_depth:.1%} 不破前高{bsp1_price:.2f}",
                        is_confirmed=True
                    )
        
        return None
    
    def _calculate_confidence(self, pullback_depth: float, bsp1: BSP1) -> float:
        """
        计算第二类买卖点置信度
        
        因素:
        - 回踩深度适中 (太浅可能继续涨，太深可能破位)
        - BSP1 的强度
        """
        # 理想回踩深度：20%-40%
        ideal_depth = 0.3
        depth_score = 1 - abs(pullback_depth - ideal_depth) / ideal_depth
        
        # BSP1 强度 (简化：假设 BSP1 置信度已知)
        bsp1_score = 0.8  # 假设 BSP1 有 80% 置信度
        
        confidence = (depth_score * 0.6 + bsp1_score * 0.4)
        return min(max(confidence, 0), 1)


def generate_sample_data() -> tuple:
    """生成第二类买卖点示例数据"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 模拟 BSP1 后的回踩走势
    price_pattern = [
        # BSP1 位置 (最低点 80)
        80,
        # 上升段
        82, 84, 86, 88, 90,
        # 回踩段 (不破 80，最低 83)
        89, 88, 87, 86, 85, 84, 83,  # 回踩低点
        # 确认上升
        84, 86, 88, 90, 92, 94, 96, 98
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
    
    # BSP1 引用
    bsp1 = BSP1(type="buy1", idx=0, price=80.0)
    
    return kline_series, bsp1


def print_bsp2_detail(bsp2: BSP2, kline_series: KlineSeries):
    """打印第二类买卖点详情"""
    klines = kline_series.klines
    
    print("\n" + "="*70)
    if bsp2.type == "buy2":
        print("🟢 第二类买点详情 (Type 2 Buy Point)")
    else:
        print("🔴 第二类卖点详情 (Type 2 Sell Point)")
    print("="*70)
    
    print(f"\n位置信息:")
    print(f"  K 线索引：#{bsp2.idx}")
    print(f"  时间：{klines[bsp2.idx].timestamp}")
    print(f"  价格：{bsp2.price:.2f}")
    
    print(f"\nBSP1 参考:")
    print(f"  BSP1 类型：{bsp2.bsp1_reference.type}")
    print(f"  BSP1 价格：{bsp2.bsp1_reference.price:.2f}")
    print(f"  间距：{bsp2.idx - bsp2.bsp1_reference.idx} 根 K 线")
    
    print(f"\n回踩分析:")
    print(f"  回踩深度：{bsp2.pullback_depth:.1%}")
    if bsp2.pullback_depth < 0.2:
        print(f"  评价：回踩较浅，可能继续强势")
    elif bsp2.pullback_depth < 0.5:
        print(f"  评价：回踩适中，理想买点")
    else:
        print(f"  评价：回踩较深，注意风险")
    
    print(f"\n置信度评估:")
    print(f"  置信度：{bsp2.confidence:.0%}")
    print(f"  确认状态：{'✓ 已确认' if bsp2.is_confirmed else '⏳ 待确认'}")
    
    print(f"\n操作建议:")
    print(f"  {bsp2.description}")
    
    if bsp2.type == "buy2":
        stop_loss = bsp2.bsp1_reference.price * 0.98
        target1 = bsp2.price * 1.05
        target2 = bsp2.price * 1.10
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (BSP1 下方 2%)")
        print(f"  目标 1: {target1:.2f} (+5%)")
        print(f"  目标 2: {target2:.2f} (+10%)")
    else:
        stop_loss = bsp2.bsp1_reference.price * 1.02
        target1 = bsp2.price * 0.95
        target2 = bsp2.price * 0.90
        print(f"\n参考价位:")
        print(f"  止损：{stop_loss:.2f} (BSP1 上方 2%)")
        print(f"  目标 1: {target1:.2f} (-5%)")
        print(f"  目标 2: {target2:.2f} (-10%)")


def compare_bsp1_bsp2(bsp1: BSP1, bsp2: BSP2):
    """对比第一类和第二类买卖点"""
    print("\n" + "="*70)
    print("BSP1 vs BSP2 对比分析")
    print("="*70)
    
    print(f"\n{'指标':<15} | {'BSP1':<15} | {'BSP2':<15}")
    print("-" * 50)
    print(f"{'价格':<15} | {bsp1.price:>15.2f} | {bsp2.price:>15.2f}")
    print(f"{'K 线位置':<15} | {bsp1.idx:>15} | {bsp2.idx:>15}")
    print(f"{'风险':<15} | {'高':>15} | {'中':>15}")
    print(f"{'收益潜力':<15} | {'高':>15} | {'中':>15}")
    print(f"{'确认性':<15} | {'低':>15} | {'高':>15}")
    print(f"{'推荐仓位':<15} | {'30%':>15} | {'50%':>15}")
    
    print(f"\n策略建议:")
    print(f"  • BSP1 适合激进型投资者，博取最大收益")
    print(f"  • BSP2 适合稳健型投资者，确认性更强")
    print(f"  • 理想策略：BSP1 建仓 30%, BSP2 加仓 50%")


def visualize_bsp2(kline_series: KlineSeries, bsp1: BSP1, bsp2: BSP2):
    """可视化第二类买卖点"""
    print("\n" + "="*70)
    print("第二类买卖点可视化")
    print("="*70)
    
    klines = kline_series.klines
    prices = [(k.high + k.low) / 2 for k in klines]
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    height = 10
    rows = []
    
    for row in range(height):
        row_price = max_price - (row / height) * price_range
        row_str = f"{row_price:7.2f} |"
        
        for col, price in enumerate(prices):
            marker = " "
            
            if col == bsp1.idx:
                marker = "1"  # BSP1
            elif col == bsp2.idx:
                marker = "2"  # BSP2
            
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
    
    print("\n图例：* = K 线，1 = BSP1, 2 = BSP2")
    print("\n走势说明:")
    print(f"  BSP1 @ {bsp1.price:.2f} → 上升 → 回踩 → BSP2 @ {bsp2.price:.2f} → 上升")


def main():
    print("\n" + "="*70)
    print("示例 07: 第二类买卖点详解")
    print("Example 07: Type 2 Buy/Sell Points (Pullback Confirmation)")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例数据...")
    kline_series, bsp1 = generate_sample_data()
    print(f"    K 线数量：{len(kline_series.klines)}")
    print(f"    BSP1 位置：K 线 #{bsp1.idx}, 价格 {bsp1.price:.2f}")
    
    # 检测第二类买卖点
    print("\n[2] 检测第二类买卖点...")
    detector = BSP2Detector(max_pullback=0.5, min_confidence=0.6)
    bsp2_list = detector.detect(kline_series, [bsp1])
    print(f"    检测到 {len(bsp2_list)} 个第二类买卖点")
    
    # 打印详情
    for bsp2 in bsp2_list:
        print_bsp2_detail(bsp2, kline_series)
        compare_bsp1_bsp2(bsp1, bsp2)
    
    # 可视化
    if bsp2_list:
        visualize_bsp2(kline_series, bsp1, bsp2_list[0])
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "bsp1": {
            "type": bsp1.type,
            "idx": bsp1.idx,
            "price": bsp1.price
        },
        "bsp2_count": len(bsp2_list),
        "buy_sell_points": [
            {
                "type": bsp2.type,
                "idx": bsp2.idx,
                "price": bsp2.price,
                "bsp1_reference": {
                    "type": bsp2.bsp1_reference.type,
                    "price": bsp2.bsp1_reference.price
                },
                "pullback_depth": bsp2.pullback_depth,
                "confidence": bsp2.confidence,
                "description": bsp2.description
            }
            for bsp2 in bsp2_list
        ]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 07 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
