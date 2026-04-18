"""
中枢动量分析模块 - Center Momentum Analysis
缠论 v6.0 核心模块

功能:
1. 判断当前级别趋势 (上涨/下降/震荡)
2. 识别当前处于第几中枢
3. 分析中枢间动量变化 (增强/衰减)
4. 评估趋势延续性

基于缠论第 18, 20, 63, 67 课
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum
import numpy as np


class TrendDirection(Enum):
    """趋势方向"""
    UP = "上涨"
    DOWN = "下跌"
    SIDEWAYS = "震荡"
    UNKNOWN = "未知"


class MomentumStatus(Enum):
    """动量状态"""
    INCREASING = "增强"      # 动量增加
    DECREASING = "衰减"      # 动量衰减
    STABLE = "稳定"
    UNKNOWN = "未知"


class CenterPosition(Enum):
    """中枢位置"""
    BEFORE_FIRST = "第一个中枢前"
    IN_FIRST = "第一个中枢"
    AFTER_FIRST = "第一个中枢后"
    IN_SECOND = "第二个中枢"
    AFTER_SECOND = "第二个中枢后"
    IN_THIRD = "第三个中枢"
    AFTER_THIRD = "第三个中枢后 (趋势背驰风险区)"
    EXTENSION = "中枢延伸"


@dataclass
class CenterMomentum:
    """中枢动量数据结构"""
    index: int  # 中枢序号 (第几个中枢)
    zg: float   # 中枢上沿
    zd: float   # 中枢下沿
    gg: float   # 中枢最高点
    dd: float   # 中枢最低点
    range_size: float  # 中枢区间大小
    segments_count: int  # 包含线段数
    
    # 动量指标
    entry_momentum: float = 0.0  # 进入段动量
    exit_momentum: float = 0.0   # 离开段动量
    momentum_change: float = 0.0 # 动量变化率
    
    # 与前一中枢比较
    range_change: float = 0.0    # 区间大小变化
    position_shift: float = 0.0  # 位置偏移
    
    # 趋势判断
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    momentum_status: MomentumStatus = MomentumStatus.UNKNOWN


@dataclass
class CenterAnalysisResult:
    """中枢分析结果"""
    # 基本信息
    level: str  # 级别 (1w/1d/30m 等)
    current_price: float
    
    # 中枢列表
    centers: List[CenterMomentum] = field(default_factory=list)
    
    # 当前位置
    current_center_index: int = -1  # -1 表示在中枢外
    center_position: CenterPosition = CenterPosition.BEFORE_FIRST
    
    # 趋势判断
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    trend_stage: str = "未知"  # 趋势阶段描述
    
    # 动量分析
    momentum_status: MomentumStatus = MomentumStatus.UNKNOWN
    momentum_score: float = 0.0  # -100 到 100
    
    # 趋势延续性
    continuation_probability: float = 0.0  # 0-100%
    reversal_risk: float = 0.0  # 0-100%
    
    # 操作建议
    suggestion: str = "观望"
    confidence: float = 0.0  # 0-100%
    
    # 详细分析
    analysis_details: Dict = field(default_factory=dict)


class CenterMomentumAnalyzer:
    """
    中枢动量分析器
    
    核心逻辑:
    1. 中枢区间变化 → 判断趋势强弱
    2. 中枢位置移动 → 判断趋势方向
    3. 进入/离开段动量 → 判断动量衰减/增强
    4. 中枢数量 → 判断趋势阶段 (第几中枢)
    """
    
    def __init__(self, level: str = "unknown"):
        """
        初始化分析器
        
        Args:
            level: 分析级别 (1w/1d/30m/5m 等)
        """
        self.level = level
        self.min_segments_for_center = 3
    
    def analyze(self, centers: List, segments: List, 
                current_price: float) -> CenterAnalysisResult:
        """
        执行中枢动量分析
        
        Args:
            centers: 中枢列表 (Center 对象)
            segments: 线段列表 (Segment 对象)
            current_price: 当前价格
        
        Returns:
            CenterAnalysisResult 分析结果
        """
        result = CenterAnalysisResult(
            level=self.level,
            current_price=current_price
        )
        
        if not centers:
            result.suggestion = "无中枢，趋势不明"
            result.confidence = 0.0
            return result
        
        # 1. 构建中枢动量数据
        result.centers = self._build_center_momentums(centers, segments)
        
        # 2. 确定当前位置
        result.current_center_index, result.center_position = \
            self._determine_current_position(centers, current_price)
        
        # 3. 判断趋势方向
        result.trend_direction = self._judge_trend_direction(centers)
        
        # 4. 分析动量变化
        result.momentum_status, result.momentum_score = \
            self._analyze_momentum_change(result.centers)
        
        # 5. 评估趋势延续性
        result.continuation_probability, result.reversal_risk = \
            self._evaluate_continuation(result)
        
        # 6. 生成操作建议
        result.suggestion, result.confidence = \
            self._generate_suggestion(result)
        
        # 7. 详细分析
        result.analysis_details = self._generate_details(result)
        
        # 8. 趋势阶段描述
        result.trend_stage = self._describe_trend_stage(result)
        
        return result
    
    def _build_center_momentums(self, centers: List, 
                                 segments: List) -> List[CenterMomentum]:
        """构建中枢动量数据列表"""
        momentums = []
        
        for i, center in enumerate(centers):
            # 计算中枢区间
            range_size = center.zg - center.zd
            
            # 计算进入段和离开段动量
            entry_momentum = 0.0
            exit_momentum = 0.0
            
            if center.start_idx > 0 and center.start_idx <= len(segments):
                entry_seg = segments[center.start_idx - 1]
                entry_momentum = abs(entry_seg.end_price - entry_seg.start_price)
            
            if center.end_idx < len(segments):
                exit_seg = segments[center.end_idx]
                exit_momentum = abs(exit_seg.end_price - exit_seg.start_price)
            
            # 动量变化率
            momentum_change = 0.0
            if entry_momentum > 0:
                momentum_change = (exit_momentum - entry_momentum) / entry_momentum
            
            # 与前一中枢比较
            range_change = 0.0
            position_shift = 0.0
            
            if i > 0 and momentums:
                prev = momentums[-1]
                range_change = (range_size - prev.range_size) / prev.range_size if prev.range_size > 0 else 0
                position_shift = (center.zd - prev.zd) / prev.zd if prev.zd > 0 else 0
            
            momentum = CenterMomentum(
                index=i + 1,  # 第几个中枢 (从 1 开始)
                zg=center.zg,
                zd=center.zd,
                gg=center.gg,
                dd=center.dd,
                range_size=range_size,
                segments_count=len(center.segments),
                entry_momentum=entry_momentum,
                exit_momentum=exit_momentum,
                momentum_change=momentum_change,
                range_change=range_change,
                position_shift=position_shift
            )
            
            momentums.append(momentum)
        
        return momentums
    
    def _determine_current_position(self, centers: List, 
                                     current_price: float) -> Tuple[int, CenterPosition]:
        """
        确定当前价格相对于中枢的位置
        
        Returns:
            (中枢索引，位置枚举)
        """
        if not centers:
            return -1, CenterPosition.BEFORE_FIRST
        
        # 检查是否在某个中枢内
        for i, center in enumerate(centers):
            if center.contains(current_price):
                # 在中枢内
                if i == 0:
                    return i, CenterPosition.IN_FIRST
                elif i == 1:
                    return i, CenterPosition.IN_SECOND
                elif i == 2:
                    return i, CenterPosition.IN_THIRD
                else:
                    return i, CenterPosition.EXTENSION
        
        # 在中枢外，判断在哪个中枢之后
        last_center = centers[-1]
        if current_price > last_center.zg:
            # 在中枢上方
            if len(centers) == 1:
                return -1, CenterPosition.AFTER_FIRST
            elif len(centers) == 2:
                return -1, CenterPosition.AFTER_SECOND
            else:
                return -1, CenterPosition.AFTER_THIRD
        else:
            # 在中枢下方
            return -1, CenterPosition.BEFORE_FIRST
    
    def _judge_trend_direction(self, centers: List) -> TrendDirection:
        """
        判断趋势方向
        
        基于中枢位置移动:
        - 中枢依次上移 → 上涨趋势
        - 中枢依次下移 → 下跌趋势
        - 中枢重叠或无明显方向 → 震荡
        """
        if len(centers) < 2:
            return TrendDirection.UNKNOWN
        
        up_count = 0
        down_count = 0
        
        for i in range(1, len(centers)):
            prev_zd = centers[i-1].zd
            curr_zd = centers[i].zd
            prev_zg = centers[i-1].zg
            curr_zg = centers[i].zg
            
            # 中枢上移
            if curr_zd > prev_zg:
                up_count += 1
            # 中枢下移
            elif curr_zg < prev_zd:
                down_count += 1
        
        total = up_count + down_count
        if total == 0:
            return TrendDirection.SIDEWAYS
        
        up_ratio = up_count / total
        
        if up_ratio > 0.6:
            return TrendDirection.UP
        elif up_ratio < 0.4:
            return TrendDirection.DOWN
        else:
            return TrendDirection.SIDEWAYS
    
    def _analyze_momentum_change(self, momentums: List[CenterMomentum]) -> Tuple[MomentumStatus, float]:
        """
        分析动量变化
        
        基于:
        1. 中枢区间变化
        2. 离开段 vs 进入段动量
        3. 中枢位置移动速度
        
        Returns:
            (动量状态，动量分数 -100 到 100)
        """
        if len(momentums) < 2:
            return MomentumStatus.UNKNOWN, 0.0
        
        scores = []
        
        for i in range(1, len(momentums)):
            prev = momentums[i-1]
            curr = momentums[i]
            
            # 1. 区间大小变化 (缩小=动量增强，扩大=动量减弱)
            range_score = 0
            if curr.range_size < prev.range_size * 0.8:
                range_score = 20  # 区间明显缩小，动量增强
            elif curr.range_size > prev.range_size * 1.2:
                range_score = -20  # 区间明显扩大，动量减弱
            
            # 2. 离开段动量变化
            momentum_score = 0
            if curr.momentum_change > 0.2:
                momentum_score = 20  # 离开段动量增强
            elif curr.momentum_change < -0.2:
                momentum_score = -20  # 离开段动量减弱
            
            # 3. 位置移动速度
            shift_score = 0
            if abs(curr.position_shift) > 0.1:
                shift_score = 10 if curr.position_shift > 0 else -10
            
            scores.append(range_score + momentum_score + shift_score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 转换为动量状态
        if avg_score > 15:
            return MomentumStatus.INCREASING, min(avg_score, 100)
        elif avg_score < -15:
            return MomentumStatus.DECREASING, max(avg_score, -100)
        else:
            return MomentumStatus.STABLE, avg_score
    
    def _evaluate_continuation(self, result: CenterAnalysisResult) -> Tuple[float, float]:
        """
        评估趋势延续性和反转风险
        
        Returns:
            (延续概率%，反转风险%)
        """
        continuation = 50.0  # 基准
        reversal = 50.0
        
        # 1. 中枢数量影响
        if result.center_position == CenterPosition.AFTER_THIRD:
            # 第三个中枢后，背驰风险高
            continuation -= 30
            reversal += 30
        elif result.center_position in [CenterPosition.AFTER_FIRST, CenterPosition.AFTER_SECOND]:
            # 第一、二个中枢后，趋势可能延续
            continuation += 15
            reversal -= 15
        
        # 2. 动量状态影响
        if result.momentum_status == MomentumStatus.INCREASING:
            continuation += 20
            reversal -= 20
        elif result.momentum_status == MomentumStatus.DECREASING:
            continuation -= 20
            reversal += 20
        
        # 3. 趋势方向影响
        if result.trend_direction == TrendDirection.UP:
            # 上涨趋势中，延续概率略高
            continuation += 10
            reversal -= 10
        elif result.trend_direction == TrendDirection.DOWN:
            continuation -= 10
            reversal += 10
        
        # 4. 中枢延伸
        if result.center_position == CenterPosition.EXTENSION:
            # 中枢延伸，级别扩张，趋势可能转变
            continuation -= 15
            reversal += 15
        
        # 限制范围
        continuation = max(0, min(100, continuation))
        reversal = max(0, min(100, reversal))
        
        return continuation, reversal
    
    def _generate_suggestion(self, result: CenterAnalysisResult) -> Tuple[str, float]:
        """生成操作建议"""
        suggestion = "观望"
        confidence = 50.0
        
        # 基于趋势方向和动量状态
        if result.trend_direction == TrendDirection.UP:
            if result.momentum_status == MomentumStatus.INCREASING:
                if result.continuation_probability > 70:
                    suggestion = "持有/做多"
                    confidence = 75.0
                else:
                    suggestion = "谨慎做多"
                    confidence = 60.0
            elif result.momentum_status == MomentumStatus.DECREASING:
                if result.reversal_risk > 60:
                    suggestion = "减仓/止盈"
                    confidence = 70.0
                else:
                    suggestion = "持有观望"
                    confidence = 55.0
        
        elif result.trend_direction == TrendDirection.DOWN:
            if result.momentum_status == MomentumStatus.INCREASING:
                if result.continuation_probability > 70:
                    suggestion = "持有空单/观望"
                    confidence = 75.0
                else:
                    suggestion = "谨慎看空"
                    confidence = 60.0
            elif result.momentum_status == MomentumStatus.DECREASING:
                if result.reversal_risk > 60:
                    suggestion = "减仓/关注反转"
                    confidence = 70.0
                else:
                    suggestion = "持有观望"
                    confidence = 55.0
        
        elif result.trend_direction == TrendDirection.SIDEWAYS:
            suggestion = "区间操作/观望"
            confidence = 50.0
        
        # 第三个中枢后特别提示
        if result.center_position == CenterPosition.AFTER_THIRD:
            suggestion = "警惕背驰/准备离场"
            confidence = max(confidence, 65.0)
        
        return suggestion, confidence
    
    def _generate_details(self, result: CenterAnalysisResult) -> Dict:
        """生成详细分析数据"""
        details = {
            'center_count': len(result.centers),
            'trend': result.trend_direction.value,
            'momentum': result.momentum_status.value,
            'position': result.center_position.value,
            'continuation': f"{result.continuation_probability:.1f}%",
            'reversal_risk': f"{result.reversal_risk:.1f}%",
        }
        
        if result.centers:
            last = result.centers[-1]
            details['last_center'] = {
                'index': last.index,
                'zg': f"{last.zg:.2f}",
                'zd': f"{last.zd:.2f}",
                'range': f"{last.range_size:.2f}",
                'range_change': f"{last.range_change*100:.1f}%",
                'momentum_change': f"{last.momentum_change*100:.1f}%",
            }
        
        return details
    
    def _describe_trend_stage(self, result: CenterAnalysisResult) -> str:
        """描述趋势阶段"""
        if not result.centers:
            return "无中枢，趋势未明"
        
        stage = ""
        
        # 中枢数量阶段
        if len(result.centers) == 1:
            stage = "第一中枢阶段 - 趋势初现"
        elif len(result.centers) == 2:
            stage = "第二中枢阶段 - 趋势确认"
        elif len(result.centers) >= 3:
            stage = "第三中枢阶段 - 警惕背驰"
        
        # 动量状态
        if result.momentum_status == MomentumStatus.INCREASING:
            stage += "，动量增强"
        elif result.momentum_status == MomentumStatus.DECREASING:
            stage += "，动量衰减"
        
        # 趋势方向
        if result.trend_direction == TrendDirection.UP:
            stage += "，上涨趋势"
        elif result.trend_direction == TrendDirection.DOWN:
            stage += "，下跌趋势"
        else:
            stage += "，震荡整理"
        
        return stage


def format_center_analysis_report(result: CenterAnalysisResult) -> str:
    """格式化中枢分析报告"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"📊 中枢动量分析报告 - {result.level}")
    lines.append("=" * 70)
    lines.append(f"当前价格：${result.current_price:.2f}")
    lines.append("")
    
    # 趋势判断
    lines.append("【趋势判断】")
    lines.append(f"  方向：{result.trend_direction.value}")
    lines.append(f"  阶段：{result.trend_stage}")
    lines.append(f"  位置：{result.center_position.value}")
    lines.append("")
    
    # 动量分析
    lines.append("【动量分析】")
    lines.append(f"  状态：{result.momentum_status.value}")
    lines.append(f"  分数：{result.momentum_score:.1f}")
    lines.append("")
    
    # 中枢列表
    if result.centers:
        lines.append("【中枢序列】")
        for c in result.centers:
            lines.append(f"  第{c.index}中枢: ZG={c.zg:.2f}, ZD={c.zd:.2f}, "
                        f"区间={c.range_size:.2f}, "
                        f"区间变化={c.range_change*100:+.1f}%, "
                        f"动量变化={c.momentum_change*100:+.1f}%")
        lines.append("")
    
    # 延续性评估
    lines.append("【趋势评估】")
    lines.append(f"  延续概率：{result.continuation_probability:.1f}%")
    lines.append(f"  反转风险：{result.reversal_risk:.1f}%")
    lines.append("")
    
    # 操作建议
    lines.append("【操作建议】")
    lines.append(f"  建议：{result.suggestion}")
    lines.append(f"  置信度：{result.confidence:.1f}%")
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


# 测试函数
def test_center_momentum_analyzer():
    """测试中枢动量分析器"""
    print("Testing Center Momentum Analyzer...")
    print()
    
    # 模拟中枢数据
    import sys
    sys.path.insert(0, '/home/wei/.openclaw/workspace/chanlunInvester/python-layer')
    from trading_system.center import Center
    from trading_system.segment import Segment
    
    # 创建测试线段
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
    
    # 运行分析
    analyzer = CenterMomentumAnalyzer(level="1d")
    result = analyzer.analyze(centers, segments, current_price=115.0)
    
    # 输出报告
    report = format_center_analysis_report(result)
    print(report)
    
    return result


if __name__ == "__main__":
    test_center_momentum_analyzer()
