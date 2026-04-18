#!/usr/bin/env python3
"""
SMR 深度分析 - v6.0 中枢动量版
分析日线和 30 分钟级别的买卖点及中枢趋势情况
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.kline import KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator
from trading_system.center_momentum_confidence import (
    CenterMomentumConfidenceCalculator,
    CenterPosition,
    MomentumStatus
)


def fetch_data(symbol: str, period: str, interval: str) -> KlineSeries:
    """获取 K 线数据"""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval)
    
    if len(history) == 0:
        return None
    
    # 转换为 Kline 对象
    from trading_system.kline import Kline
    klines = []
    for idx, row in history.iterrows():
        klines.append(Kline(
            timestamp=idx,
            open=row['Open'],
            high=row['High'],
            low=row['Low'],
            close=row['Close'],
            volume=row['Volume']
        ))
    
    return KlineSeries(klines=klines)


def analyze_level(series: KlineSeries, level_name: str) -> dict:
    """分析单个级别"""
    print(f"\n【{level_name}级别分析】")
    print("=" * 60)
    
    # 检测分型
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    # 检测笔
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    
    # 检测线段
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    
    # 检测中枢
    center_det = CenterDetector(min_segments=3)
    centers = center_det.detect_centers(segments)
    
    # 计算 MACD
    prices = [k.close for k in series.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_data = macd.calculate(prices)
    
    # 当前价格
    current_price = series.klines[-1].close
    
    print(f"K 线数量：{len(series.klines)}")
    print(f"分型：{len(fractals)} (顶：{len(top_fractals)}, 底：{len(bottom_fractals)})")
    print(f"笔：{len(pens)}")
    print(f"线段：{len(segments)}")
    print(f"中枢：{len(centers)}")
    
    if centers:
        print(f"\n中枢详情:")
        for i, c in enumerate(centers):
            print(f"  中枢{i+1}: ZG={c.zg:.2f}, ZD={c.zd:.2f}, 区间={c.zg-c.zd:.2f}")
    
    # 中枢动量分析
    if centers and len(segments) >= 3:
        print(f"\n【中枢动量分析】")
        momentum_calc = CenterMomentumConfidenceCalculator()
        momentum_result = momentum_calc.calculate(
            symbol="SMR",
            level=level_name,
            price=current_price,
            centers=centers,
            segments=segments,
            level_name=level_name
        )
        
        print(f"  中枢数量：{momentum_result.center_count}")
        print(f"  当前位置：{momentum_result.center_position.value}")
        print(f"  动量状态：{momentum_result.momentum_status.value}")
        print(f"  趋势方向：{momentum_result.trend_direction.value}")
        print(f"  可信度调整：{momentum_result.total_bonus*100:+.1f}%")
        print(f"  背驰风险：{'⚠️ 高' if momentum_result.divergence_risk else '✅ 低'}")
        print(f"  延续概率：{momentum_result.raw_analysis.continuation_probability:.1f}%" if momentum_result.raw_analysis else "N/A")
        print(f"  反转风险：{momentum_result.raw_analysis.reversal_risk:.1f}%" if momentum_result.raw_analysis else "N/A")
        
        return {
            'level': level_name,
            'centers': centers,
            'segments': segments,
            'momentum_result': momentum_result,
            'current_price': current_price,
        }
    else:
        print(f"  ⚪ 无中枢或线段不足，无法进行动量分析")
        return {
            'level': level_name,
            'centers': [],
            'segments': segments,
            'momentum_result': None,
            'current_price': current_price,
        }


def main():
    """主函数"""
    print("=" * 70)
    print("SMR (NuScale Power) 深度分析 - v6.0 中枢动量版")
    print("=" * 70)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    # 获取数据
    print("📈 获取数据...")
    series_1d = fetch_data("SMR", "1y", "1d")
    series_30m = fetch_data("SMR", "10d", "30m")
    
    if not series_1d or not series_30m:
        print("❌ 数据获取失败")
        return
    
    current_price = series_1d.klines[-1].close
    print(f"当前价格：${current_price:.2f}")
    print(f"日线数据：{len(series_1d.klines)}条")
    print(f"30 分钟数据：{len(series_30m.klines)}条")
    
    # 分析各级别
    print("\n" + "=" * 70)
    print("缠论结构分析")
    print("=" * 70)
    
    result_1d = analyze_level(series_1d, "1d")
    result_30m = analyze_level(series_30m, "30m")
    
    # 综合分析
    print("\n" + "=" * 70)
    print("【v6.0 综合评估】")
    print("=" * 70)
    
    print(f"\n当前价格：${current_price:.2f}")
    print()
    
    # 日线评估
    if result_1d['momentum_result']:
        m1d = result_1d['momentum_result']
        print(f"日线级别:")
        print(f"  中枢序号：第{m1d.center_count}中枢{m1d.center_position.value.replace('第', '').replace('中枢', '')}")
        print(f"  动量状态：{m1d.momentum_status.value}")
        print(f"  可信度调整：{m1d.total_bonus*100:+.1f}%")
        
        if m1d.center_position == CenterPosition.AFTER_FIRST:
            print(f"  ✅ 第一中枢后，趋势初现，可关注 30m 确认")
        elif m1d.center_position == CenterPosition.AFTER_SECOND:
            print(f"  ✅ 第二中枢后，趋势确认，可积极操作")
        elif m1d.center_position == CenterPosition.AFTER_THIRD:
            print(f"  ⚠️ 第三中枢后，警惕背驰，等待反转信号")
    
    print()
    
    # 30 分钟评估
    if result_30m['momentum_result']:
        m30 = result_30m['momentum_result']
        print(f"30 分钟级别:")
        print(f"  中枢序号：第{m30.center_count}中枢{m30.center_position.value.replace('第', '').replace('中枢', '')}")
        print(f"  动量状态：{m30.momentum_status.value}")
        print(f"  可信度调整：{m30.total_bonus*100:+.1f}%")
    
    print()
    print("=" * 70)
    print("【操作建议】")
    print("=" * 70)
    
    # 根据日线 buy1 信号和中枢位置给出建议
    if result_1d['momentum_result']:
        m1d = result_1d['momentum_result']
        
        if m1d.center_position in [CenterPosition.AFTER_FIRST, CenterPosition.AFTER_SECOND]:
            print("\n✅  favorable 场景:")
            print("  日线第一/二中枢后出现 buy1 背驰信号")
            print("  建议：等待 30m 级别 buy2 确认")
            print("  仓位：确认后 30-40%")
            print("  止损：背驰低点下方 8-10%")
        elif m1d.center_position == CenterPosition.AFTER_THIRD:
            print("\n⚠️ 背驰风险场景:")
            print("  日线第三中枢后，警惕趋势背驰")
            print("  建议：等待明确反转信号，不急于入场")
            print("  仓位：观望或轻仓 (<20%)")
        else:
            print("\n⚪ 观望场景:")
            print("  中枢结构不明，等待清晰信号")
            print("  建议：观望，等待日线/30m 确认")
    
    print()
    print("=" * 70)
    print("分析完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
