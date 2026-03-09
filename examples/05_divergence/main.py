#!/usr/bin/env python3
"""
示例 05: 背驰识别与买卖点
Example 05: Divergence and Buy/Sell Points

对应课程：Lesson 15, 24, 27 (背驰), Lesson 12, 20, 21 (买卖点)
演示缠论背驰判断和三买卖点识别

核心概念:
1. 背驰：价格创新高/低但动能指标不创新高/低
2. 第一类买卖点：趋势背驰点
3. 第二类买卖点：次级别回踩确认
4. 第三类买卖点：中枢突破回踩确认
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
from typing import List, Optional, Tuple
import math


@dataclass
class Pen:
    """笔数据结构"""
    direction: str
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float


@dataclass
class Segment:
    """线段数据结构"""
    direction: str
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    pens: List[Pen]


@dataclass
class Center:
    """中枢数据结构"""
    start_idx: int
    end_idx: int
    high: float  # 中枢上沿 (ZG)
    low: float   # 中枢下沿 (ZD)
    segments: List[Segment]


@dataclass 
class BuySellPoint:
    """买卖点数据结构"""
    type: str  # "buy1", "buy2", "buy3", "sell1", "sell2", "sell3"
    idx: int
    price: float
    confidence: float  # 0-1
    description: str


class MACDIndicator:
    """MACD 指标计算器"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
    
    def calculate(self, prices: List[float]) -> List[dict]:
        """
        计算 MACD 指标
        
        Returns:
            List of dicts with keys: dif, dea, macd, histogram
        """
        if len(prices) < self.slow:
            return []
        
        # 计算 EMA
        ema_fast = self._ema(prices, self.fast)
        ema_slow = self._ema(prices, self.slow)
        
        # 计算 DIF
        dif = [f - s for f, s in zip(ema_fast, ema_slow)]
        
        # 计算 DEA (DIF 的 EMA)
        dea = self._ema(dif, self.signal_period)
        
        # 计算 MACD 柱
        macd = [(d - e) * 2 for d, e in zip(dif, dea)]
        
        result = []
        for i in range(len(prices)):
            result.append({
                'dif': dif[i] if i < len(dif) else 0,
                'dea': dea[i] if i < len(dea) else 0,
                'macd': macd[i] if i < len(macd) else 0,
                'histogram': macd[i] if i < len(macd) else 0
            })
        
        return result
    
    def _ema(self, data: List[float], period: int) -> List[float]:
        """计算指数移动平均"""
        if len(data) < period:
            return [0] * len(data)
        
        multiplier = 2 / (period + 1)
        ema = [sum(data[:period]) / period]  # 初始 SMA
        
        for i in range(period, len(data)):
            ema.append((data[i] - ema[-1]) * multiplier + ema[-1])
        
        # 填充前面的值
        return [ema[0]] * (period - 1) + ema


class DivergenceDetector:
    """背驰检测器"""
    
    def __init__(self):
        self.macd = MACDIndicator()
    
    def detect_divergence(self, kline_series: KlineSeries, 
                         segments: List[Segment]) -> List[dict]:
        """
        检测背驰
        
        背驰类型:
        1. 顶背驰：价格创新高，MACD 不创新高 → 卖出信号
        2. 底背驰：价格创新低，MACD 不创新低 → 买入信号
        """
        prices = [(k.high + k.low) / 2 for k in kline_series.klines]
        macd_data = self.macd.calculate(prices)
        
        if len(segments) < 2 or not macd_data:
            return []
        
        divergences = []
        
        # 检测相邻同向线段的背驰
        for i in range(len(segments) - 1):
            seg1 = segments[i]
            seg2 = segments[i + 1]
            
            if seg1.direction != seg2.direction:
                continue
            
            # 获取线段端点的 MACD 值
            macd1 = macd_data[seg1.end_idx]['histogram']
            macd2 = macd_data[seg2.end_idx]['histogram']
            
            price1 = seg1.end_price
            price2 = seg2.end_price
            
            divergence = None
            
            if seg1.direction == "up":
                # 上升线段：检查顶背驰
                if price2 > price1 and macd2 < macd1:
                    # 价格创新高，MACD 未创新高 → 顶背驰
                    divergence = {
                        'type': 'top_divergence',
                        'segment_idx': i + 1,
                        'price_high': max(price1, price2),
                        'macd_peak1': macd1,
                        'macd_peak2': macd2,
                        'divergence_strength': abs(macd1 - macd2) / max(abs(macd1), 0.001),
                        'signal': 'sell',
                        'idx': seg2.end_idx,
                        'price': price2
                    }
            
            elif seg1.direction == "down":
                # 下降线段：检查底背驰
                if price2 < price1 and macd2 > macd1:
                    # 价格创新低，MACD 未创新低 → 底背驰
                    divergence = {
                        'type': 'bottom_divergence',
                        'segment_idx': i + 1,
                        'price_low': min(price1, price2),
                        'macd_trough1': macd1,
                        'macd_trough2': macd2,
                        'divergence_strength': abs(macd1 - macd2) / max(abs(macd1), 0.001),
                        'signal': 'buy',
                        'idx': seg2.end_idx,
                        'price': price2
                    }
            
            if divergence:
                divergences.append(divergence)
        
        return divergences


class BuySellPointDetector:
    """买卖点检测器"""
    
    def __init__(self):
        self.divergence_detector = DivergenceDetector()
    
    def detect_all_bsp(self, kline_series: KlineSeries,
                       segments: List[Segment],
                       centers: List[Center]) -> List[BuySellPoint]:
        """检测所有三类买卖点"""
        bsp_list = []
        
        # 第一类买卖点：趋势背驰点
        bsp1 = self._detect_bsp1(kline_series, segments)
        bsp_list.extend(bsp1)
        
        # 第二类买卖点：次级别回踩确认
        bsp2 = self._detect_bsp2(kline_series, segments, bsp1)
        bsp_list.extend(bsp2)
        
        # 第三类买卖点：中枢突破回踩
        bsp3 = self._detect_bsp3(kline_series, segments, centers)
        bsp_list.extend(bsp3)
        
        return bsp_list
    
    def _detect_bsp1(self, kline_series: KlineSeries, 
                     segments: List[Segment]) -> List[BuySellPoint]:
        """
        第一类买卖点：趋势背驰点
        
        条件:
        - 存在明显的趋势背驰
        - 背驰强度 > 阈值
        """
        divergences = self.divergence_detector.detect_divergence(kline_series, segments)
        bsp_list = []
        
        for div in divergences:
            if div['divergence_strength'] > 0.3:  # 背驰强度阈值
                if div['signal'] == 'buy':
                    bsp_list.append(BuySellPoint(
                        type="buy1",
                        idx=div['idx'],
                        price=div['price'],
                        confidence=min(div['divergence_strength'], 1.0),
                        description=f"第一类买点：底背驰，强度{div['divergence_strength']:.2f}"
                    ))
                else:
                    bsp_list.append(BuySellPoint(
                        type="sell1",
                        idx=div['idx'],
                        price=div['price'],
                        confidence=min(div['divergence_strength'], 1.0),
                        description=f"第一类卖点：顶背驰，强度{div['divergence_strength']:.2f}"
                    ))
        
        return bsp_list
    
    def _detect_bsp2(self, kline_series: KlineSeries,
                     segments: List[Segment],
                     bsp1_list: List[BuySellPoint]) -> List[BuySellPoint]:
        """
        第二类买卖点：次级别回踩确认
        
        条件:
        - 在第一类买卖点之后
        - 次级别回踩不破前低/高
        """
        bsp_list = []
        klines = kline_series.klines
        
        for bsp1 in bsp1_list:
            if bsp1.type == "buy1":
                # 寻找买点 2：回踩不破前低
                for i in range(bsp1.idx + 1, min(bsp1.idx + 20, len(klines))):
                    if klines[i].low > bsp1.price * 0.98:  # 不破前低 2%
                        # 找到回踩后的上升起点
                        if i + 2 < len(klines):
                            if klines[i+2].high > klines[i].high:
                                bsp_list.append(BuySellPoint(
                                    type="buy2",
                                    idx=i,
                                    price=klines[i].low,
                                    confidence=0.7,
                                    description="第二类买点：回踩确认不破前低"
                                ))
                                break
            
            elif bsp1.type == "sell1":
                # 寻找卖点 2：反弹不破前高
                for i in range(bsp1.idx + 1, min(bsp1.idx + 20, len(klines))):
                    if klines[i].high < bsp1.price * 1.02:  # 不破前高 2%
                        # 找到反弹后的下降起点
                        if i + 2 < len(klines):
                            if klines[i+2].low < klines[i].low:
                                bsp_list.append(BuySellPoint(
                                    type="sell2",
                                    idx=i,
                                    price=klines[i].high,
                                    confidence=0.7,
                                    description="第二类卖点：反弹确认不破前高"
                                ))
                                break
        
        return bsp_list
    
    def _detect_bsp3(self, kline_series: KlineSeries,
                     segments: List[Segment],
                     centers: List[Center]) -> List[BuySellPoint]:
        """
        第三类买卖点：中枢突破回踩确认
        
        条件:
        - 价格突破中枢
        - 回踩不进入中枢
        """
        bsp_list = []
        klines = kline_series.klines
        
        for center in centers:
            # 检查中枢后的走势
            for i in range(center.end_idx + 1, len(klines) - 10):
                # 向上突破
                if klines[i].high > center.high:
                    # 检查回踩
                    for j in range(i + 1, min(i + 15, len(klines))):
                        if klines[j].low > center.high:  # 回踩不破中枢上沿
                            bsp_list.append(BuySellPoint(
                                type="buy3",
                                idx=j,
                                price=klines[j].low,
                                confidence=0.75,
                                description=f"第三类买点：突破中枢后回踩确认 (中枢：{center.low:.2f}-{center.high:.2f})"
                            ))
                            break
                    break
                
                # 向下跌破
                elif klines[i].low < center.low:
                    # 检查反弹
                    for j in range(i + 1, min(i + 15, len(klines))):
                        if klines[j].high < center.low:  # 反弹不破中枢下沿
                            bsp_list.append(BuySellPoint(
                                type="sell3",
                                idx=j,
                                price=klines[j].high,
                                confidence=0.75,
                                description=f"第三类卖点：跌破中枢后反弹确认 (中枢：{center.low:.2f}-{center.high:.2f})"
                            ))
                            break
                    break
        
        return bsp_list


def generate_sample_data() -> tuple:
    """生成包含背驰和买卖点的示例数据"""
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 模拟一个完整的趋势背驰走势
    # 下降趋势 + 底背驰 + 上升 + 中枢 + 突破
    price_pattern = [
        # 第一段下降
        100, 98, 96, 94, 92, 90,
        # 反弹
        91, 93, 95, 94, 93,
        # 第二段下降 (创新低，但力度减弱 - 背驰)
        92, 90, 89, 88, 87, 86,  # 创新低
        # 上升段 1
        87, 89, 91, 93, 95, 97,
        # 中枢形成 (横盘)
        96, 95, 97, 96, 95, 96, 97, 95,
        # 突破中枢
        98, 100, 102, 104, 103, 105, 107, 109
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
    
    # 简化：手动定义线段和中枢
    segments = [
        Segment("down", 0, 5, 100.0, 86.0, []),   # 下降段 1
        Segment("up", 5, 10, 86.0, 95.0, []),     # 反弹段
        Segment("down", 10, 16, 95.0, 86.0, []),  # 下降段 2 (背驰段)
        Segment("up", 16, 21, 86.0, 97.0, []),    # 上升段
        Segment("up", 21, 35, 97.0, 109.0, []),   # 突破段
    ]
    
    centers = [
        Center(21, 28, 97.0, 95.0, [])  # 中枢
    ]
    
    return kline_series, segments, centers


def print_macd_analysis(kline_series: KlineSeries):
    """打印 MACD 分析"""
    print("\n" + "="*70)
    print("MACD 指标分析")
    print("="*70)
    
    prices = [(k.high + k.low) / 2 for k in kline_series.klines]
    macd = MACDIndicator()
    macd_data = macd.calculate(prices)
    
    print(f"\n{'K 线':>4} | {'价格':>8} | {'DIF':>10} | {'DEA':>10} | {'MACD':>10}")
    print("-" * 50)
    
    # 打印关键位置的 MACD 值
    key_indices = [0, 10, 16, 21, 30, len(prices)-1]
    for i in key_indices:
        if i < len(macd_data):
            print(f"{i:>4} | {prices[i]:>8.2f} | {macd_data[i]['dif']:>10.4f} | "
                  f"{macd_data[i]['dea']:>10.4f} | {macd_data[i]['macd']:>10.4f}")


def print_divergence_analysis(divergences: List[dict]):
    """打印背驰分析"""
    print("\n" + "="*70)
    print("背驰分析 (Divergence Analysis)")
    print("="*70)
    
    if not divergences:
        print("未检测到明显背驰")
        return
    
    for div in divergences:
        print(f"\n{div['type'].upper()}:")
        if div['type'] == 'top_divergence':
            print(f"  价格高点：{div['price_high']:.2f}")
            print(f"  MACD 峰值 1: {div['macd_peak1']:.4f}")
            print(f"  MACD 峰值 2: {div['macd_peak2']:.4f} (未创新高)")
            print(f"  背驰强度：{div['divergence_strength']:.2f}")
            print(f"  信号：⚠️  卖出")
        else:
            print(f"  价格低点：{div['price_low']:.2f}")
            print(f"  MACD 谷值 1: {div['macd_trough1']:.4f}")
            print(f"  MACD 谷值 2: {div['macd_trough2']:.4f} (未创新低)")
            print(f"  背驰强度：{div['divergence_strength']:.2f}")
            print(f"  信号：✅ 买入")


def print_bsp_analysis(bsp_list: List[BuySellPoint]):
    """打印买卖点分析"""
    print("\n" + "="*70)
    print("买卖点分析 (Buy/Sell Points)")
    print("="*70)
    
    if not bsp_list:
        print("未检测到明确买卖点")
        return
    
    # 按类型分组
    buy_points = [b for b in bsp_list if b.type.startswith('buy')]
    sell_points = [b for b in bsp_list if b.type.startswith('sell')]
    
    if buy_points:
        print(f"\n🟢 买点 ({len(buy_points)} 个):")
        for bsp in buy_points:
            type_name = {
                'buy1': '第一类买点 (趋势背驰)',
                'buy2': '第二类买点 (回踩确认)',
                'buy3': '第三类买点 (突破回踩)'
            }.get(bsp.type, bsp.type)
            print(f"  • {type_name}")
            print(f"    位置：K 线#{bsp.idx}, 价格：{bsp.price:.2f}")
            print(f"    置信度：{bsp.confidence:.0%}")
            print(f"    说明：{bsp.description}")
    
    if sell_points:
        print(f"\n🔴 卖点 ({len(sell_points)} 个):")
        for bsp in sell_points:
            type_name = {
                'sell1': '第一类卖点 (趋势背驰)',
                'sell2': '第二类卖点 (反弹确认)',
                'sell3': '第三类卖点 (跌破反弹)'
            }.get(bsp.type, bsp.type)
            print(f"  • {type_name}")
            print(f"    位置：K 线#{bsp.idx}, 价格：{bsp.price:.2f}")
            print(f"    置信度：{bsp.confidence:.0%}")
            print(f"    说明：{bsp.description}")


def visualize_bsp(kline_series: KlineSeries, bsp_list: List[BuySellPoint]):
    """可视化买卖点"""
    print("\n" + "="*70)
    print("买卖点位置可视化")
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
            # 检查买卖点标记
            marker = " "
            for bsp in bsp_list:
                if bsp.idx == col:
                    if bsp.type.startswith('buy'):
                        marker = "B"
                    else:
                        marker = "S"
            
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
    
    print("\n图例：* = K 线，B = 买点，S = 卖点")


def main():
    print("\n" + "="*70)
    print("示例 05: 背驰识别与买卖点")
    print("Example 05: Divergence and Buy/Sell Points")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例数据...")
    kline_series, segments, centers = generate_sample_data()
    print(f"    K 线数量：{len(kline_series.klines)}")
    print(f"    线段数量：{len(segments)}")
    print(f"    中枢数量：{len(centers)}")
    
    # MACD 分析
    print("\n[2] 计算 MACD 指标...")
    print_macd_analysis(kline_series)
    
    # 背驰检测
    print("\n[3] 检测背驰...")
    divergence_detector = DivergenceDetector()
    divergences = divergence_detector.detect_divergence(kline_series, segments)
    print(f"    检测到 {len(divergences)} 个背驰信号")
    
    # 打印背驰分析
    print_divergence_analysis(divergences)
    
    # 买卖点检测
    print("\n[4] 检测买卖点...")
    bsp_detector = BuySellPointDetector()
    bsp_list = bsp_detector.detect_all_bsp(kline_series, segments, centers)
    print(f"    检测到 {len(bsp_list)} 个买卖点")
    
    # 打印买卖点分析
    print_bsp_analysis(bsp_list)
    
    # 可视化
    visualize_bsp(kline_series, bsp_list)
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "kline_count": len(kline_series.klines),
        "divergence_count": len(divergences),
        "divergences": divergences,
        "bsp_count": len(bsp_list),
        "buy_sell_points": [
            {
                "type": bsp.type,
                "idx": bsp.idx,
                "price": bsp.price,
                "confidence": bsp.confidence,
                "description": bsp.description
            }
            for bsp in bsp_list
        ]
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 05 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
