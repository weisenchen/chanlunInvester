"""
ChanLun Stock Monitor - Python Core
通用股票监控系统核心模块
支持任意美股/ETF/加密货币

Usage:
    from trading_system.monitor import ChanLunMonitor
    
    monitor = ChanLunMonitor()
    results = monitor.analyze('AAPL', timeframes=['1d', '30m', '5m'])
    signal = monitor.generate_signal(results)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import yfinance as yf

from .kline import Kline, KlineSeries
from .fractal import FractalDetector
from .pen import PenCalculator, PenConfig
from .segment import SegmentCalculator
from .indicators import MACDIndicator


@dataclass
class MonitorConfig:
    """监控配置"""
    timeframes: List[str] = None
    min_confidence: float = 0.7
    weights: Dict[str, Dict[str, float]] = None
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ['1d', '30m', '5m']
        
        if self.weights is None:
            self.weights = {
                '1d': {'direction': 3.0, 'divergence': 6.0},
                '4h': {'direction': 2.5, 'divergence': 5.0},
                '1h': {'direction': 2.0, 'divergence': 4.0},
                '30m': {'direction': 2.0, 'divergence': 4.0},
                '15m': {'direction': 1.5, 'divergence': 3.0},
                '5m': {'direction': 1.0, 'divergence': 4.0}
            }


@dataclass
class AnalysisResult:
    """分析结果"""
    symbol: str
    timestamp: str
    current_price: float
    signal: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    strength: float
    reasoning: List[str]
    levels: Dict[str, Any]


class ChanLunMonitor:
    """缠论股票监控器"""
    
    def __init__(self, config: MonitorConfig = None):
        """
        初始化监控器
        
        Args:
            config: 监控配置
        """
        self.config = config or MonitorConfig()
        
        # 初始化分析模块
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def fetch_data(self, symbol: str, timeframe: str = '5m', count: int = 100) -> Optional[KlineSeries]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            timeframe: 时间周期
            count: K 线数量
        
        Returns:
            KlineSeries 或 None
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # 根据时间周期获取数据
            period_map = {
                '1m': '1d',
                '2m': '1d',
                '5m': '5d',
                '15m': '1mo',
                '30m': '1mo',
                '1h': '3mo',
                '2h': '3mo',
                '4h': '3mo',
                '1d': '1y',
                '5d': '1y',
                '1wk': '2y',
                '1mo': '5y'
            }
            
            period = period_map.get(timeframe, '1mo')
            history = ticker.history(period=period, interval=timeframe)
            
            if len(history) == 0:
                return None
            
            klines = []
            for idx, row in history.iterrows():
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
            
            if len(klines) > count:
                klines = klines[-count:]
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def analyze_level(self, series: KlineSeries) -> Dict[str, Any]:
        """
        分析单个级别
        
        Args:
            series: K 线序列
        
        Returns:
            分析结果字典
        """
        results = {}
        
        # 1. 分型
        fractals = self.fractal_detector.detect_all(series)
        results['fractals'] = {
            'total': len(fractals),
            'top': len([f for f in fractals if f.is_top]),
            'bottom': len([f for f in fractals if not f.is_top])
        }
        
        # 2. 笔
        pens = self.pen_calculator.identify_pens(series)
        results['pens'] = {
            'total': len(pens),
            'up': len([p for p in pens if p.is_up]),
            'down': len([p for p in pens if p.is_down]),
            'latest': pens[-1] if pens else None
        }
        
        # 3. 线段
        segments = self.segment_calculator.detect_segments(pens)
        results['segments'] = {
            'total': len(segments),
            'up': len([s for s in segments if s.is_up]),
            'down': len([s for s in segments if s.is_down]),
            'latest': segments[-1] if segments else None
        }
        
        # 4. MACD 背驰
        prices = [k.close for k in series.klines]
        macd_data = self.macd.calculate(prices)
        results['divergence'] = self._detect_divergence(segments, macd_data)
        
        # 5. 买卖点
        results['buy_sell_points'] = self._detect_buy_sell_points(segments, results['divergence'])
        
        return results
    
    def _detect_divergence(self, segments: List, macd_data: List) -> Dict[str, Any]:
        """检测背驰"""
        if len(segments) < 2 or not macd_data:
            return {'detected': False}
        
        last_seg = segments[-1]
        prev_seg = None
        
        for seg in reversed(segments[:-1]):
            if seg.direction == last_seg.direction:
                prev_seg = seg
                break
        
        if not prev_seg:
            return {'detected': False}
        
        try:
            macd_prev = macd_data[prev_seg.end_idx].histogram
            macd_last = macd_data[last_seg.end_idx].histogram
            
            price_prev = prev_seg.end_price
            price_last = last_seg.end_price
            
            if last_seg.direction == 'up':
                if price_last > price_prev and macd_last < macd_prev:
                    strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                    return {
                        'detected': True,
                        'type': 'top_divergence',
                        'price': price_last,
                        'strength': strength,
                        'signal': 'sell'
                    }
            else:
                if price_last < price_prev and macd_last > macd_prev:
                    strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                    return {
                        'detected': True,
                        'type': 'bottom_divergence',
                        'price': price_last,
                        'strength': strength,
                        'signal': 'buy'
                    }
        except:
            pass
        
        return {'detected': False}
    
    def _detect_buy_sell_points(self, segments: List, divergence: Dict) -> List[Dict]:
        """识别买卖点"""
        bsp_list = []
        
        if divergence.get('detected'):
            bsp = {
                'type': f"第一类{'买点' if divergence['signal'] == 'buy' else '卖点'}",
                'type_en': f"bsp{'1_buy' if divergence['signal'] == 'buy' else '1_sell'}",
                'price': divergence.get('price'),
                'confidence': min(divergence.get('strength', 0), 0.9),
                'description': f"趋势背驰点 - {divergence['type']}"
            }
            bsp_list.append(bsp)
        
        return bsp_list
    
    def analyze(self, symbol: str, timeframes: List[str] = None) -> Optional[AnalysisResult]:
        """
        多级别联动分析
        
        Args:
            symbol: 股票代码
            timeframes: 时间周期列表
        
        Returns:
            AnalysisResult 或 None
        """
        if timeframes is None:
            timeframes = self.config.timeframes
        
        # 获取多个级别数据
        data = {}
        current_price = None
        
        for timeframe in timeframes:
            series = self.fetch_data(symbol, timeframe, 100)
            if series is None or len(series.klines) == 0:
                continue
            
            price = series.klines[-1].close
            if current_price is None:
                current_price = price
            
            data[timeframe] = {
                'series': series,
                'price': price
            }
        
        if not data:
            return None
        
        # 执行分析
        analysis_results = {}
        for timeframe, level_data in data.items():
            analysis_results[timeframe] = self.analyze_level(level_data['series'])
        
        # 多级别联动分析
        signal_strength = 0.0
        reasoning = []
        
        for timeframe, results in analysis_results.items():
            weight = self.config.weights.get(timeframe, {'direction': 1.0, 'divergence': 2.0})
            
            # 线段方向
            if results['segments']['latest']:
                direction = results['segments']['latest'].direction
                if direction == 'up':
                    signal_strength += weight['direction']
                    reasoning.append(f"✓ {timeframe}上涨线段 (+{weight['direction']})")
                else:
                    signal_strength -= weight['direction']
                    reasoning.append(f"✗ {timeframe}下跌线段 (-{weight['direction']})")
            
            # 背驰
            if results['divergence'].get('detected'):
                div = results['divergence']
                if div['signal'] == 'buy':
                    signal_strength += weight['divergence']
                    reasoning.append(f"🟢 {timeframe}底背驰 (强度:{div['strength']:.2f}) (+{weight['divergence']})")
                else:
                    signal_strength -= weight['divergence']
                    reasoning.append(f"🔴 {timeframe}顶背驰 (强度:{div['strength']:.2f}) (-{weight['divergence']})")
            
            # 买卖点
            if results['buy_sell_points']:
                for bsp in results['buy_sell_points']:
                    if 'buy' in bsp['type_en']:
                        signal_strength += weight['divergence']
                        reasoning.append(f"🟢 {timeframe}第一类买点 (+{weight['divergence']})")
                    else:
                        signal_strength -= weight['divergence']
                        reasoning.append(f"🔴 {timeframe}第一类卖点 (+{weight['divergence']})")
        
        # 生成信号
        if signal_strength >= 8:
            final_signal = "STRONG_BUY"
        elif signal_strength >= 4:
            final_signal = "BUY"
        elif signal_strength <= -8:
            final_signal = "STRONG_SELL"
        elif signal_strength <= -4:
            final_signal = "SELL"
        else:
            final_signal = "HOLD"
        
        return AnalysisResult(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            signal=final_signal,
            strength=signal_strength,
            reasoning=reasoning,
            levels=analysis_results
        )
    
    def generate_trading_plan(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        生成交易计划
        
        Args:
            result: 分析结果
        
        Returns:
            交易计划字典
        """
        if not result or not result.current_price:
            return {}
        
        price = result.current_price
        
        if 'BUY' in result.signal:
            stop_loss = price * 0.97
            target1 = price * 1.03
            target2 = price * 1.05
            position_size = "heavy" if 'STRONG' in result.signal else "normal"
            
            return {
                'action': 'BUY',
                'entry': price,
                'stop_loss': stop_loss,
                'target1': target1,
                'target2': target2,
                'position_size': position_size,
                'risk_reward': 1.7
            }
        elif 'SELL' in result.signal:
            stop_loss = price * 1.03
            target1 = price * 0.97
            target2 = price * 0.95
            position_size = "heavy" if 'STRONG' in result.signal else "normal"
            
            return {
                'action': 'SELL',
                'entry': price,
                'stop_loss': stop_loss,
                'target1': target1,
                'target2': target2,
                'position_size': position_size,
                'risk_reward': 1.7
            }
        else:
            return {
                'action': 'HOLD',
                'reason': 'Wait for clearer signals'
            }
