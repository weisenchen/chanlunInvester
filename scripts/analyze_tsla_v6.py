#!/usr/bin/env python3
"""
TSLA 30 分钟深度分析 - v6.0 中枢动量版
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator
from trading_system.center_momentum import CenterMomentumAnalyzer, CenterPosition, MomentumStatus


def fetch_data(symbol: str, period: str, interval: str):
    """获取数据"""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval)
    return history


def detect_fractals(prices):
    """检测分型"""
    fractals = []
    for i in range(2, len(prices) - 2):
        # 顶分型
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
            prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': prices[i]})
        # 底分型
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
              prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': prices[i]})
    return fractals


def detect_pivots(fractals):
    """检测笔"""
    pivots = []
    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]
        if f1['type'] != f2['type']:
            pivots.append({
                'start': f1,
                'end': f2,
                'direction': 'down' if f1['type'] == 'top' else 'up'
            })
    return pivots


def detect_segments(pivots):
    """检测线段 (简化版)"""
    segments = []
    i = 0
    while i < len(pivots) - 1:
        p1 = pivots[i]
        p2 = pivots[i + 1]
        if p1['direction'] == p2['direction']:
            segments.append({
                'start_idx': p1['start']['index'],
                'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'],
                'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
            i += 2
        else:
            i += 1
    return segments


def analyze_tsla_30m():
    """分析 TSLA 30 分钟"""
    print("=" * 70)
    print("TSLA (Tesla) 30 分钟深度分析 - v6.0 中枢动量版")
    print("=" * 70)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    # 获取数据
    print("📈 获取数据...")
    data = fetch_data("TSLA", "5d", "30m")
    
    if len(data) == 0:
        print("❌ 数据获取失败")
        return
    
    prices = data['Close'].tolist()
    current_price = prices[-1]
    
    print(f"K 线数量：{len(prices)}")
    print(f"当前价格：${current_price:.2f}")
    print()
    
    # 检测结构
    print("【缠论结构检测】")
    print("-" * 60)
    
    fractals = detect_fractals(prices)
    top_fractals = [f for f in fractals if f['type'] == 'top']
    bottom_fractals = [f for f in fractals if f['type'] == 'bottom']
    
    pivots = detect_pivots(fractals)
    segments = detect_segments(pivots)
    
    print(f"分型：{len(fractals)} (顶：{len(top_fractals)}, 底：{len(bottom_fractals)})")
    print(f"笔：{len(pivots)}")
    print(f"线段：{len(segments)}")
    
    if segments:
        print(f"\n线段详情:")
        for i, seg in enumerate(segments):
            print(f"  线段{i+1}: {seg['direction']} @ ${seg['start_price']:.2f} → ${seg['end_price']:.2f}")
    
    # 检测中枢
    print()
    print("【中枢检测】")
    print("-" * 60)
    
    # 创建 Segment 对象
    from trading_system.segment import Segment
    seg_objects = []
    for seg in segments:
        seg_obj = Segment(
            direction=seg['direction'],
            start_idx=seg['start_idx'],
            end_idx=seg['end_idx'],
            start_price=seg['start_price'],
            end_price=seg['end_price'],
            amplitude=abs(seg['end_price'] - seg['start_price']),
            fractals=[],
            is_temp=False,
            confirmed=True
        )
        seg_objects.append(seg_obj)
    
    # 检测中枢 (使用 min_segments=2)
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    if centers:
        print(f"中枢数量：{len(centers)}")
        print(f"\n中枢详情:")
        for i, c in enumerate(centers):
            print(f"  中枢{i+1}: ZG={c.zg:.2f}, ZD={c.zd:.2f}, 区间={c.zg-c.zd:.2f}")
            print(f"    位置：索引 {c.start_idx} - {c.end_idx}")
    else:
        print("中枢数量：0")
        print("⚪ 线段数量不足或无明显重叠区间")
    
    # v6.0 中枢动量分析
    print()
    print("【v6.0 中枢动量分析】")
    print("-" * 60)
    
    if centers and len(seg_objects) >= 2:
        analyzer = CenterMomentumAnalyzer(level="30m")
        analysis = analyzer.analyze(centers, seg_objects, current_price)
        
        print(f"中枢数量：{len(analysis.centers)}")
        print(f"当前位置：{analysis.center_position.value}")
        print(f"趋势方向：{analysis.trend_direction.value}")
        print(f"动量状态：{analysis.momentum_status.value}")
        print(f"动量分数：{analysis.momentum_score:+.1f}")
        print(f"趋势阶段：{analysis.trend_stage}")
        print(f"延续概率：{analysis.continuation_probability:.1f}%")
        print(f"反转风险：{analysis.reversal_risk:.1f}%")
        print(f"操作建议：{analysis.suggestion} (置信度：{analysis.confidence:.1f}%)")
        
        # 详细分析
        print()
        print("【中枢序列分析】")
        print("-" * 60)
        if analysis.centers:
            for c in analysis.centers:
                print(f"第{c.index}中枢:")
                print(f"  ZG={c.zg:.2f}, ZD={c.zd:.2f}, 区间={c.range_size:.2f}")
                print(f"  区间变化：{c.range_change*100:+.1f}%")
                print(f"  动量变化：{c.momentum_change*100:+.1f}%")
        
        # 操作建议
        print()
        print("=" * 70)
        print("【操作建议】")
        print("=" * 70)
        
        if analysis.center_position == CenterPosition.BEFORE_FIRST:
            print("\n⚪ 第一个中枢前 - 观望等待")
            print("  说明：中枢结构尚未形成，趋势不明")
            print("  建议：等待中枢形成后再判断")
            print("  仓位：0-10%")
        elif analysis.center_position in [CenterPosition.IN_FIRST, CenterPosition.AFTER_FIRST]:
            print("\n✅ 第一中枢阶段 - 趋势初现")
            print("  说明：第一个中枢形成，趋势初现")
            print("  建议：轻仓试单，等待第二中枢确认")
            print("  仓位：20-30%")
        elif analysis.center_position in [CenterPosition.IN_SECOND, CenterPosition.AFTER_SECOND]:
            print("\n✅ 第二中枢阶段 - 趋势确认")
            print("  说明：第二个中枢形成，趋势确认")
            print("  建议：积极操作，顺势而为")
            print("  仓位：40-50%")
        elif analysis.center_position == CenterPosition.IN_THIRD:
            print("\n⚠️ 第三中枢 - 警惕背驰")
            print("  说明：第三个中枢，背驰风险区")
            print("  建议：减仓观望，准备离场")
            print("  仓位：20-30%")
        elif analysis.center_position == CenterPosition.AFTER_THIRD:
            print("\n⚠️ 第三中枢后 - 背驰高风险")
            print("  说明：第三个中枢后，背驰高风险区")
            print("  建议：等待反转信号，避免追涨杀跌")
            print("  仓位：0-20%")
        
        # 关键位置
        print()
        print("【关键位置】")
        print("-" * 60)
        if centers:
            last_center = centers[-1]
            print(f"最新中枢上沿 (ZG): ${last_center.zg:.2f}")
            print(f"最新中枢下沿 (ZD): ${last_center.zd:.2f}")
            print(f"突破目标：${last_center.zg * 1.05:.2f} (+5%)")
            print(f"跌破风险：${last_center.zd * 0.95:.2f} (-5%)")
        
    else:
        print("⚪ 中枢数量不足，无法进行动量分析")
        print("\n【操作建议】")
        print("-" * 60)
        print("  说明：线段数量不足，中枢尚未形成")
        print("  建议：观望，等待中枢结构清晰")
        print("  仓位：0-10%")
    
    print()
    print("=" * 70)
    print("分析完成")
    print("=" * 70)


if __name__ == "__main__":
    analyze_tsla_30m()
