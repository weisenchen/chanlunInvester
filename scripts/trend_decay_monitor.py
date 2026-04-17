#!/usr/bin/env python3
"""
趋势衰减监测模块
Trend Decay Monitor

缠论改进版 - Phase 2

目标：实时监测趋势衰减，提前 3-5 天预警
核心：多维度检测 (力度递减 + 中枢扩大 + 时间延长 + 量价背离 + 多级别背离)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator


@dataclass
class TrendDecaySignal:
    """趋势衰减信号"""
    symbol: str
    level: str
    timestamp: datetime
    
    # 信号强度
    decay_probability: float = 0.0  # 衰减概率 (0-1)
    confidence: float = 0.0  # 置信度 (0-1)
    
    # 触发信号
    signals: List[str] = field(default_factory=list)
    
    # 预警级别
    warning_level: str = 'LOW'  # LOW, MEDIUM, HIGH, CRITICAL
    
    # 详细数据
    strength_decline_rate: float = 0.0  # 力度递减率
    center_expansion_rate: float = 0.0  # 中枢扩大率
    time_extension_rate: float = 0.0  # 时间延长率
    volume_price_divergence: bool = False  # 量价背离
    multi_level_divergence: bool = False  # 多级别背离
    
    # 预估
    days_to_reversal: int = 0  # 预估反转天数


class TrendDecayMonitor:
    """
    趋势衰减监测器
    
    核心逻辑:
    1. 力度递减检测 (30%) - 离开中枢的线段力度减弱
    2. 中枢扩大检测 (20%) - 中枢区间变大，震荡加剧
    3. 时间延长检测 (20%) - 中枢形成时间变长
    4. 量价背离检测 (15%) - 价格上涨但成交量萎缩
    5. 多级别背离检测 (15%) - 大级别涨小级别跌
    """
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'strength_decline': 0.30,
            'center_expansion': 0.20,
            'time_extension': 0.20,
            'volume_price_divergence': 0.15,
            'multi_level_divergence': 0.15,
        }
        
        # 阈值配置 (Phase 5 优化版 - 进一步降低门槛)
        self.thresholds = {
            'strength_decline_rate': -0.15,  # 力度下降 15% (原 20%)
            'center_expansion_rate': 0.2,    # 中枢扩大 20% (原 30%)
            'time_extension_rate': 0.2,      # 时间延长 20% (原 30%)
            'volume_decline_rate': -0.15,    # 成交量萎缩 15% (原 20%)
        }
        
        # 检测器 (Phase 5 优化版 - 进一步降低中枢检测门槛)
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=False,
            min_klines_between_turns=1  # 从 2 降到 1
        ))
        self.segment_calculator = SegmentCalculator(min_pens=1)  # 从 2 降到 1
        self.center_detector = CenterDetector(min_segments=1)  # 从 2 降到 1
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def monitor(self, series: KlineSeries, symbol: str, level: str,
                small_level_series: Optional[KlineSeries] = None) -> TrendDecaySignal:
        """
        监测趋势衰减
        
        Args:
            series: K 线序列 (当前级别)
            symbol: 股票代码
            level: 级别 (1d, 30m, 5m)
            small_level_series: 小级别 K 线序列 (用于多级别背离检测)
        
        Returns:
            TrendDecaySignal: 衰减信号
        """
        prices = [k.close for k in series.klines]
        volumes = [k.volume for k in series.klines]
        
        # 检测中枢和线段
        fractals = self.fractal_detector.detect_all(series)
        pens = self.pen_calculator.identify_pens(series)
        segments = self.segment_calculator.detect_segments(pens)
        centers = self.center_detector.detect_centers(segments)
        
        # 计算 MACD
        macd_data = self.macd.calculate(prices)
        
        # 初始化信号
        signal = TrendDecaySignal(
            symbol=symbol,
            level=level,
            timestamp=datetime.now()
        )
        
        # 无中枢或线段，无法检测衰减
        if len(centers) < 2 or len(segments) < 3:
            signal.decay_probability = 0.0
            signal.confidence = 0.0
            signal.warning_level = 'LOW'
            return signal
        
        # 信号检测
        signals = []
        probability = 0.0
        
        # 1. 力度递减检测 (30%)
        strength_result = self._detect_strength_decline(centers, segments)
        if strength_result['declining']:
            probability += self.weights['strength_decline']
            signals.append('strength_decline')
            signal.strength_decline_rate = strength_result['decline_rate']
        
        # 2. 中枢扩大检测 (20%)
        expansion_result = self._detect_center_expansion(centers)
        if expansion_result['expanding']:
            probability += self.weights['center_expansion']
            signals.append('center_expansion')
            signal.center_expansion_rate = expansion_result['expansion_rate']
        
        # 3. 时间延长检测 (20%)
        time_result = self._detect_time_extension(centers)
        if time_result['extending']:
            probability += self.weights['time_extension']
            signals.append('time_extension')
            signal.time_extension_rate = time_result['extension_rate']
        
        # 4. 量价背离检测 (15%)
        if self._detect_volume_price_divergence(prices, volumes):
            probability += self.weights['volume_price_divergence']
            signals.append('volume_price_divergence')
            signal.volume_price_divergence = True
        
        # 5. 多级别背离检测 (15%)
        if small_level_series and self._detect_multi_level_divergence(series, small_level_series):
            probability += self.weights['multi_level_divergence']
            signals.append('multi_level_divergence')
            signal.multi_level_divergence = True
        
        # 计算置信度
        signal.decay_probability = probability
        signal.confidence = self._calculate_confidence(probability, len(signals))
        signal.signals = signals
        
        # 预警级别
        signal.warning_level = self._get_warning_level(probability)
        
        # 预估反转天数
        signal.days_to_reversal = self._estimate_days_to_reversal(probability, len(signals))
        
        return signal
    
    def _detect_strength_decline(self, centers: List, segments: List) -> Dict:
        """
        力度递减检测
        
        计算离开中枢的线段力度，判断是否递减
        
        力度 = 斜率 × 长度
        """
        if len(centers) < 2 or len(segments) < len(centers) + 1:
            return {'declining': False, 'decline_rate': 0.0}
        
        strengths = []
        for i, center in enumerate(centers[:-1]):
            # 离开中枢的线段
            if center.end_idx + 1 < len(segments):
                exit_segment = segments[center.end_idx + 1]
                # 力度 = 幅度 × 笔数 (使用 Segment 的 magnitude 和 pen_count)
                strength = abs(exit_segment.magnitude) * exit_segment.pen_count
                strengths.append(strength)
        
        # 判断是否递减
        if len(strengths) >= 2:
            decline_rate = (strengths[-1] - strengths[-2]) / strengths[-2] if strengths[-2] > 0 else 0
            
            if decline_rate < self.thresholds['strength_decline_rate']:  # 力度下降 30%
                return {
                    'declining': True,
                    'decline_rate': decline_rate,
                    'last_strength': strengths[-1]
                }
        
        return {'declining': False, 'decline_rate': 0.0}
    
    def _detect_center_expansion(self, centers: List) -> Dict:
        """
        中枢扩大检测
        
        中枢区间 = ZG - ZD
        判断中枢区间是否持续扩大
        """
        if len(centers) < 2:
            return {'expanding': False, 'expansion_rate': 0.0}
        
        # 中枢区间扩大
        if centers[-1].range > centers[-2].range * (1 + self.thresholds['center_expansion_rate']):
            expansion_rate = (centers[-1].range - centers[-2].range) / centers[-2].range
            return {
                'expanding': True,
                'expansion_rate': expansion_rate,
                'last_range': centers[-1].range
            }
        
        return {'expanding': False, 'expansion_rate': 0.0}
    
    def _detect_time_extension(self, centers: List) -> Dict:
        """
        时间延长检测
        
        中枢形成时间 = end_idx - start_idx
        判断中枢形成时间是否延长
        """
        if len(centers) < 2:
            return {'extending': False, 'extension_rate': 0.0}
        
        # 中枢形成时间延长
        duration_last = centers[-1].end_idx - centers[-1].start_idx
        duration_prev = centers[-2].end_idx - centers[-2].start_idx
        
        if duration_prev > 0 and duration_last > duration_prev * (1 + self.thresholds['time_extension_rate']):
            extension_rate = (duration_last - duration_prev) / duration_prev
            return {
                'extending': True,
                'extension_rate': extension_rate,
                'last_duration': duration_last
            }
        
        return {'extending': False, 'extension_rate': 0.0}
    
    def _detect_volume_price_divergence(self, prices: List[float], volumes: List[int]) -> bool:
        """
        量价背离检测
        
        价格上涨但成交量萎缩
        """
        if len(prices) < 20 or len(volumes) < 20:
            return False
        
        # 最近 5 日价格 vs 前 5 日价格
        recent_price_change = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] > 0 else 0
        
        # 最近 5 日成交量 vs 前 5 日成交量
        recent_vol_change = (sum(volumes[-5:]) - sum(volumes[-10:-5])) / sum(volumes[-10:-5]) if sum(volumes[-10:-5]) > 0 else 0
        
        # 量价背离：价格上涨但成交量萎缩
        if recent_price_change > 0.02 and recent_vol_change < self.thresholds['volume_decline_rate']:
            return True
        
        return False
    
    def _detect_multi_level_divergence(self, series: KlineSeries, 
                                        small_series: KlineSeries) -> bool:
        """
        多级别背离检测
        
        大级别上涨，小级别下跌
        """
        # 简化实现：比较两个级别的 MACD 状态
        prices = [k.close for k in series.klines]
        small_prices = [k.close for k in small_series.klines]
        
        macd = self.macd.calculate(prices)
        small_macd = self.macd.calculate(small_prices)
        
        # 大级别金叉，小级别死叉 = 背离
        if len(macd) >= 2 and len(small_macd) >= 2:
            big_bullish = macd[-1].dif > macd[-1].dea
            small_bearish = small_macd[-1].dif < small_macd[-1].dea
            
            if big_bullish and small_bearish:
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
    
    def _get_warning_level(self, probability: float) -> str:
        """获取预警级别"""
        if probability >= 0.7:
            return 'CRITICAL'  # 严重预警
        elif probability >= 0.5:
            return 'HIGH'      # 高级预警
        elif probability >= 0.3:
            return 'MEDIUM'    # 中级预警
        else:
            return 'LOW'       # 低级预警
    
    def _estimate_days_to_reversal(self, probability: float, signal_count: int) -> int:
        """
        预估反转天数
        
        基于概率和信号数量
        """
        if probability >= 0.7:
            return 3  # 高概率，3 天内反转
        elif probability >= 0.5:
            return 5  # 中概率，5 天内反转
        elif probability >= 0.3:
            return 7  # 低概率，7 天内反转
        else:
            return 0  # 无预警
    
    def format_signal(self, signal: TrendDecaySignal) -> str:
        """格式化信号输出"""
        warning_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        lines = [
            "=" * 70,
            f"📉 趋势衰减预警 - {signal.symbol} ({signal.level})",
            "=" * 70,
            f"时间：{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"衰减概率：{signal.decay_probability*100:.0f}%",
            f"置信度：  {signal.confidence*100:.0f}%",
            f"预警级别：{warning_emoji.get(signal.warning_level, '')} {signal.warning_level}",
            f"",
            f"触发信号 ({len(signal.signals)}个):",
        ]
        
        for sig in signal.signals:
            lines.append(f"   ✅ {sig}")
        
        if signal.strength_decline_rate != 0:
            lines.append(f"力度递减：{signal.strength_decline_rate*100:.1f}%")
        if signal.center_expansion_rate != 0:
            lines.append(f"中枢扩大：{signal.center_expansion_rate*100:.1f}%")
        if signal.time_extension_rate != 0:
            lines.append(f"时间延长：{signal.time_extension_rate*100:.1f}%")
        if signal.volume_price_divergence:
            lines.append(f"量价背离：✅ 是")
        if signal.multi_level_divergence:
            lines.append(f"多级别背离：✅ 是")
        
        if signal.days_to_reversal > 0:
            lines.append(f"预估反转：{signal.days_to_reversal} 天内")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ==================== 测试函数 ====================

def test_trend_decay_monitor():
    """测试趋势衰减监测器"""
    import yfinance as yf
    
    print("=" * 70)
    print("趋势衰减监测器测试")
    print("=" * 70)
    
    # 获取测试数据
    symbol = 'TSLA'
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
    monitor = TrendDecayMonitor()
    signal = monitor.monitor(series, symbol, '1d')
    
    # 输出
    print(monitor.format_signal(signal))
    
    return signal


if __name__ == '__main__':
    test_trend_decay_monitor()
