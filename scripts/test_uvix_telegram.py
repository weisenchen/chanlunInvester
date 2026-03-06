#!/usr/bin/env python3
"""
UVIX 缠论买卖点提醒 - Telegram 测试
"""

import sys
from pathlib import Path

# 添加 examples 目录到路径
examples_dir = Path(__file__).parent.parent / 'examples'
sys.path.insert(0, str(examples_dir))

from uvix_monitor import send_alert

# 测试消息
test_message = """
【UVIX 缠论买卖点信号 - 测试】

📊 标的：UVIX
⏰ 级别：5m
🎯 类型：第二类买点
💰 价格：$6.85
📈 置信度：85%
📝 说明：次级别回踩确认

操作建议：BUY
入场：$6.85
止损：$6.51 (-5%)
目标：$7.54 (+10%)

✅ 如果你收到这条消息，说明 Telegram 告警配置成功！
"""

print("\n" + "="*70)
print("UVIX Telegram 告警测试")
print("="*70 + "\n")
print("正在发送测试消息到 Telegram...\n")

# 发送 Telegram 告警
send_alert(test_message, channels=['telegram', 'console'])

print("\n" + "="*70)
print("测试完成！请检查 Telegram 是否收到消息。")
print("="*70 + "\n")
