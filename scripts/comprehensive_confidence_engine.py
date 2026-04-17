#!/usr/bin/env python3
"""
综合置信度引擎
Comprehensive Confidence Engine

缠论改进版 - Phase 4

目标：整合 Phase 1-3，统一置信度评估
核心：多因子加权模型 (起势 + 衰减 + 反转)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

from trading_system.kline import Kline, KlineSeries
from trend_start_detector import TrendStartDetector, TrendStartSignal
from trend_decay_monitor import TrendDecayMonitor, TrendDecaySignal
from trend_reversal_warning import TrendReversalWarner, TrendReversalSignal


@dataclass
class ComprehensiveSignal:
    """综合信号"""
    symbol: str
    level: str
    timestamp: datetime
    
    # 各维度信号
    start_signal: Optional[TrendStartSignal] = None
    decay_signal: Optional[TrendDecaySignal] = None
    reversal_signal: Optional[TrendReversalSignal] = None
    
    # 综合评估
    comprehensive_confidence: float = 0.0  # 综合置信度 (0-1)
    recommendation: str = 'HOLD'  # 操作建议
    position_ratio: float = 0.0  # 建议仓位 (0-1)
    
    # 详细评估
    start_confidence: float = 0.0  # 起势置信度
    decay_confidence: float = 0.0  # 衰减置信度
    reversal_confidence: float = 0.0  # 反转置信度
    
    # 风险评估
    risk_level: str = 'MEDIUM'  # 风险等级
    confidence_range: str = 'MEDIUM'  # 置信度区间


class ComprehensiveConfidenceEngine:
    """
    综合置信度引擎
    
    核心逻辑:
    1. 整合 Phase 1 趋势起势检测
    2. 整合 Phase 2 趋势衰减检测
    3. 整合 Phase 3 趋势反转预警
    4. 综合置信度计算 (简单平均)
    5. 操作建议生成
    """
    
    def __init__(self):
        # 检测器
        self.start_detector = TrendStartDetector()
        self.decay_monitor = TrendDecayMonitor()
        self.reversal_warner = TrendReversalWarner()
        
        # 权重配置 (Phase 5 优化版 - 基于回测表现加权)
        # Phase 3 表现最好 (76.3% 识别率) → 权重最高
        # Phase 2 表现良好 (94.8% 准确率) → 权重中等
        # Phase 1 表现一般 (65% 胜率) → 权重最低
        self.weights = {
            'start': 0.25,      # 25% (Phase 1)
            'decay': 0.35,      # 35% (Phase 2)
            'reversal': 0.40,   # 40% (Phase 3)
        }
    
    def evaluate(self, series: KlineSeries, symbol: str, level: str,
                 small_level_series: Optional[KlineSeries] = None,
                 large_level_series: Optional[KlineSeries] = None) -> ComprehensiveSignal:
        """
        综合评估
        
        Args:
            series: K 线序列 (当前级别)
            symbol: 股票代码
            level: 级别 (1d, 30m, 5m)
            small_level_series: 小级别 K 线序列
            large_level_series: 大级别 K 线序列
        
        Returns:
            ComprehensiveSignal: 综合信号
        """
        # 初始化综合信号
        signal = ComprehensiveSignal(
            symbol=symbol,
            level=level,
            timestamp=datetime.now()
        )
        
        # 1. Phase 1: 趋势起势检测
        signal.start_signal = self.start_detector.detect(series, symbol, level, small_level_series)
        signal.start_confidence = signal.start_signal.start_probability
        
        # 2. Phase 2: 趋势衰减检测
        signal.decay_signal = self.decay_monitor.monitor(series, symbol, level, small_level_series)
        signal.decay_confidence = 1.0 - signal.decay_signal.decay_probability  # 衰减概率越低越好
        
        # 3. Phase 3: 趋势反转预警
        signal.reversal_signal = self.reversal_warner.warn(series, symbol, level, small_level_series, large_level_series)
        signal.reversal_confidence = 1.0 - signal.reversal_signal.reversal_probability  # 反转概率越低越好
        
        # 4. 综合置信度计算 (简单平均)
        signal.comprehensive_confidence = self._calculate_comprehensive_confidence(
            signal.start_confidence,
            signal.decay_confidence,
            signal.reversal_confidence
        )
        
        # 5. 操作建议生成
        signal.recommendation = self._get_recommendation(signal.comprehensive_confidence)
        signal.position_ratio = self._get_position_ratio(signal.comprehensive_confidence)
        
        # 6. 风险评估
        signal.risk_level = self._get_risk_level(signal.comprehensive_confidence)
        signal.confidence_range = self._get_confidence_range(signal.comprehensive_confidence)
        
        return signal
    
    def _calculate_comprehensive_confidence(self, start: float, decay: float, reversal: float) -> float:
        """
        计算综合置信度
        
        简单平均:
        confidence = (start + decay + reversal) / 3
        """
        confidence = (start + decay + reversal) / 3
        return min(max(confidence, 0.0), 1.0)  # 限制在 0-1 范围
    
    def _get_recommendation(self, confidence: float) -> str:
        """
        生成操作建议
        
        基于综合置信度
        """
        if confidence >= 0.8:
            return 'STRONG_BUY'  # 强烈买入
        elif confidence >= 0.6:
            return 'BUY'         # 买入
        elif confidence >= 0.4:
            return 'HOLD'        # 持有
        elif confidence >= 0.2:
            return 'SELL'        # 卖出
        else:
            return 'STRONG_SELL' # 强烈卖出
    
    def _get_position_ratio(self, confidence: float) -> float:
        """
        获取建议仓位
        
        基于综合置信度
        """
        if confidence >= 0.8:
            return 0.8  # 80% 仓位
        elif confidence >= 0.6:
            return 0.6  # 60% 仓位
        elif confidence >= 0.4:
            return 0.4  # 40% 仓位
        elif confidence >= 0.2:
            return 0.2  # 20% 仓位
        else:
            return 0.0  # 空仓
    
    def _get_risk_level(self, confidence: float) -> str:
        """
        获取风险等级
        
        置信度越低，风险越高
        """
        if confidence >= 0.7:
            return 'LOW'      # 低风险
        elif confidence >= 0.5:
            return 'MEDIUM'   # 中风险
        else:
            return 'HIGH'     # 高风险
    
    def _get_confidence_range(self, confidence: float) -> str:
        """
        获取置信度区间
        
        用于快速判断
        """
        if confidence >= 0.8:
            return 'VERY_HIGH'  # 极高
        elif confidence >= 0.6:
            return 'HIGH'       # 高
        elif confidence >= 0.4:
            return 'MEDIUM'     # 中
        elif confidence >= 0.2:
            return 'LOW'        # 低
        else:
            return 'VERY_LOW'   # 极低
    
    def format_signal(self, signal: ComprehensiveSignal) -> str:
        """格式化信号输出"""
        recommendation_emoji = {
            'STRONG_BUY': '🚀',
            'BUY': '🟢',
            'HOLD': '⚪',
            'SELL': '🔴',
            'STRONG_SELL': '💥'
        }
        
        risk_emoji = {
            'LOW': '🟢',
            'MEDIUM': '🟡',
            'HIGH': '🔴'
        }
        
        lines = [
            "=" * 70,
            f"📊 综合置信度评估 - {signal.symbol} ({signal.level})",
            "=" * 70,
            f"时间：{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"综合置信度：{signal.comprehensive_confidence*100:.0f}%",
            f"置信度区间：{signal.confidence_range}",
            f"风险等级：  {risk_emoji.get(signal.risk_level, '')} {signal.risk_level}",
            f"",
            f"各维度置信度:",
            f"   起势检测：{signal.start_confidence*100:.0f}%",
            f"   衰减检测：{signal.decay_confidence*100:.0f}%",
            f"   反转预警：{signal.reversal_confidence*100:.0f}%",
            f"",
            f"操作建议：{recommendation_emoji.get(signal.recommendation, '')} {signal.recommendation}",
            f"建议仓位：{signal.position_ratio*100:.0f}%",
            "",
        ]
        
        # 各维度详情
        if signal.start_signal and signal.start_signal.start_probability > 0.3:
            lines.append(f"起势信号:")
            lines.append(f"   概率：{signal.start_signal.start_probability*100:.0f}%")
            lines.append(f"   触发信号：{', '.join(signal.start_signal.signals)}")
            lines.append("")
        
        if signal.decay_signal and signal.decay_signal.decay_probability > 0.3:
            lines.append(f"衰减信号:")
            lines.append(f"   概率：{signal.decay_signal.decay_probability*100:.0f}%")
            lines.append(f"   预警级别：{signal.decay_signal.warning_level}")
            lines.append("")
        
        if signal.reversal_signal and signal.reversal_signal.reversal_probability > 0.3:
            lines.append(f"反转信号:")
            lines.append(f"   概率：{signal.reversal_signal.reversal_probability*100:.0f}%")
            lines.append(f"   预警级别：{signal.reversal_signal.warning_level}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ==================== 测试函数 ====================

def test_comprehensive_confidence_engine():
    """测试综合置信度引擎"""
    import yfinance as yf
    
    print("=" * 70)
    print("综合置信度引擎测试")
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
    
    # 评估
    engine = ComprehensiveConfidenceEngine()
    signal = engine.evaluate(series, symbol, '1d')
    
    # 输出
    print(engine.format_signal(signal))
    
    return signal


if __name__ == '__main__':
    test_comprehensive_confidence_engine()
