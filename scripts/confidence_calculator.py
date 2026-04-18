#!/usr/bin/env python3
"""
综合可信度计算器
Comprehensive Confidence Calculator

整合多维度指标，计算买卖点的综合可信度

整合维度：
1. 缠论价格结构 (基础)
2. 成交量确认 (新增)
3. MACD 多维度分析 (新增)
4. 行业趋势 (现有)
5. 基本面 (现有)
6. 消息面 (现有)

输出：
- 综合置信度 (0-100%)
- 可靠性等级 (VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW)
- 操作建议 (Strong Buy, Buy, Light Buy, Observe, Avoid)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
from volume_confirmation import VolumeConfirmation, VolumeConfirmationResult
from macd_advanced_analysis import MACDAdvancedAnalyzer, MACDComprehensiveResult

# v6.0 新增：中枢动量可信度整合
try:
    from trading_system.center_momentum_confidence import (
        CenterMomentumConfidenceCalculator,
        CenterMomentumConfidenceResult
    )
    CENTER_MOMENTUM_ENABLED = True
except ImportError:
    CENTER_MOMENTUM_ENABLED = False


class ReliabilityLevel(Enum):
    """可靠性等级"""
    VERY_HIGH = "very_high"  # ≥85%
    HIGH = "high"            # 70-84%
    MEDIUM = "medium"        # 55-69%
    LOW = "low"              # 40-54%
    VERY_LOW = "very_low"    # <40%


class OperationSuggestion(Enum):
    """操作建议"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    LIGHT_BUY = "LIGHT_BUY"
    OBSERVE = "OBSERVE"
    AVOID = "AVOID"
    STRONG_SELL = "STRONG_SELL"
    SELL = "SELL"
    LIGHT_SELL = "LIGHT_SELL"


@dataclass
class ConfidenceFactors:
    """置信度因子"""
    # 基础因子 (缠论价格结构)
    chanlun_base: float = 0.5  # 缠论基础置信度 (0-1)
    
    # 成交量因子
    volume_verified: bool = False
    volume_confidence_boost: float = 0.0
    volume_reliability: str = "unknown"
    
    # MACD 因子
    macd_divergence: bool = False
    macd_confidence_boost: float = 0.0
    macd_reliability: str = "unknown"
    macd_zero_axis: str = "unknown"
    macd_resonance: str = "unknown"
    
    # 多级别确认因子
    multi_level_confirmed: bool = False
    multi_level_count: int = 0
    
    # 外部因子 (可选，来自 enhanced_confidence_analyzer)
    industry_score: float = 0.5
    fundamental_score: float = 0.5
    sentiment_score: float = 0.5
    
    # 中枢动量因子 (v6.0 新增)
    center_momentum_adjustment: float = 0.0  # 中枢动量调整值 (-0.4 到 +0.4)
    center_count: int = 0  # 中枢数量
    center_position: str = "unknown"  # 中枢位置
    momentum_status: str = "unknown"  # 动量状态
    divergence_risk: bool = False  # 背驰风险


@dataclass
class ComprehensiveConfidenceResult:
    """综合可信度结果"""
    # 输入信号信息
    symbol: str
    signal_type: str  # buy1, buy2, sell1, sell2
    level: str  # 5m, 30m, 1d
    price: float
    
    # 各维度得分
    chanlun_score: float  # 缠论基础得分
    volume_score: float   # 成交量得分
    macd_score: float     # MACD 得分
    multi_level_score: float  # 多级别得分
    external_score: float     # 外部因子得分 (行业/基本面/消息面)
    
    # 综合结果
    final_confidence: float  # 最终置信度 (0-1)
    reliability_level: ReliabilityLevel
    operation_suggestion: OperationSuggestion
    
    # 详细分析
    factors: ConfidenceFactors
    breakdown: Dict[str, float]  # 各因子贡献明细
    analysis_summary: str
    timestamp: datetime = None
    
    # 计算字段 (由 __post_init__ 设置)
    confidence_percent: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.confidence_percent = f"{self.final_confidence*100:.0f}%"


class ComprehensiveConfidenceCalculator:
    """综合可信度计算器"""
    
    def __init__(self):
        self.volume_confirm = VolumeConfirmation()
        self.macd_analyzer = MACDAdvancedAnalyzer()
        
        # 权重配置
        self.WEIGHTS = {
            'chanlun_base': 0.35,       # 缠论价格结构 (基础)
            'volume': 0.15,             # 成交量确认
            'macd': 0.20,               # MACD 多维度
            'multi_level': 0.15,        # 多级别确认
            'external': 0.15,           # 外部因子 (行业/基本面/消息面)
        }
        
        # 可靠性阈值
        self.THRESHOLDS = {
            'very_high': 0.85,
            'high': 0.70,
            'medium': 0.55,
            'low': 0.40,
        }
    
    def calculate(self, symbol: str, signal_type: str, level: str, price: float,
                  prices: List[float], volumes: List[float],
                  macd_data: List,
                  chanlun_base_confidence: float = 0.5,
                  divergence_start_idx: Optional[int] = None,
                  divergence_end_idx: Optional[int] = None,
                  confirmation_start_idx: Optional[int] = None,
                  confirmation_end_idx: Optional[int] = None,
                  macd_1d: Optional[List] = None,
                  macd_30m: Optional[List] = None,
                  macd_5m: Optional[List] = None,
                  multi_level_confirmed: bool = False,
                  multi_level_count: int = 0,
                  external_factors: Optional[Dict] = None,
                  centers: Optional[List] = None,
                  segments: Optional[List] = None) -> ComprehensiveConfidenceResult:
        """
        计算综合可信度
        
        Args:
            symbol: 股票代码
            signal_type: 信号类型 (buy1, buy2, sell1, sell2)
            level: 级别 (5m, 30m, 1d)
            price: 当前价格
            prices: 价格序列
            volumes: 成交量序列
            macd_data: MACD 数据
            chanlun_base_confidence: 缠论基础置信度
            divergence_start_idx: 背驰段起始索引
            divergence_end_idx: 背驰段结束索引
            confirmation_start_idx: 确认段起始索引
            confirmation_end_idx: 确认段结束索引
            macd_1d/30m/5m: 多级别 MACD 数据
            multi_level_confirmed: 多级别是否确认
            multi_level_count: 确认的级别数量
            external_factors: 外部因子 (行业/基本面/消息面得分)
            centers: 中枢列表 (v6.0 新增，用于中枢动量分析)
            segments: 线段列表 (v6.0 新增，用于中枢动量分析)
        """
        factors = ConfidenceFactors(
            chanlun_base=chanlun_base_confidence,
            multi_level_confirmed=multi_level_confirmed,
            multi_level_count=multi_level_count
        )
        
        # 设置外部因子
        if external_factors:
            factors.industry_score = external_factors.get('industry', 0.5)
            factors.fundamental_score = external_factors.get('fundamental', 0.5)
            factors.sentiment_score = external_factors.get('sentiment', 0.5)
        
        # 【v6.0 新增】中枢动量分析
        center_momentum_result = None
        if CENTER_MOMENTUM_ENABLED and centers and segments:
            try:
                center_calc = CenterMomentumConfidenceCalculator()
                center_momentum_result = center_calc.calculate(
                    symbol=symbol,
                    level=level,
                    price=price,
                    centers=centers,
                    segments=segments,
                    level_name=level
                )
                
                # 填充因子
                factors.center_momentum_adjustment = center_momentum_result.total_bonus
                factors.center_count = center_momentum_result.center_count
                factors.center_position = center_momentum_result.center_position.value
                factors.momentum_status = center_momentum_result.momentum_status.value
                factors.divergence_risk = center_momentum_result.divergence_risk
                
                # 应用中枢动量调整到缠论基础置信度
                adjusted_chanlun_base = chanlun_base_confidence + center_momentum_result.total_bonus
                
                # 背驰风险强制降级
                if center_momentum_result.divergence_risk:
                    adjusted_chanlun_base = min(adjusted_chanlun_base, 0.40)
                
                # 限制范围
                factors.chanlun_base = max(0.0, min(1.0, adjusted_chanlun_base))
                
            except Exception as e:
                # 中枢动量分析失败，使用原始值
                factors.center_momentum_adjustment = 0.0
        # 1. 成交量分析
        volume_result = self._analyze_volume(
            signal_type, level, prices, volumes,
            divergence_start_idx, divergence_end_idx,
            confirmation_start_idx, confirmation_end_idx
        )
        factors.volume_verified = volume_result.verified
        factors.volume_confidence_boost = volume_result.confidence_boost
        factors.volume_reliability = volume_result.reliability_level
        
        # 2. MACD 分析
        macd_result = self._analyze_macd(
            signal_type, level, prices, macd_data,
            macd_1d, macd_30m, macd_5m,
            divergence_start_idx, divergence_end_idx,
            seg2_range=(confirmation_start_idx, confirmation_end_idx) if confirmation_start_idx else None
        )
        factors.macd_divergence = macd_result.area_analysis.divergence_strength != 'none' if macd_result.area_analysis else False
        factors.macd_confidence_boost = macd_result.total_confidence_boost
        factors.macd_reliability = macd_result.reliability_level
        factors.macd_zero_axis = macd_result.zero_axis.position if macd_result.zero_axis else 'unknown'
        factors.macd_resonance = macd_result.resonance.resonance_type if macd_result.resonance else 'unknown'
        
        # 3. 计算各维度得分
        # 缠论基础得分 (已包含中枢动量调整)
        chanlun_score = factors.chanlun_base
        
        # 成交量得分
        volume_score = 0.5 + factors.volume_confidence_boost
        volume_score = max(0, min(1, volume_score))
        
        macd_score = 0.5 + factors.macd_confidence_boost
        macd_score = max(0, min(1, macd_score))
        
        multi_level_score = self._calculate_multi_level_score(
            multi_level_confirmed, multi_level_count
        )
        
        external_score = self._calculate_external_score(factors)
        
        # 4. 加权计算最终置信度
        final_confidence = (
            chanlun_score * self.WEIGHTS['chanlun_base'] +
            volume_score * self.WEIGHTS['volume'] +
            macd_score * self.WEIGHTS['macd'] +
            multi_level_score * self.WEIGHTS['multi_level'] +
            external_score * self.WEIGHTS['external']
        )
        final_confidence = max(0, min(1, final_confidence))
        
        # 5. 确定可靠性等级
        reliability_level = self._get_reliability_level(final_confidence)
        
        # 6. 生成操作建议
        operation_suggestion = self._get_operation_suggestion(
            signal_type, reliability_level, final_confidence
        )
        
        # 7. 计算各因子贡献明细
        breakdown = {
            '缠论基础': chanlun_score * self.WEIGHTS['chanlun_base'],
            '成交量': volume_score * self.WEIGHTS['volume'],
            'MACD': macd_score * self.WEIGHTS['macd'],
            '多级别': multi_level_score * self.WEIGHTS['multi_level'],
            '外部因子': external_score * self.WEIGHTS['external'],
        }
        
        # 【v6.0 新增】中枢动量调整明细
        if CENTER_MOMENTUM_ENABLED and center_momentum_result:
            breakdown['中枢动量调整'] = factors.center_momentum_adjustment
            breakdown['缠论基础 (原始)'] = chanlun_base_confidence * self.WEIGHTS['chanlun_base']
            breakdown['缠论基础 (调整后)'] = factors.chanlun_base * self.WEIGHTS['chanlun_base']
        
        # 8. 生成分析总结
        analysis_summary = self._generate_summary(
            symbol, signal_type, level, price,
            factors, reliability_level, operation_suggestion
        )
        
        return ComprehensiveConfidenceResult(
            symbol=symbol,
            signal_type=signal_type,
            level=level,
            price=price,
            chanlun_score=round(chanlun_score, 3),
            volume_score=round(volume_score, 3),
            macd_score=round(macd_score, 3),
            multi_level_score=round(multi_level_score, 3),
            external_score=round(external_score, 3),
            final_confidence=round(final_confidence, 3),
            reliability_level=reliability_level,
            operation_suggestion=operation_suggestion,
            factors=factors,
            breakdown=breakdown,
            analysis_summary=analysis_summary
        )
    
    def _analyze_volume(self, signal_type: str, level: str,
                        prices: List[float], volumes: List[float],
                        div_start: Optional[int], div_end: Optional[int],
                        conf_start: Optional[int], conf_end: Optional[int]) -> VolumeConfirmationResult:
        """成交量分析"""
        if signal_type in ['buy1', 'sell1']:
            if div_start is not None and div_end is not None:
                return self.volume_confirm.analyze_buy1_divergence(
                    prices, volumes, div_start, div_end
                )
        elif signal_type == 'buy2':
            if conf_start is not None and conf_end is not None and div_end is not None:
                return self.volume_confirm.analyze_buy2_confirmation(
                    prices, volumes, conf_start, conf_end, div_end
                )
        elif signal_type == 'sell2':
            if conf_start is not None and conf_end is not None:
                return self.volume_confirm.analyze_sell_signals(
                    prices, volumes, signal_type, conf_start, conf_end
                )
        
        # 默认返回中性结果
        return VolumeConfirmationResult(
            signal_type=signal_type,
            level=level,
            verified=False,
            confidence_boost=0.0,
            reliability_level='medium',
            details={'note': '数据不足，无法进行成交量分析'}
        )
    
    def _analyze_macd(self, signal_type: str, level: str,
                      prices: List[float], macd_data: List,
                      macd_1d: Optional[List], macd_30m: Optional[List], macd_5m: Optional[List],
                      div_start: Optional[int], div_end: Optional[int],
                      seg2_range: Optional[Tuple]) -> MACDComprehensiveResult:
        """MACD 分析"""
        seg1_range = None
        if div_start is not None and div_end is not None:
            seg1_range = (div_start, div_end)
        
        is_bull = signal_type in ['buy1', 'buy2']
        
        return self.macd_analyzer.comprehensive_analysis(
            prices=prices,
            macd_1d=macd_1d,
            macd_30m=macd_30m,
            macd_5m=macd_5m,
            seg1_range=seg1_range,
            seg2_range=seg2_range,
            is_bull_divergence=is_bull
        )
    
    def _calculate_multi_level_score(self, confirmed: bool, count: int) -> float:
        """计算多级别得分"""
        if not confirmed:
            return 0.5
        
        # 根据确认的级别数量加分
        if count >= 3:
            return 0.95  # 三级别共振
        elif count == 2:
            return 0.80  # 双级别共振
        else:
            return 0.65  # 单级别确认
    
    def _calculate_external_score(self, factors: ConfidenceFactors) -> float:
        """计算外部因子得分"""
        # 简单平均
        return (factors.industry_score + factors.fundamental_score + factors.sentiment_score) / 3
    
    def _get_reliability_level(self, confidence: float) -> ReliabilityLevel:
        """获取可靠性等级"""
        if confidence >= self.THRESHOLDS['very_high']:
            return ReliabilityLevel.VERY_HIGH
        elif confidence >= self.THRESHOLDS['high']:
            return ReliabilityLevel.HIGH
        elif confidence >= self.THRESHOLDS['medium']:
            return ReliabilityLevel.MEDIUM
        elif confidence >= self.THRESHOLDS['low']:
            return ReliabilityLevel.LOW
        else:
            return ReliabilityLevel.VERY_LOW
    
    def _get_operation_suggestion(self, signal_type: str, 
                                   reliability: ReliabilityLevel,
                                   confidence: float) -> OperationSuggestion:
        """生成操作建议"""
        is_buy = signal_type in ['buy1', 'buy2', 'buy3']
        
        if reliability == ReliabilityLevel.VERY_HIGH:
            return OperationSuggestion.STRONG_BUY if is_buy else OperationSuggestion.STRONG_SELL
        elif reliability == ReliabilityLevel.HIGH:
            return OperationSuggestion.BUY if is_buy else OperationSuggestion.SELL
        elif reliability == ReliabilityLevel.MEDIUM:
            return OperationSuggestion.LIGHT_BUY if is_buy else OperationSuggestion.LIGHT_SELL
        elif reliability == ReliabilityLevel.LOW:
            return OperationSuggestion.OBSERVE
        else:
            return OperationSuggestion.AVOID
    
    def _generate_summary(self, symbol: str, signal_type: str, level: str, price: float,
                          factors: ConfidenceFactors, reliability: ReliabilityLevel,
                          suggestion: OperationSuggestion) -> str:
        """生成分析总结"""
        parts = []
        
        # 信号信息
        signal_name = {
            'buy1': '第一类买点',
            'buy2': '第二类买点',
            'sell1': '第一类卖点',
            'sell2': '第二类卖点',
        }.get(signal_type, signal_type)
        
        parts.append(f"{symbol} {level} {signal_name} @ ${price:.2f}")
        
        # 成交量状态
        if factors.volume_verified:
            parts.append(f"✅ 成交量确认 ({factors.volume_reliability})")
        else:
            parts.append(f"⚪ 成交量未确认")
        
        # MACD 状态
        if factors.macd_divergence:
            parts.append(f"✅ MACD 背驰 ({factors.macd_reliability})")
        if factors.macd_zero_axis != 'unknown':
            parts.append(f"零轴：{factors.macd_zero_axis}")
        if factors.macd_resonance != 'unknown':
            parts.append(f"共振：{factors.macd_resonance}")
        
        # 多级别状态
        if factors.multi_level_confirmed:
            parts.append(f"✅ 多级别确认 ({factors.multi_level_count}级别)")
        
        # 综合结果
        parts.append(f"综合：{reliability.value.upper()} → {suggestion.value}")
        
        return " | ".join(parts)
    
    def format_report(self, result: ComprehensiveConfidenceResult) -> str:
        """格式化报告输出"""
        lines = [
            "=" * 60,
            f"📊 综合可信度分析报告",
            "=" * 60,
            "",
            f"🎯 信号信息",
            f"   标的：{result.symbol}",
            f"   类型：{result.signal_type}",
            f"   级别：{result.level}",
            f"   价格：${result.price:.2f}",
            "",
            f"📈 各维度得分",
            f"   缠论基础：{result.chanlun_score:.1%} (权重 {self.WEIGHTS['chanlun_base']:.0%})",
            f"   成交量：  {result.volume_score:.1%} (权重 {self.WEIGHTS['volume']:.0%})",
            f"   MACD:     {result.macd_score:.1%} (权重 {self.WEIGHTS['macd']:.0%})",
            f"   多级别：  {result.multi_level_score:.1%} (权重 {self.WEIGHTS['multi_level']:.0%})",
            f"   外部因子：{result.external_score:.1%} (权重 {self.WEIGHTS['external']:.0%})",
            "",
            f"═══════════════════════════════════════",
            f"综合置信度：{result.confidence_percent}",
            f"可靠性等级：{result.reliability_level.value.upper()}",
            f"操作建议：  {result.operation_suggestion.value}",
            f"═══════════════════════════════════════",
            "",
            f"📝 详细分析",
            f"   {result.analysis_summary}",
            "",
            f"生成时间：{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ]
        return "\n".join(lines)


# ==================== 测试函数 ====================

def test_confidence_calculator():
    """测试综合可信度计算器"""
    np.random.seed(42)
    
    # 生成测试数据
    prices = (100 + np.cumsum(np.random.randn(100) * 0.5)).tolist()
    volumes = (1000 + np.random.randn(100) * 200).tolist()
    volumes = [max(100, v) for v in volumes]  # 确保正数
    
    calculator = ComprehensiveConfidenceCalculator()
    macd_data = calculator.macd_analyzer.macd.calculate(prices)
    
    # 模拟 buy1 信号
    result = calculator.calculate(
        symbol='SMR',
        signal_type='buy1',
        level='30m',
        price=11.27,
        prices=prices,
        volumes=volumes,
        macd_data=macd_data,
        chanlun_base_confidence=0.65,
        divergence_start_idx=80,
        divergence_end_idx=99,
        multi_level_confirmed=True,
        multi_level_count=2,
        external_factors={
            'industry': 0.70,
            'fundamental': 0.60,
            'sentiment': 0.65,
        }
    )
    
    print(calculator.format_report(result))
    
    return result


if __name__ == '__main__':
    test_confidence_calculator()
