#!/usr/bin/env python3
"""
缠论企业级交易客户端 - ChanLun Enterprise Trading Client

支持多券商、统一接口、风险控制。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """订单"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"  # DAY, GTC, IOC, FOK
    client_order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.client_order_id is None:
            self.client_order_id = f"CL-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


@dataclass
class OrderResult:
    """订单执行结果"""
    order_id: str
    client_order_id: str
    status: OrderStatus
    filled_quantity: float = 0
    avg_fill_price: float = 0
    commission: float = 0
    submit_time: Optional[datetime] = None
    fill_time: Optional[datetime] = None
    message: str = ""


@dataclass
class RiskCheckResult:
    """风控检查结果"""
    passed: bool
    reason: str = ""
    rule_name: str = ""


class BrokerAdapter(ABC):
    """券商适配器基类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """连接券商 API"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        pass
    
    @abstractmethod
    def submit_order(self, order: Order) -> OrderResult:
        """提交订单"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderResult:
        """获取订单状态"""
        pass


class IBKRAdapter(BrokerAdapter):
    """Interactive Brokers 适配器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7496, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        self.app = None
    
    def connect(self) -> bool:
        try:
            from ib_insync import IB
            
            self.app = IB()
            self.app.connect(self.host, self.port, self.client_id)
            self.connected = True
            logger.info(f"IBKR 连接成功：{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"IBKR 连接失败：{e}")
            return False
    
    def disconnect(self):
        if self.app:
            self.app.disconnect()
            self.connected = False
    
    def get_positions(self) -> List[Position]:
        if not self.connected:
            return []
        
        positions = []
        for pos in self.app.positions():
            positions.append(Position(
                symbol=pos.contract.symbol,
                quantity=pos.position,
                avg_price=pos.avgCost,
                market_value=pos.marketValue,
                unrealized_pnl=pos.unrealizedPNL,
                unrealized_pnl_pct=pos.unrealizedPNL / pos.avgCost if pos.avgCost else 0
            ))
        return positions
    
    def submit_order(self, order: Order) -> OrderResult:
        from ib_insync import Stock, MarketOrder, LimitOrder
        
        if not self.connected:
            return OrderResult(
                order_id="",
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                message="未连接"
            )
        
        try:
            contract = Stock(order.symbol, 'SMART', 'USD')
            
            if order.type == OrderType.MARKET:
                ib_order = MarketOrder(
                    order.side.value,
                    order.quantity
                )
            else:
                ib_order = LimitOrder(
                    order.side.value,
                    order.quantity,
                    order.limit_price
                )
            
            trade = self.app.placeOrder(contract, ib_order)
            
            return OrderResult(
                order_id=str(trade.order.orderId),
                client_order_id=order.client_order_id,
                status=OrderStatus.SUBMITTED,
                submit_time=datetime.now()
            )
        except Exception as e:
            return OrderResult(
                order_id="",
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                message=str(e)
            )
    
    def cancel_order(self, order_id: str) -> bool:
        if not self.connected:
            return False
        
        try:
            self.app.cancelOrderById(int(order_id))
            return True
        except Exception as e:
            logger.error(f"取消订单失败：{e}")
            return False
    
    def get_order_status(self, order_id: str) -> OrderResult:
        # 简化实现
        return OrderResult(
            order_id=order_id,
            client_order_id="",
            status=OrderStatus.PENDING
        )


class FutuAdapter(BrokerAdapter):
    """富途牛牛适配器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.connected = False
        self.quote_ctx = None
        self.trade_ctx = None
    
    def connect(self) -> bool:
        try:
            from futu import OpenQuoteContext, OpenTradeContext
            
            self.quote_ctx = OpenQuoteContext(self.host, self.port)
            self.trade_ctx = OpenTradeContext(self.host, self.port)
            self.connected = True
            logger.info(f"富途连接成功：{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"富途连接失败：{e}")
            return False
    
    def disconnect(self):
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.connected = False
    
    def get_positions(self) -> List[Position]:
        # 简化实现
        return []
    
    def submit_order(self, order: Order) -> OrderResult:
        from futu import OrderType as FutuOrderType, HKOrderSide
        
        if not self.connected:
            return OrderResult(
                order_id="",
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                message="未连接"
            )
        
        try:
            # 富途下单逻辑
            ret_code, ret_data = self.trade_ctx.place_order(
                price=order.limit_price or 0,
                qty=order.quantity,
                code=order.symbol,
                trd_side=HKOrderSide.BUY if order.side == OrderSide.BUY else HKOrderSide.SELL,
                order_type=FutuOrderType.MARKET if order.type == OrderType.MARKET else FutuOrderType.NORMAL
            )
            
            if ret_code == 0:
                return OrderResult(
                    order_id=str(ret_data['order_id'][0]),
                    client_order_id=order.client_order_id,
                    status=OrderStatus.SUBMITTED,
                    submit_time=datetime.now()
                )
            else:
                return OrderResult(
                    order_id="",
                    client_order_id=order.client_order_id,
                    status=OrderStatus.REJECTED,
                    message=ret_data
                )
        except Exception as e:
            return OrderResult(
                order_id="",
                client_order_id=order.client_order_id,
                status=OrderStatus.REJECTED,
                message=str(e)
            )
    
    def cancel_order(self, order_id: str) -> bool:
        if not self.connected:
            return False
        
        try:
            ret_code, _ = self.trade_ctx.cancel_order(order_id)
            return ret_code == 0
        except Exception as e:
            logger.error(f"取消订单失败：{e}")
            return False
    
    def get_order_status(self, order_id: str) -> OrderResult:
        # 简化实现
        return OrderResult(
            order_id=order_id,
            client_order_id="",
            status=OrderStatus.PENDING
        )


class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.rules: List[Callable] = []
        self.daily_loss_limit: float = 10000
        self.position_limit: float = 0.20
        self.order_size_limit: int = 1000
    
    def add_rule(self, rule: Callable):
        """添加风控规则"""
        self.rules.append(rule)
    
    def check(self, order: Order, portfolio: Dict) -> RiskCheckResult:
        """风控检查"""
        # 检查订单大小
        if order.quantity > self.order_size_limit:
            return RiskCheckResult(
                passed=False,
                reason=f"订单数量超过限制：{order.quantity} > {self.order_size_limit}",
                rule_name="order_size_limit"
            )
        
        # 检查仓位限制
        total_value = portfolio.get('total_value', 0)
        order_value = order.quantity * (order.limit_price or 0)
        
        if order_value / total_value > self.position_limit:
            return RiskCheckResult(
                passed=False,
                reason=f"订单超过仓位限制：{order_value/total_value:.2%} > {self.position_limit:.2%}",
                rule_name="position_limit"
            )
        
        # 执行自定义规则
        for rule in self.rules:
            result = rule(order, portfolio)
            if not result.passed:
                return result
        
        return RiskCheckResult(passed=True)


class TradingClient:
    """统一交易客户端"""
    
    def __init__(self, broker: str = "ibkr", **kwargs):
        self.broker = broker
        self.adapter = self._create_adapter(broker, **kwargs)
        self.risk_manager = RiskManager()
        self.order_callbacks: List[Callable] = []
    
    def _create_adapter(self, broker: str, **kwargs) -> BrokerAdapter:
        """创建券商适配器"""
        adapters = {
            'ibkr': IBKRAdapter,
            'futu': FutuAdapter,
        }
        
        adapter_class = adapters.get(broker)
        if not adapter_class:
            raise ValueError(f"不支持的券商：{broker}")
        
        return adapter_class(**kwargs)
    
    def connect(self) -> bool:
        """连接券商"""
        return self.adapter.connect()
    
    def disconnect(self):
        """断开连接"""
        self.adapter.disconnect()
    
    def get_positions(self) -> List[Position]:
        """获取持仓"""
        return self.adapter.get_positions()
    
    def submit_order(self, order: Order, skip_risk_check: bool = False) -> OrderResult:
        """提交订单"""
        # 风控检查
        if not skip_risk_check:
            portfolio = {'total_value': 100000}  # 简化
            risk_result = self.risk_manager.check(order, portfolio)
            
            if not risk_result.passed:
                return OrderResult(
                    order_id="",
                    client_order_id=order.client_order_id,
                    status=OrderStatus.REJECTED,
                    message=f"风控拦截：{risk_result.reason}"
                )
        
        # 提交订单
        result = self.adapter.submit_order(order)
        
        # 通知回调
        for callback in self.order_callbacks:
            callback(result)
        
        return result
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        return self.adapter.cancel_order(order_id)
    
    def get_order_status(self, order_id: str) -> OrderResult:
        """获取订单状态"""
        return self.adapter.get_order_status(order_id)
    
    def on_order_update(self, callback: Callable):
        """注册订单更新回调"""
        self.order_callbacks.append(callback)


if __name__ == "__main__":
    # 示例：使用交易客户端
    client = TradingClient(broker="ibkr", host="127.0.0.1", port=7496)
    
    if client.connect():
        # 查询持仓
        positions = client.get_positions()
        for pos in positions:
            print(f"{pos.symbol}: {pos.quantity} @ ${pos.avg_price:.2f}")
        
        # 提交订单
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=100
        )
        
        result = client.submit_order(order)
        print(f"订单提交：{result.order_id}, 状态：{result.status}")
        
        client.disconnect()
