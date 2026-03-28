#!/bin/bash
# SQQQ 缠论监控系统 - 5 分钟和 30 分钟级别预警
# 每 5 分钟检查一次，发现买卖点立即发送 Telegram 预警

export PYTHONPATH=/home/wei/.openclaw/workspace/trading-system/python-layer:$PYTHONPATH
export PATH=/home/linuxbrew/.linuxbrew/bin:$PATH

cd /home/wei/.openclaw/workspace/trading-system

echo "🔍 SQQQ 缠论分析 - $(date '+%Y-%m-%d %H:%M:%S')"

# 运行分析
python3 -c "
from trading_system import ChanLunMonitor, send_alert
import json

monitor = ChanLunMonitor()
result = monitor.analyze('SQQQ', ['30m', '5m'])

if not result:
    print('❌ 分析失败')
    exit(1)

print(f'💰 当前价格：\${result.current_price:.2f}')
print(f'🎯 信号：{result.signal}')
print(f'📈 强度：{result.strength:+.1f}')

# 检查是否有交易信号
if abs(result.strength) >= 4.0:
    print(f'🚨 发现交易信号！')
    
    # 生成预警消息
    action = '🟢 买入' if result.strength > 0 else '🔴 卖出'
    
    # 生成交易计划
    plan = monitor.generate_trading_plan(result)
    
    message = f'''
🚨 **SQQQ 缠论买卖点预警**

📊 标的：SQQQ (3x Inverse QQQ)
⏰ 时间：{result.timestamp}
🔧 系统：chanlunInvester v1.1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{action}信号 - {result.signal}

💰 入场：\${result.current_price:.2f}
📈 信号强度：{result.strength:+.1f}
📝 置信度：{'高' if abs(result.strength) >= 6.0 else '中'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **交易计划**

入场价：\${plan[\"entry\"]:.2f}
止损价：\${plan[\"stop_loss\"]:.2f}
目标 1: \${plan[\"target1\"]:.2f}
目标 2: \${plan[\"target2\"]:.2f}
仓位：{plan[\"position_size\"]}
风险收益比：1:{plan[\"risk_reward\"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 **缠论分析**

'''
    
    for reason in result.reasoning:
        message += f'{reason}\\n'
    
    message += '''
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **风险提示**

• SQQQ 是 3x 杠杆 ETF，波动极大
• 严格执行止损，每笔交易风险不超过 2%
• 仅限日内交易，不可长期持有
• 本信号仅供参考，不构成投资建议

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 GitHub: https://github.com/weisenchen/chanlunInvester
'''
    
    # 发送 Telegram 预警
    send_alert(message, chat_id='default')
    print(f'✅ 预警已发送')
    
    # 保存到日志
    with open('logs/sqqq_alerts.log', 'a') as f:
        f.write(f'\\n{\"=\"*60}\\n')
        f.write(f'Time: {result.timestamp}\\n')
        f.write(f'Signal: {result.signal}\\n')
        f.write(f'Strength: {result.strength:+.1f}\\n')
        f.write(f'Price: \${result.current_price:.2f}\\n')
        f.write(f'{message}\\n')
    
else:
    print(f'⚪ 无交易信号 (强度：{result.strength:+.1f})')
    print(f'ℹ️ 需要强度≥4.0 才触发预警')
    
    # 记录到日志
    with open('logs/sqqq_monitor.log', 'a') as f:
        f.write(f'{result.timestamp} | SQQQ | {result.signal} | {result.strength:+.1f} | \${result.current_price:.2f}\\n')
" 2>&1

echo "✅ 检查完成"
