#!/usr/bin/env python3
"""
ChanLun Invester v7.0 - Real-time Monitor with Telegram Alerts
缠论智能监控系统 v7.0 - Telegram 预警

基于趋势段识别和中枢周期分析的多级别监控
支持：周线 (长线) | 日线 (中长线) | 30m (短线)
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add python-layer to path
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

# Import v7.0 components
from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator
from trading_system.center import CenterDetector
from trading_system.trend_segment import identify_trend_segments
from trading_system.center_cycle import CenterCycleAnalyzer, evaluate_cycle_divergence_risk

# Import volume/MACD confirmation
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from volume_confirmation import VolumeConfirmation
from macd_advanced_analysis import MACDAdvancedAnalyzer
from confidence_calculator import ComprehensiveConfidenceCalculator

# Configuration
TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
OPENCLAW_PATH = "/home/linuxbrew/.linuxbrew/bin/openclaw"
ALERT_STATE_FILE = "/home/wei/.openclaw/workspace/chanlunInvester/.alert_state.json"

# Anti-spam settings
MIN_PRICE_CHANGE = 0.003
SILENCE_PERIOD_MINUTES = 60

# Symbols to monitor
SYMBOLS = [
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'levels': ['1d', '30m']},
    {'symbol': 'PAAS.TO', 'name': 'Pan American Silver', 'levels': ['1d', '30m']},
    {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['1d', '30m']},
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d', '30m']},
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'SMR', 'name': 'NuScale Power Corporation (美股)', 'levels': ['1w', '1d', '30m']},
    {'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1w', '1d', '30m']},
    {'symbol': 'TSLA', 'name': 'Tesla Inc (美股/电动车)', 'levels': ['1w', '1d', '30m']},
    {'symbol': 'OKLO', 'name': 'Oklo Inc (美股/核能)', 'levels': ['1d', '30m']},
]


def fetch_yahoo_data(symbol: str, timeframe: str = '30m', count: int = 100):
    """Fetch real-time data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        if timeframe in ['1d', 'day']:
            period, interval = '1y', '1d'
        elif timeframe == '1w':
            period, interval = '2y', '1wk'
        elif timeframe == '30m':
            period, interval = '10d', '30m'
        elif timeframe == '5m':
            period, interval = '2d', '5m'
        else:
            period, interval = '10d', '30m'
        
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        
        if len(history) == 0:
            return None
        
        klines = []
        for idx, row in history.iterrows():
            klines.append(Kline(
                timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            ))
        
        return KlineSeries(klines=klines)
        
    except Exception as e:
        print(f"    ❌ Data fetch error: {e}")
        return None


def detect_buy_sell_points_v7(series, fractals, pens, segments, macd_data, level="30m"):
    """
    v7.0 买卖点检测 (保留原有逻辑)
    """
    signals = []
    prices = [k.close for k in series.klines]
    volumes = [k.volume for k in series.klines]
    current_price = prices[-1] if prices else 0
    
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    
    # Simple buy/sell point detection
    if len(bottom_fractals) >= 2:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]
        if last_low.price < prev_low.price:
            signals.append({
                'type': 'buy1',
                'name': f'{level}级别第一类买点 (背驰)',
                'price': current_price,
                'confidence': 'medium',
                'data': {'prices': prices, 'volumes': volumes, 'macd_data': macd_data}
            })
    
    return signals


def analyze_level_v7(series, level: str):
    """
    v7.0 级别分析 (趋势段 + 中枢周期)
    """
    if series is None or len(series.klines) < 30:
        return {'status': 'no_data', 'level': level}
    
    # Detect structure
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    
    seg_calc = SegmentCalculator(min_pens=3)
    segments_raw = seg_calc.detect_segments(pens)
    
    # Convert to dict format for trend_segment module
    segments = []
    for seg in segments_raw:
        segments.append({
            'direction': seg.direction,
            'start_idx': seg.start_idx,
            'end_idx': seg.end_idx,
            'start_price': seg.start_price,
            'end_price': seg.end_price,
            'start_date': series.klines[seg.start_idx].timestamp if seg.start_idx < len(series.klines) else None,
            'end_date': series.klines[min(seg.end_idx, len(series.klines)-1)].timestamp if seg.end_idx < len(series.klines) else None,
        })
    
    # Identify trend segments
    trend_segments = identify_trend_segments(segments)
    
    if not trend_segments:
        return {
            'status': 'no_trend',
            'level': level,
            'segments': len(segments),
        }
    
    # Analyze current trend segment
    cycle_analyzer = CenterCycleAnalyzer()
    current_trend = trend_segments[-1]
    current_cycle = cycle_analyzer.analyze(current_trend)
    current_risk = evaluate_cycle_divergence_risk(current_cycle)
    
    # Rating
    if current_cycle.stage in ['诞生期', '成长期']:
        rating = '买入' if current_cycle.stage == '成长期' else '建仓'
        rating_score = 80 if current_cycle.stage == '成长期' else 70
    elif current_cycle.stage == '成熟期':
        rating = '观望'
        rating_score = 40
    else:  # 衰退期
        rating = '观望'
        rating_score = 50 if current_risk['adjustment'] > -0.1 else 30
    
    prices = [k.close for k in series.klines]
    
    return {
        'status': 'ok',
        'level': level,
        'price': prices[-1],
        'trend': current_trend.trend,
        'cycle': current_cycle,
        'risk': current_risk,
        'rating': rating,
        'rating_score': rating_score,
        'trend_segments': trend_segments,
    }


def get_investment_advice_v7(weekly=None, daily=None, intraday=None):
    """v7.0 投资建议"""
    advice = {
        'long_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
        'medium_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
        'short_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
    }
    
    if weekly and weekly.get('status') == 'ok':
        cycle = weekly['cycle']
        risk = weekly['risk']
        
        if cycle.stage == '成长期':
            advice['long_term'] = {'action': '买入', 'position': '40-60%', 'period': '3-12 个月', 'reason': f"周线成长期 (第{cycle.center_count}中枢)"}
        elif cycle.stage == '诞生期':
            advice['long_term'] = {'action': '建仓', 'position': '30-50%', 'period': '6-12 个月', 'reason': f"周线诞生期 (第{cycle.center_count}中枢)"}
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['long_term'] = {'action': '轻仓', 'position': '10-20%', 'period': '3-6 个月', 'reason': f"周线衰退期 (第{cycle.center_count}中枢)"}
        else:
            advice['long_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"周线{cycle.stage} (第{cycle.center_count}中枢)"}
    
    if daily and daily.get('status') == 'ok':
        cycle = daily['cycle']
        risk = daily['risk']
        
        if cycle.stage == '成长期':
            advice['medium_term'] = {'action': '参与', 'position': '30-50%', 'period': '1-12 周', 'reason': f"日线成长期 (第{cycle.center_count}中枢)"}
        elif cycle.stage == '诞生期':
            advice['medium_term'] = {'action': '试单', 'position': '20-30%', 'period': '2-8 周', 'reason': f"日线诞生期 (第{cycle.center_count}中枢)"}
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['medium_term'] = {'action': '轻仓', 'position': '10-20%', 'period': '1-4 周', 'reason': f"日线衰退期 (第{cycle.center_count}中枢)"}
        else:
            advice['medium_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"日线{cycle.stage} (第{cycle.center_count}中枢)"}
    
    if intraday and intraday.get('status') == 'ok':
        cycle = intraday['cycle']
        
        if cycle.stage == '成长期':
            advice['short_term'] = {'action': '参与', 'position': '20-40%', 'period': '1-10 天', 'reason': f"30m 成长期 (第{cycle.center_count}中枢)"}
        elif cycle.stage == '诞生期':
            advice['short_term'] = {'action': '试单', 'position': '10-30%', 'period': '1-5 天', 'reason': f"30m 诞生期 (第{cycle.center_count}中枢)"}
        else:
            advice['short_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"30m{cycle.stage} (第{cycle.center_count}中枢)"}
    
    return advice


def format_v7_alert(symbol: str, name: str, weekly, daily, intraday, advice):
    """v7.0 警报格式"""
    lines = []
    lines.append(f"📊 **{symbol} ({name})** v7.0 多级别分析")
    lines.append("")
    
    # 各级别状态
    if weekly and weekly.get('status') == 'ok':
        w = weekly
        emoji = "✅" if w['rating'] == '买入' else "⚪"
        lines.append(f"{emoji} **周线级别 (长线 3-12 个月)**")
        lines.append(f"   趋势：{w['trend']} | 周期：{w['cycle'].stage} (第{w['cycle'].center_count}中枢)")
        lines.append(f"   背驰风险：{w['risk']['risk_level']} ({w['risk']['adjustment']*100:+.0f}%)")
        lines.append(f"   建议：{advice['long_term']['action']} {advice['long_term']['position']}")
        lines.append("")
    
    if daily and daily.get('status') == 'ok':
        d = daily
        emoji = "✅" if d['rating'] in ['买入', '参与'] else "⚪"
        lines.append(f"{emoji} **日线级别 (中长线 1-12 周)**")
        lines.append(f"   趋势：{d['trend']} | 周期：{d['cycle'].stage} (第{d['cycle'].center_count}中枢)")
        lines.append(f"   背驰风险：{d['risk']['risk_level']} ({d['risk']['adjustment']*100:+.0f}%)")
        lines.append(f"   建议：{advice['medium_term']['action']} {advice['medium_term']['position']}")
        lines.append("")
    
    if intraday and intraday.get('status') == 'ok':
        i = intraday
        emoji = "✅" if i['rating'] in ['买入', '参与'] else "⚪"
        lines.append(f"{emoji} **30 分钟级别 (短线 1-10 天)**")
        lines.append(f"   趋势：{i['trend']} | 周期：{i['cycle'].stage} (第{i['cycle'].center_count}中枢)")
        lines.append(f"   背驰风险：{i['risk']['risk_level']} ({i['risk']['adjustment']*100:+.0f}%)")
        lines.append(f"   建议：{advice['short_term']['action']} {advice['short_term']['position']}")
        lines.append("")
    
    # 综合评分
    scores = []
    if weekly and weekly.get('status') == 'ok': scores.append(weekly['rating_score'])
    if daily and daily.get('status') == 'ok': scores.append(daily['rating_score'])
    if intraday and intraday.get('status') == 'ok': scores.append(intraday['rating_score'])
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    lines.append("═══════════════════════════════════════")
    lines.append(f"综合评分：{avg_score:.0f}/100")
    lines.append(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("⚠️ 投资有风险，决策需谨慎")
    
    return "\n".join(lines)


def should_send_alert(symbol: str, signal_type: str, level: str, price: float) -> bool:
    """防重复警报检查"""
    try:
        if not os.path.exists(ALERT_STATE_FILE):
            return True
        
        with open(ALERT_STATE_FILE, 'r') as f:
            state = json.load(f)
        
        key = f"{symbol}_{signal_type}_{level}"
        if key in state:
            last_price = state[key]['price']
            last_time = datetime.fromisoformat(state[key]['time'])
            
            price_change = abs(price - last_price) / last_price if last_price > 0 else 0
            time_since = datetime.now() - last_time
            
            if price_change < MIN_PRICE_CHANGE and time_since < timedelta(minutes=SILENCE_PERIOD_MINUTES):
                return False
        
        return True
        
    except Exception:
        return True


def update_alert_state(symbol: str, signal_type: str, level: str, price: float):
    """更新警报状态"""
    try:
        if os.path.exists(ALERT_STATE_FILE):
            with open(ALERT_STATE_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {}
        
        key = f"{symbol}_{signal_type}_{level}"
        state[key] = {
            'price': price,
            'time': datetime.now().isoformat()
        }
        
        with open(ALERT_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
            
    except Exception as e:
        print(f"    ⚠️ State update error: {e}")


def analyze_symbol_v7(symbol_config):
    """v7.0 多级别分析"""
    symbol = symbol_config['symbol']
    name = symbol_config['name']
    levels = symbol_config['levels']
    
    print(f"\n{'='*80}")
    print(f"📊 {symbol} ({name})")
    print(f"{'='*80}")
    
    results = {'weekly': None, 'daily': None, 'intraday': None}
    
    for level in levels:
        print(f"\n  [{level}] Analyzing...")
        
        series = fetch_yahoo_data(symbol, level, count=100)
        if series is None:
            print(f"    ❌ No data")
            continue
        
        result = analyze_level_v7(series, level)
        
        if result['status'] == 'ok':
            print(f"    趋势：{result['trend']} | 周期：{result['cycle'].stage} (第{result['cycle'].center_count}中枢)")
            print(f"    背驰风险：{result['risk']['risk_level']} ({result['risk']['adjustment']*100:+.0f}%)")
            print(f"    评级：{result['rating']} ({result['rating_score']}分)")
        else:
            print(f"    ⚪ {result['status']}")
        
        if level == '1w':
            results['weekly'] = result
        elif level == '1d':
            results['daily'] = result
        elif level in ['30m', '5m']:
            results['intraday'] = result
    
    # 获取投资建议
    advice = get_investment_advice_v7(results['weekly'], results['daily'], results['intraday'])
    
    # 计算综合评分
    scores = []
    if results['weekly'] and results['weekly'].get('status') == 'ok':
        scores.append(results['weekly']['rating_score'])
    if results['daily'] and results['daily'].get('status') == 'ok':
        scores.append(results['daily']['rating_score'])
    if results['intraday'] and results['intraday'].get('status') == 'ok':
        scores.append(results['intraday']['rating_score'])
    
    composite_score = sum(scores) / len(scores) if scores else 0
    
    print(f"\n  综合评分：{composite_score:.0f}/100")
    print(f"  长线：{advice['long_term']['action']} {advice['long_term']['position']}")
    print(f"  中长线：{advice['medium_term']['action']} {advice['medium_term']['position']}")
    print(f"  短线：{advice['short_term']['action']} {advice['short_term']['position']}")
    
    return {
        'symbol': symbol,
        'name': name,
        'results': results,
        'advice': advice,
        'composite_score': composite_score,
    }


def send_v7_alert(symbol: str, name: str, results: dict, advice: dict):
    """发送 v7.0 警报"""
    # 检查是否有买入/参与信号
    has_signal = False
    signal_type = None
    
    if advice['long_term']['action'] in ['买入', '建仓']:
        has_signal = True
        signal_type = 'long_buy'
    elif advice['medium_term']['action'] in ['参与', '试单']:
        has_signal = True
        signal_type = 'medium_buy'
    elif advice['short_term']['action'] in ['参与', '试单']:
        has_signal = True
        signal_type = 'short_buy'
    
    if not has_signal:
        return
    
    # 防重复检查
    price = results['daily']['price'] if results['daily'] and results['daily'].get('status') == 'ok' else 0
    if not should_send_alert(symbol, signal_type, 'v7', price):
        print(f"    ⏭️ 跳过：静默期内")
        return
    
    # 格式化警报
    message = format_v7_alert(symbol, name, results['weekly'], results['daily'], results['intraday'], advice)
    
    # 记录日志
    with open(ALERT_LOG, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {symbol} v7.0 - 综合评分:{results.get('composite_score', 0):.0f}\n")
    
    # 发送 Telegram
    try:
        safe_message = message.replace("'", "'\"'\"'").replace('"', '\\"').replace('$', '\\$')
        env = os.environ.copy()
        env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + env.get('PATH', '')
        cmd = f"{OPENCLAW_PATH} message send --target 'telegram:{TELEGRAM_CHAT_ID}' -m '{safe_message}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, env=env)
        
        if result.returncode == 0:
            print(f"    ✅ Telegram alert sent: {symbol} v7.0")
            update_alert_state(symbol, signal_type, 'v7', price)
        else:
            print(f"    ⚠️ Telegram send failed: {result.stderr}")
            
    except Exception as e:
        print(f"    ❌ Error sending alert: {e}")


def main():
    """Main monitoring loop v7.0"""
    print(f"\n{'='*80}")
    print(f"缠论智能监控系统 v7.0 - ChanLun Invester")
    print(f"{'='*80}")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控标的：{len(SYMBOLS)}")
    print(f"Telegram: {TELEGRAM_CHAT_ID}")
    print(f"分析框架：周线 (长线) | 日线 (中长线) | 30m (短线)")
    print(f"{'='*80}")
    
    total_signals = 0
    
    for symbol_config in SYMBOLS:
        result = analyze_symbol_v7(symbol_config)
        
        # 发送警报 (如果有买入信号)
        send_v7_alert(
            result['symbol'],
            result['name'],
            result['results'],
            result['advice']
        )
    
    print(f"\n{'='*80}")
    print(f"监控完成")
    print(f"{'='*80}")
    print(f"日志文件：{ALERT_LOG}")
    print(f"下次检查：15 分钟后")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
