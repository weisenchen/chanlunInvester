#!/usr/bin/env python3
"""
缠论多级别联动监控系统 - 通用版
支持任意美股/ETF/加密货币监控
使用 chanlunInvester 项目核心功能
GitHub: https://github.com/weisenchen/chanlunInvester

用法:
    python3 chanlun_monitor.py AAPL          # 监控 Apple
    python3 chanlun_monitor.py TSLA --level 30m  # 监控 Tesla 30 分钟级别
    python3 chanlun_monitor.py BTC-USD --levels 1d,30m,5m  # 多级别分析
    python3 chanlun_monitor.py --list        # 查看支持的市场
"""

import sys
import argparse
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
DEFAULT_CONFIG = {
    'timeframes': ['1d', '30m', '5m'],  # 日线 +30 分钟 +5 分钟
    'check_interval_minutes': 15,
    'min_confidence': 0.7,
    'weights': {
        '1d': {'direction': 3, 'divergence': 6},
        '30m': {'direction': 2, 'divergence': 4},
        '5m': {'direction': 1, 'divergence': 4}
    }
}


def fetch_data(symbol, timeframe='5m', count=100):
    """获取股票数据"""
    ticker = yf.Ticker(symbol)
    
    # 根据时间周期获取数据
    if timeframe == '5m':
        history = ticker.history(period='5d', interval='5m')
    elif timeframe == '15m':
        history = ticker.history(period='1mo', interval='15m')
    elif timeframe == '30m':
        history = ticker.history(period='1mo', interval='30m')
    elif timeframe == '1h':
        history = ticker.history(period='3mo', interval='1h')
    elif timeframe == '1d':
        history = ticker.history(period='1y', interval='1d')
    elif timeframe == '1wk':
        history = ticker.history(period='2y', interval='1wk')
    else:
        history = ticker.history(period='1mo', interval=timeframe)
    
    if len(history) == 0:
        return None
    
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
    
    return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)


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


def multi_level_analysis(symbol, timeframes=['1d', '30m', '5m']):
    """多级别联动分析"""
    print("\n" + "="*70)
    print("🚀 缠论多级别联动监控系统")
    print("🔧 Powered by chanlunInvester")
    print("="*70)
    print(f"\n📊 标的：{symbol}")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"📈 数据源：Yahoo Finance (实时)")
    print(f"🎯 级别：{' + '.join(timeframes)} (区间套)")
    
    # 获取多个级别数据
    print(f"\n{'='*70}")
    print("📊 获取数据...")
    print(f"{'='*70}")
    
    results = {}
    current_price = None
    
    for timeframe in timeframes:
        series = fetch_data(symbol, timeframe, 100)
        if series is None or len(series.klines) == 0:
            print(f"  ❌ {timeframe}: 数据获取失败")
            continue
        
        price = series.klines[-1].close
        print(f"  ✓ {timeframe}: {len(series.klines)} 根 K 线，当前价格：${price:.2f}")
        
        if current_price is None:
            current_price = price
        
        results[timeframe] = {
            'series': series,
            'price': price
        }
    
    if not results:
        print("\n❌ 无法获取数据，请检查股票代码是否正确")
        return None
    
    # 执行分析
    print(f"\n{'='*70}")
    print("🔍 执行缠论分析...")
    print(f"{'='*70}")
    
    analysis_results = {}
    for timeframe in results:
        print(f"\n  [{timeframe}] 分析中...")
        analysis_results[timeframe] = analyze_chanlun(results[timeframe]['series'])
        print(f"      ✓ 完成")
    
    # 多级别联动分析
    print(f"\n{'='*70}")
    print("🎯 多级别联动分析 (第 14 课)")
    print(f"{'='*70}")
    
    signal_strength = 0
    reasoning = []
    
    for timeframe in analysis_results:
        tf_results = analysis_results[timeframe]
        weight = DEFAULT_CONFIG['weights'].get(timeframe, {'direction': 1, 'divergence': 2})
        
        print(f"\n【{timeframe}级别】")
        
        # 线段方向
        if tf_results['segments']['latest']:
            direction = tf_results['segments']['latest'].direction
            if direction == 'up':
                signal_strength += weight['direction']
                reasoning.append(f"✓ {timeframe}上涨线段 (+{weight['direction']})")
                print(f"  📈 {timeframe}: 上涨线段")
            else:
                signal_strength -= weight['direction']
                reasoning.append(f"✗ {timeframe}下跌线段 (-{weight['direction']})")
                print(f"  📉 {timeframe}: 下跌线段")
        
        # 背驰
        if tf_results['divergence'].get('detected'):
            div = tf_results['divergence']
            if div['signal'] == 'buy':
                signal_strength += weight['divergence']
                reasoning.append(f"🟢 {timeframe}底背驰 (强度:{div['strength']:.2f}) (+{weight['divergence']})")
                print(f"  🟢 {timeframe}底背驰！强度:{div['strength']:.2f}")
            else:
                signal_strength -= weight['divergence']
                reasoning.append(f"🔴 {timeframe}顶背驰 (强度:{div['strength']:.2f}) (-{weight['divergence']})")
                print(f"  🔴 {timeframe}顶背驰！强度:{div['strength']:.2f}")
        
        # 买卖点
        if tf_results['buy_sell_points']:
            for bsp in tf_results['buy_sell_points']:
                if 'buy' in bsp['type_en']:
                    signal_strength += weight['divergence']
                    reasoning.append(f"🟢 {timeframe}第一类买点 (置信度:{bsp['confidence']:.0%}) (+{weight['divergence']})")
                    print(f"  🟢 {timeframe}第一类买点！置信度:{bsp['confidence']:.0%}")
                else:
                    signal_strength -= weight['divergence']
                    reasoning.append(f"🔴 {timeframe}第一类卖点 (置信度:{bsp['confidence']:.0%}) (-{weight['divergence']})")
                    print(f"  🔴 {timeframe}第一类卖点！置信度:{bsp['confidence']:.0%}")
    
    # 生成交易信号
    print(f"\n{'='*70}")
    print("💡 交易信号")
    print(f"{'='*70}")
    
    if signal_strength >= 6:
        final_signal = "STRONG BUY"
        emoji = "🟢"
    elif signal_strength >= 3:
        final_signal = "BUY"
        emoji = "🟢"
    elif signal_strength <= -6:
        final_signal = "STRONG SELL"
        emoji = "🔴"
    elif signal_strength <= -3:
        final_signal = "SELL"
        emoji = "🔴"
    else:
        final_signal = "HOLD"
        emoji = "⚪"
    
    print(f"\n  {emoji} {final_signal} (强度：{signal_strength:+.1f})")
    print(f"  依据：{len(reasoning)}个因素共振")
    
    for reason in reasoning:
        print(f"    • {reason}")
    
    # 交易建议
    print(f"\n{'='*70}")
    print("💡 交易建议")
    print(f"{'='*70}")
    
    if current_price:
        if 'BUY' in final_signal:
            stop_loss = current_price * 0.97
            target1 = current_price * 1.03
            target2 = current_price * 1.05
            
            position_size = "重仓" if 'STRONG' in final_signal else "标准"
            
            print(f"  🟢 买入策略")
            print(f"     标的：{symbol}")
            print(f"     入场：${current_price:.2f}")
            print(f"     止损：${stop_loss:.2f} (-3%)")
            print(f"     目标 1: ${target1:.2f} (+3%)")
            print(f"     目标 2: ${target2:.2f} (+5%)")
            print(f"     仓位：{position_size}")
            print(f"     依据：多级别共振 ({len(reasoning)}个利好)")
        
        elif 'SELL' in final_signal:
            stop_loss = current_price * 1.03
            target1 = current_price * 0.97
            target2 = current_price * 0.95
            
            position_size = "重仓" if 'STRONG' in final_signal else "标准"
            
            print(f"  🔴 卖出策略")
            print(f"     标的：{symbol}")
            print(f"     入场：${current_price:.2f}")
            print(f"     止损：${stop_loss:.2f} (+3%)")
            print(f"     目标 1: ${target1:.2f} (-3%)")
            print(f"     目标 2: ${target2:.2f} (-5%)")
            print(f"     仓位：{position_size}")
            print(f"     依据：多级别共振 ({len(reasoning)}个利空)")
        
        else:
            print(f"  ⚪ 观望")
            print(f"     标的：{symbol}")
            print(f"     等待更明确的多级别共振信号")
            print(f"     当前信号强度：{signal_strength:+.1f}")
    
    # 风险提示
    print(f"\n{'='*70}")
    print("⚠️  风险提示")
    print(f"{'='*70}")
    print("  • 多级别联动提高胜率，但不保证盈利")
    print("  • 严格执行止损，每笔交易风险不超过 2%")
    print("  • 本系统使用 chanlunInvester 项目核心功能")
    print(f"\n{'='*70}\n")
    
    # 返回结果
    return {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'signal': final_signal,
        'strength': signal_strength,
        'reasoning': reasoning,
        'current_price': current_price,
        'analysis': analysis_results
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='缠论多级别联动监控系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s AAPL                    # 监控 Apple
  %(prog)s TSLA --level 30m        # 监控 Tesla 30 分钟级别
  %(prog)s BTC-USD --levels 1d,30m,5m  # 多级别分析
  %(prog)s --list                  # 查看支持的热门股票
        """
    )
    
    parser.add_argument('symbol', nargs='?', help='股票代码 (如：AAPL, TSLA, BTC-USD)')
    parser.add_argument('--level', '-l', default='30m', 
                       help='单级别分析 (默认：30m)')
    parser.add_argument('--levels', '-L', default='1d,30m,5m',
                       help='多级别分析 (默认：1d,30m,5m)')
    parser.add_argument('--output', '-o', help='输出结果到 JSON 文件')
    parser.add_argument('--list', action='store_true', help='查看支持的热门股票')
    
    args = parser.parse_args()
    
    # 显示热门股票列表
    if args.list:
        print("\n支持的热门股票:")
        print("\n科技股:")
        print("  AAPL - Apple")
        print("  MSFT - Microsoft")
        print("  GOOGL - Alphabet")
        print("  AMZN - Amazon")
        print("  TSLA - Tesla")
        print("  NVDA - NVIDIA")
        print("  META - Meta")
        
        print("\nETF:")
        print("  SPY - S&P 500 ETF")
        print("  QQQ - Nasdaq 100 ETF")
        print("  UVIX - 2x Long VIX")
        print("  VIX - 波动率指数")
        
        print("\n加密货币:")
        print("  BTC-USD - Bitcoin")
        print("  ETH-USD - Ethereum")
        
        print("\n使用示例:")
        print("  python3 chanlun_monitor.py AAPL")
        print("  python3 chanlun_monitor.py BTC-USD --levels 1d,30m,5m")
        return 0
    
    # 检查股票代码
    if not args.symbol:
        parser.print_help()
        print("\n❌ 错误：请提供股票代码")
        print("   使用 --list 查看支持的股票")
        return 1
    
    # 确定分析级别
    if args.level:
        timeframes = [args.level]
    else:
        timeframes = args.levels.split(',')
    
    # 执行分析
    try:
        results = multi_level_analysis(args.symbol, timeframes)
        
        if results is None:
            return 1
        
        # 保存结果
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(exist_ok=True)
            
            # 简化结果用于保存
            simplified = {
                'timestamp': results['timestamp'],
                'symbol': results['symbol'],
                'signal': results['signal'],
                'strength': results['strength'],
                'reasoning': results['reasoning'],
                'current_price': results['current_price']
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(simplified, f, indent=2, ensure_ascii=False)
            
            print(f"📝 分析结果已保存：{output_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
