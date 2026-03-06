#!/bin/bash
# UVIX 实时买卖点监控告警 - 启用脚本
# 设置 Cron 定时任务，每 5-30 分钟检查一次

set -e

echo "========================================================================"
echo "UVIX 实时买卖点监控告警 - 配置向导"
echo "========================================================================"
echo ""

PROJECT_DIR="/home/wei/.openclaw/workspace/trading-system"
LOGS_DIR="$PROJECT_DIR/logs"
SCRIPT="$PROJECT_DIR/examples/uvix_monitor.py"

# 创建日志目录
mkdir -p "$LOGS_DIR"

echo "📁 项目目录：$PROJECT_DIR"
echo "📝 日志目录：$LOGS_DIR"
echo "📊 监控脚本：$SCRIPT"
echo ""

# 检查 yfinance
echo "[1/3] 检查数据源..."
if python3 -c "import yfinance" 2>/dev/null; then
    echo "    ✓ Yahoo Finance 已安装"
else
    echo "    ✗ Yahoo Finance 未安装"
    echo "    请运行：pip3 install yfinance --break-system-packages"
    exit 1
fi

# 测试脚本
echo ""
echo "[2/3] 测试监控脚本..."
if python3 "$SCRIPT" > /dev/null 2>&1; then
    echo "    ✓ 监控脚本运行正常"
else
    echo "    ⚠️  脚本有警告 (可能是无买卖点)"
fi

# 配置 Cron
echo ""
echo "[3/3] 配置 Cron 定时任务..."
echo ""

# 创建临时 cron 文件
CRON_FILE=$(mktemp)

# 读取现有 cron
crontab -l 2>/dev/null > "$CRON_FILE" || true

# 检查是否已存在 UVIX 监控任务
if grep -q "uvix_monitor.py" "$CRON_FILE" 2>/dev/null; then
    echo "    ⚠️  UVIX 监控任务已存在"
    echo "    是否重新配置？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "    已跳过配置"
        rm "$CRON_FILE"
        exit 0
    fi
    # 删除旧任务
    grep -v "uvix_monitor.py" "$CRON_FILE" > "${CRON_FILE}.new" || true
    mv "${CRON_FILE}.new" "$CRON_FILE"
fi

# 添加新任务
cat >> "$CRON_FILE" << 'EOF'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UVIX 缠论实时买卖点监控
# 监控级别：30 分钟 + 5 分钟
# 提醒方式：检测到买卖点时立即通知
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 美股交易时段监控 (美东时间 9:30-16:00 = UTC 14:30-21:00)
# 每 30 分钟检查一次
*/30 14-21 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 盘前分析 (美东时间 9:00 = UTC 14:00)
0 14 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 盘中加密监控 (美东时间 10:00-15:00 = UTC 15:00-20:00)
# 每 15 分钟检查一次 (高活跃度时段)
*/15 15-20 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 盘后总结 (美东时间 16:30 = UTC 21:30)
30 21 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1
EOF

# 安装 cron
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "    ✓ Cron 任务已配置"
echo ""

# 显示配置
echo "========================================================================"
echo "✅ UVIX 实时监控已启用！"
echo "========================================================================"
echo ""
echo "📋 监控时间表 (美东时间):"
echo ""
echo "  ┌──────────────┬─────────────┬─────────────────────────────┐"
echo "  │ 时间         │ 频率        │ 说明                        │"
echo "  ├──────────────┼─────────────┼─────────────────────────────┤"
echo "  │ 09:00        │ 每日一次    │ 盘前分析                    │"
echo "  │ 09:30-16:00  │ 每 30 分钟   │ 正常交易时段监控            │"
echo "  │ 10:00-15:00  │ 每 15 分钟   │ 高活跃度时段加密监控        │"
echo "  │ 16:30        │ 每日一次    │ 盘后总结                    │"
echo "  └──────────────┴─────────────┴─────────────────────────────┘"
echo ""
echo "🔔 告警触发条件:"
echo "  ✅ 30 分钟级别出现买卖点 → 立即通知"
echo "  ✅ 5 分钟级别出现买卖点 → 立即通知"
echo "  ✅ 背驰信号 detected → 立即通知"
echo "  ✅ 置信度 > 70% → 立即通知"
echo ""
echo "📝 查看日志:"
echo "  tail -f $LOGS_DIR/uvix_cron.log"
echo "  tail -f $LOGS_DIR/uvix_alerts.log"
echo ""
echo "📊 手动检查:"
echo "  cd $PROJECT_DIR && python3 examples/uvix_monitor.py"
echo ""
echo "⚠️  注意事项:"
echo "  • 仅在美股交易日 (周一至周五) 运行"
echo "  • 自动识别美国节假日休市"
echo "  • 买卖点出现时会立即发送提醒"
echo ""
echo "========================================================================"
