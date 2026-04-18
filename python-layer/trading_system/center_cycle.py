"""
中枢周期模块 - Center Cycle
缠论 v7.0 核心模块

功能:
1. 根据趋势段确定中枢周期
2. 识别趋势阶段 (诞生期/成长期/成熟期/衰退期)
3. 计算周期长度和中枢数量
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from .trend_segment import TrendSegment


@dataclass
class CenterCycle:
    """中枢周期数据结构"""
    trend_segment: TrendSegment  # 所属趋势段
    start_date: datetime  # 周期起点
    end_date: datetime  # 周期终点
    duration: timedelta  # 周期长度
    center_count: int  # 中枢数量
    stage: str  # 趋势阶段
    
    # 阶段特征
    stage_description: str = ""
    divergence_risk: str = "低"  # 背驰风险等级
    recommended_action: str = "观望"  # 建议操作
    
    def __post_init__(self):
        """初始化后处理"""
        self._update_stage_info()
    
    def _update_stage_info(self):
        """更新阶段信息"""
        stage_info = {
            '形成期': {
                'desc': '趋势初步形成，第一个中枢正在形成中',
                'risk': '低',
                'action': '观望，等待中枢形成'
            },
            '诞生期': {
                'desc': '趋势诞生，第一个中枢形成',
                'risk': '低',
                'action': '轻仓试单 (10-20%)'
            },
            '成长期': {
                'desc': '趋势成长，第二个中枢形成，趋势确认',
                'risk': '低',
                'action': '积极建仓 (30-50%)'
            },
            '成熟期': {
                'desc': '趋势成熟，第三个中枢形成，背驰风险高',
                'risk': '高',
                'action': '减仓观望 (20-30%)'
            },
            '衰退期': {
                'desc': '趋势衰退，第四个中枢后，背驰风险递减',
                'risk': '中',
                'action': '清仓等待 (0-10%)'
            }
        }
        
        info = stage_info.get(self.stage, stage_info['形成期'])
        self.stage_description = info['desc']
        self.divergence_risk = info['risk']
        self.recommended_action = info['action']


class CenterCycleAnalyzer:
    """
    中枢周期分析器
    
    核心逻辑:
    1. 根据趋势段内的中枢数量确定周期阶段
    2. 计算周期长度
    3. 评估背驰风险
    """
    
    def __init__(self):
        """初始化分析器"""
        # 周期阶段阈值 (可配置)
        self.STAGE_THRESHOLDS = {
            '形成期': 0,
            '诞生期': 1,
            '成长期': 2,
            '成熟期': 3,
            '衰退期': 4,
        }
    
    def analyze(self, trend_segment: TrendSegment) -> CenterCycle:
        """
        分析中枢周期
        
        Args:
            trend_segment: 趋势段
        
        Returns:
            CenterCycle: 中枢周期
        """
        # 计算周期长度
        duration = trend_segment.end_date - trend_segment.start_date if trend_segment.start_date and trend_segment.end_date else None
        
        # 确定周期阶段
        stage = self._determine_stage(trend_segment.center_count)
        
        return CenterCycle(
            trend_segment=trend_segment,
            start_date=trend_segment.start_date,
            end_date=trend_segment.end_date,
            duration=duration,
            center_count=trend_segment.center_count,
            stage=stage
        )
    
    def _determine_stage(self, center_count: int) -> str:
        """
        根据中枢数量确定周期阶段
        
        Args:
            center_count: 中枢数量
        
        Returns:
            阶段名称
        """
        if center_count == 0:
            return '形成期'
        elif center_count == 1:
            return '诞生期'
        elif center_count == 2:
            return '成长期'
        elif center_count == 3:
            return '成熟期'
        else:
            return '衰退期'
    
    def evaluate_divergence_risk(self, cycle: CenterCycle) -> Dict:
        """
        评估背驰风险
        
        Args:
            cycle: 中枢周期
        
        Returns:
            背驰风险评估结果
        """
        stage = cycle.stage
        center_count = cycle.center_count
        
        if stage == '成熟期':
            # 第 3 中枢，背驰高发区
            risk_level = '高'
            adjustment = -0.25
            description = '第三中枢后，背驰风险最高'
        elif stage == '衰退期':
            # 第 4+ 中枢，风险递减
            risk_factor = 1.0 / (center_count - 2)
            risk_level = '中' if risk_factor > 0.5 else '低'
            adjustment = -0.25 * risk_factor
            description = f'第{center_count}中枢后，背驰风险递减 (因子：{risk_factor:.2f})'
        else:
            # 形成期/诞生期/成长期，风险低
            risk_level = '低'
            adjustment = 0.0
            description = f'第{center_count}中枢，趋势{stage}'
        
        return {
            'risk_level': risk_level,
            'adjustment': adjustment,
            'risk_factor': 1.0 / (center_count - 2) if stage == '衰退期' else None,
            'description': description,
        }


def determine_center_cycle(trend_segment: TrendSegment) -> CenterCycle:
    """便捷函数：确定中枢周期"""
    analyzer = CenterCycleAnalyzer()
    return analyzer.analyze(trend_segment)


def evaluate_cycle_divergence_risk(cycle: CenterCycle) -> Dict:
    """便捷函数：评估周期背驰风险"""
    analyzer = CenterCycleAnalyzer()
    return analyzer.evaluate_divergence_risk(cycle)


# 测试函数
def test_center_cycle_analyzer():
    """测试中枢周期分析"""
    print("=" * 70)
    print("中枢周期分析器 - 测试")
    print("=" * 70)
    print()
    
    from datetime import datetime
    
    # 创建测试趋势段
    test_segments = [
        TrendSegment(
            index=1,
            trend='up',
            segments=[],
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 15),
            start_price=100.0,
            end_price=120.0,
            center_count=0,
            stage='形成期'
        ),
        TrendSegment(
            index=2,
            trend='up',
            segments=[],
            start_date=datetime(2025, 1, 16),
            end_date=datetime(2025, 2, 15),
            start_price=120.0,
            end_price=140.0,
            center_count=1,
            stage='诞生期'
        ),
        TrendSegment(
            index=3,
            trend='up',
            segments=[],
            start_date=datetime(2025, 2, 16),
            end_date=datetime(2025, 3, 15),
            start_price=140.0,
            end_price=160.0,
            center_count=2,
            stage='成长期'
        ),
        TrendSegment(
            index=4,
            trend='up',
            segments=[],
            start_date=datetime(2025, 3, 16),
            end_date=datetime(2025, 4, 15),
            start_price=160.0,
            end_price=180.0,
            center_count=3,
            stage='成熟期'
        ),
        TrendSegment(
            index=5,
            trend='down',
            segments=[],
            start_date=datetime(2025, 4, 16),
            end_date=datetime(2025, 6, 15),
            start_price=180.0,
            end_price=150.0,
            center_count=5,
            stage='衰退期'
        ),
    ]
    
    # 分析每个趋势段
    analyzer = CenterCycleAnalyzer()
    
    for ts in test_segments:
        cycle = analyzer.analyze(ts)
        risk = analyzer.evaluate_divergence_risk(cycle)
        
        print(f"趋势段 {ts.index} ({ts.trend}):")
        print(f"  中枢数：{ts.center_count}")
        print(f"  周期阶段：{cycle.stage}")
        print(f"  阶段描述：{cycle.stage_description}")
        print(f"  背驰风险：{risk['risk_level']} ({risk['description']})")
        print(f"  v7.0 调整：{risk['adjustment']*100:+.1f}%")
        print(f"  建议操作：{cycle.recommended_action}")
        print()
    
    return test_segments


if __name__ == "__main__":
    test_center_cycle_analyzer()
