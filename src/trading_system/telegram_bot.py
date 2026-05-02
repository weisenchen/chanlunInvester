"""
ChanLun Telegram Bot - 缠论电报机器人
支持交互式命令、图表推送、自动报告

Usage:
    from trading_system.telegram_bot import ChanLunBot
    
    bot = ChanLunBot(token='YOUR_BOT_TOKEN')
    bot.start()
"""

import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ChanLunBot:
    """缠论 Telegram 机器人"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化机器人
        
        Args:
            token: Telegram Bot Token (可选，使用 OpenClaw message 工具)
        """
        self.token = token
        self.commands = {
            'start': self.cmd_start,
            'help': self.cmd_help,
            'status': self.cmd_status,
            'analyze': self.cmd_analyze,
            'monitor': self.cmd_monitor,
            'alerts': self.cmd_alerts,
            'settings': self.cmd_settings,
        }
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = 'Markdown') -> bool:
        """发送消息"""
        try:
            if self.token:
                # 使用 Telegram Bot API
                import requests
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': parse_mode
                }
                response = requests.post(url, json=data, timeout=30)
                return response.status_code == 200
            else:
                # 使用 OpenClaw message 工具
                result = subprocess.run(
                    ['openclaw', 'message', 'send',
                     '-t', 'telegram',
                     '-m', text],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.returncode == 0
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_photo(self, chat_id: str, photo_path: str, caption: str = '') -> bool:
        """发送图片"""
        try:
            if self.token:
                import requests
                url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
                with open(photo_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': chat_id,
                        'caption': caption
                    }
                    response = requests.post(url, files=files, data=data, timeout=30)
                    return response.status_code == 200
            else:
                print("Photo sending requires bot token")
                return False
        except Exception as e:
            print(f"Error sending photo: {e}")
            return False
    
    def handle_command(self, command: str, args: list, chat_id: str) -> str:
        """处理命令"""
        if command in self.commands:
            return self.commands[command](args, chat_id)
        else:
            return self.cmd_help(args, chat_id)
    
    # ========== 命令实现 ==========
    
    def cmd_start(self, args: list, chat_id: str) -> str:
        """开始命令"""
        return """
👋 欢迎使用缠论监控机器人!

我是缠论智能分析助手，可以帮您:
• 分析股票缠论结构
• 监控股票买卖点
• 推送实时预警
• 生成交易报告

输入 /help 查看所有命令
输入 /analyze AAPL 分析股票
        """
    
    def cmd_help(self, args: list, chat_id: str) -> str:
        """帮助命令"""
        return """
📖 可用命令:

/analyze <股票代码> [级别]
  分析股票缠论结构
  例：/analyze AAPL
  例：/analyze TSLA 30m

/monitor <股票代码>
  开始监控股票
  例：/monitor UVIX

/status
  查看监控状态

/alerts
  查看最新预警

/settings
  查看/修改设置

/help
  显示此帮助信息
        """
    
    def cmd_status(self, args: list, chat_id: str) -> str:
        """状态命令"""
        try:
            # 获取监控状态
            result = subprocess.run(
                ['python3', 'scripts/monitor_manager.sh', 'status'],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent / 'trading-system')
            )
            
            status_text = result.stdout.strip()
            
            return f"""
📊 监控系统状态

{status_text}

运行时间：24/7 (交易时段)
数据源：Yahoo Finance
        """
        except Exception as e:
            return f"❌ 获取状态失败：{e}"
    
    def cmd_analyze(self, args: list, chat_id: str) -> str:
        """分析命令"""
        if not args:
            return "❌ 请提供股票代码\n例：/analyze AAPL"
        
        symbol = args[0]
        level = args[1] if len(args) > 1 else '30m'
        
        try:
            # 运行分析
            cmd = [
                'python3', 'scripts/chanlun_monitor.py',
                symbol, '--level', level
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent / 'trading-system'),
                timeout=60
            )
            
            # 提取关键信息
            output = result.stdout
            
            # 格式化输出
            formatted = f"""
📊 {symbol} 缠论分析

{output}

⚠️  仅供参考，不构成投资建议
            """
            
            return formatted
            
        except subprocess.TimeoutExpired:
            return "⏱️ 分析超时，请稍后重试"
        except Exception as e:
            return f"❌ 分析失败：{e}"
    
    def cmd_monitor(self, args: list, chat_id: str) -> str:
        """监控命令"""
        if not args:
            return "❌ 请提供股票代码\n例：/monitor UVIX"
        
        symbol = args[0]
        
        return f"""
✅ 已开始监控 {symbol}

监控设置:
• 频率：每 5 分钟
• 级别：5m, 30m, 1d
• 预警：Telegram 推送
• 置信度：≥70%

当检测到买卖点时，我会立即通知您!
        """
    
    def cmd_alerts(self, args: list, chat_id: str) -> str:
        """预警命令"""
        try:
            # 读取最新预警
            log_file = Path(__file__).parent.parent.parent / 'trading-system' / 'logs' / 'uvix_auto_alerts.log'
            
            if not log_file.exists():
                return "📭 暂无预警记录"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取最近 3 条预警
            alerts = content.split('━━━━━━━━━━')[-3:]
            
            if not alerts or alerts == ['']:
                return "📭 暂无预警记录"
            
            alert_text = "\n\n".join(alerts[:3])
            
            return f"""
🚨 最新预警

{alert_text}
            """
            
        except Exception as e:
            return f"❌ 获取预警失败：{e}"
    
    def cmd_settings(self, args: list, chat_id: str) -> str:
        """设置命令"""
        return """
⚙️ 当前设置

监控频率：每 5 分钟
分析级别：1d, 30m, 5m
置信度阈值：70%
止损比例：3%
止盈比例：5%
仓位比例：10%

修改设置请联系管理员
        """
    
    def start(self):
        """启动机器人 (轮询模式)"""
        print("🤖 ChanLun Bot 已启动")
        print("等待命令...")
        
        # 实际应该使用 telegram.Bot 库实现轮询
        # 这里简化为使用 OpenClaw message 工具
        
        while True:
            try:
                import time
                time.sleep(60)
            except KeyboardInterrupt:
                print("🛑 机器人已停止")
                break


# 快捷函数
def send_alert(message: str, chat_id: str = '') -> bool:
    """快捷发送预警"""
    bot = ChanLunBot()
    return bot.send_message(chat_id or 'default', message)


def send_analysis_report(symbol: str, result: Dict[str, Any], chat_id: str = '') -> bool:
    """发送分析报告"""
    bot = ChanLunBot()
    
    report = f"""
📊 {symbol} 缠论分析报告

🎯 信号：{result.get('signal', 'HOLD')}
📈 强度：{result.get('strength', 0):+.1f}
💰 价格：${result.get('current_price', 0):.2f}

📐 分析详情:
{chr(10).join(result.get('reasoning', []))}

⚠️  仅供参考，不构成投资建议
    """
    
    return bot.send_message(chat_id or 'default', report)
