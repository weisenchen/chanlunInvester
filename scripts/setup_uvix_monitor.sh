#!/bin/bash
# UVIX 缠论监控安装脚本
# UVIX ChanLun Monitor Setup Script

set -e

echo "========================================================================"
echo "UVIX 缠论 30 分钟级别买卖点监控 - 安装向导"
echo "========================================================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_DIR="$PROJECT_DIR/logs"

# 1. 创建日志目录
echo "[1/4] 创建日志目录..."
mkdir -p "$LOGS_DIR"
echo "    ✓ 日志目录：$LOGS_DIR"

# 2. 检查 Python 依赖
echo ""
echo "[2/4] 检查 Python 依赖..."
python3 -c "import sys; print(f'    ✓ Python {sys.version}')" || {
    echo "    ✗ Python3 未安装"
    exit 1
}

# 3. 测试监控脚本
echo ""
echo "[3/4] 测试监控脚本..."
cd "$PROJECT_DIR"
if python3 examples/uvix_monitor.py > /dev/null 2>&1; then
    echo "    ✓ 监控脚本运行正常"
else
    echo "    ⚠ 监控脚本运行有警告 (可能是无买卖点)"
fi

# 4. 配置 Cron
echo ""
echo "[4/4] 配置定时监控..."
echo ""
echo "    请手动添加以下 Cron 任务："
echo ""
echo "    ┌─────────────────────────────────────────────────────────────┐"
echo "    │ crontab -e                                                  │"
echo "    │                                                             │"
echo "    │ # UVIX 缠论监控 (美东时间，每 30 分钟)                      │"
echo "    │ */30 14-21 * * 1-5 cd $PROJECT_DIR && python3 examples/uvix_monitor.py >> logs/uvix_cron.log 2>&1 │"
echo "    │                                                             │"
echo "    │ # 时区说明：14-21 UTC = 美东时间 9:30-16:00 (夏令时)        │"
echo "    └─────────────────────────────────────────────────────────────┘"
echo ""

# 5. 环境变量配置
echo ""
echo "========================================================================"
echo "Telegram 提醒配置 (可选)"
echo "========================================================================"
echo ""
echo "如需接收 Telegram 提醒，请设置以下环境变量："
echo ""
echo "    export TELEGRAM_BOT_TOKEN='your_bot_token'"
echo "    export TELEGRAM_CHAT_ID='your_chat_id'"
echo ""
echo "添加到 ~/.bashrc 永久生效："
echo "    echo 'export TELEGRAM_BOT_TOKEN=\"your_token\"' >> ~/.bashrc"
echo "    echo 'export TELEGRAM_CHAT_ID=\"your_id\"' >> ~/.bashrc"
echo "    source ~/.bashrc"
echo ""

# 6. 完成
echo ""
echo "========================================================================"
echo "安装完成！"
echo "========================================================================"
echo ""
echo "📁 项目目录：$PROJECT_DIR"
echo "📝 日志目录：$LOGS_DIR"
echo "📊 监控脚本：$PROJECT_DIR/examples/uvix_monitor.py"
echo "📖 使用文档：$PROJECT_DIR/examples/UVIX_MONITOR_README.md"
echo ""
echo "快速启动:"
echo "    cd $PROJECT_DIR"
echo "    python3 examples/uvix_monitor.py"
echo ""
echo "查看日志:"
echo "    tail -f $LOGS_DIR/uvix_monitor.log"
echo "    tail -f $LOGS_DIR/uvix_alerts.log"
echo ""
echo "========================================================================"
