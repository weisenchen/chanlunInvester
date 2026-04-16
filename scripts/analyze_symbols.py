#!/usr/bin/env python3
"""
个股深度分析脚本
Deep Analysis for Specific Symbols

使用综合可信度系统深度分析指定股票
"""

import sys
from pathlib import Path
from datetime import datetime
import yfinance as yf
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator
from volume_confirmation import VolumeConfirmation
from macd_advanced_analysis import MACDAdvancedAnalyzer
from confidence_calculator import ComprehensiveConfidenceCalculator


def convert_to_klines(history, symbol, timeframe):
    """转换 Yahoo Finance 数据为 Kline 格式"""
    klines = []
    for idx, row in history.iterrows():
        kline = Kline(
            timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
            open=float(row['Open']),
            high=float(row['High']),
            low=float(row['Low']),
            close=float(row['Close']),
            volume=int(row.get('Volume', 0))
        )
        klines.append(kline)
    return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)


def analyze_level(series, level):
    """分析单个级别"""
    # 分型
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    # 笔
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    
    # 线段
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    
    # MACD
    prices = [k.close for k in series.klines]
    volumes = [k.volume for k in series.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_data = macd.calculate(prices)
    
    # 检测买卖点
    signals = []
    
    if len(bottom_fractals) >= 2:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        
        if last_low.price < prev_low.price:
            last_idx = last_low.kline_index
            prev_idx = prev_low.kline_index
            
            if last_idx < len(macd_data) and prev_idx < len(macd_data):
                last_macd = macd_data[last_idx].histogram
                prev_macd = macd_data[prev_idx].histogram
                
                if last_macd > prev_macd:
                    signals.append({
                        'type': 'buy1',
                        'name': f'{level}级别第一类买点 (背驰)',
                        'price': prices[-1],
                        'confidence': 'high' if last_macd > prev_macd * 1.5 else 'medium',
                        'last_low_idx': last_idx,
                        'prev_low_idx': prev_idx,
                        'last_low_price': last_low.price,
                        'prev_low_price': prev_low.price,
                        'macd_last': last_macd,
                        'macd_prev': prev_macd,
                        'prices': prices,
                        'volumes': volumes,
                        'macd_data': macd_data
                    })
    
    if len(bottom_fractals) >= 2 and len(pens) >= 2:
        last_pen = pens[-1]
        if last_pen.is_up:
            last_low = bottom_fractals[-1]
            prev_low = bottom_fractals[-2]
            
            if last_low.price > prev_low.price:
                current_price = series.klines[-1].close
                distance = (current_price - last_low.price) / last_low.price
                
                if 0 < distance <= 0.015:
                    signals.append({
                        'type': 'buy2',
                        'name': f'{level}级别第二类买点',
                        'price': current_price,
                        'confidence': 'medium',
                        'last_low_idx': last_low.kline_index,
                        'prev_low_idx': prev_low.kline_index,
                        'last_low_price': last_low.price,
                        'prev_low_price': prev_low.price,
                        'prices': prices,
                        'volumes': volumes,
                        'macd_data': macd_data
                    })
    
    return {
        'level': level,
        'fractals': len(fractals),
        'top_fractals': len(top_fractals),
        'bottom_fractals': len(bottom_fractals),
        'pens': len(pens),
        'segments': len(segments),
        'macd_dif': macd_data[-1].dif,
        'macd_dea': macd_data[-1].dea,
        'macd_histogram': macd_data[-1].histogram,
        'signals': signals,
        'prices': prices,
        'volumes': volumes,
        'macd_data': macd_data
    }


def deep_analyze_symbol(symbol: str, name: str):
    """深度分析单个标的"""
    
    print("=" * 70)
    print(f"📊 {symbol} ({name}) - 深度分析")
    print("=" * 70)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取数据
    print(f"\n📈 获取数据...")
    
    try:
        data_1d = yf.Ticker(symbol).history(period='60d', interval='1d')
        data_30m = yf.Ticker(symbol).history(period='10d', interval='30m')
        data_5m = yf.Ticker(symbol).history(period='5d', interval='5m')
        
        print(f"   日线：{len(data_1d)} 根 K 线")
        print(f"   30 分钟：{len(data_30m)} 根 K 线")
        print(f"   5 分钟：{len(data_5m)} 根 K 线")
        print(f"   最新价格：${data_30m['Close'].iloc[-1]:.2f}")
        
        # 转换数据
        series_1d = convert_to_klines(data_1d, symbol, '1d')
        series_30m = convert_to_klines(data_30m, symbol, '30m')
        series_5m = convert_to_klines(data_5m, symbol, '5m')
        
    except Exception as e:
        print(f"   ❌ 数据获取失败：{e}")
        return None
    
    # 分析各级别
    print(f"\n🔍 缠论结构分析...")
    
    result_1d = analyze_level(series_1d, '1d')
    result_30m = analyze_level(series_30m, '30m')
    result_5m = analyze_level(series_5m, '5m')
    
    print(f"\n【日线 (1d)】")
    print(f"   分型：{result_1d['fractals']} (顶：{result_1d['top_fractals']}, 底：{result_1d['bottom_fractals']})")
    print(f"   笔：{result_1d['pens']}")
    print(f"   线段：{result_1d['segments']}")
    print(f"   MACD: DIF={result_1d['macd_dif']:.3f}, DEA={result_1d['macd_dea']:.3f}")
    print(f"   买卖点：{len(result_1d['signals'])}")
    
    print(f"\n【30 分钟 (30m)】")
    print(f"   分型：{result_30m['fractals']} (顶：{result_30m['top_fractals']}, 底：{result_30m['bottom_fractals']})")
    print(f"   笔：{result_30m['pens']}")
    print(f"   线段：{result_30m['segments']}")
    print(f"   MACD: DIF={result_30m['macd_dif']:.3f}, DEA={result_30m['macd_dea']:.3f}")
    print(f"   买卖点：{len(result_30m['signals'])}")
    
    print(f"\n【5 分钟 (5m)】")
    print(f"   分型：{result_5m['fractals']} (顶：{result_5m['top_fractals']}, 底：{result_5m['bottom_fractals']})")
    print(f"   笔：{result_5m['pens']}")
    print(f"   线段：{result_5m['segments']}")
    print(f"   MACD: DIF={result_5m['macd_dif']:.3f}, DEA={result_5m['macd_dea']:.3f}")
    print(f"   买卖点：{len(result_5m['signals'])}")
    
    # 检测到的所有信号
    all_signals = []
    for result in [result_1d, result_30m, result_5m]:
        for signal in result['signals']:
            signal['level'] = result['level']
            all_signals.append(signal)
    
    if not all_signals:
        print(f"\n⚪ 未检测到买卖点信号")
        return {'symbol': symbol, 'signals': [], 'analysis': None}
    
    print(f"\n🎯 检测到 {len(all_signals)} 个信号:")
    for sig in all_signals:
        print(f"   • {sig['level']} {sig['type']} @ ${sig['price']:.2f}")
    
    # 对每个信号进行综合可信度分析
    print(f"\n{'='*70}")
    print("【综合可信度分析】")
    print(f"{'='*70}")
    
    calculator = ComprehensiveConfidenceCalculator()
    results = []
    
    for signal in all_signals:
        print(f"\n--- {signal['level']} {signal['type']} @ ${signal['price']:.2f} ---\n")
        
        # 确定行业因子
        if symbol in ['SMR', 'EOSE']:
            industry_score = 0.65  # 新能源/储能
        else:
            industry_score = 0.50
        
        result = calculator.calculate(
            symbol=symbol,
            signal_type=signal['type'],
            level=signal['level'],
            price=signal['price'],
            prices=signal['prices'],
            volumes=signal['volumes'],
            macd_data=signal['macd_data'],
            chanlun_base_confidence=0.65 if signal['confidence'] == 'high' else 0.55,
            divergence_start_idx=signal.get('prev_low_idx'),
            divergence_end_idx=signal.get('last_low_idx'),
            macd_1d=result_1d['macd_data'] if signal['level'] != '1d' else None,
            macd_30m=result_30m['macd_data'] if signal['level'] == '1d' else None,
            macd_5m=result_5m['macd_data'] if signal['level'] in ['1d', '30m'] else None,
            multi_level_confirmed=len(all_signals) > 1,
            multi_level_count=len(set(s['level'] for s in all_signals)),
            external_factors={
                'industry': industry_score,
                'fundamental': 0.55,
                'sentiment': 0.60,
            }
        )
        
        print(calculator.format_report(result))
        results.append(result)
    
    # 总结
    print(f"\n{'='*70}")
    print("【分析总结】")
    print(f"{'='*70}")
    
    best_result = max(results, key=lambda r: r.final_confidence)
    
    print(f"\n最佳信号：{best_result.signal_type} @ ${best_result.price:.2f}")
    print(f"综合置信度：{best_result.final_confidence*100:.0f}%")
    print(f"可靠性等级：{best_result.reliability_level.value}")
    print(f"操作建议：{best_result.operation_suggestion.value}")
    
    # 关键位置
    print(f"\n【关键位置】")
    current_price = data_30m['Close'].iloc[-1]
    print(f"当前价格：${current_price:.2f}")
    
    if best_result.signal_type.startswith('buy'):
        low_prices = [s.get('last_low_price', current_price) for s in all_signals if s['type'].startswith('buy')]
        if low_prices:
            stop_loss = min(low_prices) * 0.92
            print(f"背驰低点：${min(low_prices):.2f}")
            print(f"止损位：${stop_loss:.2f} (-8%)")
            print(f"第一目标：${current_price * 1.10:.2f} (+10%)")
            print(f"第二目标：${current_price * 1.20:.2f} (+20%)")
    
    return {
        'symbol': symbol,
        'signals': all_signals,
        'results': results,
        'best_result': best_result
    }


def compare_symbols(symbols_data):
    """比较多个标的"""
    
    print(f"\n{'='*70}")
    print("【标的对比】")
    print(f"{'='*70}")
    
    print(f"\n{'标的':<8} {'信号数':<6} {'最佳信号':<10} {'置信度':<8} {'可靠性':<12} {'建议':<15}")
    print(f"{'-'*70}")
    
    for data in symbols_data:
        if data and data['signals']:
            best = data['best_result']
            print(f"{data['symbol']:<8} {len(data['signals']):<6} {best.signal_type:<10} "
                  f"{best.final_confidence*100:.0f}%{'':<4} {best.reliability_level.value:<12} "
                  f"{best.operation_suggestion.value:<15}")
        else:
            print(f"{data['symbol']:<8} {'0':<6} {'-':<10} {'-':<8} {'-':<12} {'观望':<15}")


def main():
    """主函数"""
    
    print("=" * 70)
    print("缠论综合可信度系统 - 个股深度分析")
    print("=" * 70)
    
    # 分析标的
    symbols = [
        {'symbol': 'RKLB', 'name': 'Rocket Lab USA (航天)'},
    ]
    
    results = []
    for symbol_config in symbols:
        result = deep_analyze_symbol(symbol_config['symbol'], symbol_config['name'])
        results.append(result)
        print(f"\n\n")
    
    # 对比分析
    compare_symbols(results)
    
    # 最终建议
    print(f"\n{'='*70}")
    print("【最终投资建议】")
    print(f"{'='*70}")
    
    for data in results:
        if data and data['signals']:
            best = data['best_result']
            print(f"\n{data['symbol']}:")
            
            if best.reliability_level.value == 'very_high':
                print(f"   ✅ 极高可靠性 - {best.operation_suggestion.value}")
                print(f"      综合置信度：{best.final_confidence*100:.0f}%")
                print(f"      建议仓位：70-100%")
            elif best.reliability_level.value == 'high':
                print(f"   ✅ 高可靠性 - {best.operation_suggestion.value}")
                print(f"      综合置信度：{best.final_confidence*100:.0f}%")
                print(f"      建议仓位：50-70%")
            elif best.reliability_level.value == 'medium':
                print(f"   ⚠️ 中等可靠性 - {best.operation_suggestion.value}")
                print(f"      综合置信度：{best.final_confidence*100:.0f}%")
                print(f"      建议仓位：20-30%")
                print(f"      提示：等待更多确认信号可提升置信度")
            else:
                print(f"   🔵 低可靠性 - 建议观望")
                print(f"      综合置信度：{best.final_confidence*100:.0f}%")
        elif data:
            print(f"\n{data['symbol']}:")
            print(f"   ⚪ 无买卖点信号 - 继续观望")
    
    print(f"\n{'='*70}")
    print(f"分析完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
