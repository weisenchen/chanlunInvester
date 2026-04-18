#!/usr/bin/env python3
"""
ChanLun Invester - Real-time Monitor with Telegram Alerts
缠论智能监控系统 - Telegram 预警

基于 chanlunInvester 核心引擎，实现多级别买卖点监控
支持：分型、笔、线段、中枢、背驰、买卖点检测
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add python-layer to path
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

# Import trading system components
from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator
from trading_system.center import CenterDetector

# Import comprehensive confidence system
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from volume_confirmation import VolumeConfirmation
from macd_advanced_analysis import MACDAdvancedAnalyzer
from confidence_calculator import ComprehensiveConfidenceCalculator

# v6.0: Import center momentum confidence
from trading_system.center_momentum_confidence import CenterMomentumConfidenceCalculator

# Configuration
TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
OPENCLAW_PATH = "/home/linuxbrew/.linuxbrew/bin/openclaw"
ALERT_STATE_FILE = "/home/wei/.openclaw/workspace/chanlunInvester/.alert_state.json"

# Anti-spam settings (防重复警报设置)
MIN_PRICE_CHANGE = 0.003  # 最小价格变化 0.3% 才触发新警报
SILENCE_PERIOD_MINUTES = 60  # 同一信号静默期 60 分钟

# 多级别共振过滤 (Multi-Level Resonance Filter)
# 只有多级别共振确认时才发送警报，减少噪音
ENABLE_RESONANCE_FILTER = True  # 启用共振过滤
RESONANCE_MIN_CONFIDENCE = 0.75  # 最低置信度要求 (75%)

# Symbols to monitor
SYMBOLS = [
    # UVIX 已移除 (用户要求取消)
    # XEG.TO, CVE.TO 已移除 (用户要求取消)
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'levels': ['30m', '1d']},
    {'symbol': 'PAAS.TO', 'name': 'Pan American Silver', 'levels': ['30m', '1d']},
    {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['30m', '1d']},
    # 美股
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['30m', '1d']},
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d']},
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['30m', '1d']},
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['30m', '1d']},
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'SMR', 'name': 'NuScale Power Corporation (美股)', 'levels': ['1d', '30m', '5m']},
    {'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1d', '30m']},
    {'symbol': 'TSLA', 'name': 'Tesla Inc (美股/电动车)', 'levels': ['1d', '30m']},
]

def fetch_yahoo_data(symbol: str, timeframe: str = '30m', count: int = 100):
    """Fetch real-time data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        # Get historical data based on timeframe
        if timeframe == 'day' or timeframe == '1d':
            period = '60d'
            interval = '1d'
        elif timeframe == '5m':
            period = '5d'
            interval = '5m'
        elif timeframe == '30m':
            period = '10d'
            interval = '30m'
        elif timeframe == '1w' or timeframe == 'week':
            period = '1y'
            interval = '1wk'
        else:  # default 30m
            period = '10d'
            interval = '30m'
        
        # Fetch data
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        
        if len(history) == 0:
            return None
        
        # Convert to Kline objects
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
                volume=int(row.get('Volume', 0))
            )
            klines.append(kline)
        
        # Take last 'count' klines
        if len(klines) > count:
            klines = klines[-count:]
        
        series = KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
        return series
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        return None


def buy1_confirmed(fractals, macd_data) -> bool:
    """
    检查第一类买点 (buy1) 是否已经发生
    
    buy1 条件:
    • 价格新低
    • MACD 背驰 (价格新低但 MACD 不新低)
    
    这是第二类买点的前置条件！
    """
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    if len(bottom_fractals) < 2 or not macd_data:
        return False
    
    last_low = bottom_fractals[-1]
    prev_low = bottom_fractals[-2]
    
    # 条件 1: 价格新低
    if last_low.price >= prev_low.price:
        return False
    
    # 条件 2: MACD 背驰
    last_idx = last_low.kline_index
    prev_idx = prev_low.kline_index
    
    if last_idx >= len(macd_data) or prev_idx >= len(macd_data):
        return False
    
    last_macd = macd_data[last_idx].histogram if hasattr(macd_data[last_idx], 'histogram') else 0
    prev_macd = macd_data[prev_idx].histogram if hasattr(macd_data[prev_idx], 'histogram') else 0
    
    # 价格新低但 MACD 不新低 = 背驰
    if last_macd <= prev_macd:
        return False  # MACD 也新低，背驰不成立
    
    return True  # buy1 已确认


def sell1_confirmed(fractals, macd_data) -> bool:
    """
    检查第一类卖点 (sell1) 是否已经发生
    
    sell1 条件:
    • 价格新高
    • MACD 背驰 (价格新高但 MACD 不新高)
    
    这是第二类卖点的前置条件！
    """
    top_fractals = [f for f in fractals if f.is_top]
    
    if len(top_fractals) < 2 or not macd_data:
        return False
    
    last_high = top_fractals[-1]
    prev_high = top_fractals[-2]
    
    # 条件 1: 价格新高
    if last_high.price <= prev_high.price:
        return False
    
    # 条件 2: MACD 背驰
    last_idx = last_high.kline_index
    prev_idx = prev_high.kline_index
    
    if last_idx >= len(macd_data) or prev_idx >= len(macd_data):
        return False
    
    last_macd = macd_data[last_idx].histogram if hasattr(macd_data[last_idx], 'histogram') else 0
    prev_macd = macd_data[prev_idx].histogram if hasattr(macd_data[prev_idx], 'histogram') else 0
    
    # 价格新高但 MACD 不新高 = 背驰
    if last_macd >= prev_macd:
        return False  # MACD 也新高，背驰不成立
    
    return True  # sell1 已确认


def detect_buy_sell_points(series, fractals, pens, segments, macd_data, level="30m"):
    """
    Detect ChanLun buy/sell points
    缠论买卖点检测
    
    修复：
    1. 添加趋势方向过滤，避免买卖点同时出现（缠论走势类型互斥原理）
    2. 第二类买卖点必须检查第一类买卖点已确认（缠论定义）
    3. 买卖点必须结合中枢判断（缠论核心）
    """
    signals = []
    
    if len(fractals) < 4 or len(pens) < 4:
        return signals
    
    # 检测中枢
    center_det = CenterDetector(min_segments=3)
    centers = center_det.detect_centers(segments)
    last_center = centers[-1] if centers else None
    
    # Get recent fractals
    top_fractals = [f for f in fractals if f.is_top][-3:]
    bottom_fractals = [f for f in fractals if not f.is_top][-3:]
    
    current_price = series.klines[-1].close
    prices = [k.close for k in series.klines]
    volumes = [k.volume for k in series.klines]
    
    # ========== 获取当前趋势方向（关键修复）==========
    # 根据最后一笔的方向判断当前趋势
    last_pen = pens[-1]
    current_trend = 'up' if last_pen.is_up else 'down'
    
    # 获取倒数第二笔（用于确认趋势延续）
    prev_pen = pens[-2] if len(pens) >= 2 else None
    
    # Thresholds by level (优化：收紧阈值，避免震荡市误触发)
    thresholds = {
        '5m': {'bsp2': 0.01, 'bsp1': 2.0, 'min_distance': 0.005},
        '30m': {'bsp2': 0.015, 'bsp1': 3.0, 'min_distance': 0.008},
        '1d': {'bsp2': 0.03, 'bsp1': 5.0, 'min_distance': 0.01}
    }
    thresh = thresholds.get(level, thresholds['30m'])
    
    # ========== Buy Point 3 (第三类买点) ==========
    # 缠论定义：中枢形成后，突破中枢上沿，回测不破中枢上沿 (ZG)
    # 条件：
    #   1. 中枢已形成
    #   2. 价格突破中枢上沿 (ZG)
    #   3. 回测不破中枢上沿
    if last_center and len(bottom_fractals) >= 2:
        # 检查是否突破中枢
        recent_high = max(f.price for f in top_fractals[-3:]) if top_fractals else 0
        if recent_high > last_center.zg:
            # 突破中枢后回测
            if last_center.contains(current_price) or \
               abs(current_price - last_center.zg) / last_center.zg < 0.01:
                # 回测不破中枢上沿
                if current_price > last_center.zg * 0.99:
                    signals.append({
                        'type': 'buy3',
                        'name': f'{level}级别第三类买点 (中枢突破)',
                        'price': current_price,
                        'confidence': 'high',
                        'description': f'突破中枢后回测，不破 ZG {last_center.zg:.2f}',
                        'center_breakout': True,
                        # 详细触发依据
                        'trigger_details': {
                            'condition': '中枢突破 + 回测确认',
                            'center_zg': last_center.zg,
                            'center_zd': last_center.zd,
                            'recent_high': recent_high,
                            'pullback_price': current_price
                        },
                        'data': {
                            'prices': prices,
                            'volumes': volumes,
                            'macd_data': macd_data,
                            'center': {'zg': last_center.zg, 'zd': last_center.zd}
                        }
                    })
    
    # ========== Buy Point 2 (第二类买点) ==========
    # 缠论定义：buy1 确认后，回调回到中枢内或中枢边界，不破前低
    # 条件：
    #   1. buy1 已确认
    #   2. 回调进入中枢区间 (或接近中枢)
    #   3. 不破 buy1 低点
    if len(bottom_fractals) >= 2 and current_trend == 'up':
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        
        # 条件 1: 不破前低
        if last_low.price > prev_low.price:
            # 条件 2: buy1 已确认
            if buy1_confirmed(fractals, macd_data):
                # 条件 3: 回测中枢 (价格回到中枢内或接近中枢)
                center_pullback = False
                if last_center:
                    # 价格在中枢区间内，或在中枢下沿附近 (1% 容差)
                    if last_center.contains(current_price) or \
                       abs(current_price - last_center.zd) / last_center.zd < 0.01:
                        center_pullback = True
                elif len(bottom_fractals) >= 2:
                    # 无中枢时，只要是 buy1 后的回调即可
                    center_pullback = True
                
                if center_pullback:
                    distance = (current_price - last_low.price) / last_low.price
                    # 添加最小距离过滤，避免太近触发
                    if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                        signals.append({
                            'type': 'buy2',
                            'name': f'{level}级别第二类买点',
                            'price': current_price,
                            'confidence': 'medium',
                            'description': f'回调不破前低 {prev_low.price:.2f}, 当前价 {current_price:.2f}',
                            'buy1_confirmed': True,
                            'center_pullback': center_pullback,
                            # 详细触发依据
                            'trigger_details': {
                                'condition': '回调不破前低 + 回测中枢',
                                'last_low': last_low.price,
                                'prev_low': prev_low.price,
                                'distance': f'{distance*100:.2f}%',
                                'trend': '上涨趋势中的回调',
                                'buy1_status': '已确认',
                                'center_status': f'回测中枢 (ZD={last_center.zd:.2f})' if last_center else '无中枢'
                            },
                            'data': {
                                'prices': prices,
                                'volumes': volumes,
                                'macd_data': macd_data,
                                'last_low_idx': last_low.kline_index,
                                'prev_low_idx': prev_low.kline_index
                            }
                        })
    
    # ========== Buy Point 1 (第一类买点 - 背驰) ==========
    # 缠论定义：离开中枢后的背驰
    # 条件：
    #   1. 价格新低
    #   2. MACD 背驰
    #   3. 离开中枢 (价格低于中枢下沿)
    if len(bottom_fractals) >= 2 and macd_data:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        
        if last_low.price < prev_low.price:
            # Check MACD divergence
            last_idx = last_low.kline_index
            prev_idx = prev_low.kline_index
            
            if last_idx < len(macd_data) and prev_idx < len(macd_data):
                last_macd = macd_data[last_idx].histogram if hasattr(macd_data[last_idx], 'histogram') else 0
                prev_macd = macd_data[prev_idx].histogram if hasattr(macd_data[prev_idx], 'histogram') else 0
                
                # Price new low but MACD not new low = divergence
                if last_macd > prev_macd:
                    # 条件 3: 检查是否离开中枢
                    center_confirmed = False
                    if last_center and last_low.price < last_center.zd:
                        center_confirmed = True  # 价格低于中枢下沿，确认离开中枢
                    elif not last_center:
                        center_confirmed = True  # 无中枢，可能是第一个趋势
                    
                    if center_confirmed:
                        macd_strength = last_macd / prev_macd if prev_macd != 0 else 1.0
                        signals.append({
                            'type': 'buy1',
                            'name': f'{level}级别第一类买点 (背驰)',
                            'price': current_price,
                            'confidence': 'high' if last_macd > prev_macd * 1.5 else 'medium',
                            'description': f'底背驰：新低 {last_low.price:.2f} vs 前低 {prev_low.price:.2f}',
                            'center_confirmed': center_confirmed,
                            # 详细触发依据
                            'trigger_details': {
                                'condition': 'MACD 底背驰 + 离开中枢',
                                'price_new_low': last_low.price,
                                'price_prev_low': prev_low.price,
                                'macd_last': last_macd,
                                'macd_prev': prev_macd,
                                'macd_strength': f'{macd_strength*100:.1f}%',
                                'divergence': '价格新低但 MACD 未新低',
                                'center_status': f'离开中枢 (ZD={last_center.zd:.2f})' if last_center else '无中枢'
                            },
                            'data': {
                                'prices': prices,
                                'volumes': volumes,
                                'macd_data': macd_data,
                                'last_low_idx': last_low.kline_index,
                                'prev_low_idx': prev_low.kline_index
                            }
                        })
    
    # ========== Sell Point 1 (第一类卖点 - 背驰) ==========
    # 缠论定义：离开中枢后的背驰
    # 条件：
    #   1. 价格新高
    #   2. MACD 背驰
    #   3. 离开中枢 (价格高于中枢上沿)
    if len(top_fractals) >= 2 and macd_data:
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]
        
        if last_high.price > prev_high.price:
            # Check MACD divergence
            last_idx = last_high.kline_index
            prev_idx = prev_high.kline_index
            
            if last_idx < len(macd_data) and prev_idx < len(macd_data):
                last_macd = macd_data[last_idx].histogram if hasattr(macd_data[last_idx], 'histogram') else 0
                prev_macd = macd_data[prev_idx].histogram if hasattr(macd_data[prev_idx], 'histogram') else 0
                
                # Price new high but MACD not new high = divergence
                if last_macd < prev_macd:
                    # 条件 3: 检查是否离开中枢
                    center_confirmed = False
                    if last_center and last_high.price > last_center.zg:
                        center_confirmed = True  # 价格高于中枢上沿，确认离开中枢
                    elif not last_center:
                        center_confirmed = True  # 无中枢，可能是第一个趋势
                    
                    if center_confirmed:
                        macd_strength = prev_macd / last_macd if last_macd != 0 else 1.0
                        signals.append({
                            'type': 'sell1',
                            'name': f'{level}级别第一类卖点 (背驰)',
                            'price': current_price,
                            'confidence': 'high' if prev_macd > last_macd * 1.5 else 'medium',
                            'description': f'顶背驰：新高 {last_high.price:.2f} vs 前高 {prev_high.price:.2f}',
                            'center_confirmed': center_confirmed,
                            # 详细触发依据
                            'trigger_details': {
                                'condition': 'MACD 顶背驰 + 离开中枢',
                                'price_new_high': last_high.price,
                                'price_prev_high': prev_high.price,
                                'macd_last': last_macd,
                                'macd_prev': prev_macd,
                                'macd_strength': f'{macd_strength*100:.1f}%',
                                'divergence': '价格新高但 MACD 未新高',
                                'center_status': f'离开中枢 (ZG={last_center.zg:.2f})' if last_center else '无中枢'
                            },
                            'data': {
                                'prices': prices,
                                'volumes': volumes,
                                'macd_data': macd_data,
                                'last_high_idx': last_high.kline_index,
                                'prev_high_idx': prev_high.kline_index
                            }
                        })
    
    # ========== Sell Point 3 (第三类卖点) ==========
    # 缠论定义：中枢形成后，跌破中枢下沿，回测不过中枢下沿 (ZD)
    # 条件：
    #   1. 中枢已形成
    #   2. 价格跌破中枢下沿 (ZD)
    #   3. 回测不过中枢下沿
    if last_center and len(top_fractals) >= 2:
        # 检查是否跌破中枢
        recent_low = min(f.price for f in bottom_fractals[-3:]) if bottom_fractals else float('inf')
        if recent_low < last_center.zd:
            # 跌破中枢后回测
            if last_center.contains(current_price) or \
               abs(current_price - last_center.zd) / last_center.zd < 0.01:
                # 回测不过中枢下沿
                if current_price < last_center.zd * 1.01:
                    signals.append({
                        'type': 'sell3',
                        'name': f'{level}级别第三类卖点 (中枢跌破)',
                        'price': current_price,
                        'confidence': 'high',
                        'description': f'跌破中枢后回测，不过 ZD {last_center.zd:.2f}',
                        'center_breakdown': True,
                        # 详细触发依据
                        'trigger_details': {
                            'condition': '中枢跌破 + 回测确认',
                            'center_zg': last_center.zg,
                            'center_zd': last_center.zd,
                            'recent_low': recent_low,
                            'pullback_price': current_price
                        },
                        'data': {
                            'prices': prices,
                            'volumes': volumes,
                            'macd_data': macd_data,
                            'center': {'zg': last_center.zg, 'zd': last_center.zd}
                        }
                    })
    
    # ========== Sell Point 2 (第二类卖点) ==========
    # 缠论定义：sell1 确认后，反弹回到中枢内或中枢边界，不过前高
    # 条件：
    #   1. sell1 已确认
    #   2. 反弹进入中枢区间 (或接近中枢)
    #   3. 不过 sell1 高点
    if len(top_fractals) >= 2 and current_trend == 'down':
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]
        
        # 条件 1: 不过前高
        if last_high.price < prev_high.price:
            # 条件 2: sell1 已确认
            if sell1_confirmed(fractals, macd_data):
                # 条件 3: 回测中枢 (价格回到中枢内或接近中枢)
                center_pullback = False
                if last_center:
                    # 价格在中枢区间内，或在中枢上沿附近 (1% 容差)
                    if last_center.contains(current_price) or \
                       abs(current_price - last_center.zg) / last_center.zg < 0.01:
                        center_pullback = True
                elif len(top_fractals) >= 2:
                    # 无中枢时，只要是 sell1 后的反弹即可
                    center_pullback = True
                
                if center_pullback:
                    distance = (last_high.price - current_price) / last_high.price
                    # 添加最小距离过滤，避免太近触发
                    if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                        signals.append({
                            'type': 'sell2',
                            'name': f'{level}级别第二类卖点',
                            'price': current_price,
                            'confidence': 'medium',
                            'description': f'反弹不过前高 {prev_high.price:.2f}, 当前价 {current_price:.2f}',
                            'sell1_confirmed': True,
                            'center_pullback': center_pullback,
                            # 详细触发依据
                            'trigger_details': {
                                'condition': '反弹不过前高 + 回测中枢',
                                'last_high': last_high.price,
                                'prev_high': prev_high.price,
                                'distance': f'{distance*100:.2f}%',
                                'trend': '下跌趋势中的反弹',
                                'sell1_status': '已确认',
                                'center_status': f'回测中枢 (ZG={last_center.zg:.2f})' if last_center else '无中枢'
                            },
                            'data': {
                                'prices': prices,
                                'volumes': volumes,
                                'macd_data': macd_data,
                                'last_high_idx': last_high.kline_index,
                                'prev_high_idx': prev_high.kline_index
                            }
                        })
    
    # ========== 信号互斥检查（关键修复）==========
    # 缠论原理：同一级别同一时间只能有一个主导趋势
    # 如果同时出现买卖点，只保留置信度更高的信号
    buy_signals = [s for s in signals if s['type'].startswith('buy')]
    sell_signals = [s for s in signals if s['type'].startswith('sell')]
    
    if buy_signals and sell_signals:
        # 计算各自信号强度
        buy_confidence = sum(1 if s['confidence'] == 'high' else 0.5 for s in buy_signals)
        sell_confidence = sum(1 if s['confidence'] == 'high' else 0.5 for s in sell_signals)
        
        # 只保留更强的一方
        if buy_confidence >= sell_confidence:
            signals = buy_signals
        else:
            signals = sell_signals
        
        print(f"    ⚠️ 买卖点冲突检测：保留 {'买点' if buy_confidence >= sell_confidence else '卖点'} (买:{buy_confidence:.1f} vs 卖:{sell_confidence:.1f})")
    
    return signals


def load_alert_state():
    """Load alert state from file (价格变化和去重状态)"""
    if os.path.exists(ALERT_STATE_FILE):
        try:
            with open(ALERT_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"alerts": {}}


def save_alert_state(state):
    """Save alert state to file"""
    try:
        with open(ALERT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        print(f"⚠️ Failed to save alert state: {e}")


def should_send_alert(symbol: str, signal_type: str, level: str, current_price: float) -> bool:
    """
    Check if alert should be sent (防重复警报检查)
    
    Returns True if:
    - First alert for this signal
    - Price changed significantly (> MIN_PRICE_CHANGE)
    - Silence period has passed
    """
    state = load_alert_state()
    now = datetime.now()
    
    # Create unique key for this signal
    key = f"{symbol}:{signal_type}:{level}"
    
    if key in state["alerts"]:
        last_alert = state["alerts"][key]
        last_price = last_alert.get("price", 0)
        last_time = datetime.fromisoformat(last_alert["time"])
        
        # Check price change
        price_change = abs(current_price - last_price) / last_price if last_price > 0 else 0
        if price_change < MIN_PRICE_CHANGE:
            print(f"    ⏭️ Skip: 价格变化 {price_change*100:.2f}% < {MIN_PRICE_CHANGE*100:.1f}% 阈值")
            return False
        
        # Check silence period
        minutes_since = (now - last_time).total_seconds() / 60
        if minutes_since < SILENCE_PERIOD_MINUTES:
            print(f"    ⏭️ Skip: 静默期剩余 {SILENCE_PERIOD_MINUTES - minutes_since:.0f} 分钟")
            return False
        
        print(f"    ✅ 价格变化 {price_change*100:.2f}% > {MIN_PRICE_CHANGE*100:.1f}%，允许警报")
    
    return True


def update_alert_state(symbol: str, signal_type: str, level: str, price: float):
    """Update alert state after sending"""
    state = load_alert_state()
    key = f"{symbol}:{signal_type}:{level}"
    
    state["alerts"][key] = {
        "price": price,
        "time": datetime.now().isoformat(),
        "symbol": symbol,
        "signal_type": signal_type,
        "level": level
    }
    
    # Cleanup old alerts (older than 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    keys_to_remove = []
    for k, v in state["alerts"].items():
        try:
            alert_time = datetime.fromisoformat(v["time"])
            if alert_time < cutoff:
                keys_to_remove.append(k)
        except:
            pass
    
    for k in keys_to_remove:
        del state["alerts"][k]
    
    save_alert_state(state)


def calculate_comprehensive_confidence(symbol: str, signal: dict, level: str, all_macd_data: dict = None,
                                        centers: list = None, segments: list = None) -> dict:
    """
    Calculate comprehensive confidence for a signal (v6.0 with center momentum)
    计算信号的综合可信度 (v6.0 整合中枢动量)
    
    整合：
    1. 缠论价格结构 (基础)
    2. 成交量确认 (背驰段缩量/确认段放量)
    3. MACD 多维度分析 (零轴 + 面积 + 共振)
    4. 多级别确认
    5. 外部因子 (可选)
    6. 中枢动量 (v6.0 新增)
    
    Args:
        symbol: 股票代码
        signal: 买卖点信号字典
        level: 级别 (5m, 30m, 1d)
        all_macd_data: 各级别 MACD 数据 {'1d': [...], '30m': [...], '5m': [...]}
        centers: 中枢列表 (v6.0 新增)
        segments: 线段列表 (v6.0 新增)
    
    Returns:
        综合可信度结果字典 (含中枢动量信息)
    """
    try:
        calculator = ComprehensiveConfidenceCalculator()
        
        # 提取信号数据
        prices = signal.get('data', {}).get('prices', [])
        volumes = signal.get('data', {}).get('volumes', [])
        macd_data = signal.get('data', {}).get('macd_data', [])
        
        if not prices or len(prices) < 30:
            # 数据不足，返回默认结果
            return {
                'final_confidence': 0.5,
                'reliability_level': 'medium',
                'operation_suggestion': 'observe',
                'breakdown': {},
                'analysis_summary': '数据不足，无法计算综合可信度'
            }
        
        # 获取背驰段/确认段索引
        data = signal.get('data', {})
        div_start = data.get('prev_low_idx', data.get('prev_high_idx', None))
        div_end = data.get('last_low_idx', data.get('last_high_idx', None))
        
        # 计算综合可信度 (v6.0: 添加 centers 和 segments 参数)
        result = calculator.calculate(
            symbol=symbol,
            signal_type=signal['type'].split()[0],  # buy1, buy2, etc.
            level=level,
            price=signal['price'],
            prices=prices,
            volumes=volumes,
            macd_data=macd_data,
            chanlun_base_confidence=0.65 if signal['confidence'] == 'high' else 0.55,
            divergence_start_idx=div_start,
            divergence_end_idx=div_end,
            macd_1d=all_macd_data.get('1d') if all_macd_data else None,
            macd_30m=all_macd_data.get('30m') if all_macd_data else None,
            macd_5m=all_macd_data.get('5m') if all_macd_data else None,
            multi_level_confirmed=signal.get('resonance') == 'multi_level_confirmed',
            multi_level_count=2 if signal.get('resonance') == 'multi_level_confirmed' else 1,
            centers=centers,      # v6.0 新增
            segments=segments     # v6.0 新增
        )
        
        # v6.0: 构建返回结果 (含中枢动量信息)
        return_dict = {
            'final_confidence': result.final_confidence,
            'reliability_level': result.reliability_level.value,
            'operation_suggestion': result.operation_suggestion.value,
            'breakdown': result.breakdown,
            'analysis_summary': result.analysis_summary,
            'volume_verified': result.factors.volume_verified,
            'volume_reliability': result.factors.volume_reliability,
            'macd_divergence': result.factors.macd_divergence,
            'macd_reliability': result.factors.macd_reliability,
            'macd_zero_axis': result.factors.macd_zero_axis,
            'macd_resonance': result.factors.macd_resonance,
        }
        
        # v6.0 新增：中枢动量信息
        if hasattr(result.factors, 'center_momentum_adjustment'):
            return_dict['center_momentum'] = {
                'adjustment': result.factors.center_momentum_adjustment,
                'center_count': result.factors.center_count,
                'center_position': result.factors.center_position,
                'momentum_status': result.factors.momentum_status,
                'divergence_risk': result.factors.divergence_risk,
            }
        
        return return_dict
        
    except Exception as e:
        print(f"    ⚠️ 综合可信度计算失败：{e}")
        return {
            'final_confidence': 0.5,
            'reliability_level': 'medium',
            'operation_suggestion': 'observe',
            'breakdown': {},
            'analysis_summary': f'计算错误：{e}'
        }


def format_detailed_alert(symbol: str, signal: dict, level: str, confidence_result: dict) -> str:
    """
    Format detailed alert message with trigger reasons and basis
    格式化详细警报信息，包含触发原因和依据
    
    Args:
        symbol: 股票代码
        signal: 买卖点信号
        level: 级别
        confidence_result: 综合可信度结果
    
    Returns:
        格式化后的警报消息
    """
    emoji = {
        'buy1': '🟢',
        'buy2': '🟢',
        'buy3': '🟢',
        'sell1': '🔴',
        'sell2': '🔴',
        'sell3': '🔴'
    }.get(signal['type'].split()[0], '⚪')
    
    # 可靠性徽章
    reliability_badge = {
        'very_high': '✅ 极高可靠性',
        'high': '✅ 高可靠性',
        'medium': '⚠️ 中等可靠性',
        'low': '🔵 低可靠性',
        'very_low': '❌ 极低可靠性'
    }.get(confidence_result.get('reliability_level', 'medium'), '⚠️ 中等可靠性')
    
    # 操作建议
    suggestion = confidence_result.get('operation_suggestion', 'OBSERVE')
    suggestion_display = {
        'STRONG_BUY': '强烈买入 (全仓)',
        'BUY': '买入 (正常仓位)',
        'LIGHT_BUY': '轻仓买入',
        'OBSERVE': '观望',
        'AVOID': '避免',
        'STRONG_SELL': '强烈卖出',
        'SELL': '卖出',
        'LIGHT_SELL': '轻仓卖出'
    }.get(suggestion, '观望')
    
    # 触发详情
    trigger_details = signal.get('trigger_details', {})
    trigger_lines = []
    for key, value in trigger_details.items():
        if isinstance(value, float):
            trigger_lines.append(f"   • {key}: {value:.2f}")
        else:
            trigger_lines.append(f"   • {key}: {value}")
    
    # 成交量状态
    volume_status = ""
    if confidence_result.get('volume_verified'):
        volume_status = f"✅ 成交量确认 ({confidence_result.get('volume_reliability', 'unknown')})"
    else:
        volume_status = "⚪ 成交量未确认"
    
    # MACD 状态
    macd_status = ""
    if confidence_result.get('macd_divergence'):
        macd_status = f"✅ MACD 背驰 ({confidence_result.get('macd_reliability', 'unknown')})"
    if confidence_result.get('macd_zero_axis') != 'unknown':
        macd_status += f"\n   零轴：{confidence_result.get('macd_zero_axis')}"
    if confidence_result.get('macd_resonance') != 'unknown':
        macd_status += f"\n   共振：{confidence_result.get('macd_resonance')}"
    
    # 多级别状态
    resonance_status = signal.get('resonance', 'unknown')
    resonance_badge = ""
    if resonance_status == 'multi_level_confirmed':
        resonance_badge = "\n✅ **多级别共振确认**"
        parent = signal.get('parent_signal', {})
        if parent:
            resonance_badge += f"\n   大级别：{parent.get('level', '1d')} {parent.get('name', '')}"
    elif resonance_status == 'single_level_high_confidence':
        resonance_badge = "\n🎯 高置信度单级别信号"
    
    # v6.0: 中枢动量信息
    center_momentum_text = ""
    if 'center_momentum' in confidence_result:
        cm = confidence_result['center_momentum']
        adj = cm.get('adjustment', 0) * 100
        adj_str = f" ⬆️ +{adj:.0f}%" if adj > 5 else f" ⬇️ {adj:.0f}%" if adj < -5 else ""
        
        divergence_warning = ""
        if cm.get('divergence_risk'):
            divergence_warning = "\n   ⚠️ **背驰风险：高**"
        else:
            divergence_warning = "\n   ✅ 背驰风险：低"
        
        center_momentum_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 中枢分析 (v6.0)
   中枢数量：{cm.get('center_count', 0)}
   当前位置：{cm.get('center_position', 'unknown')}
   动量状态：{cm.get('momentum_status', 'unknown')}{divergence_warning}
   可信度调整：{adj_str if adj_str.strip() else '±0%'}
"""
    
    # 可信度分解
    breakdown = confidence_result.get('breakdown', {})
    breakdown_text = ""
    if breakdown:
        breakdown_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 可信度分解
   缠论基础：{breakdown.get('缠论基础', 0)*100:.0f}%
   成交量：  {breakdown.get('成交量', 0)*100:.0f}%
   MACD:     {breakdown.get('MACD', 0)*100:.0f}%
   多级别：  {breakdown.get('多级别', 0)*100:.0f}%
"""
    
    # 构建消息 (v6.0: 添加中枢分析)
    price_str = f"USD {signal['price']:.2f}"
    
    # v6.0: 显示置信度调整
    conf = confidence_result.get('final_confidence', 0) * 100
    if 'center_momentum' in confidence_result:
        adj = confidence_result['center_momentum'].get('adjustment', 0) * 100
        adj_str = f" ⬆️ +{adj:.0f}%" if adj > 5 else f" ⬇️ {adj:.0f}%" if adj < -5 else ""
        conf_display = f"{conf:.0f}%{adj_str}"
    else:
        conf_display = f"{conf:.0f}%"
    
    message = f"""{emoji} **{symbol} 缠论买卖点提醒**{resonance_badge}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 信号信息
   类型：{signal['name']}
   价格：{price_str}
   级别：{level}

📝 触发原因
{chr(10).join(trigger_lines)}

🔍 验证状态
   {volume_status}
   {macd_status}
{center_momentum_text}
═══════════════════════════════════════
{reliability_badge}
综合置信度：**{conf_display}**
操作建议：{suggestion_display}
═══════════════════════════════════════
{breakdown_text}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 投资有风险，决策需谨慎
"""
    
    return message


def check_multi_level_resonance(symbol: str, levels: list, all_signals: dict) -> list:
    """
    Check for multi-level resonance confirmation
    多级别共振确认检查
    
    只有当大级别 (日线) 和次级别 (30m) 同时出现同向买卖点时才确认
    
    Args:
        symbol: 股票代码
        levels: 监控级别列表 ['1d', '30m']
        all_signals: {level: [signals]} 各级别信号
    
    Returns:
        共振确认的信号列表
    """
    if not ENABLE_RESONANCE_FILTER:
        # 如果未启用过滤，返回所有信号
        result = []
        for level, signals in all_signals.items():
            result.extend(signals)
        return result
    
    resonance_signals = []
    
    # 获取各级别信号
    daily_signals = all_signals.get('1d', []) or all_signals.get('day', [])
    thirty_min_signals = all_signals.get('30m', [])
    
    # 如果没有日线信号，只返回 30m 的高置信度信号
    if not daily_signals:
        for sig in thirty_min_signals:
            # Convert confidence to float for comparison
            conf = sig.get('confidence', 0)
            if isinstance(conf, str):
                try:
                    conf = float(conf.replace('%', '')) / 100.0
                except:
                    conf = 0
            if conf >= RESONANCE_MIN_CONFIDENCE:
                sig['resonance'] = 'single_level_high_confidence'
                resonance_signals.append(sig)
        return resonance_signals
    
    # 检查多级别共振
    for signal_30m in thirty_min_signals:
        signal_type_30m = signal_30m['type'].split()[0]  # buy1, buy2, sell1, sell2
        
        # 查找日线同向信号
        for signal_1d in daily_signals:
            signal_type_1d = signal_1d['type'].split()[0]
            
            # 检查是否同向 (都是买点或都是卖点)
            is_buy = signal_type_30m.startswith('buy') and signal_type_1d.startswith('buy')
            is_sell = signal_type_30m.startswith('sell') and signal_type_1d.startswith('sell')
            
            if is_buy or is_sell:
                # 共振确认！
                signal_30m['resonance'] = 'multi_level_confirmed'
                signal_30m['parent_signal'] = {
                    'level': '1d',
                    'type': signal_type_1d,
                    'name': signal_1d['name'],
                    'price': signal_1d['price']
                }
                # 提升置信度 (处理类型转换)
                confidence = signal_30m.get('confidence', 0.8)
                if isinstance(confidence, str):
                    try:
                        confidence = float(confidence.replace('%', '')) / 100.0
                    except:
                        confidence = 0.8
                signal_30m['confidence'] = max(confidence, 0.85)
                resonance_signals.append(signal_30m)
                print(f"    ✅ 多级别共振确认：1d {signal_type_1d} + 30m {signal_type_30m}")
                break
    
    # 如果没有共振信号，检查是否有高置信度的单级别信号
    if not resonance_signals:
        for sig in thirty_min_signals:
            # Convert confidence to float for comparison
            conf = sig.get('confidence', 0)
            if isinstance(conf, str):
                try:
                    conf = float(conf.replace('%', '')) / 100.0
                except:
                    conf = 0
            if conf >= RESONANCE_MIN_CONFIDENCE:
                sig['resonance'] = 'single_level_high_confidence'
                resonance_signals.append(sig)
    
    return resonance_signals


def send_telegram_alert(symbol: str, signals: list, level: str, all_macd_data: dict = None,
                         centers: list = None, segments: list = None):
    """
    Send Telegram alert via OpenClaw message tool with anti-spam protection
    发送详细警报，包含触发原因和综合可信度分析 (v6.0 含中枢动量)
    """
    if not signals:
        return
    
    for signal in signals:
        # Anti-spam check (防重复警报检查)
        signal_type = signal['type'].replace(' (背驰)', '')  # Normalize type
        if not should_send_alert(symbol, signal_type, level, signal['price']):
            continue
        
        # 计算综合可信度 (v6.0: 传递中枢数据)
        confidence_result = calculate_comprehensive_confidence(
            symbol=symbol,
            signal=signal,
            level=level,
            all_macd_data=all_macd_data,
            centers=centers,      # v6.0 新增
            segments=segments     # v6.0 新增
        )
        
        # 只推送中高可靠性信号
        if confidence_result.get('reliability_level') in ['low', 'very_low']:
            print(f"    ⏭️ 跳过：可靠性 {confidence_result.get('reliability_level')}，置信度 {confidence_result.get('final_confidence', 0)*100:.0f}%")
            continue
        
        # 格式化详细警报
        message = format_detailed_alert(symbol, signal, level, confidence_result)
        
        # Log to file
        price_str = f"USD {signal['price']:.2f}"
        with open(ALERT_LOG, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {signal['type']} @ {price_str} - {confidence_result.get('reliability_level', 'unknown')} ({confidence_result.get('final_confidence', 0)*100:.0f}%)\n")
        
        # Send Telegram message
        try:
            # Escape special characters for shell
            safe_message = message.replace("'", "'\"'\"'").replace('"', '\\"').replace('$', '\\$')
            env = os.environ.copy()
            env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + env.get('PATH', '')
            env.pop('NODE_OPTIONS', None)
            cmd = f"{OPENCLAW_PATH} message send --target 'telegram:{TELEGRAM_CHAT_ID}' -m '{safe_message}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, env=env)
            
            if result.returncode == 0:
                print(f"✅ Telegram alert sent: {symbol} {signal['type']} (可靠性：{confidence_result.get('reliability_level')}, 置信度：{confidence_result.get('final_confidence', 0)*100:.0f}%)")
                # Update state after successful send
                update_alert_state(symbol, signal_type, level, signal['price'])
            else:
                print(f"⚠️ Telegram send failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error sending alert: {e}")


def analyze_symbol(symbol_config):
    """Analyze a single symbol across all levels with multi-level resonance filter"""
    symbol = symbol_config['symbol']
    name = symbol_config['name']
    levels = symbol_config['levels']
    
    print(f"\n{'='*60}")
    print(f"📊 {symbol} ({name})")
    print(f"{'='*60}")
    
    # Store signals by level for resonance check
    signals_by_level = {}
    all_signals_raw = []
    all_macd_data = {}  # 存储各级别 MACD 数据用于综合分析
    
    for level in levels:
        print(f"\n  [{level}] Analyzing...")
        
        # Fetch data
        series = fetch_yahoo_data(symbol, level, count=100)
        if series is None:
            print(f"    ❌ No data")
            continue
        
        # Detect fractals
        fractal_det = FractalDetector()
        fractals = fractal_det.detect_all(series)
        top_fractals = [f for f in fractals if f.is_top]
        bottom_fractals = [f for f in fractals if not f.is_top]
        
        # Detect pens
        pen_calc = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        pens = pen_calc.identify_pens(series)
        
        # Detect segments
        seg_calc = SegmentCalculator(min_pens=3)
        segments = seg_calc.detect_segments(pens)
        
        # v6.0: Detect centers (中枢检测)
        center_det = CenterDetector(min_segments=3)
        centers = center_det.detect_centers(segments)
        
        # Calculate MACD
        prices = [k.close for k in series.klines]
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        macd_data = macd.calculate(prices)
        
        # 存储 MACD 数据用于综合分析
        level_key = '1d' if level in ['1d', 'day'] else '30m' if level == '30m' else '5m'
        all_macd_data[level_key] = macd_data
        
        # Detect buy/sell points
        signals = detect_buy_sell_points(series, fractals, pens, segments, macd_data, level)
        
        # v6.0: 打印中枢信息
        if centers:
            print(f"    中枢：{len(centers)} 个")
            for i, c in enumerate(centers):
                print(f"      中枢{i+1}: ZG={c.zg:.2f}, ZD={c.zd:.2f}")
        
        print(f"    分型：{len(fractals)} (顶：{len(top_fractals)}, 底：{len(bottom_fractals)})")
        print(f"    笔：{len(pens)}")
        print(f"    线段：{len(segments)}")
        print(f"    买卖点：{len(signals)}")
        
        signals_by_level[level] = signals
        all_signals_raw.extend(signals)
        
        if signals:
            for sig in signals:
                print(f"      🎯 {sig['type']}: {sig['name']} @ ${sig['price']:.2f}")
    
    # Apply multi-level resonance filter
    resonance_signals = check_multi_level_resonance(symbol, levels, signals_by_level)
    
    print(f"\n    📡 原始信号：{len(all_signals_raw)} 条")
    print(f"    ✅ 共振过滤后：{len(resonance_signals)} 条")
    
    # Send alerts only for resonance-confirmed signals with comprehensive confidence
    # v6.0: 传递中枢数据 (使用主要级别的中枢)
    if resonance_signals:
        # 使用第一个级别的中枢数据 (通常是日线或 30 分钟)
        primary_level = levels[0]
        primary_centers = signals_by_level.get(primary_level, [{}])[0].get('centers', []) if signals_by_level.get(primary_level) else []
        primary_segments = segments  # 使用当前级别的线段
        
        send_telegram_alert(
            symbol=symbol,
            signals=resonance_signals,
            level=levels[0],
            all_macd_data=all_macd_data,
            centers=primary_centers if primary_centers else centers,
            segments=primary_segments
        )
    else:
        print(f"    ⏭️ 无共振确认信号，跳过警报")
    
    return resonance_signals


def main():
    """Main monitoring loop"""
    print(f"\n{'='*70}")
    print(f"缠论智能监控系统 - ChanLun Invester")
    print(f"{'='*70}")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控标的：{len(SYMBOLS)}")
    print(f"Telegram: {TELEGRAM_CHAT_ID}")
    print(f"{'='*70}")
    
    total_signals = 0
    
    for symbol_config in SYMBOLS:
        signals = analyze_symbol(symbol_config)
        total_signals += len(signals)
    
    print(f"\n{'='*70}")
    print(f"监控完成")
    print(f"{'='*70}")
    print(f"总信号数：{total_signals}")
    print(f"日志文件：{ALERT_LOG}")
    print(f"下次检查：15 分钟后")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
