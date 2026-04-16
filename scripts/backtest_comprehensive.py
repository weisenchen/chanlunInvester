#!/usr/bin/env python3
"""
综合置信度引擎 - 回测脚本
Comprehensive Confidence Engine - Backtest Script

验证 Phase 4 验收标准:
- 综合准确率≥80%
- 置信度误差<10%
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from trading_system.kline import Kline, KlineSeries
from scripts.comprehensive_confidence_engine import ComprehensiveConfidenceEngine, ComprehensiveSignal

import yfinance as yf


@dataclass
class BacktestResult:
    """回测结果"""
    symbol: str
    signal_date: datetime
    signal_price: float
    comprehensive_confidence: float
    recommendation: str
    position_ratio: float
    
    # 结果跟踪
    actual_return: float = 0.0  # 实际收益
    is_correct: bool = False  # 建议是否正确
    confidence_error: float = 0.0  # 置信度误差


class ComprehensiveBacktester:
    """综合置信度回测器"""
    
    def __init__(self, symbol_list: List[str], start_date: str, end_date: str):
        self.symbol_list = symbol_list
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.engine = ComprehensiveConfidenceEngine()
        self.results: List[BacktestResult] = []
    
    def fetch_data(self, symbol: str) -> Optional[KlineSeries]:
        """获取历史数据"""
        try:
            data = yf.Ticker(symbol).history(
                start=self.start_date - timedelta(days=90),
                end=self.end_date,
                interval='1d'
            )
            
            if len(data) == 0:
                return None
            
            klines = []
            for idx, row in data.iterrows():
                kline = Kline(
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row.get('Volume', 0))
                )
                klines.append(kline)
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe='1d')
            
        except Exception as e:
            print(f"❌ {symbol} 数据获取失败：{e}")
            return None
    
    def detect_signals(self, series: KlineSeries) -> List[ComprehensiveSignal]:
        """检测综合信号"""
        signals = []
        
        # 滚动检测
        for i in range(60, len(series.klines)):
            partial_series = KlineSeries(
                klines=series.klines[:i+1],
                symbol=series.symbol,
                timeframe=series.timeframe
            )
            
            signal = self.engine.evaluate(partial_series, series.symbol, '1d')
            
            # 记录非 HOLD 信号
            if signal.recommendation != 'HOLD':
                signals.append(signal)
        
        return signals
    
    def track_performance(self, signal: ComprehensiveSignal, series: KlineSeries, 
                         signal_idx: int, hold_days: int = 20) -> BacktestResult:
        """跟踪表现"""
        result = BacktestResult(
            symbol=signal.symbol,
            signal_date=signal.timestamp,
            signal_price=series.klines[signal_idx].close,
            comprehensive_confidence=signal.comprehensive_confidence,
            recommendation=signal.recommendation,
            position_ratio=signal.position_ratio
        )
        
        # 跟踪持有期表现
        exit_idx = min(signal_idx + hold_days, len(series.klines) - 1)
        exit_price = series.klines[exit_idx].close
        result.actual_return = (exit_price - result.signal_price) / result.signal_price
        
        # 判断建议是否正确
        if signal.recommendation in ['STRONG_BUY', 'BUY']:
            # 买入建议，实际收益>0 为正确
            result.is_correct = result.actual_return > 0
        elif signal.recommendation in ['STRONG_SELL', 'SELL']:
            # 卖出建议，实际收益<0 为正确
            result.is_correct = result.actual_return < 0
        else:
            result.is_correct = True  # HOLD 视为正确
        
        # 计算置信度误差
        expected_return = signal.comprehensive_confidence * 0.1  # 期望收益 = 置信度 * 10%
        result.confidence_error = abs(result.actual_return - expected_return)
        
        return result
    
    def run_backtest(self) -> Dict:
        """运行回测"""
        print("=" * 70)
        print("综合置信度引擎 - 回测验证")
        print("=" * 70)
        print(f"回测时间：{self.start_date.strftime('%Y-%m-%d')} 至 {self.end_date.strftime('%Y-%m-%d')}")
        print(f"回测标的：{self.symbol_list}")
        print("=" * 70)
        
        all_results = []
        
        for symbol in self.symbol_list:
            print(f"\n📊 {symbol}...")
            
            # 获取数据
            series = self.fetch_data(symbol)
            if series is None:
                print(f"  ❌ 数据获取失败")
                continue
            
            print(f"  数据：{len(series.klines)} 根 K 线")
            
            # 检测信号
            signals = self.detect_signals(series)
            print(f"  综合信号：{len(signals)} 个")
            
            # 跟踪表现
            for i, signal in enumerate(signals):
                signal_idx = len(series.klines) - len(signals) + i
                
                if signal_idx < len(series.klines) - 20:  # 至少有 20 天跟踪期
                    result = self.track_performance(signal, series, signal_idx)
                    all_results.append(result)
        
        # 统计结果
        return self._calculate_statistics(all_results)
    
    def _calculate_statistics(self, results: List[BacktestResult]) -> Dict:
        """计算统计数据"""
        if len(results) == 0:
            return {'error': 'No results'}
        
        total_signals = len(results)
        correct_signals = sum(1 for r in results if r.is_correct)
        accuracy = correct_signals / total_signals if total_signals > 0 else 0
        
        avg_confidence_error = np.mean([r.confidence_error for r in results])
        avg_return = np.mean([r.actual_return for r in results])
        
        stats = {
            'total_signals': total_signals,
            'correct_signals': correct_signals,
            'incorrect_signals': total_signals - correct_signals,
            'accuracy': accuracy,
            'avg_confidence_error': avg_confidence_error,
            'avg_return': avg_return,
            'results': results
        }
        
        # 打印统计
        self._print_statistics(stats)
        
        return stats
    
    def _print_statistics(self, stats: Dict):
        """打印统计结果"""
        print("\n" + "=" * 70)
        print("回测统计")
        print("=" * 70)
        print(f"总信号数：        {stats['total_signals']} 个")
        print(f"正确建议：        {stats['correct_signals']} 个")
        print(f"错误建议：        {stats['incorrect_signals']} 个")
        print(f"综合准确率：      {stats['accuracy']*100:.1f}%")
        print(f"平均置信度误差：  {stats['avg_confidence_error']*100:.2f}%")
        print(f"平均收益：        {stats['avg_return']*100:.2f}%")
        print("=" * 70)
        
        # 验收标准对比
        print("\n验收标准对比:")
        print(f"  综合准确率：      {stats['accuracy']*100:.1f}% / 80% {'✅' if stats['accuracy'] >= 0.80 else '❌'}")
        print(f"  置信度误差：      {stats['avg_confidence_error']*100:.2f}% / 10% {'✅' if stats['avg_confidence_error'] < 0.10 else '❌'}")
        print(f"  样本数量：        {stats['total_signals']} 个 / 50 个 {'✅' if stats['total_signals'] >= 50 else '❌'}")
        print("=" * 70)


def main():
    """主函数"""
    # 回测配置
    SYMBOL_LIST = ['TSLA', 'NVDA', 'AMD', 'COIN', 'PLTR', 'SMR', 'IONQ', 'RKLB']
    START_DATE = '2024-01-01'
    END_DATE = '2026-04-16'
    
    print(f"回测配置:")
    print(f"  标的：{SYMBOL_LIST}")
    print(f"  时间：{START_DATE} 至 {END_DATE}")
    print()
    
    # 运行回测
    backtester = ComprehensiveBacktester(SYMBOL_LIST, START_DATE, END_DATE)
    stats = backtester.run_backtest()
    
    # 检查验收标准
    print("\n验收结论:")
    if 'error' in stats:
        print(f"  ❌ 回测错误：{stats['error']}")
        return 1
    elif stats['accuracy'] >= 0.80 and stats['avg_confidence_error'] < 0.10:
        print("  ✅ Phase 4 回测通过验收标准")
        return 0
    else:
        print("  ❌ Phase 4 回测未通过验收标准")
        return 1


if __name__ == '__main__':
    sys.exit(main())
