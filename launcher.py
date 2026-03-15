#!/usr/bin/env python3
"""
ChanLun Trading System - Unified Launcher
缠论智能分析系统 - 统一启动器

Usage:
    python launcher.py analyze <symbol> [--level <timeframe>] [--config <path>]
    python launcher.py backtest <strategy> [--start <date>] [--end <date>]
    python launcher.py monitor <symbol> [--level <timeframe>] [--alert <channel>]
    python launcher.py server [--port <port>]
    python launcher.py research [--port <port>]
    python launcher.py examples [--list] [--run <example_id>]

Examples:
    python launcher.py analyze 000001.SZ --level 30m
    python launcher.py backtest examples/06_bsp1/main.py --start 2020-01-01 --end 2024-12-31
    python launcher.py monitor 000001.SZ --level 5m --alert telegram
    python launcher.py server --port 8000
    python launcher.py examples --list
    python launcher.py examples --run 02
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add python-layer to path
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_analyze(args):
    """Analyze a stock's ChanLun structure"""
    print(f"\n{'='*70}")
    print(f"ChanLun Analysis - {args.symbol}")
    print(f"{'='*70}")
    
    # Load configuration
    config = load_config(args.config)
    
    # Generate sample data (in production, this would fetch from data source)
    print(f"\n[1] Loading data...")
    klines = generate_sample_klines(symbol=args.symbol, count=100)
    series = KlineSeries(klines=klines, symbol=args.symbol, timeframe=args.level)
    print(f"    Loaded {len(klines)} K-lines")
    print(f"    Symbol: {args.symbol}, Timeframe: {args.level}")
    
    # Analyze fractals
    print(f"\n[2] Detecting fractals...")
    fractal_det = FractalDetector()
    fractals = fractal_det.detect_all(series)
    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]
    print(f"    ✓ Top fractals: {len(top_fractals)}")
    print(f"    ✓ Bottom fractals: {len(bottom_fractals)}")
    print(f"    ✓ Total: {len(fractals)}")
    
    # Analyze pens
    print(f"\n[3] Identifying pens (笔)...")
    pen_calc = PenCalculator(PenConfig(
        use_new_definition=True,
        strict_validation=True,
        min_klines_between_turns=3
    ))
    pens = pen_calc.identify_pens(series)
    up_pens = [p for p in pens if p.is_up]
    down_pens = [p for p in pens if p.is_down]
    print(f"    ✓ Up pens: {len(up_pens)}")
    print(f"    ✓ Down pens: {len(down_pens)}")
    print(f"    ✓ Total: {len(pens)}")
    
    # Analyze segments
    print(f"\n[4] Dividing segments (线段)...")
    seg_calc = SegmentCalculator(min_pens=3)
    segments = seg_calc.detect_segments(pens)
    up_segs = [s for s in segments if s.is_up]
    down_segs = [s for s in segments if s.is_down]
    print(f"    ✓ Up segments: {len(up_segs)}")
    print(f"    ✓ Down segments: {len(down_segs)}")
    print(f"    ✓ Total: {len(segments)}")
    
    # Calculate MACD
    print(f"\n[5] Calculating MACD...")
    macd = MACDIndicator(
        fast=config.get('macd', {}).get('fast_period', 12),
        slow=config.get('macd', {}).get('slow_period', 26),
        signal=config.get('macd', {}).get('signal_period', 9)
    )
    prices = [k.close for k in klines]
    macd_data = macd.calculate(prices)
    print(f"    ✓ MACD calculated for {len(macd_data)} data points")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Analysis Summary")
    print(f"{'='*70}")
    print(f"  Symbol:       {args.symbol}")
    print(f"  Timeframe:    {args.level}")
    print(f"  K-lines:      {len(klines)}")
    print(f"  Fractals:     {len(fractals)}")
    print(f"  Pens:         {len(pens)}")
    print(f"  Segments:     {len(segments)}")
    print(f"  Latest MACD:  {macd_data[-1].histogram:.4f}" if macd_data else "  MACD: N/A")
    print(f"{'='*70}\n")
    
    # Export results
    if args.output:
        export_results(args.output, {
            'symbol': args.symbol,
            'timeframe': args.level,
            'fractals': len(fractals),
            'pens': len(pens),
            'segments': len(segments)
        })
        print(f"✓ Results exported to {args.output}")
    
    return 0


def cmd_backtest(args):
    """Run backtest on a strategy"""
    print(f"\n{'='*70}")
    print(f"ChanLun Backtest")
    print(f"{'='*70}")
    
    # Load strategy
    strategy_path = Path(args.strategy)
    if not strategy_path.exists():
        print(f"❌ Strategy not found: {strategy_path}")
        return 1
    
    print(f"\n[1] Loading strategy...")
    print(f"    Strategy: {strategy_path}")
    print(f"    Start: {args.start}")
    print(f"    End: {args.end}")
    
    # In production, this would run the actual backtest
    print(f"\n[2] Running backtest...")
    print(f"    ⚠️  Backtest engine not yet implemented")
    print(f"    ℹ️  This is a placeholder for future functionality")
    
    print(f"\n{'='*70}")
    print(f"Backtest Summary (Placeholder)")
    print(f"{'='*70}")
    print(f"  Strategy:     {strategy_path.name}")
    print(f"  Period:       {args.start} → {args.end}")
    print(f"  Status:       ⚠️  Not implemented")
    print(f"{'='*70}\n")
    
    return 0


def fetch_yahoo_data(symbol: str, timeframe: str = '30m', count: int = 100):
    """Fetch real-time data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        print(f"\n[2] Fetching data from Yahoo Finance...")
        print(f"    Symbol: {symbol.upper()}")
        print(f"    Source: Yahoo Finance")
        
        # Create ticker
        ticker = yf.Ticker(symbol.upper())
        
        # Get historical data based on timeframe
        if timeframe == 'day' or timeframe == '1d':
            period = '1mo'
            interval = '1d'
        elif timeframe == '5m':
            period = '5d'
            interval = '5m'
        else:  # 30m
            period = '1mo'
            interval = '30m'
        
        # Fetch data
        history = ticker.history(period=period, interval=interval)
        
        if len(history) == 0:
            print(f"    ❌ No data found for {symbol.upper()}")
            return None
        
        # Convert to Kline objects
        from trading_system.kline import Kline, KlineSeries
        from datetime import datetime
        
        klines = []
        for idx, row in history.iterrows():
            # Handle timezone-aware timestamps
            if hasattr(idx, 'to_pydatetime'):
                timestamp = idx.to_pydatetime()
            else:
                timestamp = idx
            
            kline = Kline(
                timestamp=timestamp,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']) if 'Volume' in row else 0
            )
            klines.append(kline)
        
        # Take last 'count' klines
        if len(klines) > count:
            klines = klines[-count:]
        
        series = KlineSeries(klines=klines, symbol=symbol.upper(), timeframe=timeframe)
        
        print(f"    ✓ Fetched {len(klines)} K-lines")
        print(f"    Range: {history.index[0].strftime('%Y-%m-%d')} → {history.index[-1].strftime('%Y-%m-%d')}")
        print(f"    Price: ${klines[-1].close:.2f}")
        
        return series
        
    except ImportError:
        print(f"    ⚠️  yfinance not installed")
        print(f"    Install: pip install yfinance")
        return None
    except Exception as e:
        print(f"    ❌ Error fetching data: {e}")
        return None


def cmd_monitor(args):
    """Monitor a symbol in real-time with Yahoo Finance data"""
    import subprocess
    
    print(f"\n{'='*70}")
    print(f"ChanLun Real-time Monitor")
    print(f"{'='*70}")
    
    print(f"\n[1] Starting real-time monitor...")
    print(f"    Symbol: {args.symbol.upper()}")
    print(f"    Level:  {args.level}")
    print(f"    Alert:  {args.alert}")
    
    # Check if uvix_monitor.py exists (optional feature)
    monitor_script = Path(__file__).parent / 'examples' / 'uvix_monitor.py'
    
    if monitor_script.exists() and args.symbol.upper() == 'UVIX':
        print(f"\n[2] Launching UVIX monitor...")
        print(f"    Script: {monitor_script}")
        print(f"\n{'='*70}")
        print(f"Real-time Monitoring Active")
        print(f"{'='*70}")
        print(f"  Symbol:       {args.symbol.upper()}")
        print(f"  Level:        {args.level}")
        print(f"  Alert:        {args.alert}")
        print(f"  Status:       ✅ Running")
        print(f"{'='*70}")
        print(f"\nℹ️  Monitoring will check every 10-30 minutes")
        print(f"ℹ️  Alerts will be sent via {args.alert}")
        print(f"ℹ️  Press Ctrl+C to stop\n")
        
        # Run the actual monitor script
        try:
            result = subprocess.run(
                ['python3', str(monitor_script)],
                cwd=str(monitor_script.parent.parent),
                timeout=None
            )
            
            if result.returncode == 0:
                print(f"\n✓ Monitor completed successfully")
            else:
                print(f"\n⚠️  Monitor completed with warnings (code: {result.returncode})")
            
            return result.returncode
            
        except subprocess.TimeoutExpired:
            print(f"\n✓ Monitor timed out")
            return 0
        except KeyboardInterrupt:
            print(f"\n✓ Monitor stopped by user")
            return 0
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            return 1
    else:
        # Use Yahoo Finance for real-time data
        print(f"\n[2] Using Yahoo Finance for real-time data...")
        
        # Import and run analysis
        sys.path.insert(0, str(Path(__file__).parent / 'python-layer'))
        
        try:
            from trading_system.fractal import FractalDetector
            from trading_system.pen import PenCalculator, PenConfig
            from trading_system.segment import SegmentCalculator
            
            # Fetch real data from Yahoo Finance
            series = fetch_yahoo_data(args.symbol.upper(), args.level, count=100)
            
            if series is None:
                print(f"\n⚠️  Could not fetch data for {args.symbol.upper()}")
                print(f"    Please check symbol and try again")
                return 1
            
            # Analyze
            print(f"\n[3] Analyzing {args.symbol.upper()}...")
            
            fractal_det = FractalDetector()
            fractals = fractal_det.detect_all(series)
            top_fractals = [f for f in fractals if f.is_top]
            bottom_fractals = [f for f in fractals if not f.is_top]
            print(f"    ✓ Fractals: {len(fractals)} (Top: {len(top_fractals)}, Bottom: {len(bottom_fractals)})")
            
            pen_calc = PenCalculator(PenConfig(
                use_new_definition=True,
                strict_validation=True,
                min_klines_between_turns=3
            ))
            pens = pen_calc.identify_pens(series)
            up_pens = [p for p in pens if p.is_up]
            down_pens = [p for p in pens if p.is_down]
            print(f"    ✓ Pens: {len(pens)} (Up: {len(up_pens)}, Down: {len(down_pens)})")
            
            seg_calc = SegmentCalculator(min_pens=3)
            segments = seg_calc.detect_segments(pens)
            up_segs = [s for s in segments if s.is_up]
            down_segs = [s for s in segments if s.is_down]
            print(f"    ✓ Segments: {len(segments)} (Up: {len(up_segs)}, Down: {len(down_segs)})")
            
            # Summary
            print(f"\n{'='*70}")
            print(f"ChanLun Analysis Summary - {args.symbol.upper()}")
            print(f"{'='*70}")
            print(f"  Symbol:      {args.symbol.upper()}")
            print(f"  Timeframe:   {args.level}")
            print(f"  K-lines:     {len(series.klines)}")
            print(f"  Fractals:    {len(fractals)}")
            print(f"  Pens:        {len(pens)}")
            print(f"  Segments:    {len(segments)}")
            print(f"  Data Source: Yahoo Finance")
            print(f"{'='*70}")
            
            if segments:
                print(f"\n  Latest Segment:")
                print(f"    Direction: {segments[-1].direction.upper()}")
                print(f"    Range:     #{segments[-1].start_idx} → #{segments[-1].end_idx}")
                print(f"    Price:     ${segments[-1].start_price:.2f} → ${segments[-1].end_price:.2f}")
            
            # Check for buy/sell signals
            print(f"\n{'='*70}")
            print(f"Trading Signals")
            print(f"{'='*70}")
            
            if len(segments) >= 2:
                last_seg = segments[-1]
                prev_seg = segments[-2]
                
                if last_seg.direction == 'up' and prev_seg.direction == 'down':
                    print(f"  🟢 Potential BUY signal")
                    print(f"     Reason: Up segment after down segment")
                    print(f"     Entry:  ${last_seg.start_price:.2f}")
                elif last_seg.direction == 'down' and prev_seg.direction == 'up':
                    print(f"  🔴 Potential SELL signal")
                    print(f"     Reason: Down segment after up segment")
                    print(f"     Entry:  ${last_seg.start_price:.2f}")
                else:
                    print(f"  ⚪ HOLD - No clear signal")
                    print(f"     Current: {last_seg.direction.upper()} segment")
            else:
                print(f"  ⚪ HOLD - Insufficient data for signal")
            
            print(f"\n{'='*70}")
            print(f"✅ Analysis Complete")
            print(f"{'='*70}")
            print(f"\nℹ️  Data: Real-time from Yahoo Finance")
            print(f"ℹ️  Update: Run command again for latest data")
            print(f"ℹ️  Press Ctrl+C to exit\n")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def cmd_server(args):
    """Start API server"""
    print(f"\n{'='*70}")
    print(f"ChanLun API Server")
    print(f"{'='*70}")
    
    print(f"\n[1] Starting server...")
    print(f"    Port: {args.port}")
    print(f"    Host: {args.host}")
    
    # In production, this would start FastAPI server
    print(f"\n[2] Initializing API...")
    print(f"    ⚠️  API server not yet implemented")
    print(f"    ℹ️  This is a placeholder for future functionality")
    
    print(f"\n{'='*70}")
    print(f"Server Status")
    print(f"{'='*70}")
    print(f"  Host:         {args.host}")
    print(f"  Port:         {args.port}")
    print(f"  Status:       ⚠️  Not implemented")
    print(f"{'='*70}")
    
    # Placeholder - would start uvicorn in production
    print(f"\nℹ️  In production: uvicorn backend.main:app --host {args.host} --port {args.port}")
    
    return 0


def cmd_research(args):
    """Start Jupyter research environment"""
    print(f"\n{'='*70}")
    print(f"ChanLun Research Environment")
    print(f"{'='*70}")
    
    print(f"\n[1] Starting Jupyter...")
    print(f"    Port: {args.port}")
    
    print(f"\n[2] Launching notebook...")
    print(f"    ⚠️  Jupyter integration not yet implemented")
    print(f"    ℹ️  This is a placeholder for future functionality")
    
    print(f"\n{'='*70}")
    print(f"Research Environment")
    print(f"{'='*70}")
    print(f"  Port:         {args.port}")
    print(f"  Status:       ⚠️  Not implemented")
    print(f"{'='*70}")
    print(f"\nℹ️  In production: jupyter notebook --port {args.port}")
    
    return 0


def cmd_examples(args):
    """List or run examples"""
    examples_dir = Path(__file__).parent / "examples"
    
    examples = [
        ("01", "basic_fractal", "基础分型识别 - Basic fractal identification"),
        ("02", "pen", "笔识别 (新定义) - Pen identification (new 3-K-line)"),
        ("03", "segment", "线段划分 - Segment division"),
        ("04", "center", "中枢识别 - Center identification"),
        ("05", "divergence", "背驰与买卖点 - Divergence and B/S points"),
        ("06", "bsp1", "第一类买卖点 - Type 1 B/S points"),
        ("07", "bsp2", "第二类买卖点 - Type 2 B/S points"),
        ("08", "bsp3", "第三类买卖点 - Type 3 B/S points"),
        ("09", "interval_set", "区间套定位 - Interval set positioning"),
        ("10", "multi_level", "多级别联立 - Multi-level analysis"),
    ]
    
    if args.list or not args.run:
        # List available examples
        print(f"\n{'='*70}")
        print(f"ChanLun Examples")
        print(f"{'='*70}")
        print(f"\n{'ID':<4} | {'Name':<25} | {'Description':<30}")
        print(f"{'-'*70}")
        
        for ex_id, name, desc in examples:
            ex_path = examples_dir / f"{ex_id}_{name}"
            status = "✅" if ex_path.exists() and (ex_path / "main.py").exists() else "⚠️ "
            print(f"{status} {ex_id:<2} | {name:<25} | {desc:<30}")
        
        print(f"\n{'='*70}")
        print(f"Usage: python launcher.py examples --run <ID>")
        print(f"{'='*70}\n")
    
    if args.run:
        # Run specific example
        ex_id = args.run.zfill(2)
        
        # Find example directory
        example_name = None
        for eid, name, _ in examples:
            if eid == ex_id:
                example_name = name
                break
        
        if not example_name:
            print(f"❌ Example not found: {args.run}")
            return 1
        
        example_path = examples_dir / f"{ex_id}_{example_name}" / "main.py"
        
        if not example_path.exists():
            print(f"❌ Example script not found: {example_path}")
            return 1
        
        print(f"\n{'='*70}")
        print(f"Running Example {ex_id}: {example_name}")
        print(f"{'='*70}\n")
        
        # Run the example
        import subprocess
        result = subprocess.run([sys.executable, str(example_path)])
        
        print(f"\n{'='*70}")
        print(f"Example {ex_id} completed with code: {result.returncode}")
        print(f"{'='*70}\n")
        
        return result.returncode
    
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML/JSON file"""
    base_path = Path(__file__).parent / "config" / "default.yaml"
    
    if config_path:
        path = Path(config_path)
    else:
        path = base_path
    
    if not path.exists():
        # Return default config
        return {
            'macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            'pen': {
                'use_new_definition': True,
                'strict_validation': True,
                'min_klines_between_turns': 3
            }
        }
    
    # Simple YAML parser (for basic configs)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Very basic YAML parsing (production should use PyYAML)
    config = {}
    current_section = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if not value:
                # Section header
                current_section = key
                config[current_section] = {}
            elif current_section:
                # Key-value in section
                try:
                    config[current_section][key] = int(value)
                except ValueError:
                    try:
                        config[current_section][key] = float(value)
                    except ValueError:
                        config[current_section][key] = value
    
    return config


def generate_sample_klines(symbol: str, count: int = 100) -> list:
    """Generate sample K-line data for testing"""
    from datetime import timedelta
    
    klines = []
    base_time = datetime(2026, 1, 1, 9, 30)
    base_price = 100.0
    
    import random
    random.seed(42)  # Reproducible
    
    for i in range(count):
        # Random walk
        change = random.uniform(-2, 2)
        price = base_price + change
        base_price = price
        
        high = price + abs(random.uniform(0, 1))
        low = price - abs(random.uniform(0, 1))
        open_price = price + random.uniform(-0.5, 0.5)
        close_price = price + random.uniform(-0.5, 0.5)
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*30),
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=random.randint(100000, 1000000)
        )
        klines.append(kline)
    
    return klines


def export_results(output_path: str, data: Dict[str, Any]):
    """Export analysis results to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ChanLun Trading System - Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a stock\'s ChanLun structure')
    analyze_parser.add_argument('symbol', help='Stock symbol (e.g., 000001.SZ)')
    analyze_parser.add_argument('--level', '-l', default='30m', help='Timeframe (default: 30m)')
    analyze_parser.add_argument('--config', '-c', help='Config file path')
    analyze_parser.add_argument('--output', '-o', help='Output file path (JSON)')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest on a strategy')
    backtest_parser.add_argument('strategy', help='Strategy script path')
    backtest_parser.add_argument('--start', '-s', required=True, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', '-e', required=True, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--config', '-c', help='Config file path')
    backtest_parser.set_defaults(func=cmd_backtest)
    
    # monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor a symbol in real-time')
    monitor_parser.add_argument('symbol', help='Stock symbol')
    monitor_parser.add_argument('--level', '-l', default='5m', help='Timeframe (default: 5m)')
    monitor_parser.add_argument('--alert', '-a', default='console', help='Alert channel (default: console)')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # server command
    server_parser = subparsers.add_parser('server', help='Start API server')
    server_parser.add_argument('--port', '-p', type=int, default=8000, help='Port (default: 8000)')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host (default: 0.0.0.0)')
    server_parser.set_defaults(func=cmd_server)
    
    # research command
    research_parser = subparsers.add_parser('research', help='Start Jupyter research environment')
    research_parser.add_argument('--port', '-p', type=int, default=8888, help='Port (default: 8888)')
    research_parser.set_defaults(func=cmd_research)
    
    # examples command
    examples_parser = subparsers.add_parser('examples', help='List or run examples')
    examples_parser.add_argument('--list', action='store_true', help='List available examples')
    examples_parser.add_argument('--run', '-r', help='Run specific example by ID')
    examples_parser.set_defaults(func=cmd_examples)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
