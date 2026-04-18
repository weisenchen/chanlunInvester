#!/usr/bin/env python3
"""
SMR 深度分析 - v6.0 中枢动量增强版
使用更宽松的中枢检测参数
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator
from trading_system.center_momentum import CenterMomentumAnalyzer, format_center_analysis_report


def fetch_data_raw(symbol: str, period: str, interval: str):
    """获取原始数据"""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval)
    return history


def detect_centers_from_price(prices: list, level_name: str, min_segments: int = 2):
    """从价格序列直接检测中枢（简化版）"""
    # 检测分型
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
    
    # 检测笔
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
    
    # 检测线段（简化：连续同向笔）
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
    
    # 创建中枢检测器（使用更宽松的 min_segments=2）
    from trading_system.center import Center
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
    
    # 检测中枢
    center_det = CenterDetector(min_segments=min_segments)
    centers = center_det.detect_centers(seg_objects)
    
    return {
        'fractals': fractals,
        'pivots': pivots,
        'segments': segments,
        'seg_objects': seg_objects,
        'centers': centers,
    }


def analyze_level_enhanced(symbol: str, level_name: str, period: str, interval: str):
    """增强版级别分析"""
    print(f"\n【{level_name}级别分析】")
    print("=" * 60)
    
    # 获取数据
    data = fetch_data_raw(symbol, period, interval)
    if len(data) == 0:
        print("❌ 数据获取失败")
        return None
    
    prices = data['Close'].tolist()
    current_price = prices[-1]
    
    print(f"K 线数量：{len(prices)}")
    print(f"当前价格：${current_price:.2f}")
    
    # 检测结构
    result = detect_centers_from_price(prices, level_name, min_segments=2)
    
    print(f"分型：{len(result['fractals'])} (顶：{len([f for f in result['fractals'] if f['type']=='top'])}, 底：{len([f for f in result['fractals'] if f['type']=='bottom'])})")
    print(f"笔：{len(result['pivots'])}")
    print(f"线段：{len(result['segments'])}")
    print(f"中枢：{len(result['centers'])}")
    
    if result['centers']:
        print(f"\n中枢详情:")
        for i, c in enumerate(result['centers']):
            print(f"  中枢{i+1}: ZG={c.zg:.2f}, ZD={c.zd:.2f}, 区间={c.zg-c.zd:.2f}")
    
    # 中枢动量分析
    if result['centers'] and len(result['seg_objects']) >= 2:
        print(f"\n【中枢动量分析】")
        analyzer = CenterMomentumAnalyzer(level=level_name)
        analysis = analyzer.analyze(result['centers'], result['seg_objects'], current_price)
        
        print(f"  中枢数量：{len(analysis.centers)}")
        print(f"  当前位置：{analysis.center_position.value}")
        print(f"  趋势方向：{analysis.trend_direction.value}")
        print(f"  动量状态：{analysis.momentum_status.value}")
        print(f"  动量分数：{analysis.momentum_score:+.1f}")
        print(f"  趋势阶段：{analysis.trend_stage}")
        print(f"  延续概率：{analysis.continuation_probability:.1f}%")
        print(f"  反转风险：{analysis.reversal_risk:.1f}%")
        print(f"  操作建议：{analysis.suggestion} (置信度：{analysis.confidence:.1f}%)")
        
        return {
            'level': level_name,
            'current_price': current_price,
            'analysis': analysis,
            'centers': result['centers'],
        }
    else:
        print(f"  ⚪ 中枢数量不足或线段太少，无法进行动量分析")
        return {
            'level': level_name,
            'current_price': current_price,
            'analysis': None,
            'centers': [],
        }


def main():
    """主函数"""
    print("=" * 70)
    print("SMR (NuScale Power) 深度分析 - v6.0 中枢动量增强版")
    print("=" * 70)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    # 分析日线
    result_1d = analyze_level_enhanced("SMR", "1d", "1y", "1d")
    
    # 分析 30 分钟
    result_30m = analyze_level_enhanced("SMR", "30m", "10d", "30m")
    
    # 综合评估
    print("\n" + "=" * 70)
    print("【v6.0 综合评估】")
    print("=" * 70)
    
    if result_1d and result_1d['analysis']:
        a1d = result_1d['analysis']
        print(f"\n日线级别:")
        print(f"  位置：{a1d.center_position.value}")
        print(f"  趋势：{a1d.trend_direction.value}")
        print(f"  动量：{a1d.momentum_status.value} ({a1d.momentum_score:+.1f})")
        print(f"  延续概率：{a1d.continuation_probability:.1f}%")
        print(f"  操作建议：{a1d.suggestion}")
    
    if result_30m and result_30m['analysis']:
        a30 = result_30m['analysis']
        print(f"\n30 分钟级别:")
        print(f"  位置：{a30.center_position.value}")
        print(f"  趋势：{a30.trend_direction.value}")
        print(f"  动量：{a30.momentum_status.value} ({a30.momentum_score:+.1f})")
        print(f"  延续概率：{a30.continuation_probability:.1f}%")
        print(f"  操作建议：{a30.suggestion}")
    
    print("\n" + "=" * 70)
    print("【操作建议】")
    print("=" * 70)
    
    # 综合判断
    if result_1d and result_30m:
        if result_1d['analysis'] and result_30m['analysis']:
            a1d = result_1d['analysis']
            a30 = result_30m['analysis']
            
            print()
            if (a1d.center_position.value in ['第一个中枢后', '第二个中枢后'] and
                a1d.trend_direction.value == '上涨'):
                print("✅  favorable 场景:")
                print("  日线第一/二中枢后，上涨趋势")
                print("  建议：等待 30m buy2 确认入场")
                print("  仓位：30-40%")
            elif a1d.center_position.value == '第三个中枢后 (趋势背驰风险区)':
                print("⚠️ 背驰风险场景:")
                print("  日线第三中枢后，警惕背驰")
                print("  建议：等待明确反转信号")
                print("  仓位：观望或<20%")
            else:
                print("⚪ 观望场景:")
                print("  中枢结构不明或趋势不明")
                print("  建议：观望，等待清晰信号")
    
    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
