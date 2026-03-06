#!/usr/bin/env python3
"""
Telegram 告警测试脚本
测试 Telegram 配置是否正确
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from uvix_monitor import send_alert


def main():
    print("\n" + "="*70)
    print("Telegram 告警测试")
    print("="*70 + "\n")
    
    # 检查环境变量
    print("[1/3] 检查环境变量...")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("    ❌ TELEGRAM_BOT_TOKEN 未设置")
        print("\n    请按照 TELEGRAM_SETUP.md 配置:")
        print("    1. 创建 Telegram Bot")
        print("    2. 获取 Bot Token")
        print("    3. 设置环境变量:")
        print("       export TELEGRAM_BOT_TOKEN='your_token'")
        print("       export TELEGRAM_CHAT_ID='your_chat_id'")
        return False
    else:
        print(f"    ✓ TELEGRAM_BOT_TOKEN: {bot_token[:20]}...")
    
    if not chat_id:
        print("    ❌ TELEGRAM_CHAT_ID 未设置")
        print("\n    请按照 TELEGRAM_SETUP.md 配置:")
        print("    1. 获取你的 Chat ID")
        print("    2. 设置环境变量:")
        print("       export TELEGRAM_CHAT_ID='your_chat_id'")
        return False
    else:
        print(f"    ✓ TELEGRAM_CHAT_ID: {chat_id}")
    
    # 发送测试消息
    print("\n[2/3] 发送测试消息...")
    
    test_message = """
【UVIX 缠论买卖点信号 - 测试】

📊 标的：UVIX
⏰ 级别：5m
🎯 类型：测试消息
💰 价格：$7.00
📈 置信度：100%
📝 说明：Telegram 告警配置测试

✅ 如果你收到这条消息，说明 Telegram 告警配置成功！

⚠️ 风险提示：缠论分析仅供参考，不构成投资建议
"""
    
    result = send_alert(test_message, channels=['telegram', 'console'])
    
    # 检查结果
    print("\n[3/3] 检查结果...")
    
    if result:
        print("\n" + "="*70)
        print("✅ Telegram 告警配置成功！")
        print("="*70)
        print("\n📱 请检查你的 Telegram，应该收到了一条测试消息。")
        print("\n🎯 配置完成！现在 UVIX 出现买卖点时会立即通知你。")
        print("\n下一步:")
        print("  1. 确认收到测试消息")
        print("  2. 运行监控：python3 examples/uvix_monitor.py")
        print("  3. 设置 Cron: ./scripts/enable_uvix_alerts.sh")
        print("="*70 + "\n")
        return True
    else:
        print("\n" + "="*70)
        print("❌ Telegram 告警发送失败")
        print("="*70)
        print("\n可能原因:")
        print("  1. Bot Token 或 Chat ID 错误")
        print("  2. Bot 未启动 (联系 @BotFather 发送 /start)")
        print("  3. 网络问题")
        print("\n请参考 TELEGRAM_SETUP.md 进行故障排查。")
        print("="*70 + "\n")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
