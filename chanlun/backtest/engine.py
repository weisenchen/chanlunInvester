#!/usr/bin/env python3
"""
缠论回测引擎 - ChanLun Backtest Engine

支持基于缠论买卖点的策略回测，提供完整的绩效分析。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class Trade:
    """单笔交易记录"""
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    position: str = "long"  # long/short
    size: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    entry_type: str = ""  # buy1, buy2, buy3
    exit_type: str = ""   # sell1, sell2, sell3


@dataclass
class BacktestResult:
    """回测结果"""
    trades: List[Trade] = field(default_factory=list)
    total_return: float = 0
    annual_return: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0
    avg_loss: float = 0
    equity_curve: List[float] = field(default_factory=list)
    
    def summary(self) -> str:
        """生成绩效摘要"""
        return f"""
=== 回测绩效摘要 ===
总收益率：{self.total_return:.2f}%
年化收益：{self.annual_return:.2f}%
胜率：{self.win_rate:.2f}%
盈亏比：{self.profit_factor:.2f}:1
最大回撤：{self.max_drawdown:.2f}%
Sharpe 比率：{self.sharpe_ratio:.2f}
总交易次数：{self.total_trades}
盈利交易：{self.winning_trades}
亏损交易：{self.losing_trades}
平均盈利：{self.avg_win:.2f}%
平均亏损：{self.avg_loss:.2f}%
"""


class BacktestEngine:
    """缠论回测引擎"""
    
    def __init__(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        level: str = "30m",
        initial_capital: float = 100000,
        commission: float = 0.001,
        slippage: float = 0.001
    ):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.level = level
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.capital = initial_capital
        self.position = 0
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        
    def load_data(self, data: pd.DataFrame) -> 'BacktestEngine':
        """加载 K 线数据"""
        self.data = data
        self.data = self.data.sort_index()
        return self
    
    def run(self, strategy: 'Strategy') -> BacktestResult:
        """运行回测"""
        print(f"开始回测 {self.symbol} ({self.start_date} ~ {self.end_date})")
        
        for i, (timestamp, row) in enumerate(self.data.iterrows()):
            # 更新资金曲线
            current_equity = self.capital + self.position * row['close']
            self.equity_curve.append(current_equity)
            
            # 策略信号
            signal = strategy.generate_signal(row, self.data.iloc[:i+1])
            
            if signal and signal['action'] == 'buy' and self.position == 0:
                # 买入
                entry_price = row['close'] * (1 + self.slippage)
                size = (self.capital * 0.95) / entry_price  # 95% 仓位
                self.capital -= size * entry_price * (1 + self.commission)
                self.position = size
                
                self.trades.append(Trade(
                    entry_time=timestamp,
                    entry_price=entry_price,
                    position='long',
                    size=size,
                    entry_type=signal.get('type', 'buy')
                ))
                
            elif signal and signal['action'] == 'sell' and self.position > 0:
                # 卖出
                exit_price = row['close'] * (1 - self.slippage)
                pnl = (exit_price - self.trades[-1].entry_price) * self.position
                pnl_pct = pnl / (self.trades[-1].entry_price * self.position)
                
                self.capital += self.position * exit_price * (1 - self.commission)
                
                self.trades[-1].exit_time = timestamp
                self.trades[-1].exit_price = exit_price
                self.trades[-1].pnl = pnl
                self.trades[-1].pnl_pct = pnl_pct
                self.trades[-1].exit_type = signal.get('type', 'sell')
                self.position = 0
        
        # 平仓未成交交易
        if self.position > 0 and len(self.data) > 0:
            last_row = self.data.iloc[-1]
            exit_price = last_row['close'] * (1 - self.slippage)
            pnl = (exit_price - self.trades[-1].entry_price) * self.position
            
            self.trades[-1].exit_time = last_row.name
            self.trades[-1].exit_price = exit_price
            self.trades[-1].pnl = pnl
            self.trades[-1].pnl_pct = pnl / (self.trades[-1].entry_price * self.position)
            self.trades[-1].exit_type = 'forced_close'
        
        return self._calculate_result()
    
    def _calculate_result(self) -> BacktestResult:
        """计算回测结果"""
        result = BacktestResult()
        result.trades = self.trades
        result.equity_curve = self.equity_curve
        
        if not self.trades:
            return result
        
        # 基础统计
        result.total_trades = len(self.trades)
        completed_trades = [t for t in self.trades if t.exit_price is not None]
        
        if completed_trades:
            result.winning_trades = sum(1 for t in completed_trades if t.pnl > 0)
            result.losing_trades = sum(1 for t in completed_trades if t.pnl <= 0)
            result.win_rate = result.winning_trades / len(completed_trades)
            
            wins = [t.pnl_pct for t in completed_trades if t.pnl > 0]
            losses = [t.pnl_pct for t in completed_trades if t.pnl <= 0]
            
            result.avg_win = np.mean(wins) if wins else 0
            result.avg_loss = abs(np.mean(losses)) if losses else 0
            result.profit_factor = abs(result.avg_win / result.avg_loss) if result.avg_loss else 0
        
        # 收益率
        result.total_return = (self.equity_curve[-1] - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益
        days = (self.data.index[-1] - self.data.index[0]).days
        if days > 0:
            result.annual_return = ((1 + result.total_return/100) ** (365/days) - 1) * 100
        
        # 最大回撤
        equity_array = np.array(self.equity_curve)
        peak = np.maximum.accumulate(equity_array)
        drawdown = (peak - equity_array) / peak * 100
        result.max_drawdown = np.max(drawdown)
        
        # Sharpe 比率
        if len(self.equity_curve) > 1:
            returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
            result.sharpe_ratio = np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        return result


class Strategy:
    """策略基类"""
    
    def generate_signal(self, row: pd.Series, history: pd.DataFrame) -> Optional[Dict]:
        """生成交易信号"""
        raise NotImplementedError


class BSPStrategy(Strategy):
    """缠论买卖点策略"""
    
    def __init__(
        self,
        buy_types: List[str] = None,
        sell_types: List[str] = None,
        stop_loss: float = 0.05,
        take_profit: float = 0.15
    ):
        self.buy_types = buy_types or ['buy1', 'buy2', 'buy3']
        self.sell_types = sell_types or ['sell1', 'sell2', 'sell3']
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_price = 0
    
    def generate_signal(self, row: pd.Series, history: pd.DataFrame) -> Optional[Dict]:
        """基于买卖点生成信号"""
        # 检查是否有买卖点信号
        if 'bsp_type' in row and row['bsp_type']:
            bsp_type = row['bsp_type']
            
            # 买入信号
            if bsp_type in self.buy_types and self.entry_price == 0:
                self.entry_price = row['close']
                return {'action': 'buy', 'type': bsp_type}
            
            # 卖出信号
            elif bsp_type in self.sell_types and self.entry_price > 0:
                self.entry_price = 0
                return {'action': 'sell', 'type': bsp_type}
        
        # 止损/止盈
        if self.entry_price > 0:
            current_price = row['close']
            
            # 止损
            if current_price < self.entry_price * (1 - self.stop_loss):
                self.entry_price = 0
                return {'action': 'sell', 'type': 'stop_loss'}
            
            # 止盈
            if current_price > self.entry_price * (1 + self.take_profit):
                self.entry_price = 0
                return {'action': 'sell', 'type': 'take_profit'}
        
        return None


def load_bsp_data(symbol: str, start: str, end: str, level: str = "30m") -> pd.DataFrame:
    """加载包含买卖点的数据"""
    # 从分析结果文件加载
    import os
    data_dir = os.path.dirname(os.path.abspath(__file__))
    analysis_file = os.path.join(data_dir, f"{symbol.lower().replace('.', '_')}_analysis.json")
    
    if os.path.exists(analysis_file):
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
        
        # 转换为 DataFrame
        # 这里简化处理，实际需要从历史数据构建
        pass
    
    # 返回示例数据
    dates = pd.date_range(start, end, freq='30min')
    df = pd.DataFrame({
        'open': np.random.uniform(30, 32, len(dates)),
        'high': np.random.uniform(30, 32, len(dates)),
        'low': np.random.uniform(30, 32, len(dates)),
        'close': np.random.uniform(30, 32, len(dates)),
        'volume': np.random.uniform(100000, 1000000, len(dates)),
        'bsp_type': [None] * len(dates)  # 买卖点类型
    }, index=dates)
    
    return df


if __name__ == "__main__":
    # 示例回测
    engine = BacktestEngine(
        symbol="CVE.TO",
        start_date="2025-01-01",
        end_date="2026-03-09",
        level="30m",
        initial_capital=100000
    )
    
    # 加载数据
    data = load_bsp_data("CVE.TO", "2025-01-01", "2026-03-09", "30m")
    engine.load_data(data)
    
    # 运行策略
    strategy = BSPStrategy(
        buy_types=['buy1', 'buy2'],
        sell_types=['sell1', 'sell2'],
        stop_loss=0.05,
        take_profit=0.15
    )
    
    result = engine.run(strategy)
    print(result.summary())
