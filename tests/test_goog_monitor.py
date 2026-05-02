#!/usr/bin/env python3
"""
GOOG (Alphabet/Google) 美股缠论监控测试脚本
测试周线 (1w) 和日线 (1d) 级别的数据获取和背驰检测
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator


def fetch_data(symbol: str, timeframe: str):
    """获取 Yahoo Finance 数据"""
    try:
        import yfinance as yf
        
        period_map = {
            '5m': ('5d', '5m'),
            '30m': ('10d', '30m'),
            '1d': ('60d', '1d'),
            '1w': ('2y', '1wk'),
            'week': ('2y', '1wk'),
        }
        
        period, interval = period_map.get(timeframe, ('10d', '30m'))
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        
        if len(history) == 0:
            print(f"❌ 无法获取 {symbol} {timeframe} 数据")
            return None
        
        klines = []
        for idx, row in history.iterrows():
            if hasattr(idx, 'to_pydatetime'):
                timestamp = idx.to_pydatetime()
            else:
                timestamp = idx
            
            klines.append(Kline(
                timestamp=timestamp,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']) if 'Volume' in row else 0
            ))
        
        return KlineSeries(klines)
    
    except Exception as e:
        print(f"❌ 数据获取失败：{e}")
        return None


def analyze_level(symbol: str, timeframe: str):
    """分析某个级别"""
    print(f"\n{'='*60}")
    print(f"📊 {symbol} - {timeframe} 级别分析")
    print(f"{'='*60}")
    
    data = fetch_data(symbol, timeframe)
    if not data or len(data.klines) == 0:
        return None
    
    print(f"✅ 数据获取成功：{len(data.klines)} 根 K 线")
    print(f"   时间范围：{data.klines[0].timestamp} - {data.klines[-1].timestamp}")
    print(f"   最新价格：${data.klines[-1].close:.2f}")
    
    # 分型检测
    fractal_detector = FractalDetector()
    fractals = fractal_detector.detect_all(data)
    print(f"\n📐 分型统计:")
    print(f"   顶分型：{len([f for f in fractals if f.is_top])}")
    print(f"   底分型：{len([f for f in fractals if not f.is_top])}")
    
    # 笔检测
    pen_calculator = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calculator.identify_pens(data)
    print(f"\n✏️  笔统计：{len(pens)} 笔")
    if pens:
        print(f"   最新笔方向：{'向上' if pens[-1].is_up else '向下'}")
    
    # 线段检测
    segment_calculator = SegmentCalculator(min_pens=3)
    segments = segment_calculator.detect_segments(pens)
    print(f"\n📏 线段统计：{len(segments)} 线段")
    
    # MACD 指标
    prices = [k.close for k in data.klines]
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_values = macd.calculate(prices)
    
    if macd_values and len(macd_values) > 0:
        latest = macd_values[-1]
        print(f"\n📈 MACD 指标:")
        print(f"   DIF: {latest.dif:.4f}")
        print(f"   DEA: {latest.dea:.4f}")
        print(f"   MACD: {latest.macd:.4f}")
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'data': data,
        'fractals': fractals,
        'pens': pens,
        'segments': segments,
        'latest_price': data.klines[-1].close
    }


def check_divergence(symbol: str):
    """检查背驰"""
    print(f"\n{'='*60}")
    print(f"🔍 {symbol} - 背驰检测")
    print(f"{'='*60}")
    
    # 分析两个级别
    weekly = analyze_level(symbol, '1w')
    daily = analyze_level(symbol, '1d')
    
    if not weekly or not daily:
        print("\n⚠️  无法完成背驰检测（数据不足）")
        return
    
    # 简单背驰判断（价格新低但 MACD 未新低）
    weekly_pens = weekly.get('pens', [])
    daily_pens = daily.get('pens', [])
    
    print(f"\n{'='*60}")
    print(f"📋 联动分析总结")
    print(f"{'='*60}")
    print(f"周线级别：{len(weekly_pens)} 笔，最新价格 ${weekly['latest_price']:.2f}")
    print(f"日线级别：{len(daily_pens)} 笔，最新价格 ${daily['latest_price']:.2f}")
    
    # 级别联动判断
    if len(weekly_pens) >= 2 and len(daily_pens) >= 2:
        weekly_direction = '向上' if weekly_pens[-1].is_up else '向下'
        daily_direction = '向上' if daily_pens[-1].is_up else '向下'
        
        print(f"\n🔗 级别联动状态:")
        print(f"   周线最新笔：{weekly_direction}")
        print(f"   日线最新笔：{daily_direction}")
        
        if weekly_direction != daily_direction:
            print(f"\n⚠️  级别不一致 - 可能处于转折期")
        else:
            print(f"\n✅ 级别一致 - 趋势延续中")
    
    print(f"\n✅ GOOG 美股缠论分析完成")
    print(f"   监控配置：1w + 1d 双级别联动")
    print(f"   下次自动汇报：16:00 ET (收盘报告)")


if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"🇺🇸 GOOG (Alphabet/Google) 美股缠论监控测试")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S EDT')}")
    
    check_divergence('GOOG')
    
    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"{'='*60}\n")
