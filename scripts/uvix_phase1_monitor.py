#!/usr/bin/env python3
"""
UVIX 缠论三级联动监控系统 - Phase 1
5 分钟 +30 分钟 + 日线 区间套精确定位
使用 chanlunInvester 项目核心功能
GitHub: https://github.com/weisenchen/chanlunInvester

缠论第 14 课 - 区间套定理实战应用
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


# 配置
CONFIG = {
    'symbol': 'UVIX',
    'levels': ['1d', '30m', '5m'],  # 日线 +30 分钟 +5 分钟
    'check_interval_minutes': 15,
    'min_confidence': 0.7,
    'alert_channels': ['telegram', 'console', 'file']
}


def fetch_data(timeframe='5m', count=100):
    """获取 UVIX 数据"""
    ticker = yf.Ticker('UVIX')
    
    # 根据时间周期获取数据
    if timeframe == '5m':
        history = ticker.history(period='5d', interval='5m')
    elif timeframe == '30m':
        history = ticker.history(period='1mo', interval='30m')
    elif timeframe == '1d':
        history = ticker.history(period='1y', interval='1d')
    else:
        history = ticker.history(period='1mo', interval=timeframe)
    
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
        'bottom': len([f for f in fractals if not f.is_top]),
        'latest_top': fractals[-1] if fractals and fractals[-1].is_top else None,
        'latest_bottom': fractals[-1] if fractals and not fractals[-1].is_top else None
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
    except Exception as e:
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


def interval_set_analysis(daily_results, thirtym_results, fivem_results):
    """
    区间套定位分析 (第 14 课)
    
    从大级别到小级别逐级定位:
    1. 日线确定大方向
    2. 30 分钟确定中段走势
    3. 5 分钟精确定位买卖点
    """
    signal_strength = 0
    reasoning = []
    precision_level = 'low'
    
    # 1. 日线级别分析 (权重×3)
    print(f"\n【日线级别 - 大方向】")
    if daily_results['segments']['latest']:
        daily_direction = daily_results['segments']['latest'].direction
        if daily_direction == 'up':
            signal_strength += 3
            reasoning.append("✓ 日线上涨线段 (+3)")
            print(f"  📈 日线：上涨线段")
        else:
            signal_strength -= 3
            reasoning.append("✗ 日线下跌线段 (-3)")
            print(f"  📉 日线：下跌线段")
    
    if daily_results['divergence'].get('detected'):
        div = daily_results['divergence']
        if div['signal'] == 'buy':
            signal_strength += 6  # 日线背驰权重最高
            reasoning.append(f"🟢 日线底背驰 (强度:{div['strength']:.2f}) (+6)")
            print(f"  🟢 日线底背驰！强度:{div['strength']:.2f}")
        else:
            signal_strength -= 6
            reasoning.append(f"🔴 日线顶背驰 (强度:{div['strength']:.2f}) (-6)")
            print(f"  🔴 日线顶背驰！强度:{div['strength']:.2f}")
    
    # 2. 30 分钟级别分析 (权重×2)
    print(f"\n【30 分钟级别 - 中段走势】")
    if thirtym_results['segments']['latest']:
        thirtym_direction = thirtym_results['segments']['latest'].direction
        if thirtym_direction == 'up':
            signal_strength += 2
            reasoning.append("✓ 30 分钟上涨线段 (+2)")
            print(f"  📈 30 分钟：上涨线段")
        else:
            signal_strength -= 2
            reasoning.append("✗ 30 分钟下跌线段 (-2)")
            print(f"  📉 30 分钟：下跌线段")
    
    if thirtym_results['divergence'].get('detected'):
        div = thirtym_results['divergence']
        if div['signal'] == 'buy':
            signal_strength += 4
            reasoning.append(f"🟢 30 分钟底背驰 (强度:{div['strength']:.2f}) (+4)")
            print(f"  🟢 30 分钟底背驰！强度:{div['strength']:.2f}")
        else:
            signal_strength -= 4
            reasoning.append(f"🔴 30 分钟顶背驰 (强度:{div['strength']:.2f}) (-4)")
            print(f"  🔴 30 分钟顶背驰！强度:{div['strength']:.2f}")
    
    # 3. 5 分钟级别分析 (权重×1)
    print(f"\n【5 分钟级别 - 精确定位】")
    if fivem_results['segments']['latest']:
        fivem_direction = fivem_results['segments']['latest'].direction
        if fivem_direction == 'up':
            signal_strength += 1
            reasoning.append("✓ 5 分钟上涨线段 (+1)")
            print(f"  📈 5 分钟：上涨线段")
        else:
            signal_strength -= 1
            reasoning.append("✗ 5 分钟下跌线段 (-1)")
            print(f"  📉 5 分钟：下跌线段")
    
    if fivem_results['buy_sell_points']:
        for bsp in fivem_results['buy_sell_points']:
            if 'buy' in bsp['type_en']:
                signal_strength += 4
                reasoning.append(f"🟢 5 分钟第一类买点 (置信度:{bsp['confidence']:.0%}) (+4)")
                print(f"  🟢 5 分钟第一类买点！置信度:{bsp['confidence']:.0%}")
            else:
                signal_strength -= 4
                reasoning.append(f"🔴 5 分钟第一类卖点 (置信度:{bsp['confidence']:.0%}) (-4)")
                print(f"  🔴 5 分钟第一类卖点！置信度:{bsp['confidence']:.0%}")
    
    # 区间套精度评估
    if len(reasoning) >= 5:
        precision_level = 'high'
    elif len(reasoning) >= 3:
        precision_level = 'medium'
    else:
        precision_level = 'low'
    
    return {
        'signal_strength': signal_strength,
        'reasoning': reasoning,
        'precision_level': precision_level
    }


def generate_trading_signal(signal_strength, precision_level):
    """生成最终交易信号"""
    if signal_strength >= 6:
        return "STRONG BUY", "🟢"
    elif signal_strength >= 3:
        return "BUY", "🟢"
    elif signal_strength <= -6:
        return "STRONG SELL", "🔴"
    elif signal_strength <= -3:
        return "SELL", "🔴"
    else:
        return "HOLD", "⚪"


def multi_level_analysis():
    """三级联动分析主函数"""
    print("\n" + "="*70)
    print("🚀 UVIX 缠论三级联动监控 - Phase 1")
    print("🔧 Powered by chanlunInvester")
    print("="*70)
    print(f"\n📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"📈 数据源：Yahoo Finance (实时)")
    print(f"🎯 级别：日线 +30 分钟 +5 分钟 (区间套)")
    
    # 获取三个级别数据
    print(f"\n{'='*70}")
    print("📊 获取数据...")
    print(f"{'='*70}")
    
    series_daily = fetch_data('1d', 200)
    print(f"  ✓ 日线：{len(series_daily.klines)} 根 K 线，当前价格：${series_daily.klines[-1].close:.2f}")
    
    series_30m = fetch_data('30m', 100)
    print(f"  ✓ 30 分钟：{len(series_30m.klines)} 根 K 线，当前价格：${series_30m.klines[-1].close:.2f}")
    
    series_5m = fetch_data('5m', 100)
    print(f"  ✓ 5 分钟：{len(series_5m.klines)} 根 K 线，当前价格：${series_5m.klines[-1].close:.2f}")
    
    current_price = series_5m.klines[-1].close
    
    # 执行分析
    print(f"\n{'='*70}")
    print("🔍 执行缠论分析...")
    print(f"{'='*70}")
    
    print(f"\n  [1/3] 日线级别分析...")
    results_daily = analyze_chanlun(series_daily)
    print(f"      ✓ 完成")
    
    print(f"  [2/3] 30 分钟级别分析...")
    results_30m = analyze_chanlun(series_30m)
    print(f"      ✓ 完成")
    
    print(f"  [3/3] 5 分钟级别分析...")
    results_5m = analyze_chanlun(series_5m)
    print(f"      ✓ 完成")
    
    # 区间套分析
    print(f"\n{'='*70}")
    print("🎯 区间套联动分析 (第 14 课)")
    print(f"{'='*70}")
    
    interval_result = interval_set_analysis(results_daily, results_30m, results_5m)
    
    # 生成交易信号
    print(f"\n{'='*70}")
    print("💡 交易信号")
    print(f"{'='*70}")
    
    signal_name, emoji = generate_trading_signal(
        interval_result['signal_strength'],
        interval_result['precision_level']
    )
    
    print(f"\n  {emoji} {signal_name} (强度：{interval_result['signal_strength']:+.1f})")
    print(f"  精度等级：{interval_result['precision_level'].upper()}")
    print(f"  依据：{len(interval_result['reasoning'])}个因素共振")
    
    for reason in interval_result['reasoning']:
        print(f"    • {reason}")
    
    # 交易建议
    print(f"\n{'='*70}")
    print("💡 交易建议")
    print(f"{'='*70}")
    
    if 'BUY' in signal_name:
        stop_loss = current_price * 0.97
        target1 = current_price * 1.03
        target2 = current_price * 1.05
        
        position_size = "重仓" if 'STRONG' in signal_name else "标准"
        
        print(f"  🟢 买入策略")
        print(f"     入场：${current_price:.2f}")
        print(f"     止损：${stop_loss:.2f} (-3%)")
        print(f"     目标 1: ${target1:.2f} (+3%)")
        print(f"     目标 2: ${target2:.2f} (+5%)")
        print(f"     仓位：{position_size}")
        print(f"     精度：{interval_result['precision_level'].upper()}")
        print(f"     依据：多级别共振 ({len(interval_result['reasoning'])}个利好)")
    
    elif 'SELL' in signal_name:
        stop_loss = current_price * 1.03
        target1 = current_price * 0.97
        target2 = current_price * 0.95
        
        position_size = "重仓" if 'STRONG' in signal_name else "标准"
        
        print(f"  🔴 卖出策略")
        print(f"     入场：${current_price:.2f}")
        print(f"     止损：${stop_loss:.2f} (+3%)")
        print(f"     目标 1: ${target1:.2f} (-3%)")
        print(f"     目标 2: ${target2:.2f} (-5%)")
        print(f"     仓位：{position_size}")
        print(f"     精度：{interval_result['precision_level'].upper()}")
        print(f"     依据：多级别共振 ({len(interval_result['reasoning'])}个利空)")
    
    else:
        print(f"  ⚪ 观望")
        print(f"     等待更明确的多级别共振信号")
        print(f"     当前信号强度：{interval_result['signal_strength']:+.1f}")
        print(f"     精度等级：{interval_result['precision_level'].upper()}")
    
    # 风险提示
    print(f"\n{'='*70}")
    print("⚠️  风险提示")
    print(f"{'='*70}")
    print("  • 三级联动提高胜率，但不保证盈利")
    print("  • UVIX 是高波动产品 (-2x VIX)")
    print("  • 严格执行止损，每笔交易风险不超过 2%")
    print("  • 本系统使用 chanlunInvester 项目核心功能")
    print(f"\n{'='*70}\n")
    
    # 返回结果
    return {
        'timestamp': datetime.now().isoformat(),
        'signal': signal_name,
        'strength': interval_result['signal_strength'],
        'precision': interval_result['precision_level'],
        'reasoning': interval_result['reasoning'],
        'current_price': current_price,
        'daily': results_daily,
        '30m': results_30m,
        '5m': results_5m
    }


def save_results(results):
    """保存分析结果"""
    output_file = Path(__file__).parent.parent / 'logs' / 'phase1_analysis.json'
    output_file.parent.mkdir(exist_ok=True)
    
    # 简化结果用于保存
    simplified = {
        'timestamp': results['timestamp'],
        'signal': results['signal'],
        'strength': results['strength'],
        'precision': results['precision'],
        'reasoning': results['reasoning'],
        'current_price': results['current_price']
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)
    
    print(f"📝 分析结果已保存：{output_file}")


if __name__ == '__main__':
    try:
        results = multi_level_analysis()
        save_results(results)
        print("✅ Phase 1 分析完成")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
