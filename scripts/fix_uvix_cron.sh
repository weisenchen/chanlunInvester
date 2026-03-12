#!/bin/bash
# 修复 UVIX 监控 Cron 配置
# Fix UVIX Monitoring Cron Configuration

set -e

echo "========================================================================"
echo "修复 UVIX 预警系统 Cron 配置"
echo "========================================================================"
echo ""

# 备份现有 crontab
echo "[1/3] 备份现有 crontab..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "无现有 crontab"
echo "    ✓ 已备份"

# 创建新的 crontab 配置
echo ""
echo "[2/3] 创建新的 Cron 配置..."

cat > /tmp/uvix_crontab.txt << 'EOF'
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UVIX 缠论预警系统 - 完整版
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 盘前预警 (美东时间 9:00 - 开盘前 30 分钟)
0 13 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 scripts/uvix_premarket_alert.py >> logs/premarket_alerts.log 2>&1

# 开盘监控 (美东时间 9:30)
30 13 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 盘中加密监控 (美东时间 10:00-15:00, 每 15 分钟)
*/15 14-19 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 常规监控 (美东时间 9:30-16:00, 每 30 分钟)
*/30 13-20 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 盘后总结 (美东时间 16:30)
30 20 * * 1-5 cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1

# 每日总结 (美东时间 20:00)
0 0 * * * cd /home/wei/.openclaw/workspace/trading-system && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1
EOF

echo "    ✓ 配置已创建"

# 安装 crontab
echo ""
echo "[3/3] 安装新的 Cron 配置..."
crontab /tmp/uvix_crontab.txt

echo "    ✓ Cron 配置已更新"

# 验证
echo ""
echo "========================================================================"
echo "✅ Cron 配置已修复！"
echo "========================================================================"
echo ""
echo "📋 监控时间表 (美东时间):"
echo ""
echo "  ┌──────────────┬─────────────┬─────────────────────────────┐"
echo "  │ 时间         │ 频率        │ 说明                        │"
echo "  ├──────────────┼─────────────┼─────────────────────────────┤"
echo "  │ 09:00        │ 每日一次    │ 盘前预警 ⭐ NEW              │"
echo "  │ 09:30        │ 每日一次    │ 开盘监控                    │"
echo "  │ 10:00-15:00  │ 每 15 分钟   │ 高活跃度时段加密监控        │"
echo "  │ 09:30-16:00  │ 每 30 分钟   │ 正常交易时段监控            │"
echo "  │ 16:30        │ 每日一次    │ 盘后总结                    │"
echo "  │ 20:00        │ 每日一次    │ 每日总结                    │"
echo "  └──────────────┴─────────────┴─────────────────────────────┘"
echo ""
echo "📝 日志文件:"
echo "  • 监控日志：logs/uvix_cron.log"
echo "  • 盘前预警：logs/premarket_alerts.log"
echo "  • 告警日志：logs/telegram_alerts.log"
echo ""
echo "🔍 查看最新日志:"
echo "  tail -20 logs/uvix_cron.log"
echo "  tail -20 logs/premarket_alerts.log"
echo ""
echo "⚠️  注意:"
echo "  • Telegram 告警需要配置 OpenClaw message 工具"
echo "  • 买卖点出现时会自动发送通知"
echo ""
echo "========================================================================"

# 显示当前 crontab
echo ""
echo "当前 Cron 配置:"
crontab -l | grep -E "(uvix|UVIX)" | head -10
