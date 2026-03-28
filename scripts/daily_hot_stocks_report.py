#!/usr/bin/env python3
"""
缠论热点股票每日报告
每个交易日早上 9 点自动推送热点股票筛选报告
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system import ChanLunMonitor, send_alert

# 热门股票列表
HOT_STOCKS = [
    # AI/芯片
    'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM',
    # 科技巨头
    'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN',
    # AI 应用
    'TSLA', 'PLTR', 'SNOW', 'CRM', 'ORCL',
    # 半导体设备
    'AMAT', 'LRCX', 'KLAC', 'MU',
    # ETF
    'QQQ', 'SPY', 'SOXX', 'SMH',
]

def is_trading_day():
    """检查是否是交易日"""
    today = datetime.now()
    
    # 周末不交易
    if today.weekday() >= 5:
        return False
    
    # 美国节假日 (简化版)
    us_holidays = [
        (1, 1),    # 元旦
        (1, 20),   # 马丁路德金日
        (2, 17),   # 总统日
        (5, 26),   # 阵亡将士纪念日
        (7, 4),    # 独立日
        (9, 1),    # 劳动节
        (11, 27),  # 感恩节
        (12, 25),  # 圣诞节
    ]
    
    if (today.month, today.day) in us_holidays:
        return False
    
    return True

def scan_and_report():
    """扫描热点股票并生成报告"""
    
    if not is_trading_day():
        print(f"⚪ {datetime.now().strftime('%Y-%m-%d')} 不是交易日，跳过")
        return
    
    print(f"🔍 生成缠论热点股票报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    monitor = ChanLunMonitor()
    strong_buy_list = []
    buy_list = []
    
    # 扫描所有股票
    for symbol in HOT_STOCKS:
        try:
            result = monitor.analyze(symbol, ['1d', '30m', '5m'])
            
            if result:
                if result.strength >= 6.0:
                    strong_buy_list.append({
                        'symbol': symbol,
                        'price': result.current_price,
                        'strength': result.strength,
                        'reasoning': result.reasoning[:3]  # 只保留前 3 个原因
                    })
                elif result.strength >= 4.0:
                    buy_list.append({
                        'symbol': symbol,
                        'price': result.current_price,
                        'strength': result.strength
                    })
        except Exception as e:
            print(f"❌ {symbol} 分析失败：{e}")
    
    # 生成报告消息
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    message = f"""
📊 **缠论热点股票日报**

📅 日期：{date_str}
⏰ 时间：{datetime.now().strftime('%H:%M:%S')} EST
🔍 扫描股票：{len(HOT_STOCKS)}只

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if strong_buy_list:
        message += f"\n🟢🟢 **强烈买入 ({len(strong_buy_list)}只)**\n\n"
        
        # 按强度排序，只显示前 5 只
        top_stocks = sorted(strong_buy_list, key=lambda x: x['strength'], reverse=True)[:5]
        
        for i, stock in enumerate(top_stocks, 1):
            message += f"{i}️⃣ **{stock['symbol']}** (${stock['price']:.2f}) - 强度:{stock['strength']:+.1f}\n"
            
            # 添加关键信号
            for reason in stock['reasoning']:
                if '背驰' in reason or '买点' in reason:
                    message += f"  • {reason}\n"
            
            # 添加简单交易计划
            entry = stock['price']
            stop = entry * 0.97
            target1 = entry * 1.03
            message += f"  入场：${entry:.2f} | 止损：${stop:.2f} | 目标：${target1:.2f}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    else:
        message += "\n⚪ 暂无强烈买入信号 (强度≥6.0)\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if buy_list:
        message += f"\n🟢 **买入机会 ({len(buy_list)}只)**\n\n"
        
        top_buys = sorted(buy_list, key=lambda x: x['strength'], reverse=True)[:5]
        
        for stock in top_buys:
            message += f"• {stock['symbol']} @ ${stock['price']:.2f} (强度:{stock['strength']:+.1f})\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 板块总结
    message += "\n📊 **板块分析**\n\n"
    
    # 按板块分类
    sectors = {
        'AI/芯片': ['NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM', 'AMAT', 'LRCX', 'KLAC', 'MU', 'SMH', 'SOXX'],
        '科技巨头': ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN'],
        'AI 应用': ['TSLA', 'PLTR', 'SNOW', 'CRM', 'ORCL'],
        'ETF': ['QQQ', 'SPY']
    }
    
    for sector_name, sector_stocks in sectors.items():
        sector_signals = [s for s in strong_buy_list if s['symbol'] in sector_stocks]
        if sector_signals:
            avg_strength = sum(s['strength'] for s in sector_signals) / len(sector_signals)
            message += f"• **{sector_name}**: {len(sector_signals)}只强烈买入 (平均强度:{avg_strength:+.1f})\n"
    
    message += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **操作建议**

**激进型:** 关注强度≥8.0 的股票
**稳健型:** 关注 ETF (SPY, QQQ)
**保守型:** 继续观望，等待明确信号

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **风险提示**

• 缠论分析提高胜率，但不保证盈利
• 严格执行止损，每笔交易风险≤2%
• 信号强度≥6.0 为强烈买入
• 多级别共振才交易

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 完整报告：trading-system/scripts/
🔄 下次推送：下一个交易日 9:00 AM
"""
    
    # 发送 Telegram 消息
    print(f"\n📱 发送 Telegram 报告...")
    try:
        send_alert(message, chat_id='default')
        print(f"✅ 报告已发送")
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        # 保存到文件
        log_file = Path(__file__).parent.parent / 'logs' / 'daily_hot_stocks.log'
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Date: {date_str}\n")
            f.write(f"Status: Failed to send\n")
            f.write(f"Error: {e}\n")
            f.write(f"{'='*60}\n")
    
    # 保存 JSON 结果
    result_file = Path(__file__).parent.parent / 'logs' / f'hot_stocks_{date_str}.json'
    result_file.parent.mkdir(exist_ok=True)
    
    result_data = {
        'date': date_str,
        'timestamp': datetime.now().isoformat(),
        'total_scanned': len(HOT_STOCKS),
        'strong_buy_count': len(strong_buy_list),
        'buy_count': len(buy_list),
        'strong_buy_stocks': strong_buy_list,
        'buy_stocks': buy_list
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"📝 结果已保存：{result_file}")
    print(f"\n✅ 日报生成完成")
    print(f"   强烈买入：{len(strong_buy_list)}只")
    print(f"   买入机会：{len(buy_list)}只")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='缠论热点股票每日报告')
    parser.add_argument('--force', action='store_true', help='强制运行 (忽略交易日检查)')
    args = parser.parse_args()
    
    if args.force:
        print('🧪 强制运行测试模式...')
        # 临时覆盖 is_trading_day
        import builtins
        original_is_trading_day = is_trading_day
        is_trading_day = lambda: True
        scan_and_report()
    else:
        scan_and_report()
