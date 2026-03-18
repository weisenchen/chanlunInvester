#!/usr/bin/env python3
"""
缠论 WebSocket 预警服务器 - ChanLun Alert Server

实时推送买卖点、价格、背驰等预警信号。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional
import websockets
from websockets.server import WebSocketServerProtocol
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertChannel:
    """预警渠道基类"""
    
    async def send(self, alert: dict):
        raise NotImplementedError


class TelegramChannel(AlertChannel):
    """Telegram 通知渠道"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    async def send(self, alert: dict):
        import aiohttp
        
        message = self._format_message(alert)
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                async with session.post(self.base_url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"Telegram 预警发送成功：{alert.get('type')}")
                    else:
                        logger.error(f"Telegram 发送失败：{resp.status}")
        except Exception as e:
            logger.error(f"Telegram 错误：{e}")
    
    def _format_message(self, alert: dict) -> str:
        """格式化消息"""
        emoji_map = {
            'buy1': '🟢',
            'buy2': '🟢',
            'buy3': '🔵',
            'sell1': '🔴',
            'sell2': '🔴',
            'sell3': '🟠',
            'divergence': '⚠️',
            'price': '📊'
        }
        
        emoji = emoji_map.get(alert.get('type', ''), '📈')
        
        message = f"""
{emoji} *缠论预警*

*标的*: {alert.get('symbol', 'N/A')}
*类型*: {alert.get('type', 'N/A')}
*价格*: ${alert.get('price', 0):.2f}
*级别*: {alert.get('level', 'N/A')}
*时间*: {alert.get('time', datetime.now().strftime('%Y-%m-%d %H:%M'))}
*置信度*: {alert.get('confidence', 0)*100:.0f}%

{alert.get('description', '')}
"""
        return message.strip()


class WebhookChannel(AlertChannel):
    """Webhook 通知渠道"""
    
    def __init__(self, url: str):
        self.url = url
    
    async def send(self, alert: dict):
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=alert) as resp:
                    logger.info(f"Webhook 发送状态：{resp.status}")
        except Exception as e:
            logger.error(f"Webhook 错误：{e}")


class EmailChannel(AlertChannel):
    """邮件通知渠道"""
    
    def __init__(self, smtp_server: str, sender: str, recipients: List[str], password: str):
        self.smtp_server = smtp_server
        self.sender = sender
        self.recipients = recipients
        self.password = password
    
    async def send(self, alert: dict):
        import smtplib
        from email.mime.text import MIMEText
        
        subject = f"缠论预警：{alert.get('symbol')} - {alert.get('type')}"
        body = self._format_email(alert)
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)
                logger.info("邮件发送成功")
        except Exception as e:
            logger.error(f"邮件错误：{e}")
    
    def _format_email(self, alert: dict) -> str:
        """格式化邮件内容"""
        return f"""
缠论预警通知

标的：{alert.get('symbol')}
类型：{alert.get('type')}
价格：${alert.get('price', 0):.2f}
级别：{alert.get('level')}
时间：{alert.get('time')}
置信度：{alert.get('confidence', 0)*100:.0f}%

描述：
{alert.get('description', '')}

---
此邮件由缠论监控系统自动发送
"""


class Subscription:
    """预警订阅"""
    
    def __init__(
        self,
        channel: str,
        symbol: str,
        alert_types: List[str],
        levels: List[str] = None,
        min_confidence: float = 0.5
    ):
        self.channel = channel
        self.symbol = symbol
        self.alert_types = alert_types
        self.levels = levels or ['30m', '1d']
        self.min_confidence = min_confidence
    
    def matches(self, alert: dict) -> bool:
        """检查预警是否匹配订阅"""
        if self.symbol != '*' and alert.get('symbol') != self.symbol:
            return False
        
        if alert.get('type') not in self.alert_types and '*' not in self.alert_types:
            return False
        
        if alert.get('level') not in self.levels and '*' not in self.levels:
            return False
        
        if alert.get('confidence', 1.0) < self.min_confidence:
            return False
        
        return True


class AlertManager:
    """预警管理器"""
    
    def __init__(self):
        self.subscriptions: List[Subscription] = []
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: List[dict] = []
    
    def register_channel(self, name: str, channel: AlertChannel):
        """注册通知渠道"""
        self.channels[name] = channel
        logger.info(f"注册通知渠道：{name}")
    
    def subscribe(self, subscription: Subscription):
        """添加订阅"""
        self.subscriptions.append(subscription)
        logger.info(f"新订阅：{subscription.symbol} - {subscription.alert_types}")
    
    def unsubscribe(self, channel: str, symbol: str = None):
        """取消订阅"""
        self.subscriptions = [
            s for s in self.subscriptions
            if not (s.channel == channel and (symbol is None or s.symbol == symbol))
        ]
    
    async def send_alert(self, alert: dict):
        """发送预警"""
        logger.info(f"预警：{alert.get('symbol')} - {alert.get('type')}")
        
        # 记录历史
        self.alert_history.append({
            **alert,
            'sent_at': datetime.now().isoformat()
        })
        
        # 保持历史在合理大小
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # 匹配订阅并发送
        tasks = []
        
        for sub in self.subscriptions:
            if sub.matches(alert):
                channel = self.channels.get(sub.channel)
                if channel:
                    tasks.append(channel.send(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(
        self,
        symbol: str = None,
        alert_type: str = None,
        limit: int = 100
    ) -> List[dict]:
        """获取预警历史"""
        history = self.alert_history
        
        if symbol:
            history = [a for a in history if a.get('symbol') == symbol]
        
        if alert_type:
            history = [a for a in history if a.get('type') == alert_type]
        
        return history[-limit:]


class WebSocketAlertServer:
    """WebSocket 预警服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.alert_manager = AlertManager()
        self.clients: Set[WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[WebSocketServerProtocol, List[Subscription]] = {}
    
    async def register(self, websocket: WebSocketServerProtocol):
        """注册客户端"""
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = []
        logger.info(f"客户端连接：{websocket.remote_address}")
    
    async def unregister(self, websocket: WebSocketServerProtocol):
        """注销客户端"""
        self.clients.discard(websocket)
        self.client_subscriptions.pop(websocket, None)
        logger.info(f"客户端断开：{websocket.remote_address}")
    
    async def handler(self, websocket: WebSocketServerProtocol):
        """WebSocket 消息处理"""
        await self.register(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def handle_message(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'subscribe':
                await self.handle_subscribe(websocket, data)
            
            elif action == 'unsubscribe':
                await self.handle_unsubscribe(websocket, data)
            
            elif action == 'get_history':
                await self.handle_get_history(websocket, data)
            
            elif action == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))
            
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'未知动作：{action}'
                }))
        
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': '无效的 JSON'
            }))
    
    async def handle_subscribe(
        self,
        websocket: WebSocketServerProtocol,
        data: dict
    ):
        """处理订阅请求"""
        channel = data.get('channel')
        filter_data = data.get('filter', {})
        
        subscription = Subscription(
            channel='websocket',
            symbol=filter_data.get('symbol', '*'),
            alert_types=filter_data.get('types', ['*']),
            levels=filter_data.get('levels', ['30m', '1d']),
            min_confidence=filter_data.get('min_confidence', 0.5)
        )
        
        self.client_subscriptions[websocket].append(subscription)
        self.alert_manager.subscriptions.append(subscription)
        
        await websocket.send(json.dumps({
            'type': 'subscribed',
            'channel': channel,
            'filter': filter_data
        }))
        
        logger.info(f"客户端订阅：{filter_data}")
    
    async def handle_unsubscribe(
        self,
        websocket: WebSocketServerProtocol,
        data: dict
    ):
        """处理取消订阅"""
        # 简化实现：取消所有
        subs = self.client_subscriptions.get(websocket, [])
        for sub in subs:
            if sub in self.alert_manager.subscriptions:
                self.alert_manager.subscriptions.remove(sub)
        
        self.client_subscriptions[websocket] = []
        
        await websocket.send(json.dumps({
            'type': 'unsubscribed'
        }))
    
    async def handle_get_history(
        self,
        websocket: WebSocketServerProtocol,
        data: dict
    ):
        """获取预警历史"""
        symbol = data.get('symbol')
        alert_type = data.get('type')
        limit = data.get('limit', 100)
        
        history = self.alert_manager.get_history(symbol, alert_type, limit)
        
        await websocket.send(json.dumps({
            'type': 'history',
            'data': history
        }))
    
    async def broadcast(self, alert: dict):
        """广播预警给所有订阅的客户端"""
        if not self.clients:
            return
        
        message = json.dumps({
            'type': 'alert',
            'data': alert
        })
        
        # 发送给匹配的客户端
        tasks = []
        
        for client, subs in self.client_subscriptions.items():
            for sub in subs:
                if sub.matches(alert):
                    tasks.append(self._safe_send(client, message))
                    break
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_send(
        self,
        websocket: WebSocketServerProtocol,
        message: str
    ):
        """安全发送消息"""
        try:
            await websocket.send(message)
        except Exception as e:
            logger.error(f"发送失败：{e}")
    
    async def start(self):
        """启动服务器"""
        logger.info(f"WebSocket 预警服务器启动：ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # 永久运行


async def main():
    """示例：启动服务器并发送测试预警"""
    server = WebSocketAlertServer(port=8765)
    
    # 注册通知渠道
    # server.alert_manager.register_channel('telegram', TelegramChannel(...))
    # server.alert_manager.register_channel('webhook', WebhookChannel(...))
    
    # 启动服务器
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
