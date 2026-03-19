#!/usr/bin/env python3
"""
ChanLun Backtest CLI - 缠论回测命令行工具

Usage:
    python3 backtest.py AAPL --start 2025-01-01 --end 2026-03-19
    python3 backtest.py TSLA --capital 50000 --report results/tsla_backtest.json
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system.backtest import BacktestEngine, BacktestConfig


def main():
    parser = argparse.ArgumentParser(
        description='缠论回测系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s AAPL --start 2025-01-01 --end 2026-03-19
  %(prog)s TSLA --capital 50000 --report results/tsla.json
  %(prog)s NVDA --threshold 3.0 --stop-loss 0.05
        """
    )
    
    parser.add_argument('symbol', help='股票代码 (如：AAPL, TSLA)')
    parser.add_argument('--start', '-s', default='2025-01-01',
                       help='开始日期 (默认：2025-01-01)')
    parser.add_argument('--end', '-e', default='2026-12-31',
                       help='结束日期 (默认：2026-12-31)')
    parser.add_argument('--capital', '-c', type=float, default=100000,
                       help='初始资金 (默认：100000)')
    parser.add_argument('--position-size', '-p', type=float, default=0.1,
                       help='仓位比例 (默认：0.1=10%%)')
    parser.add_argument('--stop-loss', type=float, default=0.03,
                       help='止损比例 (默认：0.03=3%%)')
    parser.add_argument('--take-profit', type=float, default=0.05,
                       help='止盈比例 (默认：0.05=5%%)')
    parser.add_argument('--threshold', '-t', type=float, default=4.0,
                       help='信号强度阈值 (默认：4.0)')
    parser.add_argument('--report', '-r', help='保存报告到 JSON 文件')
    parser.add_argument('--levels', '-L', default='1d,30m,5m',
                       help='分析级别 (默认：1d,30m,5m)')
    
    args = parser.parse_args()
    
    # 创建配置
    config = BacktestConfig(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        position_size_pct=args.position_size,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        signal_threshold=args.threshold,
        timeframes=args.levels.split(',')
    )
    
    # 运行回测
    try:
        engine = BacktestEngine(config)
        result = engine.run()
        
        # 保存报告
        if args.report:
            engine.generate_report(args.report)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 回测失败：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
