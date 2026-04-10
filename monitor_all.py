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

# Configuration
TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
OPENCLAW_PATH = "/home/linuxbrew/.linuxbrew/bin/openclaw"
ALERT_STATE_FILE = "/home/wei/.openclaw/workspace/chanlunInvester/.alert_state.json"

# Anti-spam settings (防重复警报设置)
MIN_PRICE_CHANGE = 0.003  # 最小价格变化 0.3% 才触发新警报
SILENCE_PERIOD_MINUTES = 60  # 同一信号静默期 60 分钟

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


def detect_buy_sell_points(series, fractals, pens, segments, macd_data, level="30m"):
    """
    Detect ChanLun buy/sell points
    缠论买卖点检测
    
    修复：添加趋势方向过滤，避免买卖点同时出现（缠论走势类型互斥原理）
    """
    signals = []
    
    if len(fractals) < 4 or len(pens) < 4:
        return signals
    
    # Get recent fractals
    top_fractals = [f for f in fractals if f.is_top][-3:]
    bottom_fractals = [f for f in fractals if not f.is_top][-3:]
    
    current_price = series.klines[-1].close
    
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
    
    # ========== Buy Point 2 (第二类买点) ==========
    # 缠论定义：下跌趋势结束 + 第一类买点确认 + 反弹 + 回调不破前低
    # 关键：当前必须在上涨趋势的回调中（下跌笔）
    if len(bottom_fractals) >= 2 and current_trend == 'up':
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        
        # 回调不破前低（核心条件）
        if last_low.price > prev_low.price:
            distance = (current_price - last_low.price) / last_low.price
            # 添加最小距离过滤，避免太近触发
            if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                signals.append({
                    'type': 'buy2',
                    'name': f'{level}级别第二类买点',
                    'price': current_price,
                    'confidence': 'medium',
                    'description': f'回调不破前低 {prev_low.price:.2f}, 当前价 {current_price:.2f}'
                })
    
    # ========== Buy Point 1 (第一类买点 - 背驰) ==========
    # 价格新低但 MACD 不新低
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
                    signals.append({
                        'type': 'buy1',
                        'name': f'{level}级别第一类买点 (背驰)',
                        'price': current_price,
                        'confidence': 'high' if last_macd > prev_macd * 1.5 else 'medium',
                        'description': f'底背驰：新低 {last_low.price:.2f} vs 前低 {prev_low.price:.2f}'
                    })
    
    # ========== Sell Point 2 (第二类卖点) ==========
    # 缠论定义：上涨趋势结束 + 第一类卖点确认 + 回落 + 反弹不过前高
    # 关键：当前必须在下跌趋势的反弹中（上涨笔）
    if len(top_fractals) >= 2 and current_trend == 'down':
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]
        
        # 反弹不过前高（核心条件）
        if last_high.price < prev_high.price:
            distance = (last_high.price - current_price) / last_high.price
            # 添加最小距离过滤，避免太近触发
            if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                signals.append({
                    'type': 'sell2',
                    'name': f'{level}级别第二类卖点',
                    'price': current_price,
                    'confidence': 'medium',
                    'description': f'反弹不过前高 {prev_high.price:.2f}, 当前价 {current_price:.2f}'
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


def send_telegram_alert(symbol: str, signals: list, level: str):
    """Send Telegram alert via OpenClaw message tool with anti-spam protection"""
    if not signals:
        return
    
    for signal in signals:
        # Anti-spam check (防重复警报检查)
        signal_type = signal['type'].replace(' (背驰)', '')  # Normalize type
        if not should_send_alert(symbol, signal_type, level, signal['price']):
            continue
        
        emoji = {
            'buy1': '🟢',
            'buy2': '🟢',
            'buy3': '🟢',
            'sell1': '🔴',
            'sell2': '🔴',
            'sell3': '🔴'
        }.get(signal['type'].split()[0], '⚪')
        
        # Fix: Use USD prefix instead of $ to avoid shell variable expansion
        price_str = f"USD {signal['price']:.2f}"
        
        message = f"""{emoji} {symbol} 缠论买卖点提醒

📊 信号：{signal['name']}
💰 价格：{price_str}
🎯 置信度：{signal['confidence']}
📝 说明：{signal['description']}

⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
级别：{level}"""
        
        # Log to file
        with open(ALERT_LOG, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {emoji} {symbol} {signal['name']} @ {price_str}\n")
        
        # Send Telegram message
        try:
            safe_message = message.replace("'", "'\"'\"'")
            env = os.environ.copy()
            env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + env.get('PATH', '')
            env.pop('NODE_OPTIONS', None)
            cmd = f"{OPENCLAW_PATH} message send --target 'telegram:{TELEGRAM_CHAT_ID}' -m '{safe_message}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, env=env)
            
            if result.returncode == 0:
                print(f"✅ Telegram alert sent: {symbol} {signal['type']}")
                # Update state after successful send
                update_alert_state(symbol, signal_type, level, signal['price'])
            else:
                print(f"⚠️ Telegram send failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error sending alert: {e}")


def analyze_symbol(symbol_config):
    """Analyze a single symbol across all levels"""
    symbol = symbol_config['symbol']
    name = symbol_config['name']
    levels = symbol_config['levels']
    
    print(f"\n{'='*60}")
    print(f"📊 {symbol} ({name})")
    print(f"{'='*60}")
    
    all_signals = []
    
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
        
        # Calculate MACD
        prices = [k.close for k in series.klines]
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        macd_data = macd.calculate(prices)
        
        # Detect buy/sell points
        signals = detect_buy_sell_points(series, fractals, pens, segments, macd_data, level)
        
        print(f"    分型：{len(fractals)} (顶：{len(top_fractals)}, 底：{len(bottom_fractals)})")
        print(f"    笔：{len(pens)}")
        print(f"    线段：{len(segments)}")
        print(f"    买卖点：{len(signals)}")
        
        if signals:
            for sig in signals:
                print(f"      🎯 {sig['type']}: {sig['name']} @ ${sig['price']:.2f}")
            all_signals.extend(signals)
    
    # Send alerts
    if all_signals:
        send_telegram_alert(symbol, all_signals, levels[0])
    
    return all_signals


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
