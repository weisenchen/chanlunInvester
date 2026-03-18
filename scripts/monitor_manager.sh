#!/bin/bash
# UVIX 实时监控管理器
# 快速启动/停止/查看监控状态

LOG_DIR="/home/wei/.openclaw/workspace/trading-system/logs"
SCRIPT_DIR="/home/wei/.openclaw/workspace/trading-system/scripts"
MONITOR_SCRIPT="$SCRIPT_DIR/uvix_auto_monitor.py"

case "$1" in
    start)
        echo "🚀 启动 UVIX 实时监控..."
        mkdir -p "$LOG_DIR"
        nohup python3 "$MONITOR_SCRIPT" > "$LOG_DIR/uvix_realtime_monitor.log" 2>&1 &
        PID=$!
        echo "✅ 监控已启动 (PID: $PID)"
        echo "📝 日志：$LOG_DIR/uvix_realtime_monitor.log"
        ;;
    
    stop)
        echo "⏹️  停止 UVIX 实时监控..."
        pkill -f uvix_auto_monitor.py
        echo "✅ 监控已停止"
        ;;
    
    status)
        echo "📊 监控状态:"
        echo ""
        ps aux | grep uvix_auto_monitor | grep -v grep
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 监控正在运行"
        else
            echo ""
            echo "❌ 监控未运行"
        fi
        ;;
    
    logs)
        echo "📝 实时日志 (Ctrl+C 退出):"
        tail -f "$LOG_DIR/uvix_realtime_monitor.log"
        ;;
    
    alerts)
        echo "🚨 最新预警:"
        tail -50 "$LOG_DIR/uvix_auto_alerts.log" 2>/dev/null || echo "暂无预警记录"
        ;;
    
    test)
        echo "🧪 测试监控系统..."
        python3 "$SCRIPT_DIR/test_uvix_alert.py"
        ;;
    
    restart)
        echo "🔄 重启监控..."
        $0 stop
        sleep 2
        $0 start
        ;;
    
    multi)
        echo "📊 运行多级别联动分析..."
        python3 "$SCRIPT_DIR/uvix_multi_level_monitor.py"
        ;;
    
    *)
        echo "UVIX 实时监控管理器"
        echo ""
        echo "用法：$0 {start|stop|status|logs|alerts|test|restart|multi}"
        echo ""
        echo "命令说明:"
        echo "  start    - 启动后台监控"
        echo "  stop     - 停止监控"
        echo "  status   - 查看运行状态"
        echo "  logs     - 实时查看日志"
        echo "  alerts   - 查看最新预警"
        echo "  test     - 测试监控系统"
        echo "  restart  - 重启监控"
        echo "  multi    - 多级别联动分析 (5m+30m)"
        echo ""
        echo "示例:"
        echo "  $0 start          # 启动监控"
        echo "  $0 status         # 查看状态"
        echo "  $0 logs           # 查看日志"
        echo "  $0 alerts         # 查看预警"
        echo "  $0 multi          # 多级别分析"
        ;;
esac
