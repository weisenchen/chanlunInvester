#!/usr/bin/env python3
"""
SMR (NuScale Power) 多级别监控 - v6.0 中枢动量版
监控 5m + 30m + 1d 买卖点预警
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.center import CenterDetector
from trading_system.center_momentum import CenterMomentumAnalyzer, CenterPosition, MomentumStatus
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
    
    if len(segments) < 2 and len(pivots) >= 2:
        for i in range(0, len(pivots) - 1, 2):
            p1, p2 = pivots[i], pivots[i+1]
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
    
    return fractals, pivots, segments


def detect_buy_sell_points(fractals, pivots, segments, macd_data, prices, level):
    """检测买卖点"""
    signals = []
    current_price = prices[-1]
    top_fractals = [f for f in fractals if f['type'] == 'top']
    bottom_fractals = [f for f in fractals if f['type'] == 'bottom']
    
    # buy1: 底背驰
    if len(bottom_fractals) >= 2:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        if last_low['price'] < prev_low['price']:
            # MACD 背驰检查
            last_idx = last_low['index']
            prev_idx = prev_low['index']
            if macd_data and last_idx < len(macd_data) and prev_idx < len(macd_data):
                last_macd = macd_data[last_idx] if isinstance(macd_data[last_idx], (int, float)) else 0
                prev_macd = macd_data[prev_idx] if isinstance(macd_data[prev_idx], (int, float)) else 0
                if last_macd > prev_macd:
                    signals.append({
                        'type': 'buy1',
                        'name': f'{level}级别第一类买点 (背驰)',
                        'price': current_price,
                        'confidence': 'high' if last_macd > prev_macd * 1.5 else 'medium',
                    })
    
    # buy2: 回调不破前低
    if len(bottom_fractals) >= 2 and len(top_fractals) >= 1:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        if last_low['price'] > prev_low['price']:
            signals.append({
                'type': 'buy2',
                'name': f'{level}级别第二类买点',
                'price': current_price,
                'confidence': 'medium',
            })
    
    # sell1: 顶背驰
    if len(top_fractals) >= 2:
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]
        if last_high['price'] > prev_high['price']:
            signals.append({
                'type': 'sell1',
                'name': f'{level}级别第一类卖点 (背驰)',
                'price': current_price,
                'confidence': 'medium',
            })
    
    # sell2: 反弹不过前高
    if len(top_fractals) >= 2 and len(bottom_fractals) >= 1:
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]
        if last_high['price'] < prev_high['price']:
            signals.append({
                'type': 'sell2',
                'name': f'{level}级别第二类卖点',
                'price': current_price,
                'confidence': 'medium',
            })
    
    return signals


def analyze_level(symbol: str, level: str, period: str, interval: str):
    """分析单个级别"""
    data = fetch_data(symbol, period, interval)
    if data is None or len(data) < 30:
        return {'status': 'no_data', 'level': level}
    
    prices = data['Close'].tolist()
    volumes = data['Volume'].tolist()
    current_price = prices[-1]
    
    # 计算 MACD (简化)
    macd_data = []
    if len(prices) > 26:
        for i in range(len(prices)):
            if i >= 26:
                ema12 = sum(prices[max(0,i-12):i+1]) / min(12, i+1)
                ema26 = sum(prices[max(0,i-26):i+1]) / min(26, i+1)
                macd_data.append(ema12 - ema26)
            else:
                macd_data.append(0)
    
    fractals, pivots, segments = detect_structure(prices)
    
    seg_objects = []
    for seg in segments:
        seg_objects.append(Segment(
            direction=seg['direction'], start_idx=seg['start_idx'], end_idx=seg['end_idx'],
            start_price=seg['start_price'], end_price=seg['end_price'],
            pen_count=2, feature_sequence=[], has_gap=False, confirmed=True
        ))
    
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    # 检测买卖点
    bsp_signals = detect_buy_sell_points(fractals, pivots, segments, macd_data, prices, level)
    
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
            'signals': bsp_signals,
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
            'signals': bsp_signals,
        }


def send_alert(symbol: str, signal: dict, level: str, analysis=None):
    """发送警报"""
    emoji = {'buy1': '🟢', 'buy2': '🟢', 'buy3': '🟢', 'sell1': '🔴', 'sell2': '🔴', 'sell3': '🔴'}.get(signal['type'], '⚪')
    
    print(f"\n{emoji} **{symbol} {level}级别{signal['type']} @ ${signal['price']:.2f}**")
    
    if analysis:
        a = analysis
        print(f"   中枢位置：{a.center_position.value}")
        print(f"   趋势方向：{a.trend_direction.value}")
        print(f"   动量状态：{a.momentum_status.value} ({a.momentum_score:+.1f})")
        print(f"   延续概率：{a.continuation_probability:.1f}%")
        print(f"   反转风险：{a.reversal_risk:.1f}%")
        
        # v6.0 可信度调整
        if a.center_position == CenterPosition.AFTER_SECOND:
            print(f"   v6.0 调整：+15% (第 2 中枢后)")
        elif a.center_position == CenterPosition.AFTER_THIRD:
            print(f"   v6.0 调整：-25% (第 3 中枢后) ⚠️")
    
    print(f"   置信度：{signal['confidence']}")
    print(f"   操作建议：{'轻仓试多 (20-30%)' if 'buy' in signal['type'] else '轻仓试空 (20-30%)'}")


def main():
    """主函数"""
    print("=" * 90)
    print("SMR (NuScale Power) 多级别监控 - v6.0 中枢动量版")
    print("=" * 90)
    print(f"监控时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"监控级别：5m + 30m + 1d")
    print()
    
    # 分析多级别
    print("📊 多级别分析...")
    print("-" * 90)
    
    result_5m = analyze_level("SMR", "5m", "2d", "5m")
    result_30m = analyze_level("SMR", "30m", "10d", "30m")
    result_1d = analyze_level("SMR", "1d", "6mo", "1d")
    
    # 输出结果
    all_signals = []
    
    for r in [result_5m, result_30m, result_1d]:
        level_name = {'5m': '5 分钟', '30m': '30 分钟', '1d': '日线'}.get(r['level'], r['level'])
        print(f"\n【{level_name}】")
        
        if r['status'] == 'no_data':
            print("  数据不足")
            continue
        
        print(f"  价格：${r['price']:.2f}")
        print(f"  分型：{r['fractals']} (顶：{r['fractals']//2}, 底：{r['fractals']//2})")
        print(f"  笔：{r['pivots']}")
        print(f"  线段：{r['segments']}")
        print(f"  中枢：{r['centers']}个")
        
        if r['signals']:
            print(f"  买卖点：{len(r['signals'])}")
            for sig in r['signals']:
                print(f"    🎯 {sig['type']}: {sig['name']} @ ${sig['price']:.2f}")
                all_signals.append({'level': r['level'], 'signal': sig, 'analysis': r.get('analysis')})
        else:
            print(f"  买卖点：0")
        
        if r['status'] == 'ok':
            a = r['analysis']
            print(f"\n  v6.0 中枢动量:")
            print(f"    位置：{a.center_position.value}")
            print(f"    趋势：{a.trend_direction.value}")
            print(f"    动量：{a.momentum_status.value} ({a.momentum_score:+.1f})")
            print(f"    延续：{a.continuation_probability:.1f}% | 风险：{a.reversal_risk:.1f}%")
    
    print()
    print("=" * 90)
    print("【买卖点预警提醒】")
    print("=" * 90)
    
    if all_signals:
        for item in all_signals:
            send_alert("SMR", item['signal'], item['level'], item['analysis'])
    else:
        print("\n⚪ 无买卖点信号")
    
    print()
    print("=" * 90)
    print("【v6.0 综合评估】")
    print("=" * 90)
    print()
    
    if result_1d['status'] == 'ok' and result_30m['status'] == 'ok':
        a1d = result_1d['analysis']
        a30m = result_30m['analysis']
        
        # 多级别共振
        if a1d.trend_direction == a30m.trend_direction and a1d.trend_direction.value != '未知':
            print("✅ 多级别共振：日线 +30m 同向")
            resonance = "+15%"
        else:
            print("⚪ 无多级别共振：级别方向不一致")
            resonance = "0%"
        
        print()
        print("=" * 90)
        print("【操作建议】")
        print("=" * 90)
        print()
        
        # 综合建议
        has_buy = any(s['signal']['type'] in ['buy1', 'buy2'] for s in all_signals)
        has_sell = any(s['signal']['type'] in ['sell1', 'sell2'] for s in all_signals)
        
        if has_buy and not has_sell:
            print("✅ 建议：轻仓试多 (20-30%)")
            print(f"   理由：buy 信号确认，无 sell 信号")
            print(f"   共振加成：{resonance}")
        elif has_sell and not has_buy:
            print("⚠️ 建议：轻仓试空 (20-30%) 或观望")
            print(f"   理由：sell 信号确认")
        elif has_buy and has_sell:
            print("⚪ 建议：观望")
            print("   理由：买卖点同时存在，方向不明")
        else:
            print("⚪ 建议：观望")
            print("   理由：无明确买卖点信号")
        
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
    
    print()
    print("=" * 90)
    print("监控完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
