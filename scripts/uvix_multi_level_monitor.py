#!/usr/bin/env python3
"""
UVIX 缠论多级别联动监控系统
5 分钟 +30 分钟级别联合分析，精确定位买卖点
使用 chanlunInvester 项目核心功能
GitHub: https://github.com/weisenchen/chanlunInvester
"""

import sys
import json
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator


def fetch_data(timeframe='5m', count=100):
    """获取 UVIX 数据"""
    ticker = yf.Ticker('UVIX')
    
    if timeframe == '5m':
        history = ticker.history(period='5d', interval='5m')
    elif timeframe == '30m':
        history = ticker.history(period='1mo', interval='30m')
    else:
        history = ticker.history(period='3mo', interval='1d')
    
    klines = []
    for idx, row in history.iterrows():
        if hasattr(idx, 'to_pydatetime'):
            timestamp = idx.to_pydatetime()
        else:
            timestamp = idx
        
        kline = Kline(
            timestamp=timestamp,
            open=float(row['Open']),
            high=float(row['High']),
            low=float(row['Low']),
            close=float(row['Close']),
            volume=int(row['Volume']) if 'Volume' in row else 0
        )
        klines.append(kline)
    
    if len(klines) > count:
        klines = klines[-count:]
    
    return KlineSeries(klines=klines, symbol='UVIX', timeframe=timeframe)


def analyze_chanlun(series):
    """执行缠论分析"""
    results = {}
    
    # 1. 分型
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    results['fractals'] = {
        'total': len(fractals),
        'top': len([f for f in fractals if f.is_top]),
        'bottom': len([f for f in fractals if not f.is_top])
    }
    
    # 2. 笔
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    results['pens'] = {
        'total': len(pens),
        'up': len([p for p in pens if p.is_up]),
        'down': len([p for p in pens if p.is_down]),
        'latest': pens[-1] if pens else None
    }
    
    # 3. 线段
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    results['segments'] = {
        'total': len(segments),
        'up': len([s for s in segments if s.is_up]),
        'down': len([s for s in segments if s.is_down]),
        'latest': segments[-1] if segments else None
    }
    
    # 4. MACD 背驰
    prices = [k.close for k in series.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_data = macd.calculate(prices)
    results['divergence'] = detect_divergence(segments, macd_data)
    
    # 5. 买卖点
    results['buy_sell_points'] = detect_buy_sell_points(segments, results['divergence'])
    
    return results


def detect_divergence(segments, macd_data):
    """检测背驰"""
    if len(segments) < 2 or not macd_data:
        return {'detected': False}
    
    last_seg = segments[-1]
    prev_seg = None
    
    for seg in reversed(segments[:-1]):
        if seg.direction == last_seg.direction:
            prev_seg = seg
            break
    
    if not prev_seg:
        return {'detected': False}
    
    try:
        macd_prev = macd_data[prev_seg.end_idx].histogram
        macd_last = macd_data[last_seg.end_idx].histogram
        
        price_prev = prev_seg.end_price
        price_last = last_seg.end_price
        
        if last_seg.direction == 'up':
            if price_last > price_prev and macd_last < macd_prev:
                strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                return {
                    'detected': True,
                    'type': 'top_divergence',
                    'price': price_last,
                    'strength': strength,
                    'signal': 'sell'
                }
        else:
            if price_last < price_prev and macd_last > macd_prev:
                strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                return {
                    'detected': True,
                    'type': 'bottom_divergence',
                    'price': price_last,
                    'strength': strength,
                    'signal': 'buy'
                }
    except:
        pass
    
    return {'detected': False}


def detect_buy_sell_points(segments, divergence):
    """识别买卖点"""
    bsp_list = []
    
    if divergence.get('detected'):
        bsp = {
            'type': f"第一类{'买点' if divergence['signal'] == 'buy' else '卖点'}",
            'type_en': f"bsp{'1_buy' if divergence['signal'] == 'buy' else '1_sell'}",
            'price': divergence.get('price'),
            'confidence': min(divergence.get('strength', 0), 0.9),
            'description': f"趋势背驰点 - {divergence['type']}",
            'lesson': '第 12, 24 课'
        }
        bsp_list.append(bsp)
    
    return bsp_list


def multi_level_analysis():
    """多级别联动分析"""
    print("\n" + "="*70)
    print("🚀 UVIX 缠论多级别联动监控")
    print("🔧 Powered by chanlunInvester")
    print("="*70)
    print(f"\n📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"📈 数据源：Yahoo Finance (实时)")
    
    # 获取两个级别数据
    print(f"\n{'='*70}")
    print("📊 获取数据...")
    print(f"{'='*70}")
    
    series_5m = fetch_data('5m', 100)
    print(f"  ✓ 5 分钟：{len(series_5m.klines)} 根 K 线，当前价格：${series_5m.klines[-1].close:.2f}")
    
    series_30m = fetch_data('30m', 100)
    print(f"  ✓ 30 分钟：{len(series_30m.klines)} 根 K 线，当前价格：${series_30m.klines[-1].close:.2f}")
    
    # 分析
    print(f"\n{'='*70}")
    print("🔍 执行缠论分析...")
    print(f"{'='*70}")
    
    results_5m = analyze_chanlun(series_5m)
    print(f"  ✓ 5 分钟分析完成")
    
    results_30m = analyze_chanlun(series_30m)
    print(f"  ✓ 30 分钟分析完成")
    
    # 多级别联动分析
    print(f"\n{'='*70}")
    print("📐 多级别联动分析 (第 14 课 - 区间套)")
    print(f"{'='*70}")
    
    # 1. 30 分钟定方向
    print(f"\n【30 分钟级别 - 趋势方向】")
    if results_30m['segments']['latest']:
        seg_30m = results_30m['segments']['latest']
        direction_30m = seg_30m.direction
        print(f"  当前线段：{direction_30m.upper()}")
        print(f"  价格：${seg_30m.start_price:.2f} → ${seg_30m.end_price:.2f}")
    else:
        direction_30m = 'neutral'
        print(f"  无明确线段")
    
    if results_30m['divergence'].get('detected'):
        div = results_30m['divergence']
        emoji = "🟢" if div['signal'] == 'buy' else "🔴"
        print(f"  {emoji} 背驰 detected! 类型：{div['type']}, 强度：{div['strength']:.2f}")
    else:
        print(f"  ✓ 无背驰")
    
    # 2. 5 分钟找买卖点
    print(f"\n【5 分钟级别 - 买卖点定位】")
    if results_5m['segments']['latest']:
        seg_5m = results_5m['segments']['latest']
        direction_5m = seg_5m.direction
        print(f"  当前线段：{direction_5m.upper()}")
        print(f"  价格：${seg_5m.start_price:.2f} → ${seg_5m.end_price:.2f}")
    else:
        direction_5m = 'neutral'
    
    if results_5m['buy_sell_points']:
        for bsp in results_5m['buy_sell_points']:
            emoji = "🟢" if 'buy' in bsp['type_en'] else "🔴"
            print(f"  {emoji} {bsp['type']} @ ${bsp['price']:.2f}, 置信度：{bsp['confidence']:.0%}")
    else:
        print(f"  ⚪ 无明确买卖点")
    
    # 3. 区间套联动
    print(f"\n{'='*70}")
    print("🎯 区间套联动分析")
    print(f"{'='*70}")
    
    signal_strength = 0
    final_signal = "HOLD"
    reasoning = []
    
    # 30 分钟方向判断
    if direction_30m == 'up':
        reasoning.append("✓ 30 分钟上涨线段")
        signal_strength += 1
    elif direction_30m == 'down':
        reasoning.append("✗ 30 分钟下跌线段")
        signal_strength -= 1
    
    # 30 分钟背驰
    if results_30m['divergence'].get('detected'):
        div = results_30m['divergence']
        if div['signal'] == 'buy':
            reasoning.append(f"🟢 30 分钟底背驰 (强度:{div['strength']:.2f})")
            signal_strength += 2
        else:
            reasoning.append(f"🔴 30 分钟顶背驰 (强度:{div['strength']:.2f})")
            signal_strength -= 2
    
    # 5 分钟买卖点
    if results_5m['buy_sell_points']:
        bsp = results_5m['buy_sell_points'][0]
        if 'buy' in bsp['type_en']:
            reasoning.append(f"🟢 5 分钟第一类买点 (置信度:{bsp['confidence']:.0%})")
            signal_strength += 2
        else:
            reasoning.append(f"🔴 5 分钟第一类卖点 (置信度:{bsp['confidence']:.0%})")
            signal_strength -= 2
    
    # 5 分钟方向
    if direction_5m == 'up':
        reasoning.append("✓ 5 分钟上涨线段")
        signal_strength += 0.5
    elif direction_5m == 'down':
        reasoning.append("✗ 5 分钟下跌线段")
        signal_strength -= 0.5
    
    # 综合判断
    print(f"\n【综合信号】")
    
    if signal_strength >= 3:
        final_signal = "STRONG BUY"
        emoji = "🟢"
    elif signal_strength >= 1.5:
        final_signal = "BUY"
        emoji = "🟢"
    elif signal_strength <= -3:
        final_signal = "STRONG SELL"
        emoji = "🔴"
    elif signal_strength <= -1.5:
        final_signal = "SELL"
        emoji = "🔴"
    else:
        final_signal = "HOLD"
        emoji = "⚪"
    
    print(f"  {emoji} {final_signal} (强度：{signal_strength:+.1f})")
    
    for reason in reasoning:
        print(f"    • {reason}")
    
    # 交易建议
    print(f"\n{'='*70}")
    print("💡 交易建议")
    print(f"{'='*70}")
    
    if 'BUY' in final_signal:
        current_price = series_5m.klines[-1].close
        stop_loss = current_price * 0.97
        target1 = current_price * 1.03
        target2 = current_price * 1.05
        
        print(f"  🟢 买入策略")
        print(f"     入场：${current_price:.2f}")
        print(f"     止损：${stop_loss:.2f} (-3%)")
        print(f"     目标 1: ${target1:.2f} (+3%)")
        print(f"     目标 2: ${target2:.2f} (+5%)")
        print(f"     仓位：{'重仓' if 'STRONG' in final_signal else '标准'}")
        print(f"     依据：多级别共振 ({len(reasoning)}个利好)")
    
    elif 'SELL' in final_signal:
        current_price = series_5m.klines[-1].close
        stop_loss = current_price * 1.03
        target1 = current_price * 0.97
        target2 = current_price * 0.95
        
        print(f"  🔴 卖出策略")
        print(f"     入场：${current_price:.2f}")
        print(f"     止损：${stop_loss:.2f} (+3%)")
        print(f"     目标 1: ${target1:.2f} (-3%)")
        print(f"     目标 2: ${target2:.2f} (-5%)")
        print(f"     仓位：{'重仓' if 'STRONG' in final_signal else '标准'}")
        print(f"     依据：多级别共振 ({len(reasoning)}个利空)")
    
    else:
        print(f"  ⚪ 观望")
        print(f"     等待更明确的多级别共振信号")
        print(f"     当前信号强度：{signal_strength:+.1f}")
    
    # 风险提示
    print(f"\n{'='*70}")
    print("⚠️  风险提示")
    print(f"{'='*70}")
    print("  • 多级别联立分析提高胜率，但不保证盈利")
    print("  • UVIX 是高波动产品 (-2x VIX)")
    print("  • 严格执行止损，每笔交易风险不超过 2%")
    print("  • 本系统使用 chanlunInvester 项目核心功能")
    print(f"\n{'='*70}\n")
    
    return {
        'signal': final_signal,
        'strength': signal_strength,
        '30m': results_30m,
        '5m': results_5m,
        'reasoning': reasoning
    }


if __name__ == '__main__':
    try:
        result = multi_level_analysis()
        
        # 保存结果
        output_file = Path(__file__).parent.parent / 'logs' / 'multi_level_analysis.json'
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'signal': result['signal'],
                'strength': result['strength'],
                'reasoning': result['reasoning']
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📝 分析结果已保存：{output_file}")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
