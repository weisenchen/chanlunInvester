#!/usr/bin/env python3
"""
示例 09: 区间套定位
Example 09: Interval Set (Multi-Level Recursive Positioning)

对应课程：Lesson 27, 61
演示缠论区间套的精确定位方法

区间套核心概念:
- 大级别的买卖点由次级别走势确认
- 逐层递归，精确定位转折点
- 类似数学中的区间套定理

应用流程:
1. 大级别 (如日线) 发现潜在买卖点
2. 中级别 (如 30 分钟) 确认趋势背驰
3. 小级别 (如 5 分钟) 精确定位入场点
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
from typing import List, Optional, Dict
from enum import Enum


class TimeFrame(Enum):
    """时间周期"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY = "day"
    WEEK = "week"


@dataclass
class LevelAnalysis:
    """单级别分析结果"""
    timeframe: TimeFrame
    trend: str  # "up", "down", "neutral"
    segment_count: int
    divergence_detected: bool
    potential_bsp: bool
    bsp_type: Optional[str]  # "buy1", "buy2", "buy3", "sell1", etc.
    price_range: tuple  # (low, high)
    confidence: float


@dataclass
class IntervalSetResult:
    """区间套分析结果"""
    levels: List[LevelAnalysis]
    confirmed: bool
    final_bsp_type: str
    entry_price: float
    stop_loss: float
    target_price: float
    confidence: float
    description: str


class IntervalSetAnalyzer:
    """区间套分析器"""
    
    def __init__(self, levels: List[TimeFrame] = None):
        """
        初始化分析器
        
        Args:
            levels: 分析的时间周期列表 (从大到小)
        """
        self.levels = levels or [
            TimeFrame.DAY,      # 大级别
            TimeFrame.HOUR_4,   # 中级别
            TimeFrame.MINUTE_30 # 小级别
        ]
    
    def analyze(self, multi_level_data: Dict[TimeFrame, KlineSeries]) -> IntervalSetResult:
        """
        执行区间套分析
        
        算法步骤:
        1. 从大级别开始分析
        2. 检测潜在买卖点
        3. 逐级向下确认
        4. 精确定位入场点
        """
        level_results = []
        
        # 从大到小分析每个级别
        for tf in self.levels:
            if tf not in multi_level_data:
                continue
            
            kline_series = multi_level_data[tf]
            level_result = self._analyze_level(kline_series, tf)
            level_results.append(level_result)
        
        # 综合判断
        result = self._synthesize_result(level_results)
        
        return result
    
    def _analyze_level(self, kline_series: KlineSeries, 
                       timeframe: TimeFrame) -> LevelAnalysis:
        """分析单个级别"""
        klines = kline_series.klines
        prices = [(k.high + k.low) / 2 for k in klines]
        
        min_price = min(prices)
        max_price = max(prices)
        
        # 简化分析：基于价格走势判断趋势
        if len(prices) < 10:
            return LevelAnalysis(
                timeframe=timeframe,
                trend="neutral",
                segment_count=0,
                divergence_detected=False,
                potential_bsp=False,
                bsp_type=None,
                price_range=(min_price, max_price),
                confidence=0.5
            )
        
        # 判断趋势
        first_half_avg = sum(prices[:len(prices)//2]) / (len(prices)//2)
        second_half_avg = sum(prices[len(prices)//2:]) / (len(prices) - len(prices)//2)
        
        if second_half_avg > first_half_avg * 1.02:
            trend = "up"
        elif second_half_avg < first_half_avg * 0.98:
            trend = "down"
        else:
            trend = "neutral"
        
        # 检测背驰 (简化)
        divergence_detected = self._detect_divergence(prices, trend)
        
        # 判断潜在买卖点
        potential_bsp = divergence_detected
        bsp_type = None
        
        if potential_bsp:
            if trend == "down":
                bsp_type = "buy1"
            else:
                bsp_type = "sell1"
        
        # 计算置信度
        confidence = 0.5
        if divergence_detected:
            confidence = 0.7
        if len(prices) > 20:
            confidence += 0.1
        
        return LevelAnalysis(
            timeframe=timeframe,
            trend=trend,
            segment_count=max(1, len(prices) // 10),
            divergence_detected=divergence_detected,
            potential_bsp=potential_bsp,
            bsp_type=bsp_type,
            price_range=(min_price, max_price),
            confidence=min(confidence, 0.95)
        )
    
    def _detect_divergence(self, prices: List[float], trend: str) -> bool:
        """简化背驰检测"""
        if len(prices) < 10:
            return False
        
        # 检查价格创新高/低但动量减弱
        if trend == "down":
            # 检查底背驰
            recent_low = min(prices[-5:])
            earlier_low = min(prices[:5])
            
            if recent_low < earlier_low:
                # 价格创新低，检查动量
                recent_momentum = abs(prices[-1] - prices[-5])
                earlier_momentum = abs(prices[5] - prices[0])
                
                if recent_momentum < earlier_momentum * 0.8:
                    return True
        
        elif trend == "up":
            # 检查顶背驰
            recent_high = max(prices[-5:])
            earlier_high = max(prices[:5])
            
            if recent_high > earlier_high:
                recent_momentum = abs(prices[-1] - prices[-5])
                earlier_momentum = abs(prices[5] - prices[0])
                
                if recent_momentum < earlier_momentum * 0.8:
                    return True
        
        return False
    
    def _synthesize_result(self, level_results: List[LevelAnalysis]) -> IntervalSetResult:
        """综合各级别分析结果"""
        if not level_results:
            return IntervalSetResult(
                levels=[],
                confirmed=False,
                final_bsp_type="none",
                entry_price=0,
                stop_loss=0,
                target_price=0,
                confidence=0,
                description="无足够数据进行分析"
            )
        
        # 检查是否所有级别都确认买卖点
        bsp_levels = [r for r in level_results if r.potential_bsp]
        
        # 区间套确认条件：至少 2 个级别确认同向买卖点
        buy_confirmed = sum(1 for r in bsp_levels if r.bsp_type and r.bsp_type.startswith('buy')) >= 2
        sell_confirmed = sum(1 for r in bsp_levels if r.bsp_type and r.bsp_type.startswith('sell')) >= 2
        
        confirmed = buy_confirmed or sell_confirmed
        
        if buy_confirmed:
            final_bsp_type = "buy"
            # 取最小级别的入场点
            entry_level = bsp_levels[-1]
            entry_price = entry_level.price_range[0]
            stop_loss = entry_price * 0.95
            target_price = entry_price * 1.10
            description = "区间套确认买点：多级别背驰共振"
        
        elif sell_confirmed:
            final_bsp_type = "sell"
            entry_level = bsp_levels[-1]
            entry_price = entry_level.price_range[1]
            stop_loss = entry_price * 1.05
            target_price = entry_price * 0.90
            description = "区间套确认卖点：多级别背驰共振"
        
        else:
            final_bsp_type = "none"
            entry_price = level_results[-1].price_range[0]
            stop_loss = 0
            target_price = 0
            description = "未形成区间套确认，继续观察"
        
        # 计算综合置信度
        avg_confidence = sum(r.confidence for r in level_results) / len(level_results)
        if confirmed:
            confidence = min(avg_confidence + 0.15, 0.95)
        else:
            confidence = avg_confidence * 0.7
        
        return IntervalSetResult(
            levels=level_results,
            confirmed=confirmed,
            final_bsp_type=final_bsp_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            confidence=confidence,
            description=description
        )


def generate_multi_level_data() -> Dict[TimeFrame, KlineSeries]:
    """生成多级别示例数据"""
    base_time = datetime(2026, 1, 1, 9, 30)
    
    # 大级别 (日线) - 下降趋势
    daily_prices = [100, 98, 96, 94, 92, 90, 88, 86, 85, 84]
    daily_klines = []
    for i, price in enumerate(daily_prices):
        kline = Kline(
            timestamp=base_time + timedelta(days=i),
            open=price + 0.5,
            high=price + 1,
            low=price - 1,
            close=price - 0.5,
            volume=10000000
        )
        daily_klines.append(kline)
    
    # 中级别 (4 小时) - 显示背驰
    h4_prices = [90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 82, 83]
    h4_klines = []
    for i, price in enumerate(h4_prices):
        kline = Kline(
            timestamp=base_time + timedelta(hours=i*4),
            open=price + 0.3,
            high=price + 0.5,
            low=price - 0.5,
            close=price - 0.3,
            volume=2000000
        )
        h4_klines.append(kline)
    
    # 小级别 (30 分钟) - 精确定位
    m30_prices = [82, 81.5, 81, 80.5, 80, 80.5, 81, 81.5, 82, 82.5, 83, 83.5]
    m30_klines = []
    for i, price in enumerate(m30_prices):
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=price + 0.2,
            high=price + 0.3,
            low=price - 0.3,
            close=price - 0.2,
            volume=500000
        )
        m30_klines.append(kline)
    
    return {
        TimeFrame.DAY: KlineSeries(klines=daily_klines, symbol="000001.SZ", timeframe="day"),
        TimeFrame.HOUR_4: KlineSeries(klines=h4_klines, symbol="000001.SZ", timeframe="4h"),
        TimeFrame.MINUTE_30: KlineSeries(klines=m30_klines, symbol="000001.SZ", timeframe="30m")
    }


def print_level_analysis(level: LevelAnalysis):
    """打印单级别分析"""
    tf_name = {
        TimeFrame.DAY: "日线",
        TimeFrame.HOUR_4: "4 小时",
        TimeFrame.HOUR_1: "1 小时",
        TimeFrame.MINUTE_30: "30 分钟",
        TimeFrame.MINUTE_15: "15 分钟",
        TimeFrame.MINUTE_5: "5 分钟",
        TimeFrame.MINUTE_1: "1 分钟"
    }.get(level.timeframe, level.timeframe.value)
    
    trend_icon = {"up": "📈", "down": "📉", "neutral": "➡️"}.get(level.trend, "❓")
    
    print(f"\n  {tf_name} {trend_icon}")
    print(f"    趋势：{level.trend}")
    print(f"    线段数：{level.segment_count}")
    print(f"    背驰检测：{'✓ 检测到' if level.divergence_detected else '✗ 未检测到'}")
    print(f"    潜在买卖点：{'✓ 是' if level.potential_bsp else '✗ 否'}")
    if level.bsp_type:
        bsp_name = {
            "buy1": "第一类买点",
            "buy2": "第二类买点",
            "buy3": "第三类买点",
            "sell1": "第一类卖点",
            "sell2": "第二类卖点",
            "sell3": "第三类卖点"
        }.get(level.bsp_type, level.bsp_type)
        print(f"    买卖点类型：{bsp_name}")
    print(f"    价格区间：{level.price_range[0]:.2f} - {level.price_range[1]:.2f}")
    print(f"    置信度：{level.confidence:.0%}")


def print_interval_set_result(result: IntervalSetResult):
    """打印区间套分析结果"""
    print("\n" + "="*70)
    print("区间套分析结果 (Interval Set Analysis)")
    print("="*70)
    
    print(f"\n{'级别':<15} | {'趋势':<10} | {'背驰':<10} | {'买卖点':<10} | {'置信度':<10}")
    print("-" * 65)
    
    for level in result.levels:
        tf_name = level.timeframe.value
        trend = level.trend
        divergence = "✓" if level.divergence_detected else "✗"
        bsp = level.bsp_type if level.bsp_type else "-"
        confidence = f"{level.confidence:.0%}"
        
        print(f"{tf_name:<15} | {trend:<10} | {divergence:<10} | {bsp:<10} | {confidence:<10}")
    
    print("\n" + "="*70)
    print("综合结论")
    print("="*70)
    
    if result.confirmed:
        status = "✅ 区间套确认"
        if result.final_bsp_type == "buy":
            print(f"\n{status} - 买点")
            print(f"\n操作建议:")
            print(f"  入场价：{result.entry_price:.2f}")
            print(f"  止损价：{result.stop_loss:.2f} (-5%)")
            print(f"  目标价：{result.target_price:.2f} (+10%)")
            print(f"  风险收益比：1:{(result.target_price - result.entry_price) / (result.entry_price - result.stop_loss):.2f}")
        else:
            print(f"\n{status} - 卖点")
            print(f"\n操作建议:")
            print(f"  入场价：{result.entry_price:.2f}")
            print(f"  止损价：{result.stop_loss:.2f} (+5%)")
            print(f"  目标价：{result.target_price:.2f} (-10%)")
    else:
        print(f"\n❌ 区间套未确认")
        print(f"  原因：各级别信号不一致或背驰未确认")
    
    print(f"\n综合置信度：{result.confidence:.0%}")
    print(f"说明：{result.description}")


def visualize_multi_level(multi_level_data: Dict[TimeFrame, KlineSeries], result: IntervalSetResult):
    """可视化多级别走势"""
    print("\n" + "="*70)
    print("多级别走势可视化")
    print("="*70)
    
    for tf, kline_series in multi_level_data.items():
        prices = [(k.high + k.low) / 2 for k in kline_series.klines]
        
        if not prices:
            continue
        
        min_p = min(prices)
        max_p = max(prices)
        range_p = max_p - min_p
        
        print(f"\n{tf.value} ({len(prices)} 根 K 线):")
        
        # 简化 ASCII 图
        height = 6
        for row in range(height):
            row_p = max_p - (row / height) * range_p
            row_str = f"{row_p:7.2f} |"
            
            for col, p in enumerate(prices):
                price_row = int((max_p - p) / range_p * height)
                if price_row == row:
                    row_str += "*"
                else:
                    row_str += " "
            
            print(row_str)
        
        print(" " * 8 + "+" + "-" * len(prices))


def main():
    print("\n" + "="*70)
    print("示例 09: 区间套定位")
    print("Example 09: Interval Set (Multi-Level Recursive Positioning)")
    print("="*70)
    
    # 生成多级别数据
    print("\n[1] 生成多级别示例数据...")
    multi_level_data = generate_multi_level_data()
    for tf, data in multi_level_data.items():
        print(f"    {tf.value}: {len(data.klines)} 根 K 线")
    
    # 执行区间套分析
    print("\n[2] 执行区间套分析...")
    analyzer = IntervalSetAnalyzer(levels=[
        TimeFrame.DAY,
        TimeFrame.HOUR_4,
        TimeFrame.MINUTE_30
    ])
    result = analyzer.analyze(multi_level_data)
    
    # 打印各级别分析
    print("\n[3] 各级别分析:")
    for level in result.levels:
        print_level_analysis(level)
    
    # 打印综合结论
    print_interval_set_result(result)
    
    # 可视化
    visualize_multi_level(multi_level_data, result)
    
    # JSON 输出
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    
    json_result = {
        "confirmed": result.confirmed,
        "final_bsp_type": result.final_bsp_type,
        "entry_price": result.entry_price,
        "stop_loss": result.stop_loss,
        "target_price": result.target_price,
        "confidence": result.confidence,
        "description": result.description,
        "levels": [
            {
                "timeframe": level.timeframe.value,
                "trend": level.trend,
                "divergence_detected": level.divergence_detected,
                "potential_bsp": level.potential_bsp,
                "bsp_type": level.bsp_type,
                "price_range": level.price_range,
                "confidence": level.confidence
            }
            for level in result.levels
        ]
    }
    print(json.dumps(json_result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 09 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
