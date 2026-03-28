#!/usr/bin/env python3
"""
缠论市场周报
每周一早上 8 点自动生成和推送市场热点报告
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system.weekly_analysis import WeeklyDailyAnalyzer
from trading_system import send_alert

# 核心股票池
CORE_STOCKS = [
    # AI/芯片
    'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM',
    # 科技巨头
    'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN',
    # AI 应用
    'TSLA', 'PLTR', 'SNOW', 'CRM',
    # ETF
    'QQQ', 'SPY', 'SOXX', 'SMH'
]

def generate_weekly_report():
    """生成周报"""
    
    print(f"🔍 生成缠论市场周报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyzer = WeeklyDailyAnalyzer()
    
    # 扫描股票
    print(f"\n📈 扫描 {len(CORE_STOCKS)} 只核心股票...")
    
    all_stocks = []
    for symbol in CORE_STOCKS:
        result = analyzer.analyze_stock(symbol)
        if result:
            all_stocks.append(result)
    
    # 排序
    all_stocks.sort(key=lambda x: x.combined_score, reverse=True)
    
    # 分类
    strong_buys = [s for s in all_stocks if s.combined_score >= 6.0]
    buys = [s for s in all_stocks if 4.0 <= s.combined_score < 6.0]
    holds = [s for s in all_stocks if -4.0 < s.combined_score < 4.0]
    sells = [s for s in all_stocks if s.combined_score <= -4.0]
    
    # 生成报告消息
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    message = f"""
📊 **缠论市场周报**

📅 日期：{date_str}
⏰ 时间：{datetime.now().strftime('%H:%M:%S')} EST
🔍 扫描股票：{len(all_stocks)}只

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # 强烈推荐
    if strong_buys:
        message += f"\n🟢🟢 **强烈推荐 ({len(strong_buys)}只)**\n\n"
        
        for i, stock in enumerate(strong_buys[:5], 1):
            message += f"{i}️⃣ **{stock.symbol}** (${stock.price:.2f})\n"
            message += f"   综合评分：{stock.combined_score:+.1f}\n"
            message += f"   周线：{stock.weekly_signal} ({stock.weekly_strength:+.1f})\n"
            message += f"   日线：{stock.daily_signal} ({stock.daily_strength:+.1f})\n"
            
            # 关键信号
            for reason in stock.reasoning[:2]:
                if '背驰' in reason or '买点' in reason:
                    message += f"   • {reason}\n"
            
            message += f"   入场：${stock.entry_price:.2f} | 止损：${stock.stop_loss:.2f} | 目标：${stock.target_price:.2f}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    else:
        message += "\n⚪ 暂无强烈推荐 (综合评分≥6.0)\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 买入机会
    if buys:
        message += f"\n🟢 **买入机会 ({len(buys)}只)**\n\n"
        
        for stock in buys[:5]:
            message += f"• {stock.symbol} @ ${stock.price:.2f} (综合:{stock.combined_score:+.1f})\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 板块总结
    message += "\n📊 **板块热度**\n\n"
    
    # 按板块统计
    sectors = {}
    for stock in all_stocks:
        if stock.sector not in sectors:
            sectors[stock.sector] = []
        sectors[stock.sector].append(stock)
    
    for sector_name, stocks in sectors.items():
        avg_score = sum(s.combined_score for s in stocks) / len(stocks)
        strong_count = len([s for s in stocks if s.combined_score >= 6.0])
        
        if avg_score >= 4.0:
            emoji = '🟢'
        elif avg_score >= 0:
            emoji = '⚪'
        else:
            emoji = '🔴'
        
        message += f"{emoji} **{sector_name}**: {len(stocks)}只 | 平均:{avg_score:+.1f} | 强烈推荐:{strong_count}只\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 操作建议
    message += "\n💡 **操作建议**\n\n"
    
    if strong_buys:
        message += "**激进型:** 关注强烈推荐股票\n"
        for stock in strong_buys[:3]:
            message += f"  • {stock.symbol} @ ${stock.price:.2f}\n"
        message += "\n"
    
    if buys:
        message += "**稳健型:** 关注买入机会\n"
        for stock in buys[:3]:
            message += f"  • {stock.symbol} @ ${stock.price:.2f}\n"
        message += "\n"
    
    message += "**保守型:** 关注 ETF (QQQ, SPY)\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # 风险提示
    message += """
⚠️ **风险提示**

• 缠论分析提高胜率，但不保证盈利
• 周线 + 日线共振信号更可靠
• 严格执行止损，每笔交易风险≤2%
• 综合评分≥6.0 为强烈推荐，≥4.0 为买入

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 完整报告：trading-system/logs/
🔄 下次推送：下周一 8:00 AM
"""
    
    # 发送 Telegram
    print(f"\n📱 发送 Telegram 周报...")
    try:
        send_alert(message, chat_id='default')
        print(f"✅ 周报已发送")
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        # 保存到文件
        log_file = Path(__file__).parent.parent / 'logs' / 'weekly_reports.log'
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Date: {date_str}\n")
            f.write(f"Status: Failed to send\n")
            f.write(f"Error: {e}\n")
    
    # 保存 JSON
    import json
    
    result_data = {
        'date': date_str,
        'timestamp': datetime.now().isoformat(),
        'total_scanned': len(all_stocks),
        'strong_buy_count': len(strong_buys),
        'buy_count': len(buys),
        'hold_count': len(holds),
        'sell_count': len(sells),
        'top_recommendations': [
            {
                'symbol': s.symbol,
                'price': s.price,
                'combined_score': s.combined_score,
                'weekly_signal': s.weekly_signal,
                'daily_signal': s.daily_signal
            }
            for s in strong_buys[:10]
        ]
    }
    
    result_file = Path(__file__).parent.parent / 'logs' / f'weekly_report_{date_str}.json'
    result_file.parent.mkdir(exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"📝 结果已保存：{result_file}")
    print(f"\n✅ 周报生成完成")
    print(f"   强烈推荐：{len(strong_buys)}只")
    print(f"   买入机会：{len(buys)}只")
    print(f"   观望：{len(holds)}只")

if __name__ == '__main__':
    generate_weekly_report()
