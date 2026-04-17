#!/usr/bin/env python3
"""
缠论 v2.0 vs v5.3 监控股票对比分析

使用 v2.0 综合置信度引擎重新分析之前设置预警的股票
对比 v5.3 版本的监控结果
"""

import sys
from pathlib import Path
from datetime import datetime
import yfinance as yf

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

from trading_system.kline import Kline, KlineSeries
from comprehensive_confidence_engine import ComprehensiveConfidenceEngine
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.indicators import MACDIndicator

# 之前设置预警的股票池 (来自 monitor_all.py)
MONITOR_STOCKS = [
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources'},
    {'symbol': 'PAAS.TO', 'name': 'Pan American Silver'},
    {'symbol': 'TECK', 'name': 'Teck Resources'},
    {'symbol': 'TEL', 'name': 'TE Connectivity'},
    {'symbol': 'GOOG', 'name': 'Alphabet/Google'},
    {'symbol': 'INTC', 'name': 'Intel Corporation'},
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises'},
    {'symbol': 'BABA', 'name': 'Alibaba Group'},
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA'},
    {'symbol': 'SMR', 'name': 'NuScale Power'},
    {'symbol': 'IONQ', 'name': 'IonQ Inc'},
    {'symbol': 'TSLA', 'name': 'Tesla Inc'},
]

print("=" * 70)
print("缠论 v2.0 vs v5.3 监控股票对比分析")
print("=" * 70)
print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"股票池：{len(MONITOR_STOCKS)} 只监控股票")
print("=" * 70)

v2_engine = ComprehensiveConfidenceEngine()
v2_results = []
v5_results = []

for stock in MONITOR_STOCKS:
    symbol = stock['symbol']
    name = stock['name']
    
    try:
        data = yf.Ticker(symbol).history(period='60d', interval='1d')
        if len(data) == 0:
            continue
        
        klines = [Kline(
            timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
            open=float(row['Open']), high=float(row['High']),
            low=float(row['Low']), close=float(row['Close']),
            volume=int(row.get('Volume', 0))
        ) for idx, row in data.iterrows()]
        
        series = KlineSeries(klines=klines, symbol=symbol, timeframe='1d')
        
        # v2.0 分析
        v2_signal = v2_engine.evaluate(series, symbol, '1d')
        v2_results.append({
            'symbol': symbol, 'name': name,
            'confidence': v2_signal.comprehensive_confidence,
            'recommendation': v2_signal.recommendation,
            'position_ratio': v2_signal.position_ratio,
            'start_conf': v2_signal.start_confidence,
            'decay_conf': v2_signal.decay_confidence,
            'reversal_conf': v2_signal.reversal_confidence,
        })
        
        # v5.3 分析
        fractals = FractalDetector().detect_all(series)
        bottom_fractals = [f for f in fractals if not f.is_top]
        top_fractals = [f for f in fractals if f.is_top]
        pens = PenCalculator(PenConfig(use_new_definition=True, strict_validation=True, min_klines_between_turns=3)).identify_pens(series)
        prices = [k.close for k in series.klines]
        macd_data = MACDIndicator(fast=12, slow=26, signal=9).calculate(prices)
        
        signals = []
        if len(bottom_fractals) >= 2:
            last_low, prev_low = bottom_fractals[-1], bottom_fractals[-2]
            if last_low.price < prev_low.price:
                last_macd = macd_data[last_low.kline_index].histogram if last_low.kline_index < len(macd_data) else 0
                prev_macd = macd_data[prev_low.kline_index].histogram if prev_low.kline_index < len(macd_data) else 0
                if last_macd > prev_macd:
                    signals.append('buy1')
            elif pens and pens[-1].is_up:
                dist = (series.klines[-1].close - last_low.price) / last_low.price
                if 0 < dist <= 0.015:
                    signals.append('buy2')
        
        v5_results.append({'symbol': symbol, 'name': name, 'signals': signals, 'has_signal': len(signals) > 0})
        
        v2_emoji = {'STRONG_BUY': '🚀', 'BUY': '🟢', 'HOLD': '⚪', 'SELL': '🔴', 'STRONG_SELL': '💥'}
        print(f"  {symbol}: v2.0 {v2_emoji.get(v2_signal.recommendation, '⚪')} {v2_signal.recommendation} ({v2_signal.comprehensive_confidence*100:.0f}%), v5.3 {', '.join(signals) if signals else '❌ 无'}")
        
    except Exception as e:
        print(f"  {symbol}: ❌ {e}")

print(f"\n{'='*70}")
print("汇总统计")
print(f"{'='*70}")
v2_buy = sum(1 for r in v2_results if r['recommendation'] in ['STRONG_BUY', 'BUY'])
v5_sig = sum(1 for r in v5_results if r['has_signal'])
print(f"v2.0: 买入{v2_buy}/{len(v2_results)} ({v2_buy/len(v2_results)*100:.1f}%), 平均置信度{sum(r['confidence'] for r in v2_results)/len(v2_results)*100:.1f}%")
print(f"v5.3: 信号{v5_sig}/{len(v5_results)} ({v5_sig/len(v5_results)*100:.1f}%)")
print(f"{'='*70}")
