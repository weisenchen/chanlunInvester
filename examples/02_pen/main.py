#!/usr/bin/env python3
"""
示例 02: 笔识别 (新定义)
Example 02: Pen Identification (New 3-K-line Definition)

对应课程：Lesson 62, 65, 77, 81
演示缠论新笔定义的实现和识别

新笔定义核心规则:
1. 至少 3 根 K 线组成
2. 必须有明确的顶分型或底分型
3. 连续笔之间不共用 K 线
4. 满足最小价格波动
"""

import sys
sys.path.insert(0, '/home/wei/.openclaw/workspace/trading-system/python-layer')

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from datetime import datetime, timedelta
import json


def generate_sample_data() -> KlineSeries:
    """
    生成示例 K 线数据
    模拟一个包含多个笔的价格走势
    """
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    base_price = 100.0
    
    # 模拟 30 根 K 线，包含上升笔和下降笔
    price_pattern = [
        # 上升段 (形成向上笔)
        100, 101, 102, 103, 102, 104, 105, 106, 105, 104,
        # 下降段 (形成向下笔)
        103, 102, 101, 100, 99, 98, 99, 100,
        # 再上升段 (形成向上笔)
        101, 102, 103, 104, 105, 104, 103, 102, 101, 100
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
    
    return KlineSeries(klines=klines, symbol="000001.SZ", timeframe="30m")


def identify_pens(kline_series: KlineSeries) -> list:
    """
    识别 K 线序列中的所有笔
    
    算法步骤:
    1. 识别所有分型 (顶分型和底分型)
    2. 连接相邻的顶底分型形成笔
    3. 验证笔的有效性 (至少 3 根 K 线)
    """
    detector = FractalDetector()
    fractals = detector.detect_all(kline_series)
    
    pens = []
    klines = kline_series.klines
    
    # 连接相邻的分型形成笔
    for i in range(len(fractals) - 1):
        curr_fractal = fractals[i]
        next_fractal = fractals[i + 1]
        
        # 检查 K 线数量 (至少 3 根)
        kline_count = next_fractal.kline_index - curr_fractal.kline_index + 1
        if kline_count < 3:
            continue
        
        # 确定笔的方向
        if curr_fractal.is_top:
            direction = "down"
            start_price = klines[curr_fractal.kline_index].high
            end_price = klines[next_fractal.kline_index].low
        else:
            direction = "up"
            start_price = klines[curr_fractal.kline_index].low
            end_price = klines[next_fractal.kline_index].high
        
        pen = {
            "direction": direction,
            "start_idx": curr_fractal.kline_index,
            "end_idx": next_fractal.kline_index,
            "start_price": start_price,
            "end_price": end_price,
            "kline_count": kline_count,
            "magnitude": abs(end_price - start_price),
            "start_time": klines[curr_fractal.kline_index].timestamp.isoformat(),
            "end_time": klines[next_fractal.kline_index].timestamp.isoformat()
        }
        pens.append(pen)
    
    return pens


def print_pens(pens: list):
    """打印笔识别结果"""
    print("\n" + "="*70)
    print("笔识别结果 (Pen Identification Results)")
    print("="*70)
    
    if not pens:
        print("未识别到有效的笔")
        return
    
    print(f"共识别 {len(pens)} 支笔:\n")
    
    for i, pen in enumerate(pens, 1):
        arrow = "↓" if pen["direction"] == "down" else "↑"
        print(f"笔 #{i} {arrow}")
        print(f"  方向：{pen['direction']}")
        print(f"  K 线范围：#{pen['start_idx']} → #{pen['end_idx']} (共{pen['kline_count']}根)")
        print(f"  价格：{pen['start_price']:.2f} → {pen['end_price']:.2f}")
        print(f"  幅度：{pen['magnitude']:.2f} ({pen['magnitude']/pen['start_price']*100:.2f}%)")
        print(f"  时间：{pen['start_time']} → {pen['end_time']}")
        print()


def visualize_pens(kline_series: KlineSeries, pens: list):
    """简单的 ASCII 可视化"""
    print("\n" + "="*70)
    print("价格走势可视化 (ASCII Visualization)")
    print("="*70)
    
    klines = kline_series.klines
    prices = [(k.high + k.low) / 2 for k in klines]
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    # 创建价格到行的映射
    height = 15
    rows = []
    for row in range(height):
        row_price = max_price - (row / height) * price_range
        row_str = f"{row_price:7.2f} |"
        
        for col, price in enumerate(prices):
            # 检查这个位置是否有笔的标记
            pen_marker = None
            for pen in pens:
                if col == pen["start_idx"]:
                    pen_marker = "S" if pen["direction"] == "up" else "s"
                elif col == pen["end_idx"]:
                    pen_marker = "E" if pen["direction"] == "up" else "e"
            
            # 计算当前价格在这个 row 的位置
            price_row = int((max_price - price) / price_range * height)
            
            if price_row == row:
                row_str += "*" if not pen_marker else pen_marker
            elif pen_marker and abs(price_row - row) <= 1:
                row_str += pen_marker
            else:
                row_str += " "
        
        rows.append(row_str)
    
    for row in rows:
        print(row)
    
    print(" " * 8 + "+" + "-" * len(klines))
    print(" " * 8 + "0" + " " * (len(klines)//2 - 1) + "时间" + " " * (len(klines)//2 - 2) + str(len(klines)))
    
    print("\n图例：* = K 线中点，S/s = 笔起点 (上/下)，E/e = 笔终点 (上/下)")


def main():
    print("\n" + "="*70)
    print("示例 02: 笔识别 (新定义)")
    print("Example 02: Pen Identification (New 3-K-line Definition)")
    print("="*70)
    
    # 生成示例数据
    print("\n[1] 生成示例 K 线数据...")
    kline_series = generate_sample_data()
    print(f"    生成 {len(kline_series.klines)} 根 K 线")
    print(f"    代码：{kline_series.symbol}, 周期：{kline_series.timeframe}")
    
    # 识别分型
    print("\n[2] 识别分型...")
    detector = FractalDetector()
    fractals = detector.detect_all(kline_series)
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    print(f"    顶分型：{len(top_fractals)} 个")
    print(f"    底分型：{len(bottom_fractals)} 个")
    
    # 识别笔
    print("\n[3] 识别笔...")
    pens = identify_pens(kline_series)
    
    # 打印结果
    print_pens(pens)
    
    # 可视化
    visualize_pens(kline_series, pens)
    
    # 输出 JSON 结果
    print("\n" + "="*70)
    print("JSON 输出:")
    print("="*70)
    result = {
        "symbol": kline_series.symbol,
        "timeframe": kline_series.timeframe,
        "kline_count": len(kline_series.klines),
        "fractal_count": len(fractals),
        "pen_count": len(pens),
        "pens": pens
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("示例 02 完成 ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
