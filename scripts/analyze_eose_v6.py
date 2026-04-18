#!/usr/bin/env python3
"""
EOSE (Eos Energy Enterprises) v6.0 中枢动量深度分析
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.center import CenterDetector
from trading_system.center_momentum import CenterMomentumAnalyzer, CenterPosition, MomentumStatus, TrendDirection
from trading_system.segment import Segment


def fetch_data(symbol: str, period: str, interval: str):
    """获取数据"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        return history if len(history) > 0 else None
    except Exception:
        return None


def detect_structure(prices):
    """检测缠论结构"""
    fractals = []
    for i in range(2, len(prices) - 2):
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': prices[i]})
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': prices[i]})
    
    pivots = []
    for i in range(len(fractals) - 1):
        f1, f2 = fractals[i], fractals[i+1]
        if f1['type'] != f2['type']:
            pivots.append({'start': f1, 'end': f2, 'direction': 'down' if f1['type'] == 'top' else 'up'})
    
    segments = []
    i = 0
    while i < len(pivots) - 1:
        p1, p2 = pivots[i], pivots[i+1]
        if p1['direction'] == p2['direction']:
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
            i += 2
        else:
            i += 1
    
    # 宽松处理
    if len(segments) < 2 and len(pivots) >= 2:
        for i in range(0, len(pivots) - 1, 2):
            p1, p2 = pivots[i], pivots[i+1]
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
    
    return fractals, pivots, segments


def analyze_level(symbol: str, level: str, period: str, interval: str):
    """分析单个级别"""
    data = fetch_data(symbol, period, interval)
    if data is None or len(data) < 30:
        return {'status': 'no_data', 'level': level}
    
    prices = data['Close'].tolist()
    current_price = prices[-1]
    
    fractals, pivots, segments = detect_structure(prices)
    
    # 创建 Segment 对象
    seg_objects = []
    for seg in segments:
        seg_objects.append(Segment(
            direction=seg['direction'], start_idx=seg['start_idx'], end_idx=seg['end_idx'],
            start_price=seg['start_price'], end_price=seg['end_price'],
            pen_count=2, feature_sequence=[], has_gap=False, confirmed=True
        ))
    
    # 检测中枢
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    # v6.0 中枢动量分析
    if centers and len(seg_objects) >= 2:
        analyzer = CenterMomentumAnalyzer(level=level)
        analysis = analyzer.analyze(centers, seg_objects, current_price)
        
        return {
            'status': 'ok',
            'level': level,
            'price': current_price,
            'fractals': len(fractals),
            'pivots': len(pivots),
            'segments': len(segments),
            'centers': len(centers),
            'analysis': analysis,
        }
    else:
        return {
            'status': 'no_center',
            'level': level,
            'price': current_price,
            'fractals': len(fractals),
            'pivots': len(pivots),
            'segments': len(segments),
            'centers': 0,
        }


def main():
    """主函数"""
    print("=" * 90)
    print("EOSE (Eos Energy Enterprises) v6.0 中枢动量深度分析")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    # 分析多级别
    print("📊 多级别分析...")
    print("-" * 90)
    
    result_1d = analyze_level("EOSE", "1d", "6mo", "1d")
    result_30m = analyze_level("EOSE", "30m", "10d", "30m")
    result_5m = analyze_level("EOSE", "5m", "2d", "5m")
    
    # 输出结果
    for r in [result_1d, result_30m, result_5m]:
        level_name = {'1d': '日线', '30m': '30 分钟', '5m': '5 分钟'}.get(r['level'], r['level'])
        print(f"\n【{level_name}】")
        
        if r['status'] == 'no_data':
            print("  数据不足")
            continue
        
        print(f"  价格：${r['price']:.2f}")
        print(f"  分型：{r['fractals']} (顶：{r['fractals']//2}, 底：{r['fractals']//2})")
        print(f"  笔：{r['pivots']}")
        print(f"  线段：{r['segments']}")
        print(f"  中枢：{r['centers']}个")
        
        if r['status'] == 'ok':
            a = r['analysis']
            print(f"\n  v6.0 中枢动量分析:")
            print(f"    中枢位置：{a.center_position.value}")
            print(f"    趋势方向：{a.trend_direction.value}")
            print(f"    动量状态：{a.momentum_status.value} ({a.momentum_score:+.1f})")
            print(f"    趋势阶段：{a.trend_stage}")
            print(f"    延续概率：{a.continuation_probability:.1f}%")
            print(f"    反转风险：{a.reversal_risk:.1f}%")
            print(f"    操作建议：{a.suggestion} (置信度：{a.confidence:.1f}%)")
    
    print()
    print("=" * 90)
    print("【v6.0 综合评估】")
    print("=" * 90)
    print()
    
    # 综合评估
    if result_1d['status'] == 'ok' and result_30m['status'] == 'ok':
        a1d = result_1d['analysis']
        a30m = result_30m['analysis']
        
        print(f"日线：{a1d.trend_direction.value} | {a1d.center_position.value} | {a1d.momentum_status.value}")
        print(f"30m:  {a30m.trend_direction.value} | {a30m.center_position.value} | {a30m.momentum_status.value}")
        print()
        
        # 多级别共振判断
        if a1d.trend_direction == a30m.trend_direction and a1d.trend_direction != TrendDirection.UNKNOWN:
            print("✅ 多级别共振：日线 +30m 同向")
            resonance_bonus = "+15%"
        else:
            print("⚪ 无多级别共振：级别方向不一致")
            resonance_bonus = "0%"
        
        print()
        print("=" * 90)
        print("【买卖点分析】")
        print("=" * 90)
        print()
        
        # 买卖点判断
        has_buy_signal = False
        has_sell_signal = False
        
        # buy1 条件：底背驰
        if result_1d['status'] == 'ok':
            if a1d.center_position in [CenterPosition.AFTER_FIRST, CenterPosition.AFTER_SECOND]:
                if a1d.momentum_status == MomentumStatus.INCREASING:
                    print("✅ buy1 潜在信号：日线第 1/2 中枢后，动量增强")
                    has_buy_signal = True
        
        # buy2 条件：回调不破前低
        if result_30m['status'] == 'ok':
            if a30m.center_position == CenterPosition.AFTER_FIRST:
                print("✅ buy2 潜在信号：30m 第一中枢后")
                has_buy_signal = True
        
        # sell1 条件：顶背驰
        if result_1d['status'] == 'ok':
            if a1d.center_position == CenterPosition.AFTER_THIRD:
                print("⚠️ sell1 潜在信号：日线第三中枢后，背驰风险")
                has_sell_signal = True
        
        if not has_buy_signal and not has_sell_signal:
            print("⚪ 无明确买卖点信号")
            print("   原因：中枢结构不完整或趋势不明")
        
        print()
        print("=" * 90)
        print("【操作建议】")
        print("=" * 90)
        print()
        
        if has_buy_signal:
            print("✅ 建议：轻仓试多 (20-30%)")
            print(f"   理由：{'日线中枢确认后' if a1d.status == 'ok' else '30m 中枢确认'}")
            print(f"   共振加成：{resonance_bonus}")
        elif has_sell_signal:
            print("⚠️ 建议：减仓/观望")
            print("   理由：背驰风险")
        else:
            print("⚪ 建议：观望")
            print("   理由：等待中枢形成或买卖点确认")
            print("   关注：")
            print(f"     - 日线中枢形成 (当前{result_1d['centers']}个)")
            print(f"     - 30m 买卖点确认 (当前{result_30m['centers']}个中枢)")
        
        print()
        print("=" * 90)
        print("【关键位置】")
        print("=" * 90)
        print()
        
        current_price = result_1d['price']
        print(f"当前价格：${current_price:.2f}")
        print(f"阻力位：${current_price * 1.05:.2f} (+5%)")
        print(f"强阻力：${current_price * 1.10:.2f} (+10%)")
        print(f"支撑位：${current_price * 0.95:.2f} (-5%)")
        print(f"强支撑：${current_price * 0.90:.2f} (-10%)")
        
    else:
        print("数据不足，无法进行综合评估")
    
    print()
    print("=" * 90)
    print("分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
