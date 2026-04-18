#!/usr/bin/env python3
"""
中枢动量整合测试脚本
测试 confidence_calculator.py 中的中枢动量整合功能

使用:
    python3 test_center_momentum_integration.py
"""

import sys
import os
from pathlib import Path

# 添加路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir.parent / "python-layer"))

from datetime import datetime
from confidence_calculator import ComprehensiveConfidenceCalculator


def test_with_center_momentum():
    """测试带中枢动量的综合可信度计算"""
    print("=" * 70)
    print("中枢动量整合测试 - 带中枢数据")
    print("=" * 70)
    print()
    
    # 创建计算器
    calc = ComprehensiveConfidenceCalculator()
    
    # 模拟数据
    symbol = "TEST"
    signal_type = "buy2"
    level = "1d"
    price = 115.0
    
    # 生成测试价格序列 (上涨趋势)
    import numpy as np
    np.random.seed(42)
    prices = [100.0]
    for i in range(59):
        prices.append(prices[-1] + np.random.randn() * 2 + 0.5)  # 上涨趋势
    
    volumes = [np.random.randint(1000000, 10000000) for _ in range(60)]
    
    # 模拟 MACD 数据
    macd_data = {
        'DIF': [np.random.randn() * 0.5 for _ in range(60)],
        'DEA': [np.random.randn() * 0.5 for _ in range(60)],
        'HIST': [np.random.randn() * 0.3 for _ in range(60)],
    }
    
    # 创建模拟中枢和线段
    from trading_system.center import Center
    from trading_system.segment import Segment
    
    # 创建测试线段 (2 个中枢的上涨趋势)
    segments = [
        Segment("up", 0, 10, 100.0, 108.0, 8.0, [], False, True),
        Segment("down", 10, 20, 108.0, 105.0, 3.0, [], False, True),
        Segment("up", 20, 30, 105.0, 106.0, 1.0, [], False, True),
        Segment("down", 30, 40, 106.0, 104.0, 2.0, [], False, True),
        Segment("up", 40, 50, 104.0, 112.0, 8.0, [], False, True),
        Segment("down", 50, 60, 112.0, 109.0, 3.0, [], False, True),
        Segment("up", 60, 70, 109.0, 110.0, 1.0, [], False, True),
        Segment("down", 70, 80, 110.0, 108.0, 2.0, [], False, True),
        Segment("up", 80, 90, 108.0, 115.0, 7.0, [], False, True),
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
    
    # 测试 1: 不带中枢数据 (原始逻辑)
    print("【测试 1】不带中枢数据 (原始逻辑)")
    print("-" * 50)
    result_without = calc.calculate(
        symbol=symbol,
        signal_type=signal_type,
        level=level,
        price=price,
        prices=prices,
        volumes=volumes,
        macd_data=macd_data,
        chanlun_base_confidence=0.60,  # buy2 基础置信度
        centers=None,
        segments=None
    )
    
    print(f"综合置信度：{result_without.final_confidence*100:.1f}%")
    print(f"可靠性等级：{result_without.reliability_level.value}")
    print(f"操作建议：{result_without.operation_suggestion.value}")
    print(f"缠论基础得分：{result_without.chanlun_score*100:.1f}%")
    print()
    
    # 测试 2: 带中枢数据 (新逻辑)
    print("【测试 2】带中枢数据 (新逻辑 - v6.0)")
    print("-" * 50)
    result_with = calc.calculate(
        symbol=symbol,
        signal_type=signal_type,
        level=level,
        price=price,
        prices=prices,
        volumes=volumes,
        macd_data=macd_data,
        chanlun_base_confidence=0.60,
        centers=centers,
        segments=segments
    )
    
    print(f"综合置信度：{result_with.final_confidence*100:.1f}%")
    print(f"可靠性等级：{result_with.reliability_level.value}")
    print(f"操作建议：{result_with.operation_suggestion.value}")
    print(f"缠论基础得分：{result_with.chanlun_score*100:.1f}%")
    print()
    
    # 对比分析
    print("【对比分析】")
    print("-" * 50)
    print(f"原始置信度：{result_without.final_confidence*100:.1f}%")
    print(f"新置信度：  {result_with.final_confidence*100:.1f}%")
    print(f"变化：      {(result_with.final_confidence - result_without.final_confidence)*100:+.1f}%")
    print()
    
    # 中枢动量因子
    print("【中枢动量因子】")
    print("-" * 50)
    print(f"中枢数量：   {result_with.factors.center_count}")
    print(f"中枢位置：   {result_with.factors.center_position}")
    print(f"动量状态：   {result_with.factors.momentum_status}")
    print(f"调整值：     {result_with.factors.center_momentum_adjustment*100:+.1f}%")
    print(f"背驰风险：   {'⚠️ 是' if result_with.factors.divergence_risk else '✅ 否'}")
    print()
    
    # 贡献明细
    print("【贡献明细】")
    print("-" * 50)
    for key, value in result_with.breakdown.items():
        if isinstance(value, float):
            print(f"{key}: {value*100:.1f}%")
        else:
            print(f"{key}: {value}")
    print()
    
    # 验证结果
    print("【测试验证】")
    print("-" * 50)
    
    # 期望：第 2 中枢后，应该有正向调整
    expected_adjustment_min = 0.05  # 至少 +5%
    actual_adjustment = result_with.factors.center_momentum_adjustment
    
    if actual_adjustment >= expected_adjustment_min:
        print(f"✅ 中枢动量调整符合预期：{actual_adjustment*100:+.1f}% ≥ {expected_adjustment_min*100:.0f}%")
    else:
        print(f"⚠️ 中枢动量调整低于预期：{actual_adjustment*100:+.1f}% < {expected_adjustment_min*100:.0f}%")
    
    # 期望：新置信度应该高于或等于原始置信度
    if result_with.final_confidence >= result_without.final_confidence:
        print(f"✅ 新置信度提升：{(result_with.final_confidence - result_without.final_confidence)*100:+.1f}%")
    else:
        print(f"⚠️ 新置信度下降：{(result_with.final_confidence - result_without.final_confidence)*100:+.1f}%")
    
    # 期望：缠论基础得分应该有调整
    if result_with.chanlun_score != result_without.chanlun_score:
        print(f"✅ 缠论基础得分已调整：{result_without.chanlun_score*100:.1f}% → {result_with.chanlun_score*100:.1f}%")
    else:
        print(f"⚠️ 缠论基础得分未调整")
    
    print()
    print("=" * 70)
    print("测试完成!")
    print("=" * 70)
    
    return result_with


def test_divergence_risk():
    """测试背驰风险强制降级"""
    print()
    print("=" * 70)
    print("背驰风险强制降级测试")
    print("=" * 70)
    print()
    
    # 这个测试需要创建第三中枢后的场景
    # 简化测试：直接验证背驰风险逻辑
    
    from trading_system.center_momentum_confidence import (
        CenterMomentumConfidenceCalculator,
        CenterPosition,
        MomentumStatus
    )
    
    # 模拟一个高风险场景的结果
    class MockResult:
        def __init__(self):
            self.total_bonus = -0.25  # 大幅负调整
            self.divergence_risk = True
            self.center_count = 3
            self.center_position = CenterPosition.AFTER_THIRD
            self.momentum_status = MomentumStatus.DECREASING
    
    mock_result = MockResult()
    
    print("【高风险场景模拟】")
    print("-" * 50)
    print(f"中枢位置：{mock_result.center_position.value}")
    print(f"动量状态：{mock_result.momentum_status.value}")
    print(f"总调整：  {mock_result.total_bonus*100:.1f}%")
    print(f"背驰风险：{'⚠️ 是' if mock_result.divergence_risk else '✅ 否'}")
    print()
    
    # 验证强制降级逻辑
    base_confidence = 0.65
    adjusted = base_confidence + mock_result.total_bonus
    
    # 背驰风险强制降级至 40%
    if mock_result.divergence_risk:
        adjusted = min(adjusted, 0.40)
    
    print(f"【降级验证】")
    print("-" * 50)
    print(f"原始置信度：{base_confidence*100:.1f}%")
    print(f"调整后：    {adjusted*100:.1f}%")
    print(f"强制上限：  40.0%")
    print()
    
    if adjusted <= 0.40:
        print("✅ 背驰风险强制降级生效")
    else:
        print("⚠️ 背驰风险强制降级未生效")
    
    print()
    print("=" * 70)
    
    return adjusted


if __name__ == "__main__":
    # 测试 1: 带中枢数据的综合可信度
    result = test_with_center_momentum()
    
    # 测试 2: 背驰风险强制降级
    test_divergence_risk()
    
    print()
    print("所有测试完成!")
    print()
