#!/bin/bash
# UVIX Telegram 告警发送脚本
# 使用 OpenClaw message 工具

MESSAGE="$1"

if [ -z "$MESSAGE" ]; then
    MESSAGE="【UVIX 测试消息】

✅ Telegram 告警系统已就绪！

当 UVIX 出现买卖点时，你会立即收到通知。

📊 监控级别：30m + 5m
🔔 告警频率：实时
📱 通知方式：Telegram"
fi

# 使用 OpenClaw message 工具发送 Telegram 消息
openclaw message send \
    --channel telegram \
    --message "$MESSAGE"

echo "✓ Telegram 消息已发送"
