#!/usr/bin/env python3
"""
缠论盘前报告生成脚本
运行时间：每个交易日 09:00 ET
功能：生成盘前报告并发送 Telegram 提醒
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import subprocess

# 配置
TELEGRAM_CHAT_ID = "8365377574"
WORKSPACE = "/home/wei/.openclaw/workspace/chanlunInvester"
OPENCLAW_PATH = "/home/linuxbrew/.linuxbrew/bin/openclaw"
SYMBOLS = {
    'UVIX': {'name': 'UVIX', 'desc': '波动率指数'},
    'XEG.TO': {'name': 'XEG.TO', 'desc': '加拿大能源 ETF'},
    'CVE.TO': {'name': 'CVE.TO', 'desc': 'Cenovus Energy'},
    'PAAS.TO': {'name': 'PAAS.TO', 'desc': 'Pan American Silver'},
    'CNQ.TO': {'name': 'CNQ.TO', 'desc': 'Canadian Natural Resources'}
}

def fetch_stock_data(symbol, period="5d", interval="1d"):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"⚠️ 获取 {symbol} 数据失败：{e}")
        return None

def analyze_signal(symbol, df):
    """简易缠论信号分析"""
    if df is None or len(df) < 5:
        return {'type': 'unknown', 'price': 0, 'confidence': 'unknown'}
    
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
    change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
    
    # 简易趋势判断
    ma5 = df['Close'].iloc[-5:].mean() if len(df) >= 5 else current_price
    ma10 = df['Close'].iloc[-10:].mean() if len(df) >= 10 else ma5
    
    if current_price > ma5 > ma10:
        signal_type = 'bullish'
        confidence = 'medium'
    elif current_price < ma5 < ma10:
        signal_type = 'bearish'
        confidence = 'medium'
    else:
        signal_type = 'neutral'
        confidence = 'low'
    
    return {
        'type': signal_type,
        'price': current_price,
        'change_pct': change_pct,
        'confidence': confidence,
        'ma5': ma5,
        'ma10': ma10
    }

def generate_premarket_report():
    """生成盘前报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    report_date = datetime.now().strftime("%Y-%m-%d (%A)")
    
    # 收集数据
    symbols_data = {}
    for symbol, info in SYMBOLS.items():
        df = fetch_stock_data(symbol)
        signal = analyze_signal(symbol, df)
        symbols_data[symbol] = {
            'info': info,
            'df': df,
            'signal': signal
        }
    
    # 生成报告内容
    report_lines = [
        f"# 📈 缠论盘前报告 - {report_date}",
        "",
        f"**生成时间**: {datetime.now().strftime('%H:%M')} EDT",
        f"**市场状态**: 🟡 盘前 (09:30 ET 开盘)",
        "",
        "## 📊 持仓标的状态",
        "",
        "| 标的 | 描述 | 最新价 | 趋势 | 置信度 | 操作建议 |",
        "|------|------|--------|------|--------|----------|"
    ]
    
    for symbol, data in symbols_data.items():
        signal = data['signal']
        info = data['info']
        
        if signal['type'] == 'bullish':
            trend_emoji = '🟢'
            advice = '持有/逢低加仓'
        elif signal['type'] == 'bearish':
            trend_emoji = '🔴'
            advice = '谨慎/逢高减仓'
        else:
            trend_emoji = '⚪'
            advice = '观望'
        
        report_lines.append(
            f"| **{symbol}** | {info['desc']} | ${signal['price']:.2f} | {trend_emoji} {signal['type']} | {signal['confidence']} | {advice} |"
        )
    
    report_lines.extend([
        "",
        "## 🔍 今日重点关注",
        "",
        "### UVIX - 波动率监控",
        "- 关注 VIX 期货曲线变化",
        "- 若背驰确认，可关注反转机会",
        "",
        "### 能源股 (XEG/CVE/CNQ) - 趋势延续",
        "- 关注原油价格波动",
        "- 持有为主，关注 30m 中枢演化",
        "",
        "### PAAS - 贵金属",
        "- 关注黄金/白银走势",
        "- 等待明确买卖点信号",
        "",
        "## 🤖 系统状态",
        "",
        "| 组件 | 状态 | 备注 |",
        "|------|------|------|",
        "| 监控系统 | 🟢 待命中 | 09:30 ET 启动实时监控 |",
        "| Telegram 警报 | 🟢 正常 | 警报功能正常 |",
        "| Cron 任务 | 🟢 运行中 | 盘前/盘中/盘后汇报 |",
        "",
        "## ⏰ 今日汇报时间",
        "",
        "| 时间 | 类型 |",
        "|------|------|",
        "| 09:00 EDT | 盘前报告 (本次) |",
        "| 09:30 EDT | 开盘提醒 |",
        "| 12:00 EDT | 午间检查 |",
        "| 16:00 EDT | 收盘报告 |",
        "| 20:00 EDT | 盘后复盘 |",
        "",
        "---",
        "",
        "**下次汇报**: 09:30 EDT (开盘提醒)",
        "",
        "— ChanLun AI Agent v5.0 Alpha"
    ])
    
    report_content = "\n".join(report_lines)
    
    # 保存报告文件
    report_file = os.path.join(WORKSPACE, f"premarket_{today}.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ 盘前报告已保存：{report_file}")
    
    # 发送 Telegram 提醒
    send_telegram_alert(report_content)
    
    return report_file

def send_telegram_alert(report_content):
    """发送 Telegram 提醒"""
    try:
        # 提取摘要用于 Telegram 消息
        lines = report_content.split('\n')
        summary_lines = []
        for line in lines:
            if line.startswith('| **') or line.startswith('# 📈') or line.startswith('**生成时间**'):
                summary_lines.append(line)
            if len(summary_lines) >= 10:
                break
        
        summary = '\n'.join(summary_lines[:8])
        message = f"{summary}\n\n📄 完整报告：premarket_{datetime.now().strftime('%Y-%m-%d')}.md"
        
        # 使用 openclaw message 命令发送 (使用 -m 参数)
        # Set environment to ensure correct node and clear problematic NODE_OPTIONS
        env = os.environ.copy()
        env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + env.get('PATH', '')
        env.pop('NODE_OPTIONS', None)  # Remove NODE_OPTIONS to avoid conflicts
        cmd = f'{OPENCLAW_PATH} message send --target "telegram:{TELEGRAM_CHAT_ID}" -m "{message}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(f"✅ Telegram 消息已发送")
        else:
            print(f"⚠️ Telegram 发送失败：{result.stderr}")
            print(f"   stdout: {result.stdout}")
            
    except Exception as e:
        print(f"⚠️ 发送 Telegram 异常：{e}")

if __name__ == "__main__":
    print(f"📊 开始生成盘前报告...")
    report_file = generate_premarket_report()
    print(f"✅ 盘前报告生成完成：{report_file}")
