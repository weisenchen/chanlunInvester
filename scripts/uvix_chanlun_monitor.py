#!/usr/bin/env python3
"""
UVIX 缠论 5 分钟级别实时监控预警
使用 chanlunInvester 项目核心功能
GitHub: https://github.com/weisenchen/chanlunInvester
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

import yfinance as yf
from datetime import datetime
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator


def fetch_uvix_data(timeframe='5m', count=100):
    """从 Yahoo Finance 获取 UVIX 实时数据"""
    print(f"\n📡 正在获取 UVIX {timeframe} 数据...")
    
    uvix = yf.Ticker('UVIX')
    
    if timeframe == '5m':
        history = uvix.history(period='5d', interval='5m')
    elif timeframe == '30m':
        history = uvix.history(period='1mo', interval='30m')
    else:
        history = uvix.history(period='3mo', interval='1d')
    
    # 转换为 Kline 对象
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
    
    print(f"    ✓ 获取 {len(klines)} 根 K 线")
    print(f"    时间范围：{klines[0].timestamp.strftime('%Y-%m-%d')} → {klines[-1].timestamp.strftime('%Y-%m-%d')}")
    print(f"    当前价格：${klines[-1].close:.2f}")
    
    return KlineSeries(klines=klines, symbol='UVIX', timeframe=timeframe)


def analyze_chanlun(series):
    """使用 chanlunInvester 核心功能执行缠论分析"""
    print(f"\n🔍 正在执行缠论分析...")
    
    results = {}
    
    # 1. 分型分析 (第 62 课)
    print(f"    [1/5] 分型检测...")
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    results['fractals'] = {
        'total': len(fractals),
        'top': len(top_fractals),
        'bottom': len(bottom_fractals),
        'latest_top': top_fractals[-1] if top_fractals else None,
        'latest_bottom': bottom_fractals[-1] if bottom_fractals else None
    }
    print(f"        ✓ 顶分型：{len(top_fractals)}个，底分型：{len(bottom_fractals)}个")
    
    # 2. 笔分析 (第 65 课 - 新笔定义)
    print(f"    [2/5] 笔识别...")
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,  # 新笔定义：3 K 线
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    up_pens = [p for p in pens if p.is_up]
    down_pens = [p for p in pens if p.is_down]
    
    results['pens'] = {
        'total': len(pens),
        'up': len(up_pens),
        'down': len(down_pens),
        'latest': pens[-1] if pens else None
    }
    print(f"        ✓ 向上笔：{len(up_pens)}个，向下笔：{len(down_pens)}个")
    
    # 3. 线段分析 (第 67 课 - 特征序列)
    print(f"    [3/5] 线段划分...")
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    up_segs = [s for s in segments if s.is_up]
    down_segs = [s for s in segments if s.is_down]
    
    results['segments'] = {
        'total': len(segments),
        'up': len(up_segs),
        'down': len(down_segs),
        'latest': segments[-1] if segments else None
    }
    print(f"        ✓ 向上线段：{len(up_segs)}个，向下线段：{len(down_segs)}个")
    
    # 4. MACD 背驰分析 (第 24 课)
    print(f"    [4/5] 背驰检测...")
    prices = [k.close for k in series.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_data = macd.calculate(prices)
    
    divergence = detect_divergence(segments, macd_data)
    results['divergence'] = divergence
    
    if divergence.get('detected'):
        print(f"        🚨 检测到背驰！类型：{divergence['type']}")
    else:
        print(f"        ✓ 无明显背驰")
    
    # 5. 买卖点识别 (第 12, 20 课)
    print(f"    [5/5] 买卖点识别...")
    bsp_list = detect_buy_sell_points(segments, divergence)
    results['buy_sell_points'] = bsp_list
    
    if bsp_list:
        for bsp in bsp_list:
            emoji = "🟢" if 'buy' in bsp['type_en'] else "🔴"
            print(f"        {emoji} {bsp['type']} @ ${bsp['price']:.2f}")
    else:
        print(f"        ⚪ 无明确买卖点")
    
    return results


def detect_divergence(segments, macd_data):
    """检测背驰 (第 24 课)"""
    if len(segments) < 2 or not macd_data:
        return {'detected': False}
    
    # 检查最后两个同向线段
    last_seg = segments[-1]
    prev_seg = None
    
    for seg in reversed(segments[:-1]):
        if seg.direction == last_seg.direction:
            prev_seg = seg
            break
    
    if not prev_seg:
        return {'detected': False}
    
    # 获取 MACD 值
    try:
        macd_prev = macd_data[prev_seg.end_idx].histogram
        macd_last = macd_data[last_seg.end_idx].histogram
        
        price_prev = prev_seg.end_price
        price_last = last_seg.end_price
        
        if last_seg.direction == 'up':
            # 上涨背驰：价格创新高，MACD 未创新高
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
            # 下跌背驰：价格创新低，MACD 未创新低
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
        print(f"        ⚠️ MACD 计算异常：{e}")
    
    return {'detected': False}


def detect_buy_sell_points(segments, divergence):
    """识别三类买卖点 (第 12, 20 课)"""
    bsp_list = []
    
    # 第一类买卖点：背驰点
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


def generate_alert(series, results):
    """生成缠论预警报告"""
    current_price = series.klines[-1].close
    
    print("\n" + "="*70)
    print("🚨 UVIX 缠论 5 分钟级别预警系统")
    print("="*70)
    print(f"\n📊 当前价格：${current_price:.2f}")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"📈 数据源：Yahoo Finance (实时)")
    print(f"🔧 核心：chanlunInvester v1.0")
    print(f"🔗 GitHub: https://github.com/weisenchen/chanlunInvester")
    
    # 1. 分型分析
    print(f"\n{'='*70}")
    print("📐 分型分析 (第 62 课)")
    print(f"{'='*70}")
    print(f"  顶分型：{results['fractals']['top']} 个")
    print(f"  底分型：{results['fractals']['bottom']} 个")
    
    if results['fractals']['latest_top']:
        latest_top = results['fractals']['latest_top']
        print(f"  最新顶分型：K 线#{latest_top.kline_index} @ ${latest_top.price:.2f}")
    
    if results['fractals']['latest_bottom']:
        latest_bottom = results['fractals']['latest_bottom']
        print(f"  最新底分型：K 线#{latest_bottom.kline_index} @ ${latest_bottom.price:.2f}")
    
    # 2. 笔分析
    print(f"\n{'='*70}")
    print("✏️  笔分析 (第 65 课)")
    print(f"{'='*70}")
    print(f"  向上笔：{results['pens']['up']} 个")
    print(f"  向下笔：{results['pens']['down']} 个")
    
    if results['pens']['latest']:
        latest_pen = results['pens']['latest']
        direction = "↑" if latest_pen.is_up else "↓"
        print(f"  最新笔：{direction} ${latest_pen.start_price:.2f} → ${latest_pen.end_price:.2f}")
    
    # 3. 线段分析
    print(f"\n{'='*70}")
    print("📏 线段分析 (第 67 课)")
    print(f"{'='*70}")
    print(f"  向上线段：{results['segments']['up']} 个")
    print(f"  向下线段：{results['segments']['down']} 个")
    
    if results['segments']['latest']:
        latest_seg = results['segments']['latest']
        direction = "↑" if latest_seg.is_up else "↓"
        print(f"  最新线段：{direction} ${latest_seg.start_price:.2f} → ${latest_seg.end_price:.2f}")
    
    # 4. 背驰分析
    print(f"\n{'='*70}")
    print("📊 背驰分析 (第 24 课)")
    print(f"{'='*70}")
    
    if results['divergence'].get('detected'):
        div = results['divergence']
        emoji = "🟢" if div['signal'] == 'buy' else "🔴"
        print(f"  {emoji} 检测到背驰！")
        print(f"     类型：{div['type']}")
        print(f"     信号：{'🟢 买入' if div['signal'] == 'buy' else '🔴 卖出'}")
        print(f"     强度：{div['strength']:.2f}")
        print(f"     价格：${div['price']:.2f}")
    else:
        print(f"  ✓ 无明显背驰")
    
    # 5. 买卖点
    print(f"\n{'='*70}")
    print("🎯 买卖点信号 (第 12, 20 课)")
    print(f"{'='*70}")
    
    if results['buy_sell_points']:
        for bsp in results['buy_sell_points']:
            emoji = "🟢" if 'buy' in bsp['type_en'] else "🔴"
            print(f"  {emoji} {bsp['type']}")
            print(f"     价格：${bsp['price']:.2f}")
            print(f"     置信度：{bsp['confidence']:.0%}")
            print(f"     说明：{bsp['description']}")
            print(f"     依据：{bsp['lesson']}")
    else:
        print(f"  ⚪ 无明确买卖点")
        print(f"     等待背驰信号或线段转折")
    
    # 6. 操作建议
    print(f"\n{'='*70}")
    print("💡 操作建议")
    print(f"{'='*70}")
    
    if results['buy_sell_points']:
        bsp = results['buy_sell_points'][0]
        if 'buy' in bsp['type_en']:
            print(f"  🟢 第一类买点 - 买入信号")
            print(f"     入场：${bsp['price']:.2f}")
            print(f"     止损：${bsp['price'] * 0.97:.2f} (-3%)")
            print(f"     目标 1: ${bsp['price'] * 1.03:.2f} (+3%)")
            print(f"     目标 2: ${bsp['price'] * 1.05:.2f} (+5%)")
            print(f"     风险收益比：1:1.7")
        else:
            print(f"  🔴 第一类卖点 - 卖出信号")
            print(f"     入场：${bsp['price']:.2f}")
            print(f"     止损：${bsp['price'] * 1.03:.2f} (+3%)")
            print(f"     目标 1: ${bsp['price'] * 0.97:.2f} (-3%)")
            print(f"     目标 2: ${bsp['price'] * 0.95:.2f} (-5%)")
            print(f"     风险收益比：1:1.7")
    else:
        # 基于线段方向给出建议
        if results['segments']['latest']:
            direction = results['segments']['latest'].direction
            if direction == 'up':
                print(f"  🟢 持有多单")
                print(f"     当前：上涨线段中")
                print(f"     支撑：${results['segments']['latest'].start_price:.2f}")
                print(f"     策略：持有直到背驰或线段转折")
            else:
                print(f"  🔴 持有空单")
                print(f"     当前：下跌线段中")
                print(f"     阻力：${results['segments']['latest'].start_price:.2f}")
                print(f"     策略：持有直到背驰或线段转折")
        else:
            print(f"  ⚪ 观望")
            print(f"     等待明确买卖点信号")
            print(f"     关注：分型和笔的转折")
    
    print(f"\n{'='*70}")
    print("⚠️  风险提示")
    print(f"{'='*70}")
    print("  • 缠论分析仅供参考，不构成投资建议")
    print("  • UVIX 是高波动产品 (-2x VIX)，请控制仓位")
    print("  • 严格执行止损，每笔交易风险不超过 2%")
    print("  • 建议结合更大级别 (30m/ 日线) 确认信号")
    print("  • 本系统使用 chanlunInvester 项目核心功能")
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    try:
        print("\n" + "="*70)
        print("🚀 UVIX 缠论实时监控系统")
        print("🔧 Powered by chanlunInvester")
        print("="*70)
        
        # 获取数据
        series = fetch_uvix_data(timeframe='5m', count=100)
        
        # 执行缠论分析
        results = analyze_chanlun(series)
        
        # 生成预警
        generate_alert(series, results)
        
        print("✅ 分析完成")
        print("\n💡 提示:")
        print("  • 运行 'python3 scripts/uvix_chanlun_monitor.py' 刷新数据")
        print("  • 设置 Cron 定时任务实现自动监控")
        print("  • 结合 30m/日线级别确认信号")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        print("\n请检查网络连接后重试")
