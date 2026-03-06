#!/bin/bash
# UVIX Telegram 告警发送脚本
# 使用 OpenClaw message 工具

MESSAGE="$1"

if [ -z "$MESSAGE" ]; then
    echo "用法：$0 \"消息内容\""
    exit 1
fi

# 添加时间戳
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

FULL_MESSAGE="⚠️ *UVIX 缠论买卖点提醒*
📅 时间：${TIMESTAMP}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${MESSAGE}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 缠论依据：第 12, 24 课 - 背驰与买卖点
⚠️ 风险提示：缠论分析仅供参考，不构成投资建议"

# 使用 OpenClaw message 工具发送
openclaw message send \
    -t telegram \
    --channel telegram \
    -m "$FULL_MESSAGE"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Telegram 告警已发送"
    
    # 记录到日志
    LOG_FILE="$(dirname "$0")/../logs/telegram_alerts.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "" >> "$LOG_FILE"
    echo "============================================================" >> "$LOG_FILE"
    echo "Time: $TIMESTAMP" >> "$LOG_FILE"
    echo "Status: ✓ Success" >> "$LOG_FILE"
    echo "Message: $MESSAGE" >> "$LOG_FILE"
else
    echo "✗ Telegram 发送失败"
fi

exit $EXIT_CODE
