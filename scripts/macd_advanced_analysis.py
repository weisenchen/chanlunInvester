#!/usr/bin/env python3
"""
MACD 高级分析模块
MACD Advanced Analysis Module

用于增强缠论买卖点的 MACD 多维度分析

核心功能：
1. MACD 零轴位置分析
2. MACD 柱状图面积背驰
3. 多周期 MACD 共振
4. DIF/DEA 交叉分析
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys

# Add python-layer to path
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))
from trading_system.indicators import MACDIndicator, MACDResult


@dataclass
class MACDZeroAxisAnalysis:
    """MACD 零轴分析结果"""
    position: str  # above_zero, below_zero, crossing_zero
    trend: str  # bullish, bearish, transition
    dif_value: float
    dea_value: float
    histogram_value: float
    distance_from_zero: float  # 距离零轴的距离
    confidence_boost: float  # 置信度提升
    analysis: str


@dataclass
class MACDAreaAnalysis:
    """MACD 柱状图面积分析结果"""
    area1: float  # 第一段面积
    area2: float  # 第二段面积
    area_ratio: float  # 面积比 (area2/area1)
    divergence_strength: str  # very_strong, strong, medium, weak, none
    confidence_boost: float
    analysis: str


@dataclass
class MACDResonanceAnalysis:
    """多周期 MACD 共振分析结果"""
    resonance_type: str  # triple_bull, double_bull, single_bull, triple_bear, etc.
    resonance_count: int  # 共振级别数量 (0-3)
    levels: Dict[str, str]  # 各级别状态 {'1d': 'bull', '30m': 'bull', '5m': 'bear'}
    confidence: float  # 综合置信度 (0-1)
    confidence_boost: float
    analysis: str


@dataclass
class MACDCrossAnalysis:
    """MACD 交叉分析结果"""
    cross_type: str  # golden_cross, death_cross, none
    cross_idx: Optional[int]  # 交叉发生的位置
    bars_since_cross: int  # 距离交叉的 K 线数
    cross_strength: str  # strong, medium, weak
    confidence_boost: float
    analysis: str


@dataclass
class MACDComprehensiveResult:
    """MACD 综合分析结果"""
    # 基础数据
    macd_data: List[MACDResult]
    
    # 各维度分析
    zero_axis: Optional[MACDZeroAxisAnalysis] = None
    area_analysis: Optional[MACDAreaAnalysis] = None
    resonance: Optional[MACDResonanceAnalysis] = None
    cross_analysis: Optional[MACDCrossAnalysis] = None
    
    # 综合评估
    total_confidence_boost: float = 0.0
    reliability_level: str = "medium"
    summary: str = ""


class MACDAdvancedAnalyzer:
    """MACD 高级分析器"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.macd = MACDIndicator(fast=fast, slow=slow, signal=signal)
        
        # 阈值配置
        self.ZERO_AXIS_THRESHOLD = 0.05  # 零轴附近阈值
        self.STRONG_AREA_RATIO = 0.3  # 强背驰面积比阈值
        self.MEDIUM_AREA_RATIO = 0.5  # 中背驰面积比阈值
        self.WEAK_AREA_RATIO = 0.7  # 弱背驰面积比阈值
        
    def analyze_zero_axis(self, macd_data: List[MACDResult]) -> MACDZeroAxisAnalysis:
        """
        MACD 零轴位置分析
        
        零轴上方 = 多头市场
        零轴下方 = 空头市场
        穿越零轴 = 趋势转换
        """
        if not macd_data or len(macd_data) < 1:
            return MACDZeroAxisAnalysis(
                position='unknown',
                trend='unknown',
                dif_value=0, dea_value=0, histogram_value=0,
                distance_from_zero=0, confidence_boost=0,
                analysis='MACD 数据不足'
            )
        
        last = macd_data[-1]
        dif = last.dif
        dea = last.dea
        histogram = last.histogram
        
        # 计算距离零轴的距离
        distance_from_zero = min(abs(dif), abs(dea))
        
        # 判断位置
        if dif > self.ZERO_AXIS_THRESHOLD and dea > self.ZERO_AXIS_THRESHOLD:
            position = 'above_zero'
            trend = 'bullish'
            confidence_boost = 0.10
            analysis = f"MACD 位于零轴上方 (DIF:{dif:.3f}, DEA:{dea:.3f})，多头市场"
        elif dif < -self.ZERO_AXIS_THRESHOLD and dea < -self.ZERO_AXIS_THRESHOLD:
            position = 'below_zero'
            trend = 'bearish'
            confidence_boost = 0.10
            analysis = f"MACD 位于零轴下方 (DIF:{dif:.3f}, DEA:{dea:.3f})，空头市场"
        else:
            position = 'crossing_zero'
            trend = 'transition'
            confidence_boost = 0.05
            analysis = f"MACD 穿越零轴中 (DIF:{dif:.3f}, DEA:{dea:.3f})，趋势转换期"
        
        # 如果是买点且在零轴下方，额外加分 (空头市场反弹)
        # 如果是卖点且在零轴上方，额外加分 (多头市场回调)
        
        return MACDZeroAxisAnalysis(
            position=position,
            trend=trend,
            dif_value=dif,
            dea_value=dea,
            histogram_value=histogram,
            distance_from_zero=distance_from_zero,
            confidence_boost=confidence_boost,
            analysis=analysis
        )
    
    def analyze_divergence_area(self, macd_data: List[MACDResult],
                                 seg1_range: Tuple[int, int],
                                 seg2_range: Tuple[int, int],
                                 is_bull_divergence: bool = True) -> MACDAreaAnalysis:
        """
        MACD 柱状图面积背驰分析
        
        面积 = Σ|柱状图高度|
        面积比 = 第二段面积 / 第一段面积
        
        面积比越小，背驰越强
        """
        if not macd_data or len(macd_data) < max(seg1_range[1], seg2_range[1]):
            return MACDAreaAnalysis(
                area1=0, area2=0, area_ratio=1.0,
                divergence_strength='none', confidence_boost=0,
                analysis='MACD 数据不足'
            )
        
        # 计算两段面积
        area1 = sum(abs(macd_data[i].histogram) for i in range(seg1_range[0], seg1_range[1]+1))
        area2 = sum(abs(macd_data[i].histogram) for i in range(seg2_range[0], seg2_range[1]+1))
        
        # 计算面积比
        area_ratio = area2 / area1 if area1 > 0 else 1.0
        
        # 评估背驰强度
        if area_ratio < self.STRONG_AREA_RATIO:
            divergence_strength = 'very_strong'
            confidence_boost = 0.25
            analysis = f"极强背驰 (面积比:{area_ratio:.2f})，第二段面积仅为第一段的{area_ratio*100:.0f}%"
        elif area_ratio < self.MEDIUM_AREA_RATIO:
            divergence_strength = 'strong'
            confidence_boost = 0.15
            analysis = f"明显背驰 (面积比:{area_ratio:.2f})，第二段面积显著萎缩"
        elif area_ratio < self.WEAK_AREA_RATIO:
            divergence_strength = 'medium'
            confidence_boost = 0.05
            analysis = f"温和背驰 (面积比:{area_ratio:.2f})，第二段面积有所萎缩"
        elif area_ratio > 1.0:
            divergence_strength = 'weak'
            confidence_boost = -0.10
            analysis = f"背驰不成立 (面积比:{area_ratio:.2f})，第二段面积反而扩大"
        else:
            divergence_strength = 'none'
            confidence_boost = 0.0
            analysis = f"无明显背驰 (面积比:{area_ratio:.2f})"
        
        return MACDAreaAnalysis(
            area1=round(area1, 4),
            area2=round(area2, 4),
            area_ratio=round(area_ratio, 4),
            divergence_strength=divergence_strength,
            confidence_boost=confidence_boost,
            analysis=analysis
        )
    
    def analyze_multi_level_resonance(self, macd_1d: List[MACDResult],
                                       macd_30m: List[MACDResult],
                                       macd_5m: List[MACDResult]) -> MACDResonanceAnalysis:
        """
        多周期 MACD 共振分析
        
        检测各级别是否同时出现金叉/死叉
        """
        def get_macd_state(macd_data: List[MACDResult]) -> str:
            """获取 MACD 状态"""
            if not macd_data or len(macd_data) < 2:
                return 'unknown'
            
            last = macd_data[-1]
            prev = macd_data[-2]
            
            # 金叉：DIF 从下向上穿越 DEA
            if prev.dif <= prev.dea and last.dif > last.dea:
                return 'golden_cross'
            # 死叉：DIF 从上向下穿越 DEA
            elif prev.dif >= prev.dea and last.dif < last.dea:
                return 'death_cross'
            # 多头状态：DIF > DEA
            elif last.dif > last.dea:
                return 'bull'
            # 空头状态：DIF < DEA
            else:
                return 'bear'
        
        state_1d = get_macd_state(macd_1d)
        state_30m = get_macd_state(macd_30m)
        state_5m = get_macd_state(macd_5m)
        
        levels = {'1d': state_1d, '30m': state_30m, '5m': state_5m}
        
        # 计算共振数量 (只统计明确的金叉/死叉)
        bull_count = sum(1 for s in [state_1d, state_30m, state_5m] if s in ['golden_cross', 'bull'])
        bear_count = sum(1 for s in [state_1d, state_30m, state_5m] if s in ['death_cross', 'bear'])
        
        # 确定共振类型
        if state_1d == 'golden_cross' and state_30m == 'golden_cross' and state_5m == 'golden_cross':
            resonance_type = 'triple_golden'
            confidence = 0.95
            confidence_boost = 0.30
            analysis = "三周期金叉共振！极强买入信号"
        elif state_1d == 'death_cross' and state_30m == 'death_cross' and state_5m == 'death_cross':
            resonance_type = 'triple_death'
            confidence = 0.95
            confidence_boost = -0.30
            analysis = "三周期死叉共振！极强卖出信号"
        elif bull_count >= 2:
            resonance_type = 'double_bull'
            confidence = 0.75
            confidence_boost = 0.15
            analysis = f"双周期多头共振 (1d:{state_1d}, 30m:{state_30m}, 5m:{state_5m})"
        elif bear_count >= 2:
            resonance_type = 'double_bear'
            confidence = 0.75
            confidence_boost = -0.15
            analysis = f"双周期空头共振 (1d:{state_1d}, 30m:{state_30m}, 5m:{state_5m})"
        elif bull_count >= 1:
            resonance_type = 'single_bull'
            confidence = 0.55
            confidence_boost = 0.05
            analysis = f"单周期多头信号 (1d:{state_1d}, 30m:{state_30m}, 5m:{state_5m})"
        else:
            resonance_type = 'single_bear'
            confidence = 0.45
            confidence_boost = -0.05
            analysis = f"单周期空头信号 (1d:{state_1d}, 30m:{state_30m}, 5m:{state_5m})"
        
        return MACDResonanceAnalysis(
            resonance_type=resonance_type,
            resonance_count=max(bull_count, bear_count),
            levels=levels,
            confidence=confidence,
            confidence_boost=confidence_boost,
            analysis=analysis
        )
    
    def analyze_cross(self, macd_data: List[MACDResult]) -> MACDCrossAnalysis:
        """
        MACD 交叉分析 (金叉/死叉)
        """
        if not macd_data or len(macd_data) < 2:
            return MACDCrossAnalysis(
                cross_type='none', cross_idx=None,
                bars_since_cross=999, cross_strength='none',
                confidence_boost=0, analysis='MACD 数据不足'
            )
        
        # 查找最近的交叉
        cross_idx = None
        cross_type = 'none'
        
        for i in range(len(macd_data) - 1, 0, -1):
            prev = macd_data[i-1]
            curr = macd_data[i]
            
            # 金叉
            if prev.dif <= prev.dea and curr.dif > curr.dea:
                cross_idx = i
                cross_type = 'golden_cross'
                break
            # 死叉
            elif prev.dif >= prev.dea and curr.dif < curr.dea:
                cross_idx = i
                cross_type = 'death_cross'
                break
        
        if cross_idx is None:
            return MACDCrossAnalysis(
                cross_type='none', cross_idx=None,
                bars_since_cross=999, cross_strength='none',
                confidence_boost=0, analysis='近期无 MACD 交叉'
            )
        
        bars_since_cross = len(macd_data) - cross_idx
        
        # 评估交叉强度 (基于交叉时的柱状图变化)
        if cross_idx > 0:
            hist_change = abs(macd_data[cross_idx].histogram - macd_data[cross_idx-1].histogram)
            if hist_change > 0.5:
                cross_strength = 'strong'
                confidence_boost = 0.15
            elif hist_change > 0.2:
                cross_strength = 'medium'
                confidence_boost = 0.10
            else:
                cross_strength = 'weak'
                confidence_boost = 0.05
        else:
            cross_strength = 'weak'
            confidence_boost = 0.05
        
        # 交叉后时间越短，信号越强
        if bars_since_cross <= 3:
            confidence_boost += 0.10
            timing = "刚刚发生"
        elif bars_since_cross <= 10:
            timing = "近期发生"
        else:
            confidence_boost -= 0.05
            timing = "较早发生，信号可能已失效"
        
        cross_name = "金叉" if cross_type == 'golden_cross' else "死叉"
        analysis = f"MACD{cross_name} ({timing}, {bars_since_cross}K 前)，强度:{cross_strength}"
        
        return MACDCrossAnalysis(
            cross_type=cross_type,
            cross_idx=cross_idx,
            bars_since_cross=bars_since_cross,
            cross_strength=cross_strength,
            confidence_boost=confidence_boost,
            analysis=analysis
        )
    
    def comprehensive_analysis(self, prices: List[float],
                                macd_1d: Optional[List[MACDResult]] = None,
                                macd_30m: Optional[List[MACDResult]] = None,
                                macd_5m: Optional[List[MACDResult]] = None,
                                seg1_range: Optional[Tuple[int, int]] = None,
                                seg2_range: Optional[Tuple[int, int]] = None,
                                is_bull_divergence: bool = True) -> MACDComprehensiveResult:
        """
        MACD 综合分析
        
        整合所有维度的分析结果
        """
        # 使用最新级别的 MACD 数据进行基础分析
        primary_macd = macd_30m or macd_1d or macd_5m
        if not primary_macd:
            primary_macd = self.macd.calculate(prices)
        
        result = MACDComprehensiveResult(macd_data=primary_macd)
        
        # 1. 零轴分析
        result.zero_axis = self.analyze_zero_axis(primary_macd)
        
        # 2. 面积背驰分析 (如果提供了段范围)
        if seg1_range and seg2_range:
            result.area_analysis = self.analyze_divergence_area(
                primary_macd, seg1_range, seg2_range, is_bull_divergence
            )
        
        # 3. 多周期共振分析 (如果提供了多级别数据)
        if macd_1d and macd_30m and macd_5m:
            result.resonance = self.analyze_multi_level_resonance(macd_1d, macd_30m, macd_5m)
        
        # 4. 交叉分析
        result.cross_analysis = self.analyze_cross(primary_macd)
        
        # 计算总置信度提升
        total_boost = 0.0
        if result.zero_axis:
            total_boost += result.zero_axis.confidence_boost
        if result.area_analysis:
            total_boost += result.area_analysis.confidence_boost
        if result.resonance:
            total_boost += result.resonance.confidence_boost
        if result.cross_analysis:
            total_boost += result.cross_analysis.confidence_boost
        
        # 限制总提升范围 (-0.5 到 +0.5)
        total_boost = max(-0.5, min(0.5, total_boost))
        result.total_confidence_boost = round(total_boost, 2)
        
        # 评估可靠性等级
        if total_boost >= 0.30:
            result.reliability_level = 'very_high'
        elif total_boost >= 0.15:
            result.reliability_level = 'high'
        elif total_boost >= 0.0:
            result.reliability_level = 'medium'
        else:
            result.reliability_level = 'low'
        
        # 生成总结
        summary_parts = []
        if result.zero_axis:
            summary_parts.append(f"零轴：{result.zero_axis.position}")
        if result.area_analysis:
            summary_parts.append(f"背驰：{result.area_analysis.divergence_strength}")
        if result.resonance:
            summary_parts.append(f"共振：{result.resonance.resonance_type}")
        if result.cross_analysis:
            summary_parts.append(f"交叉：{result.cross_analysis.cross_type}")
        
        result.summary = " | ".join(summary_parts) if summary_parts else "无显著特征"
        
        return result


# ==================== 测试函数 ====================

def test_macd_advanced():
    """测试 MACD 高级分析模块"""
    import random
    
    # 生成测试价格数据
    np.random.seed(42)
    prices = (100 + np.cumsum(np.random.randn(100) * 0.5)).tolist()
    
    analyzer = MACDAdvancedAnalyzer()
    macd_data = analyzer.macd.calculate(prices)
    
    print("=" * 60)
    print("MACD 高级分析模块测试")
    print("=" * 60)
    
    # 测试零轴分析
    zero_axis = analyzer.analyze_zero_axis(macd_data)
    print(f"\n【零轴分析】")
    print(f"  位置：{zero_axis.position}")
    print(f"  趋势：{zero_axis.trend}")
    print(f"  DIF: {zero_axis.dif_value:.3f}")
    print(f"  DEA: {zero_axis.dea_value:.3f}")
    print(f"  置信度提升：{zero_axis.confidence_boost:+.2f}")
    print(f"  分析：{zero_axis.analysis}")
    
    # 测试交叉分析
    cross = analyzer.analyze_cross(macd_data)
    print(f"\n【交叉分析】")
    print(f"  类型：{cross.cross_type}")
    print(f"  强度：{cross.cross_strength}")
    print(f"  距离：{cross.bars_since_cross}K")
    print(f"  置信度提升：{cross.confidence_boost:+.2f}")
    print(f"  分析：{cross.analysis}")
    
    # 测试综合分析
    print(f"\n【综合分析】")
    comprehensive = analyzer.comprehensive_analysis(prices, macd_30m=macd_data)
    print(f"  总置信度提升：{comprehensive.total_confidence_boost:+.2f}")
    print(f"  可靠性等级：{comprehensive.reliability_level}")
    print(f"  总结：{comprehensive.summary}")
    
    print("=" * 60)
    
    return comprehensive


if __name__ == '__main__':
    test_macd_advanced()
