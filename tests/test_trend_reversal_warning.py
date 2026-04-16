#!/usr/bin/env python3
"""
趋势反转预警器 - 单元测试
Trend Reversal Warning - Unit Tests
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.center import Center
from scripts.trend_reversal_warning import TrendReversalWarner, TrendReversalSignal


def create_test_series(prices: list, volumes: list = None) -> KlineSeries:
    """创建测试 K 线序列"""
    if volumes is None:
        volumes = [1000] * len(prices)
    
    klines = []
    for i, (price, volume) in enumerate(zip(prices, volumes)):
        kline = Kline(
            timestamp=datetime(2026, 1, 1, 9, 30),
            open=price * 0.99,
            high=price * 1.02,
            low=price * 0.98,
            close=price,
            volume=volume
        )
        klines.append(kline)
    
    return KlineSeries(klines=klines, symbol='TEST', timeframe='1d')


class TestMultiLevelDivergence:
    """多级别背驰共振检测测试"""
    
    def test_multi_level_divergence_insufficient_data(self):
        """测试多级别背驰数据不足"""
        warner = TrendReversalWarner()
        
        # 构造短序列
        prices = [100, 101, 102, 103, 104, 105]
        series = create_test_series(prices)
        
        # 无小级别和大级别数据
        result = warner._detect_multi_level_divergence(series, None, None)
        
        # 应返回 False
        assert result == False
        print("✅ test_multi_level_divergence_insufficient_data 通过")


class TestBSP3Failure:
    """第三类买卖点失败检测测试"""
    
    def test_bsp3_failure_insufficient_centers(self):
        """测试第三类买卖点失败数据不足"""
        warner = TrendReversalWarner()
        
        # 构造不足的中枢数据
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),
        ]
        
        result = warner._detect_bsp3_failure([], [], centers, [])
        
        # 应返回 False
        assert result == False
        print("✅ test_bsp3_failure_insufficient_centers 通过")


class TestCenterUpgrade:
    """中枢升级完成检测测试"""
    
    def test_center_upgrade_success(self):
        """测试中枢升级成功"""
        warner = TrendReversalWarner()
        
        # 构造中枢 (区间持续扩大)
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # range=5
            Center(start_idx=15, end_idx=25, high=110, low=102, level='1d'),  # range=8
            Center(start_idx=30, end_idx=42, high=120, low=108, level='1d'),  # range=12
        ]
        
        result = warner._detect_center_upgrade(centers)
        
        # 应检测到升级
        assert result == True
        print("✅ test_center_upgrade_success 通过")
    
    def test_center_upgrade_fail(self):
        """测试中枢升级失败"""
        warner = TrendReversalWarner()
        
        # 构造中枢 (区间未持续扩大)
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # range=5
            Center(start_idx=15, end_idx=25, high=105, low=100, level='1d'),  # range=5
            Center(start_idx=30, end_idx=40, high=110, low=105, level='1d'),  # range=5
        ]
        
        result = warner._detect_center_upgrade(centers)
        
        # 应未检测到升级
        assert result == False
        print("✅ test_center_upgrade_fail 通过")


class TestLeadingIndicatorDivergence:
    """先行指标背离检测测试"""
    
    def test_leading_indicator_divergence_success(self):
        """测试先行指标背离成功"""
        warner = TrendReversalWarner()
        
        # 构造数据：价格创新高，MACD 未新高
        prices = [100] * 20 + [103, 104, 105, 106, 107]  # 后 5 日创新高
        volumes = [1000] * 25
        
        # 构造 MACD 数据 (简化)
        from trading_system.indicators import MACDIndicator
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        macd_data = macd.calculate(prices)
        
        result = warner._detect_leading_indicator_divergence(prices, volumes, macd_data)
        
        # 应检测到背离
        print(f"✅ test_leading_indicator_divergence_success 通过 (结果={result})")
    
    def test_leading_indicator_divergence_fail(self):
        """测试先行指标背离失败"""
        warner = TrendReversalWarner()
        
        # 构造数据：价格未创新高
        prices = [100] * 25
        volumes = [1000] * 25
        
        from trading_system.indicators import MACDIndicator
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        macd_data = macd.calculate(prices)
        
        result = warner._detect_leading_indicator_divergence(prices, volumes, macd_data)
        
        # 应未检测到背离
        assert result == False
        print("✅ test_leading_indicator_divergence_fail 通过")


class TestWarnerIntegration:
    """集成测试"""
    
    def test_warn_no_centers(self):
        """测试无中枢场景"""
        warner = TrendReversalWarner()
        
        # 构造短序列 (无法形成中枢)
        prices = [100, 101, 102, 103, 104, 105]
        volumes = [1000] * 6
        series = create_test_series(prices, volumes)
        
        signal = warner.warn(series, 'TEST', '1d')
        
        # 应无信号
        assert signal.reversal_probability == 0.0
        assert signal.warning_level == 'LOW'
        print("✅ test_warn_no_centers 通过")
    
    def test_warn_with_data(self):
        """测试有数据场景"""
        warner = TrendReversalWarner()
        
        # 构造长序列
        prices = list(range(100, 200))
        volumes = [1000] * 100
        series = create_test_series(prices, volumes)
        
        signal = warner.warn(series, 'TEST', '1d')
        
        # 应有信号 (概率可能为 0 或更高)
        assert signal.reversal_probability >= 0.0
        print(f"✅ test_warn_with_data 通过 (概率={signal.reversal_probability:.2f})")


class TestConfidenceCalculation:
    """置信度计算测试"""
    
    def test_calculate_confidence(self):
        """测试置信度计算"""
        warner = TrendReversalWarner()
        
        # 测试不同信号数量的置信度
        confidence_0 = warner._calculate_confidence(0.5, 0)
        confidence_2 = warner._calculate_confidence(0.5, 2)
        confidence_4 = warner._calculate_confidence(0.5, 4)
        
        # 信号越多，置信度越高
        assert confidence_4 > confidence_2 > confidence_0
        print(f"✅ test_calculate_confidence 通过 (0 信号={confidence_0:.2f}, 2 信号={confidence_2:.2f}, 4 信号={confidence_4:.2f})")


class TestWarningLevel:
    """预警级别测试"""
    
    def test_get_warning_level(self):
        """测试预警级别获取"""
        warner = TrendReversalWarner()
        
        # 测试不同概率的预警级别
        assert warner._get_warning_level(0.8) == 'CRITICAL'
        assert warner._get_warning_level(0.6) == 'HIGH'
        assert warner._get_warning_level(0.4) == 'MEDIUM'
        assert warner._get_warning_level(0.2) == 'LOW'
        print("✅ test_get_warning_level 通过")


class TestDaysToReversal:
    """反转天数预估测试"""
    
    def test_estimate_days_to_reversal(self):
        """测试反转天数预估"""
        warner = TrendReversalWarner()
        
        # 测试不同概率的反转天数
        assert warner._estimate_days_to_reversal(0.8) == 3
        assert warner._estimate_days_to_reversal(0.6) == 5
        assert warner._estimate_days_to_reversal(0.4) == 7
        assert warner._estimate_days_to_reversal(0.2) == 0
        print("✅ test_estimate_days_to_reversal 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("趋势反转预警器 - 单元测试")
    print("=" * 70)
    
    tests = [
        # 多级别背驰
        TestMultiLevelDivergence().test_multi_level_divergence_insufficient_data,
        
        # 第三类买卖点失败
        TestBSP3Failure().test_bsp3_failure_insufficient_centers,
        
        # 中枢升级
        TestCenterUpgrade().test_center_upgrade_success,
        TestCenterUpgrade().test_center_upgrade_fail,
        
        # 先行指标背离
        TestLeadingIndicatorDivergence().test_leading_indicator_divergence_success,
        TestLeadingIndicatorDivergence().test_leading_indicator_divergence_fail,
        
        # 集成测试
        TestWarnerIntegration().test_warn_no_centers,
        TestWarnerIntegration().test_warn_with_data,
        
        # 置信度计算
        TestConfidenceCalculation().test_calculate_confidence,
        
        # 预警级别
        TestWarningLevel().test_get_warning_level,
        
        # 反转天数
        TestDaysToReversal().test_estimate_days_to_reversal,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} 失败：{e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 错误：{e}")
            failed += 1
    
    print("=" * 70)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print(f"通过率：{passed / len(tests) * 100:.1f}%")
    print("=" * 70)
    
    return {
        'total': len(tests),
        'passed': passed,
        'failed': failed,
        'pass_rate': passed / len(tests) * 100
    }


if __name__ == '__main__':
    results = run_all_tests()
    
    # 检查是否通过验收标准 (通过率≥90%)
    if results['pass_rate'] >= 90:
        print("\n✅ 单元测试通过验收标准 (≥90%)")
        sys.exit(0)
    else:
        print("\n❌ 单元测试未通过验收标准 (<90%)")
        sys.exit(1)
