#!/usr/bin/env python3
"""
热门股票 + ETF 多级别共振扫描
Hot Stocks & ETF Multi-Level Resonance Scanner

基于同样的共振过滤条件，扫描热门股票和 ETF 的买卖点机会
每个交易日开盘前和收盘前生成分析报告

功能:
- 扫描热门股票/ETF 池
- 应用多级别共振过滤
- 生成买卖点分析报告
- 定时推送 (开盘前 1h + 收盘前 1h)
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator

# ==================== 配置 ====================

TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
REPORT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/hot_stocks_reports.log"
OPENCLAW_PATH = "/home/linuxbrew/.linuxbrew/bin/openclaw"

# 多级别共振过滤配置 (与 monitor_all.py 一致)
ENABLE_RESONANCE_FILTER = True
RESONANCE_MIN_CONFIDENCE = 0.75

# 热门股票 + ETF 池 (按板块分类)
HOT_STOCKS = {
    # AI/芯片
    'AI/芯片': [
        'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM', 'MU',
        'AMAT', 'LRCX', 'KLAC', 'MRVL', 'NXPI'
    ],
    # 科技巨头
    '科技巨头': [
        'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN',
        'NFLX', 'CRM', 'ORCL', 'ADBE'
    ],
    # AI 应用
    'AI 应用': [
        'TSLA', 'PLTR', 'SNOW', 'PANW', 'CRWD',
        'ZS', 'NET', 'DDOG'
    ],
    # 半导体设备
    '半导体设备': [
        'ASML', 'TSM', 'AMAT', 'LRCX', 'KLAC',
        'TEL', 'APH'
    ],
    # 金融
    '金融': [
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        'BLK', 'SCHW', 'AXP'
    ],
    # 医疗
    '医疗': [
        'JNJ', 'UNH', 'PFE', 'MRK', 'ABBV',
        'TMO', 'ABT', 'DHR'
    ],
    # 消费
    '消费': [
        'WMT', 'PG', 'KO', 'PEP', 'COST',
        'MCD', 'NKE', 'SBUX'
    ],
    # ETF
    'ETF': [
        'QQQ', 'SPY', 'SOXX', 'SMH', 'XLK',
        'VGT', 'ARKK', 'IWM', 'DIA', 'VTI'
    ],
}

# 监控级别配置
LEVEL_CONFIG = {
    '1d': {'period': '60d', 'interval': '1d'},
    '30m': {'period': '10d', 'interval': '30m'},
}


# ==================== 数据结构 ====================

@dataclass
class StockSignal:
    """股票信号"""
    symbol: str
    sector: str
    price: float
    daily_signal: Optional[dict] = None
    thirty_min_signal: Optional[dict] = None
    resonance: str = 'none'  # none, confirmed, high_confidence
    confidence: float = 0.0
    reasoning: List[str] = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


@dataclass
class SectorSummary:
    """板块汇总"""
    sector_name: str
    total_stocks: int
    resonance_count: int
    buy_signals: int
    sell_signals: int
    top_picks: List[StockSignal] = None
    
    def __post_init__(self):
        if self.top_picks is None:
            self.top_picks = []


# ==================== 核心分析器 ====================

class HotStocksResonanceScanner:
    """热门股票共振扫描器"""
    
    def __init__(self):
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def fetch_data(self, symbol: str, timeframe: str) -> Optional[KlineSeries]:
        """获取数据"""
        try:
            import yfinance as yf
            
            config = LEVEL_CONFIG.get(timeframe, LEVEL_CONFIG['30m'])
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=config['period'], interval=config['interval'])
            
            if len(history) == 0:
                return None
            
            klines = []
            for idx, row in history.iterrows():
                timestamp = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx
                kline = Kline(
                    timestamp=timestamp,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row.get('Volume', 0))
                )
                klines.append(kline)
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
            
        except Exception as e:
            print(f"❌ {symbol} {timeframe}: {e}")
            return None
    
    def detect_signals(self, series: KlineSeries, level: str) -> List[dict]:
        """检测买卖点"""
        fractals = self.fractal_detector.detect_all(series)
        pens = self.pen_calculator.identify_pens(series)
        segments = self.segment_calculator.detect_segments(pens)
        
        prices = [k.close for k in series.klines]
        macd_data = self.macd.calculate(prices)
        
        signals = []
        
        if len(fractals) < 4 or len(pens) < 4:
            return signals
        
        # 获取最近的分型
        top_fractals = [f for f in fractals if f.is_top][-3:]
        bottom_fractals = [f for f in fractals if not f.is_top][-3:]
        
        current_price = series.klines[-1].close
        last_pen = pens[-1]
        current_trend = 'up' if last_pen.is_up else 'down'
        
        # 阈值配置
        thresholds = {
            '30m': {'bsp2': 0.015, 'bsp1': 3.0},
            '1d': {'bsp2': 0.03, 'bsp1': 5.0}
        }
        thresh = thresholds.get(level, thresholds['30m'])
        
        # 第二类买点
        if len(bottom_fractals) >= 2 and current_trend == 'up':
            last_low = bottom_fractals[-1]
            prev_low = bottom_fractals[-2]
            
            # Fractal uses kline_index, not index
            if last_low.kline_index > prev_low.kline_index and last_low.price > prev_low.price * (1 - thresh['bsp2']):
                confidence = min(0.9, 0.7 + (last_low.price - prev_low.price) / prev_low.price * 10)
                signals.append({
                    'type': 'buy2',
                    'name': f'{level}级别第二类买点',
                    'price': current_price,
                    'confidence': confidence,
                    'description': f'{level}级别回调确认，上涨趋势延续'
                })
        
        # 第二类卖点
        if len(top_fractals) >= 2 and current_trend == 'down':
            last_high = top_fractals[-1]
            prev_high = top_fractals[-2]
            
            # Fractal uses kline_index, not index
            if last_high.kline_index > prev_high.kline_index and last_high.price < prev_high.price * (1 + thresh['bsp2']):
                confidence = min(0.9, 0.7 + (prev_high.price - last_high.price) / prev_high.price * 10)
                signals.append({
                    'type': 'sell2',
                    'name': f'{level}级别第二类卖点',
                    'price': current_price,
                    'confidence': confidence,
                    'description': f'{level}级别反弹确认，下跌趋势延续'
                })
        
        return signals
    
    def check_resonance(self, daily_signals: List[dict], thirty_min_signals: List[dict]) -> tuple:
        """
        检查多级别共振
        
        Returns:
            (resonance_type, confidence, selected_signal)
        """
        if not daily_signals and not thirty_min_signals:
            return ('none', 0.0, None)
        
        # 多级别共振确认
        for signal_30m in thirty_min_signals:
            signal_type_30m = signal_30m['type'].split()[0]
            
            for signal_1d in daily_signals:
                signal_type_1d = signal_1d['type'].split()[0]
                
                is_buy = signal_type_30m.startswith('buy') and signal_type_1d.startswith('buy')
                is_sell = signal_type_30m.startswith('sell') and signal_type_1d.startswith('sell')
                
                if is_buy or is_sell:
                    # 共振确认！
                    confidence = max(signal_30m.get('confidence', 0.8), 0.85)
                    return ('confirmed', confidence, {
                        **signal_30m,
                        'parent_signal': signal_1d,
                        'resonance': 'multi_level_confirmed'
                    })
        
        # 高置信度单级别信号
        for sig in thirty_min_signals:
            conf = sig.get('confidence', 0)
            if conf >= RESONANCE_MIN_CONFIDENCE:
                return ('high_confidence', conf, {**sig, 'resonance': 'single_level_high_confidence'})
        
        return ('none', 0.0, None)
    
    def analyze_stock(self, symbol: str, sector: str) -> Optional[StockSignal]:
        """分析单只股票"""
        # 获取数据
        daily_series = self.fetch_data(symbol, '1d')
        thirty_min_series = self.fetch_data(symbol, '30m')
        
        if not daily_series or not thirty_min_series:
            return None
        
        # 检测信号
        daily_signals = self.detect_signals(daily_series, '1d')
        thirty_min_signals = self.detect_signals(thirty_min_series, '30m')
        
        # 检查共振
        resonance_type, confidence, selected_signal = self.check_resonance(
            daily_signals, thirty_min_signals
        )
        
        if resonance_type == 'none':
            return None
        
        # 构建信号对象
        reasoning = []
        if resonance_type == 'confirmed':
            reasoning.append(f"多级别共振确认：1d {selected_signal['parent_signal']['type']} + 30m {selected_signal['type']}")
        else:
            reasoning.append(f"高置信度单级别信号：30m {selected_signal['type']} (置信度{confidence*100:.0f}%)")
        
        return StockSignal(
            symbol=symbol,
            sector=sector,
            price=thirty_min_series.klines[-1].close,
            daily_signal=daily_signals[0] if daily_signals else None,
            thirty_min_signal=thirty_min_signals[0] if thirty_min_signals else None,
            resonance=resonance_type,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def scan_all(self) -> Dict[str, List[StockSignal]]:
        """扫描所有热门股票"""
        results = {}
        
        for sector, stocks in HOT_STOCKS.items():
            print(f"\n📊 扫描板块：{sector} ({len(stocks)}只)")
            sector_signals = []
            
            for symbol in stocks:
                try:
                    signal = self.analyze_stock(symbol, sector)
                    if signal:
                        sector_signals.append(signal)
                        print(f"  ✅ {symbol}: {signal.resonance} (置信度{signal.confidence*100:.0f}%)")
                except Exception as e:
                    print(f"  ❌ {symbol}: {e}")
            
            results[sector] = sector_signals
        
        return results
    
    def generate_report(self, results: Dict[str, List[StockSignal]], report_type: str) -> str:
        """生成分析报告"""
        total_resonance = sum(len(signals) for signals in results.values())
        total_buy = sum(1 for signals in results.values() for s in signals if s.thirty_min_signal and s.thirty_min_signal['type'].startswith('buy'))
        total_sell = sum(1 for signals in results.values() for s in signals if s.thirty_min_signal and s.thirty_min_signal['type'].startswith('sell'))
        
        message = f"""📊 **热门股票 + ETF 共振分析报告**

📅 日期：{datetime.now().strftime('%Y-%m-%d')}
⏰ 时间：{datetime.now().strftime('%H:%M')} EDT
📝 类型：{report_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **市场概览**
• 扫描板块：{len(HOT_STOCKS)}个
• 共振信号：{total_resonance}只
• 买入信号：{total_buy}只
• 卖出信号：{total_sell}只

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # 按板块详细报告
        for sector, signals in results.items():
            if signals:
                emoji = '🟢' if all(s.thirty_min_signal and s.thirty_min_signal['type'].startswith('buy') for s in signals) else \
                        '🔴' if all(s.thirty_min_signal and s.thirty_min_signal['type'].startswith('sell') for s in signals) else '🔄'
                
                message += f"\n{emoji} **{sector}** ({len(signals)}只)\n"
                
                for signal in sorted(signals, key=lambda x: x.confidence, reverse=True)[:3]:  # 只显示前 3 只
                    signal_emoji = '🟢' if signal.thirty_min_signal and signal.thirty_min_signal['type'].startswith('buy') else '🔴'
                    resonance_badge = '✅ 共振' if signal.resonance == 'confirmed' else '🎯 高信'
                    
                    message += f"• {signal_emoji} {signal.symbol} @ ${signal.price:.2f}\n"
                    message += f"  {resonance_badge} 置信度{signal.confidence*100:.0f}%\n"
        
        if total_resonance == 0:
            message += "\n⚪ **当前无共振确认信号**\n市场处于震荡整理，等待方向明确"
        
        message += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"💡 **操作建议**\n"
        
        if total_resonance == 0:
            message += "• 市场震荡，建议观望\n• 等待明确共振信号\n• 关注 GOOG、INTC 等现有持仓"
        elif total_buy > total_sell:
            message += "• 买入信号多于卖出信号\n• 关注共振确认的标的\n• 注意仓位控制"
        elif total_sell > total_buy:
            message += "• 卖出信号多于买入信号\n• 注意风险控制\n• 考虑减仓观望"
        else:
            message += "• 多空信号平衡\n• 精选个股机会\n• 保持中性仓位"
        
        message += f"\n\n— ChanLun AI Agent v5.2 Alpha"
        
        return message
    
    def send_report(self, message: str, report_type: str):
        """发送报告到 Telegram"""
        try:
            safe_message = message.replace("'", "'\"'\"'")
            env = dict()
            env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + '/usr/bin:' + '/bin'
            
            cmd = f"{OPENCLAW_PATH} message send --target 'telegram:{TELEGRAM_CHAT_ID}' -m '{safe_message}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, env=env)
            
            if result.returncode == 0:
                print(f"✅ 报告已推送：{report_type}")
                with open(REPORT_LOG, 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - {report_type} - 推送成功\n")
            else:
                print(f"⚠️ 推送失败：{result.stderr}")
        except Exception as e:
            print(f"❌ 推送错误：{e}")


# ==================== 主程序 ====================

def is_trading_time():
    """检查是否在交易时间"""
    now = datetime.now()
    
    # 周末不交易
    if now.weekday() >= 5:
        return False
    
    # 美国节假日 (简化版)
    us_holidays = [
        (1, 1), (1, 20), (2, 17), (5, 26), (7, 4),
        (9, 1), (11, 27), (12, 25),
    ]
    
    if (now.month, now.day) in us_holidays:
        return False
    
    return True


def main():
    """主程序"""
    import subprocess
    
    if not is_trading_time():
        print(f"⚪ {datetime.now().strftime('%Y-%m-%d')} 不是交易日，跳过")
        return
    
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # 确定报告类型
    if now < market_open + timedelta(hours=1):
        report_type = "盘前报告 (09:00 EDT)"
    elif now > market_close - timedelta(hours=1):
        report_type = "收盘前报告 (15:00 EDT)"
    else:
        report_type = "盘中扫描"
    
    print(f"\n{'='*70}")
    print(f"热门股票 + ETF 共振扫描")
    print(f"{'='*70}")
    print(f"时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"类型：{report_type}")
    print(f"{'='*70}\n")
    
    # 扫描
    scanner = HotStocksResonanceScanner()
    results = scanner.scan_all()
    
    # 生成报告
    message = scanner.generate_report(results, report_type)
    
    # 保存报告到文件
    report_file = f"/home/wei/.openclaw/workspace/chanlunInvester/reports/hot_stocks_{now.strftime('%Y-%m-%d_%H%M')}.md"
    Path(report_file).parent.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(message)
    print(f"\n📄 报告已保存：{report_file}")
    
    # 推送报告
    scanner.send_report(message, report_type)
    
    # 汇总
    total_signals = sum(len(signals) for signals in results.values())
    print(f"\n{'='*70}")
    print(f"扫描完成")
    print(f"共振信号：{total_signals}只")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
