#!/usr/bin/env python3
"""
CVE.TO (Cenovus Energy) 缠论多级别买卖点监控脚本
支持：5 分钟、30 分钟、日线级别
简易版 - 使用 yfinance 获取数据，实现基础缠论分析
行业：能源 - 石油与天然气整合
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Telegram channel for alerts (from inbound context)
TELEGRAM_CHAT_ID = "8365377574"

def fetch_stock_data(symbol="CVE.TO", period="5d", interval="30m"):
    """获取股票数据"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    return df

def fetch_multi_level_data(symbol="CVE.TO"):
    """获取多级别数据"""
    levels = {
        '5m': fetch_stock_data(symbol, period="2d", interval="5m"),
        '30m': fetch_stock_data(symbol, period="10d", interval="30m"),
        '1d': fetch_stock_data(symbol, period="60d", interval="1d")
    }
    return levels

def find_fractal_high(df, window=5):
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

def find_fractal_low(df, window=5):
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

def detect_buy_sell_points(df, fractals_high, fractals_low, level="30m"):
    """
    检测买卖点 (简化版缠论)
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
    
    # 不同级别的阈值
    threshold_map = {
        '5m': {'buy2': 0.015, 'buy1': 2.0, 'sell2': 0.015},  # 5 分钟更敏感
        '30m': {'buy2': 0.02, 'buy1': 3.0, 'sell2': 0.02},    # 30 分钟标准
        '1d': {'buy2': 0.03, 'buy1': 5.0, 'sell2': 0.03}      # 日线更宽松
    }
    thresholds = threshold_map.get(level, threshold_map['30m'])
    
    # 检测第二类买点：回调不破前低
    if len(recent_lows) >= 2:
        last_low = recent_lows[-1]
        prev_low = recent_lows[-2]
        
        # 如果最新底分型高于前一个底分型，且价格回调接近但不破前低
        if last_low['price'] > prev_low['price']:
            if current_price <= last_low['price'] * (1 + thresholds['buy2']):
                signals.append({
                    'type': 'buy2',
                    'name': f'{level}级别第二类买点',
                    'price': current_price,
                    'time': datetime.now(),
                    'confidence': 'medium',
                    'description': f'回调不破前低 {prev_low["price"]:.2f}, 当前价 {current_price:.2f}'
                })
    
    # 检测第一类买点：底背驰 (价格新低但指标不新低 - 简化版)
    if len(recent_lows) >= 2:
        last_low = recent_lows[-1]
        prev_low = recent_lows[-2]
        
        # 如果最新低点低于前低，但差距很小 (潜在背驰)
        if last_low['price'] < prev_low['price']:
            diff_pct = (prev_low['price'] - last_low['price']) / prev_low['price'] * 100
            if abs(diff_pct) < thresholds['buy1']:  # 跌幅小于阈值，可能是背驰
                # 检查是否有反弹迹象
                if current_price > last_low['price'] * 1.01:
                    signals.append({
                        'type': 'buy1',
                        'name': f'{level}级别第一类买点 (潜在背驰)',
                        'price': current_price,
                        'time': datetime.now(),
                        'confidence': 'low',
                        'description': f'底背驰迹象：新低 {last_low["price"]:.2f} vs 前低 {prev_low["price"]:.2f} ({diff_pct:.2f}%)'
                    })
    
    # 检测卖点 (类似逻辑)
    if len(recent_highs) >= 2:
        last_high = recent_highs[-1]
        prev_high = recent_highs[-2]
        
        # 第二类卖点：反弹不过前高
        if last_high['price'] < prev_high['price']:
            if current_price >= last_high['price'] * (1 - thresholds['sell2']):
                signals.append({
                    'type': 'sell2',
                    'name': f'{level}级别第二类卖点',
                    'price': current_price,
                    'time': datetime.now(),
                    'confidence': 'medium',
                    'description': f'反弹不过前高 {prev_high["price"]:.2f}, 当前价 {current_price:.2f}'
                })
    
    return signals

def send_alert(message):
    """发送提醒 (通过 message tool)"""
    print(f"🚨 ALERT: {message}")
    # In production, this would call the message API
    # For now, we'll output to console and a file
    alert_file = "/home/wei/.openclaw/workspace/chanlun/alerts.log"
    with open(alert_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

def analyze_and_alert():
    """主分析函数 - 多级别分析"""
    print(f"📊 开始分析 CVE.TO 多级别缠论...")
    
    # 获取多级别数据
    levels_data = fetch_multi_level_data("CVE.TO")
    
    all_signals = []
    results = {}
    
    for level_name, df in levels_data.items():
        if df.empty:
            print(f"❌ {level_name}级别：无法获取数据")
            continue
        
        print(f"\n{'='*50}")
        print(f"📊 {level_name}级别分析")
        print(f"📈 最新价格：${df['Close'].iloc[-1]:.2f}")
        print(f"📅 数据范围：{df.index[0]} 到 {df.index[-1]}")
        
        # 寻找分型
        fractals_high = find_fractal_high(df)
        fractals_low = find_fractal_low(df)
        
        print(f"🔺 顶分型数量：{len(fractals_high)}")
        print(f"🔻 底分型数量：{len(fractals_low)}")
        
        # 检测买卖点
        signals = detect_buy_sell_points(df, fractals_high, fractals_low, level_name)
        
        if signals:
            print(f"\n🎯 发现 {len(signals)} 个买卖点信号:")
            for signal in signals:
                print(f"  - {signal['name']}: ${signal['price']:.2f} ({signal['confidence']})")
                print(f"    {signal['description']}")
                
                # 发送提醒
                alert_msg = f"""
🚨 CVE.TO 缠论买卖点提醒

📊 信号：{signal['name']}
💰 价格：${signal['price']:.2f}
🎯 置信度：{signal['confidence']}
📝 说明：{signal['description']}

⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
                """.strip()
                send_alert(alert_msg)
                all_signals.append(signal)
        else:
            print(f"\n✅ {level_name}级别：暂无明确买卖点信号")
        
        results[level_name] = {
            'current_price': float(df['Close'].iloc[-1]),
            'fractals_high': len(fractals_high),
            'fractals_low': len(fractals_low),
            'signals': signals
        }
    
    # 保存分析结果
    result = {
        'timestamp': datetime.now().isoformat(),
        'symbol': 'CVE.TO',
        'levels': results,
        'total_signals': len(all_signals)
    }
    
    result_file = "/home/wei/.openclaw/workspace/chanlun/cve_analysis.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n{'='*50}")
    print(f"📁 分析结果已保存：{result_file}")
    print(f"🎯 总计信号数：{len(all_signals)}")
    return result

if __name__ == "__main__":
    analyze_and_alert()
