"""
ChanLun Backtest Engine - 缠论回测引擎
基于历史数据测试买卖点成功率和盈利能力

Usage:
    from trading_system.backtest import BacktestEngine
    
    engine = BacktestEngine(
        symbol='AAPL',
        start_date='2025-01-01',
        end_date='2026-03-19',
        initial_capital=100000
    )
    
    results = engine.run()
    report = engine.generate_report()
"""

import yfinance as yf
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .monitor import ChanLunMonitor, MonitorConfig, AnalysisResult
from .kline import Kline, KlineSeries


@dataclass
class Trade:
    """交易记录"""
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    direction: str = 'BUY'  # BUY or SELL
    shares: int = 0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: str = ''  # TARGET, STOP_LOSS, SIGNAL
    duration_days: int = 0


@dataclass
class BacktestConfig:
    """回测配置"""
    symbol: str = 'AAPL'
    start_date: str = '2025-01-01'
    end_date: str = '2026-12-31'
    initial_capital: float = 100000.0
    position_size_pct: float = 0.1  # 每次交易使用 10% 资金
    stop_loss_pct: float = 0.03  # 3% 止损
    take_profit_pct: float = 0.05  # 5% 止盈
    signal_threshold: float = 4.0  # 信号强度阈值 (≥4 才交易)
    timeframes: List[str] = field(default_factory=lambda: ['1d', '30m', '5m'])


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)


class BacktestEngine:
    """缠论回测引擎"""
    
    def __init__(self, config: BacktestConfig = None):
        """
        初始化回测引擎
        
        Args:
            config: 回测配置
        """
        self.config = config or BacktestConfig()
        self.monitor = ChanLunMonitor()
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.current_capital = self.config.initial_capital
        self.current_position: Optional[Trade] = None
        
    def fetch_historical_data(self) -> Optional[KlineSeries]:
        """获取历史数据"""
        try:
            ticker = yf.Ticker(self.config.symbol)
            history = ticker.history(
                start=self.config.start_date,
                end=self.config.end_date,
                interval='1d'
            )
            
            if len(history) == 0:
                return None
            
            klines = []
            for idx, row in history.iterrows():
                kline = Kline(
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if 'Volume' in row else 0
                )
                klines.append(kline)
            
            return KlineSeries(
                klines=klines,
                symbol=self.config.symbol,
                timeframe='1d'
            )
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def run(self) -> BacktestResult:
        """运行回测"""
        print(f"\n🚀 开始回测 {self.config.symbol}")
        print(f"📅 期间：{self.config.start_date} ~ {self.config.end_date}")
        print(f"💰 初始资金：${self.config.initial_capital:,.2f}")
        print(f"{'='*70}")
        
        # 获取历史数据
        data = self.fetch_historical_data()
        if not data or len(data.klines) == 0:
            print("❌ 无法获取历史数据")
            return self._create_empty_result()
        
        print(f"✓ 获取 {len(data.klines)} 根 K 线")
        
        # 初始化
        self.current_capital = self.config.initial_capital
        self.trades = []
        self.equity_curve = []
        self.current_position = None
        
        # 滚动回测
        print(f"\n📊 运行回测...")
        for i in range(100, len(data.klines)):
            # 截取到当前的数据
            current_data = KlineSeries(
                klines=data.klines[:i+1],
                symbol=self.config.symbol,
                timeframe='1d'
            )
            
            # 获取当前 K 线
            current_kline = data.klines[i]
            current_date = current_kline.timestamp.strftime('%Y-%m-%d')
            current_price = current_kline.close
            
            # 检查是否需要平仓
            if self.current_position:
                self._check_exit(current_price, current_date)
            
            # 检查是否有交易信号
            if not self.current_position:
                self._check_entry(current_data, current_price, current_date)
            
            # 记录权益曲线
            portfolio_value = self.current_capital
            if self.current_position:
                portfolio_value += self.current_position.shares * current_price
            
            self.equity_curve.append({
                'date': current_date,
                'equity': portfolio_value,
                'price': current_price,
                'position': 1 if self.current_position else 0
            })
        
        # 平仓所有未平仓头寸
        if self.current_position and len(data.klines) > 0:
            last_kline = data.klines[-1]
            self._force_exit(
                last_kline.close,
                last_kline.timestamp.strftime('%Y-%m-%d'),
                'END_OF_BACKTEST'
            )
        
        # 生成结果
        result = self._generate_result()
        
        # 打印摘要
        self._print_summary(result)
        
        return result
    
    def _check_entry(self, data: KlineSeries, price: float, date: str):
        """检查入场信号"""
        try:
            # 使用监控器分析
            result = self.monitor.analyze(self.config.symbol, self.config.timeframes)
            
            if not result:
                return
            
            # 检查信号强度
            if abs(result.strength) < self.config.signal_threshold:
                return
            
            # 决定交易方向
            direction = 'BUY' if result.strength > 0 else 'SELL'
            
            # 计算仓位
            position_value = self.current_capital * self.config.position_size_pct
            shares = int(position_value / price)
            
            if shares <= 0:
                return
            
            # 创建交易记录
            trade = Trade(
                symbol=self.config.symbol,
                entry_date=date,
                entry_price=price,
                direction=direction,
                shares=shares
            )
            
            self.current_position = trade
            self.current_capital -= shares * price
            
            print(f"  🟢 {'买入' if direction == 'BUY' else '卖出'} @ ${price:.2f} × {shares}股 (信号强度：{result.strength:+.1f})")
            
        except Exception as e:
            pass  # 忽略分析错误
    
    def _check_exit(self, current_price: float, date: str):
        """检查出场信号"""
        if not self.current_position:
            return
        
        entry_price = self.current_position.entry_price
        direction = self.current_position.direction
        
        # 计算盈亏
        if direction == 'BUY':
            pnl_percent = (current_price - entry_price) / entry_price
        else:
            pnl_percent = (entry_price - current_price) / entry_price
        
        # 检查止损
        if pnl_percent <= -self.config.stop_loss_pct:
            self._exit_position(current_price, date, 'STOP_LOSS')
            return
        
        # 检查止盈
        if pnl_percent >= self.config.take_profit_pct:
            self._exit_position(current_price, date, 'TARGET')
            return
        
        # 检查反向信号 (简单版本：信号反转就平仓)
        # 实际应该更复杂
    
    def _exit_position(self, price: float, date: str, reason: str):
        """平仓"""
        if not self.current_position:
            return
        
        trade = self.current_position
        
        # 计算盈亏
        if trade.direction == 'BUY':
            pnl = (price - trade.entry_price) * trade.shares
        else:
            pnl = (trade.entry_price - price) * trade.shares
        
        pnl_percent = pnl / (trade.entry_price * trade.shares)
        
        # 更新交易记录
        trade.exit_date = date
        trade.exit_price = price
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.exit_reason = reason
        
        # 计算持仓天数
        entry_dt = datetime.strptime(trade.entry_date, '%Y-%m-%d')
        exit_dt = datetime.strptime(date, '%Y-%m-%d')
        trade.duration_days = (exit_dt - entry_dt).days
        
        # 回收资金
        self.current_capital += trade.shares * price + pnl
        
        # 保存交易记录
        self.trades.append(trade)
        
        action = '✅' if pnl > 0 else '❌'
        print(f"  {action} 平仓 @ ${price:.2f} | 盈亏：${pnl:+,.2f} ({pnl_percent:+.2%}) | 原因：{reason}")
        
        # 清空持仓
        self.current_position = None
    
    def _force_exit(self, price: float, date: str, reason: str):
        """强制平仓"""
        if self.current_position:
            self._exit_position(price, date, reason)
    
    def _generate_result(self) -> BacktestResult:
        """生成回测结果"""
        # 计算总收益
        final_capital = self.current_capital
        if self.current_position:
            # 如果有未平仓头寸，按最后价格计算
            pass
        
        total_return = final_capital - self.config.initial_capital
        total_return_pct = total_return / self.config.initial_capital
        
        # 计算交易统计
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = sum(1 for t in self.trades if t.pnl <= 0)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # 计算平均盈亏
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        
        # 计算盈利因子
        gross_profit = sum(profits) if profits else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        # 计算最大回撤
        equity_values = [point['equity'] for point in self.equity_curve]
        
        if not equity_values:
            max_drawdown = 0.0
            max_drawdown_pct = 0.0
        else:
            peak = equity_values[0]
            max_drawdown = 0.0
            
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            max_drawdown_pct = max_drawdown * 100
        
        # 计算夏普比率 (简化版)
        if len(equity_values) > 1:
            returns = []
            for i in range(1, len(equity_values)):
                ret = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                returns.append(ret)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        return BacktestResult(
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_capital=self.config.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct * 100,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate * 100,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            trades=self.trades,
            equity_curve=self.equity_curve
        )
    
    def _create_empty_result(self) -> BacktestResult:
        """创建空结果"""
        return BacktestResult(
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_capital=self.config.initial_capital,
            final_capital=self.config.initial_capital,
            total_return=0.0,
            total_return_pct=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            avg_profit=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            trades=[],
            equity_curve=[]
        )
    
    def _print_summary(self, result: BacktestResult):
        """打印回测摘要"""
        print(f"\n{'='*70}")
        print(f"📊 回测结果摘要")
        print(f"{'='*70}")
        
        print(f"\n💰 收益统计:")
        print(f"  初始资金：${result.initial_capital:,.2f}")
        print(f"  最终资金：${result.final_capital:,.2f}")
        print(f"  总收益：${result.total_return:,.2f} ({result.total_return_pct:+.2f}%)")
        
        print(f"\n📈 交易统计:")
        print(f"  总交易次数：{result.total_trades}")
        print(f"  盈利交易：{result.winning_trades}")
        print(f"  亏损交易：{result.losing_trades}")
        print(f"  胜率：{result.win_rate:.1f}%")
        
        print(f"\n📊 盈亏统计:")
        print(f"  平均盈利：${result.avg_profit:,.2f}")
        print(f"  平均亏损：${result.avg_loss:,.2f}")
        print(f"  盈利因子：{result.profit_factor:.2f}")
        
        print(f"\n⚠️  风险统计:")
        print(f"  最大回撤：{result.max_drawdown_pct:.2f}%")
        print(f"  夏普比率：{result.sharpe_ratio:.2f}")
        
        print(f"\n{'='*70}")
    
    def generate_report(self, output_path: str = None) -> Dict[str, Any]:
        """生成回测报告"""
        result = self._generate_result()
        
        report = {
            'summary': {
                'symbol': result.symbol,
                'period': f"{result.start_date} ~ {result.end_date}",
                'initial_capital': result.initial_capital,
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
            },
            'performance': {
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'avg_profit': result.avg_profit,
                'avg_loss': result.avg_loss,
                'profit_factor': result.profit_factor,
            },
            'risk': {
                'max_drawdown': result.max_drawdown,
                'max_drawdown_pct': result.max_drawdown_pct,
                'sharpe_ratio': result.sharpe_ratio,
            },
            'trades': [
                {
                    'symbol': t.symbol,
                    'entry_date': t.entry_date,
                    'entry_price': t.entry_price,
                    'exit_date': t.exit_date,
                    'exit_price': t.exit_price,
                    'direction': t.direction,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'exit_reason': t.exit_reason
                }
                for t in result.trades
            ]
        }
        
        # 保存报告
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📝 报告已保存：{output_file}")
        
        return report
