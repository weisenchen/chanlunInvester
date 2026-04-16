#!/usr/bin/env python3
"""
趋势起势检测模块
Trend Start Detector

缠论改进版 - Phase 1

目标：提前捕捉趋势起势，领先于传统 buy1/buy2 信号
核心：多因子融合 (中枢突破 + 动量 + 量能 + 共振)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

# Add python-layer to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator


@dataclass
class TrendStartSignal:
    """趋势起势信号"""
    symbol: str
    level: str
    timestamp: datetime
    
    # 信号强度
    start_probability: float = 0.0  # 起势概率 (0-1)
    confidence: float = 0.0  # 置信度 (0-1)
    
    # 触发信号
    signals: List[str] = field(default_factory=list)
    
    # 操作建议
    action: str = 'HOLD'  # STRONG_ENTRY, ENTRY, WATCH, HOLD
    position_ratio: float = 0.0  # 建议仓位 (0-1)
    
    # 详细数据
    breakout_price: Optional[float] = None
    center_zg: Optional[float] = None
    center_zd: Optional[float] = None
    volume_ratio: float = 1.0
    macd_status: str = 'unknown'
    
    # 风控
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TrendStartDetector:
    """
    趋势起势检测器
    
    核心逻辑:
    1. 中枢突破 (25%) - 价格突破中枢上沿
    2. 动量加速 (20%) - MACD 黄白线快速上升
    3. 量能放大 (20%) - 成交量>均量 150%
    4. 小级别共振 (15%) - 5m+30m 同向
    5. 均线多头 (10%) - 短期>中期>长期
    6. 市场情绪 (10%) - 新闻/资金流
    """
    
    def __init__(self):
        # 权重配置 (可通过回测优化)
        self.weights = {
            'center_breakout': 0.25,
            'momentum_acceleration': 0.20,
            'volume_expand': 0.20,
            'small_level_resonance': 0.15,
            'ma_bullish': 0.10,
        }
        
        # 阈值配置
        self.thresholds = {
            'breakout_tolerance': 0.01,  # 突破容差 1%
            'volume_expand_ratio': 1.5,   # 放量 50%
            'price_change_5d': 0.03,      # 5 日涨幅 3%
            'dif_slope': 0.5,             # DIF 斜率阈值
            'dea_slope': 0.3,             # DEA 斜率阈值
        }
        
        # 检测器
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
        self.center_detector = CenterDetector(min_segments=3)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def detect(self, series: KlineSeries, symbol: str, level: str,
               small_level_series: Optional[KlineSeries] = None) -> TrendStartSignal:
        """
        检测趋势起势
        
        Args:
            series: K 线序列 (当前级别)
            symbol: 股票代码
            level: 级别 (1d, 30m, 5m)
            small_level_series: 小级别 K 线序列 (用于共振检测)
        
        Returns:
            TrendStartSignal: 起势信号
        """
        prices = [k.close for k in series.klines]
        volumes = [k.volume for k in series.klines]
        
        # 检测中枢
        fractals = self.fractal_detector.detect_all(series)
        pens = self.pen_calculator.identify_pens(series)
        segments = self.segment_calculator.detect_segments(pens)
        centers = self.center_detector.detect_centers(segments)
        
        # 计算 MACD
        macd_data = self.macd.calculate(prices)
        
        # 初始化信号
        signal = TrendStartSignal(
            symbol=symbol,
            level=level,
            timestamp=datetime.now()
        )
        
        # 无中枢，无法检测突破
        if not centers:
            signal.start_probability = 0.0
            signal.confidence = 0.0
            signal.action = 'HOLD'
            return signal
        
        last_center = centers[-1]
        signal.center_zg = last_center.zg
        signal.center_zd = last_center.zd
        
        # 信号检测
        signals = []
        probability = 0.0
        
        # 1. 中枢突破检测 (25%)
        if self._center_breakout(prices, last_center):
            probability += self.weights['center_breakout']
            signals.append('center_breakout')
            signal.breakout_price = prices[-1]
        
        # 2. 动量加速检测 (20%)
        if self._momentum_acceleration(macd_data):
            probability += self.weights['momentum_acceleration']
            signals.append('momentum_acceleration')
            signal.macd_status = 'acceleration'
        
        # 3. 量能放大检测 (20%)
        volume_ratio = self._volume_expand(volumes)
        if volume_ratio > self.thresholds['volume_expand_ratio']:
            probability += self.weights['volume_expand']
            signals.append('volume_expand')
            signal.volume_ratio = volume_ratio
        
        # 4. 小级别共振检测 (15%)
        if small_level_series and self._small_level_resonance(series, small_level_series):
            probability += self.weights['small_level_resonance']
            signals.append('small_level_resonance')
        
        # 5. 均线多头检测 (10%)
        if self._ma_bullish(prices):
            probability += self.weights['ma_bullish']
            signals.append('ma_bullish')
        
        # 计算置信度
        signal.start_probability = probability
        signal.confidence = self._calculate_confidence(probability, len(signals))
        signal.signals = signals
        
        # 操作建议
        signal.action = self._get_action(probability)
        signal.position_ratio = self._get_position_ratio(probability, signal.confidence)
        
        # 风控设置
        signal.stop_loss = self._calculate_stop_loss(last_center, prices[-1])
        signal.take_profit = self._calculate_take_profit(last_center, prices[-1])
        
        return signal
    
    def _center_breakout(self, prices: List[float], center) -> bool:
        """
        中枢突破检测
        
        条件:
        1. 价格突破中枢上沿 (ZG)
        2. 突破有力度 (大阳线)
        """
        current_price = prices[-1]
        
        # 突破中枢上沿 (1% 容差)
        if current_price > center.zg * (1 + self.thresholds['breakout_tolerance']):
            # 突破有力度 (5 日涨幅>3%)
            if len(prices) >= 5:
                price_change = (prices[-1] - prices[-5]) / prices[-5]
                if price_change > self.thresholds['price_change_5d']:
                    return True
        
        return False
    
    def _momentum_acceleration(self, macd_data) -> bool:
        """
        动量加速检测
        
        条件:
        1. MACD 黄白线快速上升
        2. 金叉状态
        """
        if len(macd_data) < 5:
            return False
        
        # 计算斜率 (3 周期)
        dif_slope = (macd_data[-1].dif - macd_data[-3].dif) / 3
        dea_slope = (macd_data[-1].dea - macd_data[-3].dea) / 3
        
        # 斜率为正且加速
        if dif_slope > self.thresholds['dif_slope'] and dea_slope > self.thresholds['dea_slope']:
            # 且金叉
            if macd_data[-1].dif > macd_data[-1].dea:
                return True
        
        return False
    
    def _volume_expand(self, volumes: List[int]) -> float:
        """
        量能放大检测
        
        返回:
        成交量比率 (当前/20 日均量)
        """
        if len(volumes) < 20:
            return 1.0
        
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def _small_level_resonance(self, series: KlineSeries, 
                                small_series: KlineSeries) -> bool:
        """
        小级别共振检测
        
        条件:
        1. 当前级别上涨
        2. 小级别也上涨
        """
        # 简化实现：比较两个级别的 MACD 状态
        prices = [k.close for k in series.klines]
        small_prices = [k.close for k in small_series.klines]
        
        macd = self.macd.calculate(prices)
        small_macd = self.macd.calculate(small_prices)
        
        # 两个级别都金叉
        if macd[-1].dif > macd[-1].dea and small_macd[-1].dif > small_macd[-1].dea:
            return True
        
        return False
    
    def _ma_bullish(self, prices: List[float]) -> bool:
        """
        均线多头检测
        
        条件:
        短期>中期>长期
        """
        if len(prices) < 60:
            return False
        
        # 计算均线
        ma5 = sum(prices[-5:]) / 5
        ma10 = sum(prices[-10:]) / 10
        ma20 = sum(prices[-20:]) / 20
        
        # 多头排列
        if ma5 > ma10 > ma20:
            return True
        
        return False
    
    def _calculate_confidence(self, probability: float, signal_count: int) -> float:
        """
        计算置信度
        
        基于概率和信号数量
        """
        # 基础置信度
        base_confidence = probability
        
        # 信号数量奖励
        if signal_count >= 4:
            bonus = 0.15
        elif signal_count >= 3:
            bonus = 0.10
        elif signal_count >= 2:
            bonus = 0.05
        else:
            bonus = 0.0
        
        confidence = min(base_confidence + bonus, 1.0)
        return confidence
    
    def _get_action(self, probability: float) -> str:
        """根据概率给出操作建议"""
        if probability >= 0.7:
            return 'STRONG_ENTRY'  # 强烈入场
        elif probability >= 0.5:
            return 'ENTRY'         # 入场
        elif probability >= 0.3:
            return 'WATCH'         # 观察
        else:
            return 'HOLD'          # 持有/观望
    
    def _get_position_ratio(self, probability: float, confidence: float) -> float:
        """
        计算建议仓位
        
        基于概率和置信度
        """
        # 综合评分
        score = probability * 0.6 + confidence * 0.4
        
        if score >= 0.8:
            return 0.7  # 70% 仓位
        elif score >= 0.6:
            return 0.5  # 50% 仓位
        elif score >= 0.4:
            return 0.3  # 30% 仓位
        else:
            return 0.1  # 10% 仓位
    
    def _calculate_stop_loss(self, center, current_price: float) -> float:
        """
        计算止损位
        
        基于中枢下沿
        """
        # 止损位 = 中枢下沿 - 2% 容差
        stop_loss = center.zd * 0.98
        return stop_loss
    
    def _calculate_take_profit(self, center, current_price: float) -> float:
        """
        计算止盈位
        
        基于中枢区间
        """
        # 第一止盈 = 当前价 + 中枢区间
        range_size = center.zg - center.zd
        take_profit = current_price + range_size
        return take_profit
    
    def format_signal(self, signal: TrendStartSignal) -> str:
        """格式化信号输出"""
        action_emoji = {
            'STRONG_ENTRY': '🚀',
            'ENTRY': '🟢',
            'WATCH': '👀',
            'HOLD': '⚪'
        }
        
        lines = [
            "=" * 70,
            f"📈 趋势起势信号 - {signal.symbol} ({signal.level})",
            "=" * 70,
            f"时间：{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"起势概率：{signal.start_probability*100:.0f}%",
            f"置信度：  {signal.confidence*100:.0f}%",
            f"",
            f"触发信号 ({len(signal.signals)}个):",
        ]
        
        for sig in signal.signals:
            lines.append(f"   ✅ {sig}")
        
        lines.extend([
            f"",
            f"操作建议：{action_emoji.get(signal.action, '')} {signal.action}",
            f"建议仓位：{signal.position_ratio*100:.0f}%",
            f"",
        ])
        
        if signal.breakout_price:
            lines.append(f"突破价格：${signal.breakout_price:.2f}")
        if signal.center_zg:
            lines.append(f"中枢上沿：${signal.center_zg:.2f}")
        if signal.center_zd:
            lines.append(f"中枢下沿：${signal.center_zd:.2f}")
        if signal.volume_ratio > 1:
            lines.append(f"成交量比：{signal.volume_ratio:.2f}x")
        
        if signal.stop_loss:
            lines.append(f"止损位：  ${signal.stop_loss:.2f}")
        if signal.take_profit:
            lines.append(f"止盈位：  ${signal.take_profit:.2f}")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ==================== 测试函数 ====================

def test_trend_start_detector():
    """测试趋势起势检测器"""
    import yfinance as yf
    
    print("=" * 70)
    print("趋势起势检测器测试")
    print("=" * 70)
    
    # 获取测试数据
    symbol = 'AAPL'
    print(f"\n获取 {symbol} 数据...")
    
    data = yf.Ticker(symbol).history(period='60d', interval='1d')
    
    if len(data) == 0:
        print("❌ 数据获取失败")
        return
    
    # 转换数据
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
    
    series = KlineSeries(klines=klines, symbol=symbol, timeframe='1d')
    
    # 检测
    detector = TrendStartDetector()
    signal = detector.detect(series, symbol, '1d')
    
    # 输出
    print(detector.format_signal(signal))
    
    return signal


if __name__ == '__main__':
    test_trend_start_detector()
