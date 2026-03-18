#!/usr/bin/env python3
"""
UVIX 缠论自动监控系统
实时检测买卖点并立即发送 Telegram 预警
使用 chanlunInvester 项目核心功能
GitHub: https://github.com/weisenchen/chanlunInvester
"""

import sys
import json
import time
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
CONFIG = {
    'symbol': 'UVIX',
    'timeframe': '5m',
    'check_interval_minutes': 5,  # 每 5 分钟检查一次
    'trading_hours': {
        'start': 9,  # 美东时间 9:30
        'end': 16    # 美东时间 16:00
    },
    'alert_channels': ['telegram', 'console', 'file'],
    'min_confidence': 0.7,  # 最小置信度 70%
}


def fetch_data(symbol='UVIX', timeframe='5m', count=100):
    """获取实时数据"""
    ticker = yf.Ticker(symbol)
    
    if timeframe == '5m':
        history = ticker.history(period='5d', interval='5m')
    elif timeframe == '30m':
        history = ticker.history(period='1mo', interval='30m')
    else:
        history = ticker.history(period='3mo', interval='1d')
    
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
        'bottom': len([f for f in fractals if not f.is_top])
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
        'down': len([p for p in pens if p.is_down])
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
    
    # 4. 背驰
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


def send_telegram_alert(message):
    """发送 Telegram 预警"""
    try:
        # 使用 OpenClaw message 工具
        import subprocess
        
        result = subprocess.run(
            ['openclaw', 'message', 'send',
             '-t', 'telegram',
             '-m', message],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"    ✓ Telegram 预警已发送")
            return True
        else:
            print(f"    ✗ Telegram 发送失败：{result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"    ✗ Telegram 异常：{e}")
        return False


def send_console_alert(message):
    """发送控制台预警"""
    print("\n" + "="*70)
    print(message)
    print("="*70 + "\n")


def save_alert_to_file(message):
    """保存预警到文件"""
    log_file = Path(__file__).parent.parent / 'logs' / 'uvix_auto_alerts.log'
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"{message}\n")


def format_alert_message(results, current_price):
    """格式化预警消息"""
    bsp = results['buy_sell_points'][0]
    divergence = results['divergence']
    
    emoji = "🟢" if 'buy' in bsp['type_en'] else "🔴"
    action = "买入" if 'buy' in bsp['type_en'] else "卖出"
    
    if 'buy' in bsp['type_en']:
        stop_price = bsp['price'] * 0.97
        target1 = bsp['price'] * 1.03
        target2 = bsp['price'] * 1.05
    else:
        stop_price = bsp['price'] * 1.03
        target1 = bsp['price'] * 0.97
        target2 = bsp['price'] * 0.95
    
    message = f"""
{emoji} **UVIX 缠论买卖点预警** {emoji}

📊 标的：UVIX
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST
🔧 系统：chanlunInvester v1.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **{action}信号** - {bsp['type']}

💰 入场：${bsp['price']:.2f}
📈 置信度：{bsp['confidence']:.0%}
📝 类型：{divergence['type']}
📊 背驰强度：{divergence['strength']:.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **交易计划**

入场价：${bsp['price']:.2f}
止损价：${stop_price:.2f} ({'+3%' if 'sell' in bsp['type_en'] else '-3%'})
目标 1:  ${target1:.2f} ({'+3%' if 'buy' in bsp['type_en'] else '-3%'})
目标 2:  ${target2:.2f} ({'+5%' if 'buy' in bsp['type_en'] else '-5%'})

风险收益比：1:1.7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 **缠论分析**

分型：顶{results['fractals']['top']}个 / 底{results['fractals']['bottom']}个
笔：上{results['pens']['up']}个 / 下{results['pens']['down']}个
线段：上{results['segments']['up']}个 / 下{results['segments']['down']}个

依据：{bsp['lesson']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **风险提示**

• UVIX 是高波动产品 (-2x VIX)
• 严格执行止损
• 每笔交易风险不超过 2%
• 本信号仅供参考，不构成投资建议

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 GitHub: https://github.com/weisenchen/chanlunInvester
"""
    
    return message


def check_and_alert():
    """检查并发送预警"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在检查 UVIX...")
    
    # 获取数据
    series = fetch_data(CONFIG['symbol'], CONFIG['timeframe'])
    current_price = series.klines[-1].close
    
    print(f"    当前价格：${current_price:.2f}")
    
    # 分析
    results = analyze_chanlun(series)
    
    # 检查买卖点
    if results['buy_sell_points']:
        bsp = results['buy_sell_points'][0]
        
        # 检查置信度
        if bsp['confidence'] >= CONFIG['min_confidence']:
            print(f"    🚨 检测到买卖点！置信度：{bsp['confidence']:.0%}")
            
            # 格式化消息
            message = format_alert_message(results, current_price)
            
            # 发送预警
            alerts_sent = []
            
            if 'console' in CONFIG['alert_channels']:
                send_console_alert(message)
                alerts_sent.append('console')
            
            if 'telegram' in CONFIG['alert_channels']:
                if send_telegram_alert(message):
                    alerts_sent.append('telegram')
            
            if 'file' in CONFIG['alert_channels']:
                save_alert_to_file(message)
                alerts_sent.append('file')
            
            print(f"    ✓ 预警已发送到：{', '.join(alerts_sent)}")
            
            return True
    
    print(f"    ✓ 无买卖点信号")
    return False


def is_trading_hours():
    """检查是否在交易时段"""
    now = datetime.now()
    
    # 检查是否是工作日
    if now.weekday() >= 5:  # 周末
        return False
    
    # 检查时间 (美东时间)
    hour = now.hour
    minute = now.minute
    time_value = hour + minute / 60.0
    
    return CONFIG['trading_hours']['start'] <= time_value <= CONFIG['trading_hours']['end']


def main():
    """主循环"""
    print("\n" + "="*70)
    print("🚀 UVIX 缠论自动监控系统")
    print("🔧 Powered by chanlunInvester")
    print("="*70)
    print(f"\n⏰ 检查间隔：{CONFIG['check_interval_minutes']}分钟")
    print(f"📊 监控级别：{CONFIG['timeframe']}")
    print(f"🔔 预警渠道：{', '.join(CONFIG['alert_channels'])}")
    print(f"📈 最小置信度：{CONFIG['min_confidence']:.0%}")
    print(f"\nℹ️  按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            # 检查是否交易时段
            if is_trading_hours():
                # 检查买卖点
                check_and_alert()
            else:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 非交易时段，跳过检查")
            
            # 等待
            print(f"\n⏳ 等待 {CONFIG['check_interval_minutes']} 分钟...")
            time.sleep(CONFIG['check_interval_minutes'] * 60)
            
    except KeyboardInterrupt:
        print(f"\n\n✓ 监控已停止")
        sys.exit(0)


if __name__ == '__main__':
    main()
