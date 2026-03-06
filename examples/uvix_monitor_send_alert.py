#!/usr/bin/env python3
"""
UVIX 买卖点告警发送模块
通过 OpenClaw message 工具发送 Telegram 告警
"""

import subprocess
from pathlib import Path
from datetime import datetime


def send_telegram_alert(message: str) -> bool:
    """
    发送 Telegram 告警 (使用 OpenClaw message 工具)
    
    Args:
        message: 告警消息内容
    
    Returns:
        bool: 发送是否成功
    """
    try:
        # 获取告警发送器路径
        script_dir = Path(__file__).parent.parent / 'scripts'
        alert_script = script_dir / 'uvix_telegram_alert.py'
        
        if not alert_script.exists():
            print(f"    ✗ 告警脚本不存在：{alert_script}")
            return False
        
        # 调用告警发送器
        result = subprocess.run(
            ['python3', str(alert_script), message],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(script_dir)
        )
        
        if result.returncode == 0:
            print(f"    ✓ Telegram 告警已发送")
            return True
        else:
            print(f"    ✗ Telegram 发送失败")
            if result.stderr:
                print(f"    错误：{result.stderr[:200]}")
            return False
        
    except subprocess.TimeoutExpired:
        print(f"    ✗ Telegram 发送超时")
        return False
    except Exception as e:
        print(f"    ✗ Telegram 发送异常：{e}")
        return False


def send_alert(message: str, channels: list = None):
    """
    发送告警到指定渠道
    
    Args:
        message: 告警消息内容
        channels: 渠道列表 ['console', 'telegram', 'file']
    """
    if channels is None:
        channels = ['console', 'telegram']
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Console 输出
    if 'console' in channels:
        alert_message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ UVIX 缠论买卖点提醒
📅 时间：{timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 缠论依据：第 12, 24 课 - 背驰与买卖点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        print(alert_message)
    
    # Telegram 发送
    if 'telegram' in channels:
        send_telegram_alert(message)
    
    # 记录到日志
    if 'file' in channels:
        log_file = Path(__file__).parent.parent / 'logs' / 'uvix_alerts.log'
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Alert Time: {timestamp}\n")
            f.write(f"Message:\n{message}\n")


if __name__ == '__main__':
    # 测试
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

✅ Telegram 告警系统测试
"""
    send_alert(test_message, channels=['console', 'telegram'])
