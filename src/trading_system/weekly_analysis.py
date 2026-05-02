"""
缠论周线/日线级别分析模块
用于挖掘市场热点和推荐投资标的
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import yfinance as yf

from .kline import Kline, KlineSeries
from .fractal import FractalDetector
from .pen import PenCalculator, PenConfig
from .segment import SegmentCalculator
from .indicators import MACDIndicator


@dataclass
class StockAnalysis:
    """股票分析结果"""
    symbol: str
    name: str
    price: float
    change_pct: float
    weekly_signal: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    weekly_strength: float
    daily_signal: str
    daily_strength: float
    combined_score: float
    sector: str
    reasoning: List[str]
    entry_price: float
    stop_loss: float
    target_price: float


@dataclass
class SectorAnalysis:
    """板块分析结果"""
    sector_name: str
    total_stocks: int
    strong_buy_count: int
    buy_count: int
    avg_strength: float
    trend: str  # BULLISH, BEARISH, NEUTRAL
    top_stocks: List[StockAnalysis]


class WeeklyDailyAnalyzer:
    """周线/日线级别分析器"""
    
    def __init__(self):
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def fetch_weekly_data(self, symbol: str, count: int = 100) -> Optional[KlineSeries]:
        """获取周线数据"""
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period='2y', interval='1wk')
            
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
            
            if len(klines) > count:
                klines = klines[-count:]
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe='1wk')
            
        except Exception as e:
            return None
    
    def fetch_daily_data(self, symbol: str, count: int = 200) -> Optional[KlineSeries]:
        """获取日线数据"""
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period='1y', interval='1d')
            
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
            
            if len(klines) > count:
                klines = klines[-count:]
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe='1d')
            
        except Exception as e:
            return None
    
    def analyze_timeframe(self, series: KlineSeries) -> Dict:
        """分析单个时间级别"""
        if not series or len(series.klines) == 0:
            return {'signal': 'HOLD', 'strength': 0.0, 'reasoning': []}
        
        # 分型分析
        fractals = self.fractal_detector.detect_all(series)
        top_fractals = [f for f in fractals if f.is_top]
        bottom_fractals = [f for f in fractals if not f.is_top]
        
        # 笔分析
        pens = self.pen_calculator.identify_pens(series)
        up_pens = [p for p in pens if p.is_up]
        down_pens = [p for p in pens if p.is_down]
        
        # 线段分析
        segments = self.segment_calculator.detect_segments(pens)
        up_segs = [s for s in segments if s.is_up]
        down_segs = [s for s in segments if s.is_down]
        
        # 背驰检测
        prices = [k.close for k in series.klines]
        macd_data = self.macd.calculate(prices)
        divergence = self._detect_divergence(segments, macd_data)
        
        # 计算信号强度
        strength = 0.0
        reasoning = []
        
        # 线段方向贡献
        if up_segs and (not down_segs or len(up_segs) > len(down_segs)):
            strength += 3.0
            reasoning.append(f'上涨线段主导 ({len(up_segs)}上/{len(down_segs)}下)')
        elif down_segs and (not up_segs or len(down_segs) > len(up_segs)):
            strength -= 3.0
            reasoning.append(f'下跌线段主导 ({len(down_segs)}下/{len(up_segs)}上)')
        
        # 背驰贡献
        if divergence.get('detected'):
            if divergence['signal'] == 'buy':
                strength += divergence['strength'] * 2
                reasoning.append(f'底背驰 (强度:{divergence["strength"]:.2f})')
            else:
                strength -= divergence['strength'] * 2
                reasoning.append(f'顶背驰 (强度:{divergence["strength"]:.2f})')
        
        # 确定信号
        if strength >= 6.0:
            signal = 'STRONG_BUY'
        elif strength >= 4.0:
            signal = 'BUY'
        elif strength <= -6.0:
            signal = 'STRONG_SELL'
        elif strength <= -4.0:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': strength,
            'reasoning': reasoning,
            'divergence': divergence
        }
    
    def _detect_divergence(self, segments: List, macd_data: List) -> Dict:
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
    
    def analyze_stock(self, symbol: str) -> Optional[StockAnalysis]:
        """分析单只股票 (周线 + 日线)"""
        try:
            # 获取股票信息
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 获取数据
            weekly_series = self.fetch_weekly_data(symbol)
            daily_series = self.fetch_daily_data(symbol)
            
            if not weekly_series or not daily_series:
                return None
            
            # 分析
            weekly_result = self.analyze_timeframe(weekly_series)
            daily_result = self.analyze_timeframe(daily_series)
            
            # 综合评分 (周线权重 60%, 日线权重 40%)
            combined_score = (
                weekly_result['strength'] * 0.6 +
                daily_result['strength'] * 0.4
            )
            
            # 确定综合信号
            if combined_score >= 6.0:
                weekly_signal = 'STRONG_BUY'
            elif combined_score >= 4.0:
                weekly_signal = 'BUY'
            elif combined_score <= -6.0:
                weekly_signal = 'STRONG_SELL'
            elif combined_score <= -4.0:
                weekly_signal = 'SELL'
            else:
                weekly_signal = 'HOLD'
            
            # 获取当前价格
            current_price = daily_series.klines[-1].close
            
            # 计算交易计划
            if combined_score > 0:
                entry_price = current_price
                stop_loss = current_price * 0.95
                target_price = current_price * 1.10
            else:
                entry_price = current_price
                stop_loss = current_price * 1.05
                target_price = current_price * 0.90
            
            # 获取板块信息
            sector = info.get('sector', 'Unknown')
            
            # 合并推理
            all_reasoning = []
            all_reasoning.extend([f'周线：{r}' for r in weekly_result['reasoning']])
            all_reasoning.extend([f'日线：{r}' for r in daily_result['reasoning']])
            
            return StockAnalysis(
                symbol=symbol,
                name=info.get('shortName', symbol),
                price=current_price,
                change_pct=0.0,  # 可以计算
                weekly_signal=weekly_result['signal'],
                weekly_strength=weekly_result['strength'],
                daily_signal=daily_result['signal'],
                daily_strength=daily_result['strength'],
                combined_score=combined_score,
                sector=sector,
                reasoning=all_reasoning,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price
            )
            
        except Exception as e:
            return None
    
    def scan_market(self, stock_list: List[str]) -> List[StockAnalysis]:
        """扫描市场，找出投资机会"""
        results = []
        
        for symbol in stock_list:
            print(f'分析 {symbol}...', end=' ')
            result = self.analyze_stock(symbol)
            
            if result:
                print(f'${result.price:.2f} | 综合:{result.combined_score:+.1f}')
                results.append(result)
            else:
                print('❌')
        
        # 按综合评分排序
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return results
    
    def analyze_sectors(self, stocks_by_sector: Dict[str, List[str]]) -> List[SectorAnalysis]:
        """分析板块"""
        sector_results = []
        
        for sector_name, stock_list in stocks_by_sector.items():
            print(f'\n分析板块：{sector_name}')
            
            sector_stocks = self.scan_market(stock_list)
            
            if not sector_stocks:
                continue
            
            strong_buy = [s for s in sector_stocks if s.combined_score >= 6.0]
            buy = [s for s in sector_stocks if 4.0 <= s.combined_score < 6.0]
            
            avg_strength = sum(s.combined_score for s in sector_stocks) / len(sector_stocks)
            
            if avg_strength >= 4.0:
                trend = 'BULLISH'
            elif avg_strength <= -4.0:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            sector_results.append(SectorAnalysis(
                sector_name=sector_name,
                total_stocks=len(sector_stocks),
                strong_buy_count=len(strong_buy),
                buy_count=len(buy),
                avg_strength=avg_strength,
                trend=trend,
                top_stocks=sector_stocks[:5]
            ))
        
        # 按平均强度排序
        sector_results.sort(key=lambda x: x.avg_strength, reverse=True)
        
        return sector_results
