#!/usr/bin/env python3
"""
UVIX (Volatility Shares - 1.5x Long VIX) 缠论多级别买卖点监控脚本
支持：5 分钟、30 分钟级别
行业：金融 - 波动率产品

UVIX 是高波动性产品，适合缠论短线交易
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path for message tool
sys.path.insert(0, '/home/wei/.openclaw/workspace')

# Configuration
SYMBOL = "UVIX"
TELEGRAM_CHAT_ID = "8365377574"
ALERT_FILE = "/home/wei/.openclaw/workspace/chanlun/uvix_alerts.log"
RESULT_FILE = "/home/wei/.openclaw/workspace/chanlun/uvix_analysis.json"

# Price alert thresholds (percentage)
PRICE_ALERT_THRESHOLD = 0.02  # 2% price change alert


def fetch_stock_data(symbol="UVIX", period="5d", interval="5m"):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"❌ 获取数据失败：{e}")
        return pd.DataFrame()


def fetch_multi_level_data(symbol="UVIX"):
    """获取多级别数据 (5 分钟 + 30 分钟)"""
    levels = {
        '5m': fetch_stock_data(symbol, period="2d", interval="5m"),
        '30m': fetch_stock_data(symbol, period="10d", interval="30m")
    }
    return levels


def find_fractal_high(df, window=3):
    """寻找顶分型"""
    fractals = []
    for i in range(window, len(df) - window):
        if df['High'].iloc[i] == df['High'].iloc[i-window:i+window+1].max():
            fractals.append({
                'index': i,
                'price': df['High'].iloc[i],
                'time': df.index[i],
                'type': 'top'
            })
    return fractals


def find_fractal_low(df, window=3):
    """寻找底分型"""
    fractals = []
    for i in range(window, len(df) - window):
        if df['Low'].iloc[i] == df['Low'].iloc[i-window:i+window+1].min():
            fractals.append({
                'index': i,
                'price': df['Low'].iloc[i],
                'time': df.index[i],
                'type': 'bottom'
            })
    return fractals


def calculate_macd(df):
    """计算 MACD 指标"""
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram


def detect_divergence(df, fractals_low, macd):
    """检测底背驰"""
    if len(fractals_low) < 2:
        return False
    
    last_low = fractals_low[-1]
    prev_low = fractals_low[-2]
    
    # 价格创新低
    if last_low['price'] < prev_low['price']:
        # MACD 不创新低 (背驰)
        last_macd = macd.iloc[last_low['index']]
        prev_macd = macd.iloc[prev_low['index']]
        
        if last_macd > prev_macd:
            return True
    
    return False


def detect_buy_sell_points(df, fractals_high, fractals_low, level="5m"):
    """
    检测买卖点 (缠论)
    第一类买点：趋势背驰后，新低不创新低
    第二类买点：回调不破前低
    第三类买点：中枢突破后回踩确认
    """
    signals = []
    
    if len(fractals_low) < 2 or len(fractals_high) < 2:
        return signals
    
    # 获取最新的几个分型
    recent_lows = fractals_low[-3:] if len(fractals_low) >= 3 else fractals_low
    recent_highs = fractals_high[-3:] if len(fractals_high) >= 3 else fractals_high
    
    current_price = df['Close'].iloc[-1]
    
    # UVIX 高波动性，阈值更大
    threshold_map = {
        '5m': {'buy2': 0.015, 'buy1': 2.0, 'sell2': 0.015, 'sell1': 2.0},
        '30m': {'buy2': 0.025, 'buy1': 3.0, 'sell2': 0.025, 'sell1': 3.0}
    }
    thresholds = threshold_map.get(level, threshold_map['5m'])
    
    # 计算 MACD 用于背驰检测
    macd, signal, histogram = calculate_macd(df)
    
    # ========== 买点检测 ==========
    
    # 检测第二类买点：回调不破前低
    if len(recent_lows) >= 2:
        last_low = recent_lows[-1]
        prev_low = recent_lows[-2]
        
        # 如果最新底分型高于前一个底分型，且价格回调接近但不破前低
        if last_low['price'] > prev_low['price']:
            distance_from_low = (current_price - last_low['price']) / last_low['price']
            
            if distance_from_low <= thresholds['buy2']:
                signals.append({
                    'type': 'buy2',
                    'name': f'{level}级别第二类买点',
                    'price': current_price,
                    'time': datetime.now(),
                    'confidence': 'medium',
                    'support_level': last_low['price'],
                    'description': f'回调不破前低 {prev_low["price"]:.2f}, 当前价 {current_price:.2f} (距低点 +{distance_from_low*100:.2f}%)'
                })
    
    # 检测第一类买点：底背驰
    if len(recent_lows) >= 2:
        last_low = recent_lows[-1]
        prev_low = recent_lows[-2]
        
        # 检查背驰
        is_divergence = detect_divergence(df, recent_lows, macd)
        
        # 如果最新低点低于前低，但差距很小 (潜在背驰)
        if last_low['price'] < prev_low['price']:
            diff_pct = (prev_low['price'] - last_low['price']) / prev_low['price'] * 100
            
            if is_divergence or abs(diff_pct) < thresholds['buy1']:
                # 检查是否有反弹迹象
                current_from_low = (current_price - last_low['price']) / last_low['price'] * 100
                
                if current_from_low > 1.0:  # 从低点反弹超过 1%
                    confidence = 'high' if is_divergence else 'low'
                    signals.append({
                        'type': 'buy1',
                        'name': f'{level}级别第一类买点 {"(背驰确认)" if is_divergence else "(潜在背驰)"}',
                        'price': current_price,
                        'time': datetime.now(),
                        'confidence': confidence,
                        'support_level': last_low['price'],
                        'description': f'底背驰：新低 {last_low["price"]:.2f} vs 前低 {prev_low["price"]:.2f} ({diff_pct:.2f}%), 反弹 +{current_from_low:.2f}%'
                    })
    
    # ========== 卖点检测 ==========
    
    # 检测第二类卖点：反弹不过前高
    if len(recent_highs) >= 2:
        last_high = recent_highs[-1]
        prev_high = recent_highs[-2]
        
        # 如果最新顶分型低于前一个顶分型，且价格反弹接近但不破前高
        if last_high['price'] < prev_high['price']:
            distance_from_high = (last_high['price'] - current_price) / last_high['price']
            
            if distance_from_high <= thresholds['sell2']:
                signals.append({
                    'type': 'sell2',
                    'name': f'{level}级别第二类卖点',
                    'price': current_price,
                    'time': datetime.now(),
                    'confidence': 'medium',
                    'resistance_level': prev_high['price'],
                    'description': f'反弹不过前高 {prev_high["price"]:.2f}, 当前价 {current_price:.2f} (距高点 -{distance_from_high*100:.2f}%)'
                })
    
    # 检测第一类卖点：顶背驰
    if len(recent_highs) >= 2:
        last_high = recent_highs[-1]
        prev_high = recent_highs[-2]
        
        # 价格创新高但 MACD 不创新高 (顶背驰)
        if last_high['price'] > prev_high['price']:
            last_macd = macd.iloc[last_high['index']]
            prev_macd = macd.iloc[prev_high['index']]
            
            if last_macd < prev_macd:  # 顶背驰
                current_from_high = (last_high['price'] - current_price) / last_high['price'] * 100
                
                if current_from_high > 1.0:  # 从高点下跌超过 1%
                    signals.append({
                        'type': 'sell1',
                        'name': f'{level}级别第一类卖点 (顶背驰)',
                        'price': current_price,
                        'time': datetime.now(),
                        'confidence': 'high',
                        'resistance_level': last_high['price'],
                        'description': f'顶背驰：新高 {last_high["price"]:.2f} vs 前高 {prev_high["price"]:.2f}, MACD 走弱，下跌 -{current_from_high:.2f}%'
                    })
    
    # ========== 价格突破提醒 ==========
    
    # 检查是否突破关键位置
    if len(recent_highs) >= 1:
        last_high = recent_highs[-1]
        if current_price > last_high['price'] * 1.02:  # 突破前高 2%
            signals.append({
                'type': 'breakout_up',
                'name': f'{level}级别向上突破',
                'price': current_price,
                'time': datetime.now(),
                'confidence': 'medium',
                'resistance_level': last_high['price'],
                'description': f'突破前高 {last_high["price"]:.2f}, 当前价 {current_price:.2f} (+{(current_price-last_high["price"])/last_high["price"]*100:.2f}%)'
            })
    
    if len(recent_lows) >= 1:
        last_low = recent_lows[-1]
        if current_price < last_low['price'] * 0.98:  # 跌破前低 2%
            signals.append({
                'type': 'breakout_down',
                'name': f'{level}级别向下跌破',
                'price': current_price,
                'time': datetime.now(),
                'confidence': 'medium',
                'support_level': last_low['price'],
                'description': f'跌破前低 {last_low["price"]:.2f}, 当前价 {current_price:.2f} ({(current_price-last_low["price"])/last_low["price"]*100:.2f}%)'
            })
    
    return signals


def send_telegram_alert(message):
    """发送 Telegram 提醒"""
    print(f"🚨 TELEGRAM ALERT: {message[:100]}...")
    
    # Log to file
    with open(ALERT_FILE, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    # Note: In production, this would call the message API
    # For now, we log to file and console


def analyze_and_alert():
    """主分析函数 - 多级别分析"""
    print(f"📊 开始分析 {SYMBOL} 多级别缠论...")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取多级别数据
    levels_data = fetch_multi_level_data(SYMBOL)
    
    all_signals = []
    results = {}
    
    for level_name, df in levels_data.items():
        if df.empty:
            print(f"❌ {level_name}级别：无法获取数据")
            results[level_name] = {'error': 'No data'}
            continue
        
        print(f"\n{'='*60}")
        print(f"📊 {level_name}级别分析")
        print(f"📈 最新价格：${df['Close'].iloc[-1]:.2f}")
        print(f"📅 数据范围：{df.index[0]} 到 {df.index[-1]}")
        print(f"📊 数据点数：{len(df)}")
        
        # 计算日内变化
        if len(df) > 1:
            daily_change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
            print(f"📈 期间变化：{daily_change:+.2f}%")
        
        # 寻找分型
        fractals_high = find_fractal_high(df)
        fractals_low = find_fractal_low(df)
        
        print(f"🔺 顶分型数量：{len(fractals_high)}")
        print(f"🔻 底分型数量：{len(fractals_low)}")
        
        # 显示最新分型
        if fractals_high:
            print(f"🔺 最新顶分型：${fractals_high[-1]['price']:.2f} @ {fractals_high[-1]['time']}")
        if fractals_low:
            print(f"🔻 最新底分型：${fractals_low[-1]['price']:.2f} @ {fractals_low[-1]['time']}")
        
        # 检测买卖点
        signals = detect_buy_sell_points(df, fractals_high, fractals_low, level_name)
        
        if signals:
            print(f"\n🎯 发现 {len(signals)} 个买卖点信号:")
            for signal in signals:
                print(f"  {'🟢' if 'buy' in signal['type'] else '🔴' if 'sell' in signal['type'] else '🔵'} {signal['name']}: ${signal['price']:.2f} ({signal['confidence']})")
                print(f"     {signal['description']}")
                
                # 发送 Telegram 提醒
                emoji = '🟢' if 'buy' in signal['type'] else '🔴' if 'sell' in signal['type'] else '🔵'
                alert_msg = f"""
{emoji} {SYMBOL} 缠论买卖点提醒

📊 信号：{signal['name']}
💰 价格：${signal['price']:.2f}
🎯 置信度：{signal['confidence']}
📝 说明：{signal['description']}

⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
级别：{level_name}
                """.strip()
                send_telegram_alert(alert_msg)
                all_signals.append(signal)
        else:
            print(f"\n✅ {level_name}级别：暂无明确买卖点信号")
        
        results[level_name] = {
            'current_price': float(df['Close'].iloc[-1]),
            'daily_change': float(daily_change) if len(df) > 1 else 0,
            'fractals_high': len(fractals_high),
            'fractals_low': len(fractals_low),
            'latest_top': fractals_high[-1]['price'] if fractals_high else None,
            'latest_bottom': fractals_low[-1]['price'] if fractals_low else None,
            'signals': signals
        }
    
    # 保存分析结果
    result = {
        'timestamp': datetime.now().isoformat(),
        'symbol': SYMBOL,
        'levels': results,
        'total_signals': len(all_signals),
        'summary': {
            'buy_signals': len([s for s in all_signals if 'buy' in s['type']]),
            'sell_signals': len([s for s in all_signals if 'sell' in s['type']]),
            'breakout_signals': len([s for s in all_signals if 'breakout' in s['type']])
        }
    }
    
    with open(RESULT_FILE, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print(f"📁 分析结果已保存：{RESULT_FILE}")
    print(f"📁 提醒日志：{ALERT_FILE}")
    print(f"🎯 总计信号数：{len(all_signals)} (买：{result['summary']['buy_signals']}, 卖：{result['summary']['sell_signals']})")
    
    return result


if __name__ == "__main__":
    analyze_and_alert()
