#!/usr/bin/env python3
"""
趋势反转预警模块
Trend Reversal Warning

缠论改进版 - Phase 3

目标：多信号共振，提前 3-5 天预警趋势反转
核心：多维度检测 (多级别背驰 + buy3 失败 + 中枢升级 + 先行指标)
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
class TrendReversalSignal:
    """趋势反转信号"""
    symbol: str
    level: str
    timestamp: datetime
    
    # 信号强度
    reversal_probability: float = 0.0  # 反转概率 (0-1)
    confidence: float = 0.0  # 置信度 (0-1)
    
    # 触发信号
    signals: List[str] = field(default_factory=list)
    
    # 预警级别
    warning_level: str = 'LOW'  # LOW, MEDIUM, HIGH, CRITICAL
    
    # 详细数据
    multi_level_divergence: bool = False  # 多级别背驰
    bsp3_failure: bool = False  # 第三类买卖点失败
    center_upgrade: bool = False  # 中枢升级完成
    leading_indicator_divergence: bool = False  # 先行指标背离
    
    # 预估
    days_to_reversal: int = 0  # 预估反转天数
    profit_preservation_rate: float = 0.0  # 利润保住率


class TrendReversalWarner:
    """
    趋势反转预警器
    
    核心逻辑:
    1. 多级别背驰共振检测 (35%) - 日线 +30m+5m 同时背驰
    2. 第三类买卖点失败检测 (20%) - buy3/sell3 后迅速反转
    3. 中枢升级完成检测 (15%) - 小中枢升级为大中枢
    4. 先行指标背离检测 (15%) - MACD/成交量先行背离
    5. 市场情绪反转检测 (15%) - 延后实现
    """
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'multi_level_divergence': 0.35,
            'bsp3_failure': 0.20,
            'center_upgrade': 0.15,
            'leading_indicator_divergence': 0.15,
        }
        
        # 阈值配置
        self.thresholds = {
            'divergence_threshold': 0.7,  # 背驰阈值 70%
            'bsp3_failure_threshold': 0.05,  # buy3 失败阈值 5%
            'confidence_bonus': 0.15,  # 置信度奖励
        }
        
        # 检测器
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=False,
            min_klines_between_turns=2
        ))
        self.segment_calculator = SegmentCalculator(min_pens=2)
        self.center_detector = CenterDetector(min_segments=2)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def warn(self, series: KlineSeries, symbol: str, level: str,
             small_level_series: Optional[KlineSeries] = None,
             large_level_series: Optional[KlineSeries] = None) -> TrendReversalSignal:
        """
        预警趋势反转
        
        Args:
            series: K 线序列 (当前级别)
            symbol: 股票代码
            level: 级别 (1d, 30m, 5m)
            small_level_series: 小级别 K 线序列 (用于多级别背驰)
            large_level_series: 大级别 K 线序列 (用于多级别背驰)
        
        Returns:
            TrendReversalSignal: 反转信号
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
        signal = TrendReversalSignal(
            symbol=symbol,
            level=level,
            timestamp=datetime.now()
        )
        
        # 无中枢或线段，无法检测反转
        if len(centers) < 2 or len(segments) < 3:
            signal.reversal_probability = 0.0
            signal.confidence = 0.0
            signal.warning_level = 'LOW'
            return signal
        
        # 信号检测
        signals = []
        probability = 0.0
        
        # 1. 多级别背驰共振检测 (35%)
        if self._detect_multi_level_divergence(series, small_level_series, large_level_series):
            probability += self.weights['multi_level_divergence']
            signals.append('multi_level_divergence')
            signal.multi_level_divergence = True
        
        # 2. 第三类买卖点失败检测 (20%)
        if self._detect_bsp3_failure(fractals, pens, centers, macd_data):
            probability += self.weights['bsp3_failure']
            signals.append('bsp3_failure')
            signal.bsp3_failure = True
        
        # 3. 中枢升级完成检测 (15%)
        if self._detect_center_upgrade(centers):
            probability += self.weights['center_upgrade']
            signals.append('center_upgrade')
            signal.center_upgrade = True
        
        # 4. 先行指标背离检测 (15%)
        if self._detect_leading_indicator_divergence(prices, volumes, macd_data):
            probability += self.weights['leading_indicator_divergence']
            signals.append('leading_indicator_divergence')
            signal.leading_indicator_divergence = True
        
        # 计算置信度
        signal.reversal_probability = probability
        signal.confidence = self._calculate_confidence(probability, len(signals))
        signal.signals = signals
        
        # 预警级别
        signal.warning_level = self._get_warning_level(probability)
        
        # 预估反转天数
        signal.days_to_reversal = self._estimate_days_to_reversal(probability)
        
        # 预估利润保住率
        signal.profit_preservation_rate = self._estimate_profit_preservation(probability)
        
        return signal
    
    def _detect_multi_level_divergence(self, series: KlineSeries,
                                        small_series: Optional[KlineSeries],
                                        large_series: Optional[KlineSeries]) -> bool:
        """
        多级别背驰共振检测
        
        日线 +30m+5m 同时背驰
        """
        if not (small_series and large_series):
            return False
        
        # 计算各级别 MACD
        prices = [k.close for k in series.klines]
        small_prices = [k.close for k in small_series.klines]
        large_prices = [k.close for k in large_series.klines]
        
        macd = self.macd.calculate(prices)
        small_macd = self.macd.calculate(small_prices)
        large_macd = self.macd.calculate(large_prices)
        
        # 检测各级别背驰
        current_divergence = self._check_divergence(macd)
        small_divergence = self._check_divergence(small_macd)
        large_divergence = self._check_divergence(large_macd)
        
        # 至少 2 个级别背驰 = 共振
        divergence_count = sum([current_divergence, small_divergence, large_divergence])
        
        return divergence_count >= 2
    
    def _check_divergence(self, macd_data) -> bool:
        """检查 MACD 背驰"""
        if len(macd_data) < 10:
            return False
        
        # 简化检测：最近 MACD 柱状图下降
        recent_hist = [macd_data[-i].histogram for i in range(1, 6)]
        if len(recent_hist) >= 3:
            # 连续下降
            if all(recent_hist[i] < recent_hist[i-1] for i in range(1, len(recent_hist))):
                return True
        
        return False
    
    def _detect_bsp3_failure(self, fractals, pens, centers, macd_data) -> bool:
        """
        第三类买卖点失败检测
        
        buy3/sell3 后迅速反转
        """
        if len(centers) < 2:
            return False
        
        # 检测最近的 buy3/sell3
        last_center = centers[-1]
        prev_center = centers[-2]
        
        # buy3 失败：突破后迅速跌回
        if last_center.zg > prev_center.zg:  # 中枢上移
            # 检查是否跌回
            current_price = macd_data[-1].histogram if macd_data else 0
            if current_price < 0:  # MACD 转负
                return True
        
        # sell3 失败：跌破后迅速涨回
        if last_center.zd < prev_center.zd:  # 中枢下移
            # 检查是否涨回
            current_price = macd_data[-1].histogram if macd_data else 0
            if current_price > 0:  # MACD 转正
                return True
        
        return False
    
    def _detect_center_upgrade(self, centers: List) -> bool:
        """
        中枢升级完成检测
        
        小中枢升级为大中枢
        """
        if len(centers) < 3:
            return False
        
        # 中枢数量增加，区间扩大 = 升级
        recent_centers = centers[-3:]
        
        # 检查中枢区间是否扩大
        ranges = [c.range for c in recent_centers]
        if len(ranges) >= 3:
            # 中枢区间持续扩大
            if ranges[-1] > ranges[-2] > ranges[-3]:
                return True
        
        return False
    
    def _detect_leading_indicator_divergence(self, prices: List[float],
                                              volumes: List[int],
                                              macd_data) -> bool:
        """
        先行指标背离检测
        
        MACD/成交量先行背离
        """
        if len(prices) < 20 or len(volumes) < 20:
            return False
        
        # 价格创新高
        recent_high = max(prices[-10:])
        prev_high = max(prices[-20:-10])
        price_new_high = recent_high > prev_high * 1.02  # 2% 以上
        
        # MACD 未创新高
        recent_macd_high = max(m.histogram for m in macd_data[-10:]) if macd_data else 0
        prev_macd_high = max(m.histogram for m in macd_data[-20:-10]) if len(macd_data) >= 20 else 0
        macd_not_new_high = recent_macd_high < prev_macd_high
        
        # 成交量萎缩
        recent_vol = sum(volumes[-5:])
        prev_vol = sum(volumes[-10:-5])
        volume_decline = recent_vol < prev_vol * 0.8
        
        # 价格新高但 MACD 和成交量未新高 = 背离
        if price_new_high and (macd_not_new_high or volume_decline):
            return True
        
        return False
    
    def _calculate_confidence(self, probability: float, signal_count: int) -> float:
        """计算置信度"""
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
            return 'CRITICAL'
        elif probability >= 0.5:
            return 'HIGH'
        elif probability >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _estimate_days_to_reversal(self, probability: float) -> int:
        """预估反转天数"""
        if probability >= 0.7:
            return 3
        elif probability >= 0.5:
            return 5
        elif probability >= 0.3:
            return 7
        else:
            return 0
    
    def _estimate_profit_preservation(self, probability: float) -> float:
        """预估利润保住率"""
        # 概率越高，保住率越高
        if probability >= 0.7:
            return 0.90  # 90%
        elif probability >= 0.5:
            return 0.80  # 80%
        elif probability >= 0.3:
            return 0.70  # 70%
        else:
            return 0.50  # 50%
    
    def format_signal(self, signal: TrendReversalSignal) -> str:
        """格式化信号输出"""
        warning_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '🔴',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        lines = [
            "=" * 70,
            f"🔄 趋势反转预警 - {signal.symbol} ({signal.level})",
            "=" * 70,
            f"时间：{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"反转概率：{signal.reversal_probability*100:.0f}%",
            f"置信度：  {signal.confidence*100:.0f}%",
            f"预警级别：{warning_emoji.get(signal.warning_level, '')} {signal.warning_level}",
            f"",
            f"触发信号 ({len(signal.signals)}个):",
        ]
        
        for sig in signal.signals:
            lines.append(f"   ✅ {sig}")
        
        if signal.multi_level_divergence:
            lines.append(f"多级别背驰：✅ 是")
        if signal.bsp3_failure:
            lines.append(f"第三类买卖点失败：✅ 是")
        if signal.center_upgrade:
            lines.append(f"中枢升级完成：✅ 是")
        if signal.leading_indicator_divergence:
            lines.append(f"先行指标背离：✅ 是")
        
        if signal.days_to_reversal > 0:
            lines.append(f"预估反转：{signal.days_to_reversal} 天内")
        if signal.profit_preservation_rate > 0:
            lines.append(f"利润保住率：{signal.profit_preservation_rate*100:.0f}%")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ==================== 测试函数 ====================

def test_trend_reversal_warning():
    """测试趋势反转预警器"""
    import yfinance as yf
    
    print("=" * 70)
    print("趋势反转预警器测试")
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
    warner = TrendReversalWarner()
    signal = warner.warn(series, symbol, '1d')
    
    # 输出
    print(warner.format_signal(signal))
    
    return signal


if __name__ == '__main__':
    test_trend_reversal_warning()
