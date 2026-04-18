"""
中枢动量可信度整合模块
Center Momentum Confidence Integration
缠论 v6.0 - Phase 1

功能:
1. 根据中枢序号调整可信度
2. 根据动量状态调整可信度
3. 根据趋势延续性调整可信度
4. 背驰风险预警

整合到综合可信度计算流程中
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from center_momentum import (
    CenterMomentumAnalyzer,
    CenterAnalysisResult,
    CenterPosition,
    MomentumStatus,
    TrendDirection,
    format_center_analysis_report
)


class ConfidenceAdjustmentLevel(Enum):
    """可信度调整等级"""
    STRONG_POSITIVE = "strong_positive"    # +20% 以上
    MODERATE_POSITIVE = "moderate_positive"  # +10-20%
    SLIGHT_POSITIVE = "slight_positive"     # +5-10%
    NEUTRAL = "neutral"                     # -5% 到 +5%
    SLIGHT_NEGATIVE = "slight_negative"     # -5% 到 -10%
    MODERATE_NEGATIVE = "moderate_negative"  # -10% 到 -20%
    STRONG_NEGATIVE = "strong_negative"     # -20% 以下


@dataclass
class CenterMomentumConfidenceResult:
    """
    中枢动量可信度结果
    
    用于整合到综合可信度计算中
    """
    # 输入信息
    symbol: str
    level: str
    price: float
    
    # 中枢分析基础数据
    center_count: int = 0
    center_position: CenterPosition = CenterPosition.BEFORE_FIRST
    momentum_status: MomentumStatus = MomentumStatus.UNKNOWN
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    
    # 可信度调整值 (-1.0 到 1.0)
    position_bonus: float = 0.0       # 中枢序号调整
    momentum_bonus: float = 0.0       # 动量状态调整
    continuation_bonus: float = 0.0   # 延续性调整
    total_bonus: float = 0.0          # 总调整
    
    # 风险评估
    divergence_risk: bool = False     # 背驰风险
    reversal_risk: float = 0.0        # 反转风险 (0-1)
    risk_score: float = 0.0           # 综合风险评分 (0-1)
    
    # 调整等级评估
    adjustment_level: ConfidenceAdjustmentLevel = ConfidenceAdjustmentLevel.NEUTRAL
    
    # 操作建议
    suggestion: str = "OBSERVE"
    confidence_level: str = "MEDIUM"  # HIGH/MEDIUM/LOW
    
    # 详细分析
    analysis_details: Dict = field(default_factory=dict)
    
    # 原始分析结果 (可选)
    raw_analysis: Optional[CenterAnalysisResult] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'level': self.level,
            'price': self.price,
            'center_count': self.center_count,
            'center_position': self.center_position.value,
            'momentum_status': self.momentum_status.value,
            'trend_direction': self.trend_direction.value,
            'position_bonus': self.position_bonus,
            'momentum_bonus': self.momentum_bonus,
            'continuation_bonus': self.continuation_bonus,
            'total_bonus': self.total_bonus,
            'divergence_risk': self.divergence_risk,
            'reversal_risk': self.reversal_risk,
            'risk_score': self.risk_score,
            'adjustment_level': self.adjustment_level.value,
            'suggestion': self.suggestion,
            'confidence_level': self.confidence_level,
        }


class CenterMomentumConfidenceCalculator:
    """
    中枢动量可信度计算器
    
    核心逻辑:
    1. 执行中枢动量分析
    2. 计算各维度可信度调整
    3. 评估背驰风险
    4. 生成操作建议
    
    整合到综合可信度计算:
    adjusted_chanlun_base = base_confidence + total_bonus
    adjusted_chanlun_base = max(0.0, min(1.0, adjusted_chanlun_base))
    
    背驰风险强制降级:
    if divergence_risk:
        adjusted_chanlun_base = min(adjusted_chanlun_base, 0.40)
    """
    
    def __init__(self):
        """初始化计算器"""
        self.analyzer = CenterMomentumAnalyzer()
        
        # ==================== 配置参数 ====================
        # 这些参数可以通过回测优化
        
        # 中枢序号调整配置
        self.POSITION_BONUS_CONFIG = {
            CenterPosition.BEFORE_FIRST: 0.00,    # 无中枢，不调整
            CenterPosition.IN_FIRST: 0.05,        # 第一中枢中，轻微正面
            CenterPosition.AFTER_FIRST: 0.10,     # 第一中枢后，趋势初现
            CenterPosition.IN_SECOND: 0.10,       # 第二中枢中，正面
            CenterPosition.AFTER_SECOND: 0.15,    # 第二中枢后，趋势确认 ✅
            CenterPosition.IN_THIRD: -0.10,       # 第三中枢中，警惕 ⚠️
            CenterPosition.AFTER_THIRD: -0.25,    # 第三中枢后，背驰风险 ⚠️
            CenterPosition.EXTENSION: -0.05,      # 中枢延伸，级别扩张
        }
        
        # 动量状态调整配置
        self.MOMENTUM_BONUS_CONFIG = {
            MomentumStatus.INCREASING: 0.10,      # 动量增强 ✅
            MomentumStatus.STABLE: 0.00,          # 动量稳定
            MomentumStatus.DECREASING: -0.10,     # 动量衰减 ⚠️
            MomentumStatus.UNKNOWN: 0.00,         # 未知
        }
        
        # 延续性调整配置
        self.CONTINUATION_BONUS_THRESHOLD_HIGH = 70.0   # >70% → +10%
        self.CONTINUATION_BONUS_THRESHOLD_LOW = 50.0    # <50% → -10%
        self.CONTINUATION_BONUS_VALUE = 0.10
        
        # 背驰风险预警配置
        self.DIVERGENCE_RISK_THRESHOLD = 0.50    # 风险评分≥50% 触发预警
        self.DIVERGENCE_RISK_FORCED_CAP = 0.40   # 强制降级上限 40%
        
        # 风险评分权重
        self.RISK_WEIGHTS = {
            'position': 0.40,    # 中枢位置权重 40%
            'momentum': 0.35,    # 动量状态权重 35%
            'reversal': 0.25,    # 反转风险权重 25%
        }
        
        # 调整等级阈值
        self.ADJUSTMENT_LEVEL_THRESHOLDS = {
            ConfidenceAdjustmentLevel.STRONG_POSITIVE: 0.20,
            ConfidenceAdjustmentLevel.MODERATE_POSITIVE: 0.10,
            ConfidenceAdjustmentLevel.SLIGHT_POSITIVE: 0.05,
            ConfidenceAdjustmentLevel.SLIGHT_NEGATIVE: -0.05,
            ConfidenceAdjustmentLevel.MODERATE_NEGATIVE: -0.10,
            ConfidenceAdjustmentLevel.STRONG_NEGATIVE: -0.20,
        }
    
    def calculate(self, symbol: str, level: str, price: float,
                  centers: List, segments: List,
                  level_name: str = "unknown") -> CenterMomentumConfidenceResult:
        """
        计算中枢动量可信度
        
        Args:
            symbol: 股票代码
            level: 级别 (1d/30m/5m)
            price: 当前价格
            centers: 中枢列表 (Center 对象)
            segments: 线段列表 (Segment 对象)
            level_name: 级别名称 (用于分析器)
        
        Returns:
            CenterMomentumConfidenceResult: 可信度结果
        """
        # 初始化结果
        result = CenterMomentumConfidenceResult(
            symbol=symbol,
            level=level,
            price=price
        )
        
        # 处理空数据
        if not centers or not segments:
            result.suggestion = "NO_DATA"
            result.confidence_level = "UNKNOWN"
            result.analysis_details['reason'] = "无中枢或线段数据"
            return result
        
        try:
            # 1. 执行中枢动量分析
            raw_analysis = self.analyzer.analyze(centers, segments, price)
            result.raw_analysis = raw_analysis
            
            # 2. 填充基础数据
            result.center_count = len(raw_analysis.centers)
            result.center_position = raw_analysis.center_position
            result.momentum_status = raw_analysis.momentum_status
            result.trend_direction = raw_analysis.trend_direction
            result.reversal_risk = raw_analysis.reversal_risk / 100.0
            
            # 3. 计算各维度调整
            result.position_bonus = self._calculate_position_bonus(raw_analysis.center_position)
            result.momentum_bonus = self._calculate_momentum_bonus(raw_analysis.momentum_status)
            result.continuation_bonus = self._calculate_continuation_bonus(raw_analysis.continuation_probability)
            
            # 4. 计算总调整
            result.total_bonus = result.position_bonus + result.momentum_bonus + result.continuation_bonus
            
            # 限制总调整范围 (-0.40 到 +0.40)
            result.total_bonus = max(-0.40, min(0.40, result.total_bonus))
            
            # 5. 计算风险评分
            result.risk_score = self._calculate_risk_score(raw_analysis)
            result.divergence_risk = result.risk_score >= self.DIVERGENCE_RISK_THRESHOLD
            
            # 6. 评估调整等级
            result.adjustment_level = self._evaluate_adjustment_level(result.total_bonus)
            
            # 7. 生成操作建议
            result.suggestion, result.confidence_level = self._generate_suggestion(result)
            
            # 8. 填充详细分析
            result.analysis_details = self._generate_details(raw_analysis, result)
            
        except Exception as e:
            result.suggestion = "ERROR"
            result.confidence_level = "ERROR"
            result.analysis_details['error'] = str(e)
        
        return result
    
    def _calculate_position_bonus(self, position: CenterPosition) -> float:
        """计算中枢序号调整值"""
        return self.POSITION_BONUS_CONFIG.get(position, 0.0)
    
    def _calculate_momentum_bonus(self, status: MomentumStatus) -> float:
        """计算动量状态调整值"""
        return self.MOMENTUM_BONUS_CONFIG.get(status, 0.0)
    
    def _calculate_continuation_bonus(self, continuation_probability: float) -> float:
        """计算延续性调整值"""
        if continuation_probability > self.CONTINUATION_BONUS_THRESHOLD_HIGH:
            return self.CONTINUATION_BONUS_VALUE
        elif continuation_probability < self.CONTINUATION_BONUS_THRESHOLD_LOW:
            return -self.CONTINUATION_BONUS_VALUE
        else:
            return 0.0
    
    def _calculate_risk_score(self, analysis: CenterAnalysisResult) -> float:
        """
        计算综合风险评分 (0-1)
        
        风险因素:
        1. 中枢位置 (第三中枢后风险高)
        2. 动量状态 (衰减风险高)
        3. 反转风险 (直接来自分析结果)
        """
        risk_score = 0.0
        
        # 1. 中枢位置风险
        position_risk = 0.0
        if analysis.center_position == CenterPosition.AFTER_THIRD:
            position_risk = 1.0
        elif analysis.center_position == CenterPosition.IN_THIRD:
            position_risk = 0.6
        elif analysis.center_position == CenterPosition.EXTENSION:
            position_risk = 0.3
        else:
            position_risk = 0.0
        
        # 2. 动量状态风险
        momentum_risk = 0.0
        if analysis.momentum_status == MomentumStatus.DECREASING:
            momentum_risk = 0.8
        elif analysis.momentum_status == MomentumStatus.UNKNOWN:
            momentum_risk = 0.3
        else:
            momentum_risk = 0.0
        
        # 3. 反转风险 (归一化)
        reversal_risk = analysis.reversal_risk / 100.0
        
        # 加权计算
        risk_score = (
            position_risk * self.RISK_WEIGHTS['position'] +
            momentum_risk * self.RISK_WEIGHTS['momentum'] +
            reversal_risk * self.RISK_WEIGHTS['reversal']
        )
        
        return min(1.0, max(0.0, risk_score))
    
    def _evaluate_adjustment_level(self, total_bonus: float) -> ConfidenceAdjustmentLevel:
        """评估调整等级"""
        if total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.STRONG_POSITIVE]:
            return ConfidenceAdjustmentLevel.STRONG_POSITIVE
        elif total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.MODERATE_POSITIVE]:
            return ConfidenceAdjustmentLevel.MODERATE_POSITIVE
        elif total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.SLIGHT_POSITIVE]:
            return ConfidenceAdjustmentLevel.SLIGHT_POSITIVE
        elif total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.SLIGHT_NEGATIVE]:
            return ConfidenceAdjustmentLevel.NEUTRAL
        elif total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.MODERATE_NEGATIVE]:
            return ConfidenceAdjustmentLevel.SLIGHT_NEGATIVE
        elif total_bonus >= self.ADJUSTMENT_LEVEL_THRESHOLDS[ConfidenceAdjustmentLevel.STRONG_NEGATIVE]:
            return ConfidenceAdjustmentLevel.MODERATE_NEGATIVE
        else:
            return ConfidenceAdjustmentLevel.STRONG_NEGATIVE
    
    def _generate_suggestion(self, result: CenterMomentumConfidenceResult) -> tuple:
        """
        生成操作建议和置信度等级
        
        Returns:
            (suggestion, confidence_level)
        """
        # 背驰风险强制降级
        if result.divergence_risk:
            return "AVOID", "LOW"
        
        # 根据总调整生成建议
        if result.total_bonus >= 0.20:
            return "STRONG_FAVORABLE", "HIGH"
        elif result.total_bonus >= 0.10:
            return "FAVORABLE", "MEDIUM_HIGH"
        elif result.total_bonus >= 0.05:
            return "SLIGHTLY_FAVORABLE", "MEDIUM"
        elif result.total_bonus >= -0.05:
            return "NEUTRAL", "MEDIUM"
        elif result.total_bonus >= -0.10:
            return "CAUTION", "MEDIUM_LOW"
        elif result.total_bonus >= -0.20:
            return "AVOID", "LOW"
        else:
            return "STRONG_AVOID", "VERY_LOW"
    
    def _generate_details(self, analysis: CenterAnalysisResult, 
                          result: CenterMomentumConfidenceResult) -> Dict:
        """生成详细分析数据"""
        details = {
            'trend_stage': analysis.trend_stage,
            'continuation_probability': f"{analysis.continuation_probability:.1f}%",
            'reversal_risk': f"{analysis.reversal_risk:.1f}%",
            'momentum_score': f"{analysis.momentum_score:.1f}",
            'adjustment_breakdown': {
                'position': f"{result.position_bonus*100:+.1f}%",
                'momentum': f"{result.momentum_bonus*100:+.1f}%",
                'continuation': f"{result.continuation_bonus*100:+.1f}%",
                'total': f"{result.total_bonus*100:+.1f}%",
            },
            'risk_breakdown': {
                'position_risk': 'HIGH' if analysis.center_position in [
                    CenterPosition.AFTER_THIRD, CenterPosition.IN_THIRD
                ] else 'LOW',
                'momentum_risk': 'HIGH' if analysis.momentum_status == MomentumStatus.DECREASING else 'LOW',
                'reversal_risk': 'HIGH' if analysis.reversal_risk > 60 else 'LOW',
            },
        }
        
        # 中枢序列详情
        if analysis.centers:
            details['centers'] = []
            for c in analysis.centers:
                details['centers'].append({
                    'index': c.index,
                    'zg': f"{c.zg:.2f}",
                    'zd': f"{c.zd:.2f}",
                    'range': f"{c.range_size:.2f}",
                    'range_change': f"{c.range_change*100:+.1f}%",
                    'momentum_change': f"{c.momentum_change*100:+.1f}%",
                })
        
        return details
    
    def apply_to_confidence(self, base_confidence: float, 
                            result: CenterMomentumConfidenceResult) -> float:
        """
        将中枢动量调整应用到基础置信度
        
        Args:
            base_confidence: 原始缠论基础置信度 (0-1)
            result: 中枢动量可信度结果
        
        Returns:
            调整后的置信度 (0-1)
        """
        # 应用调整
        adjusted = base_confidence + result.total_bonus
        
        # 背驰风险强制降级
        if result.divergence_risk:
            adjusted = min(adjusted, self.DIVERGENCE_RISK_FORCED_CAP)
        
        # 限制范围
        return max(0.0, min(1.0, adjusted))
    
    def format_report(self, result: CenterMomentumConfidenceResult) -> str:
        """格式化可信度报告"""
        lines = []
        lines.append("=" * 70)
        lines.append(f"📊 中枢动量可信度报告 - {result.symbol} ({result.level})")
        lines.append("=" * 70)
        lines.append(f"当前价格：${result.price:.2f}")
        lines.append("")
        
        # 中枢分析
        lines.append("【中枢分析】")
        lines.append(f"  中枢数量：{result.center_count}")
        lines.append(f"  当前位置：{result.center_position.value}")
        lines.append(f"  动量状态：{result.momentum_status.value}")
        lines.append(f"  趋势方向：{result.trend_direction.value}")
        lines.append("")
        
        # 可信度调整
        lines.append("【可信度调整】")
        lines.append(f"  中枢序号：{result.position_bonus*100:+.1f}%")
        lines.append(f"  动量状态：{result.momentum_bonus*100:+.1f}%")
        lines.append(f"  延续性：  {result.continuation_bonus*100:+.1f}%")
        lines.append(f"  ─────────────────")
        lines.append(f"  总调整：  {result.total_bonus*100:+.1f}%")
        lines.append(f"  调整等级：{result.adjustment_level.value}")
        lines.append("")
        
        # 风险评估
        lines.append("【风险评估】")
        lines.append(f"  风险评分：{result.risk_score*100:.1f}%")
        lines.append(f"  背驰风险：{'⚠️ 是' if result.divergence_risk else '✅ 否'}")
        lines.append(f"  反转风险：{result.reversal_risk*100:.1f}%")
        lines.append("")
        
        # 操作建议
        lines.append("【操作建议】")
        lines.append(f"  建议：{result.suggestion}")
        lines.append(f"  置信度：{result.confidence_level}")
        lines.append("")
        
        # 详细分析
        if result.analysis_details:
            lines.append("【详细分析】")
            for key, value in result.analysis_details.items():
                if key not in ['centers', 'adjustment_breakdown', 'risk_breakdown']:
                    lines.append(f"  {key}: {value}")
            
            if 'adjustment_breakdown' in result.analysis_details:
                lines.append("  调整明细:")
                for k, v in result.analysis_details['adjustment_breakdown'].items():
                    lines.append(f"    {k}: {v}")
            
            if 'risk_breakdown' in result.analysis_details:
                lines.append("  风险明细:")
                for k, v in result.analysis_details['risk_breakdown'].items():
                    lines.append(f"    {k}: {v}")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


def test_center_momentum_confidence():
    """测试中枢动量可信度计算器"""
    print("=" * 70)
    print("中枢动量可信度计算器 - 测试")
    print("=" * 70)
    print()
    
    # 模拟数据
    from trading_system.center import Center, CenterDetector
    from trading_system.segment import Segment
    
    # 创建测试线段 (上涨趋势，2 个中枢)
    segments = [
        Segment("up", 0, 10, 100.0, 108.0, 8.0, [], False, True),
        Segment("down", 10, 20, 108.0, 105.0, 3.0, [], False, True),
        Segment("up", 20, 30, 105.0, 106.0, 1.0, [], False, True),
        Segment("down", 30, 40, 106.0, 104.0, 2.0, [], False, True),
        Segment("up", 40, 50, 104.0, 112.0, 8.0, [], False, True),
        Segment("down", 50, 60, 112.0, 109.0, 3.0, [], False, True),
        Segment("up", 60, 70, 109.0, 110.0, 1.0, [], False, True),
        Segment("down", 70, 80, 110.0, 108.0, 2.0, [], False, True),
        Segment("up", 80, 90, 108.0, 118.0, 10.0, [], False, True),
    ]
    
    # 创建测试中枢
    center1 = Center(
        start_idx=1, end_idx=3,
        high=106.0, low=104.0,
        segments=segments[1:4],
        level="test", confirmed=True
    )
    
    center2 = Center(
        start_idx=5, end_idx=7,
        high=110.0, low=108.0,
        segments=segments[5:8],
        level="test", confirmed=True
    )
    
    centers = [center1, center2]
    price = 115.0
    
    # 运行测试
    calculator = CenterMomentumConfidenceCalculator()
    result = calculator.calculate(
        symbol="TEST",
        level="1d",
        price=price,
        centers=centers,
        segments=segments,
        level_name="1d"
    )
    
    # 输出报告
    report = calculator.format_report(result)
    print(report)
    print()
    
    # 测试应用到置信度
    base_confidence = 0.60
    adjusted = calculator.apply_to_confidence(base_confidence, result)
    
    print(f"【置信度调整测试】")
    print(f"  原始置信度：{base_confidence*100:.0f}%")
    print(f"  中枢动量调整：{result.total_bonus*100:+.1f}%")
    print(f"  调整后置信度：{adjusted*100:.0f}%")
    print(f"  背驰风险：{'⚠️ 是' if result.divergence_risk else '✅ 否'}")
    print()
    
    # 验证结果
    print("【测试验证】")
    print(f"  ✅ 中枢数量：{result.center_count} (期望：2)")
    print(f"  ✅ 中枢位置：{result.center_position.value} (期望：AFTER_SECOND)")
    print(f"  ✅ 总调整：{result.total_bonus*100:+.1f}% (期望：+10-20%)")
    print(f"  ✅ 调整后置信度：{adjusted*100:.0f}% (期望：70-80%)")
    print(f"  ✅ 背驰风险：{'否' if not result.divergence_risk else '是'} (期望：否)")
    print()
    
    return result


if __name__ == "__main__":
    test_center_momentum_confidence()
