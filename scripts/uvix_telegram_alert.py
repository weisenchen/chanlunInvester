#!/usr/bin/env python3
"""
UVIX Telegram 告警发送器
通过 OpenClaw message 工具发送 Telegram 告警

用法:
    python3 uvix_telegram_alert.py "消息内容"
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def send_telegram_message(message: str) -> bool:
    """
    通过 OpenClaw message 工具发送 Telegram 消息
    
    Args:
        message: 要发送的消息内容
    
    Returns:
        bool: 发送是否成功
    """
    try:
        # 使用 OpenClaw message 工具
        # 注意：OpenClaw message 工具会自动发送到配置的 Telegram 频道
        cmd = [
            'openclaw', 'message', 'send',
            '-t', 'telegram',  # target (Telegram chat)
            '--channel', 'telegram',  # channel type
            '-m', message  # message
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # 解析返回的 JSON
            try:
                response = json.loads(result.stdout)
                if response.get('ok'):
                    print(f"✓ Telegram 消息已发送 (Message ID: {response.get('messageId')})")
                    return True
            except:
                pass
            
            print(f"✓ Telegram 消息已发送")
            return True
        else:
            print(f"✗ 发送失败：{result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"✗ 发送超时")
        return False
    except Exception as e:
        print(f"✗ 发送异常：{e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python3 uvix_telegram_alert.py \"消息内容\"")
        print("\n示例:")
        print('  python3 uvix_telegram_alert.py "【UVIX 测试】告警系统正常"')
        sys.exit(1)
    
    # 获取消息内容
    message = ' '.join(sys.argv[1:])
    
    # 添加时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    full_message = f"""
⚠️ *UVIX 缠论买卖点提醒*
📅 时间：{timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 缠论依据：第 12, 24 课 - 背驰与买卖点
⚠️ 风险提示：缠论分析仅供参考，不构成投资建议
"""
    
    print(f"\n发送 Telegram 告警...")
    success = send_telegram_message(full_message)
    
    # 记录到日志
    log_file = Path(__file__).parent.parent / 'logs' / 'telegram_alerts.log'
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Time: {timestamp}\n")
        f.write(f"Status: {'✓ Success' if success else '✗ Failed'}\n")
        f.write(f"Message:\n{message}\n")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
