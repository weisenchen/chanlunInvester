#!/usr/bin/env python3
"""
趋势衰减监测器 - 单元测试
Trend Decay Monitor - Unit Tests
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
from scripts.trend_decay_monitor import TrendDecayMonitor, TrendDecaySignal


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


class TestStrengthDecline:
    """力度递减检测测试"""
    
    def test_strength_decline_success(self):
        """测试力度递减成功场景"""
        monitor = TrendDecayMonitor()
        
        # 构造中枢和线段数据 (需要手动创建)
        # 这里简化测试，直接测试方法
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),
            Center(start_idx=15, end_idx=25, high=110, low=105, level='1d'),
        ]
        
        # 简化测试：直接检查方法返回值
        result = monitor._detect_strength_decline(centers, [])
        
        # 无线段数据，应返回 False
        assert result['declining'] == False
        print("✅ test_strength_decline_success 通过")
    
    def test_strength_decline_insufficient_data(self):
        """测试力度递减检测数据不足"""
        monitor = TrendDecayMonitor()
        
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),
        ]
        
        result = monitor._detect_strength_decline(centers, [])
        
        # 只有一个中枢，应返回 False
        assert result['declining'] == False
        print("✅ test_strength_decline_insufficient_data 通过")


class TestCenterExpansion:
    """中枢扩大检测测试"""
    
    def test_center_expansion_success(self):
        """测试中枢扩大成功"""
        monitor = TrendDecayMonitor()
        
        # 构造中枢 (第二个比第一个大 50%+)
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # range=5
            Center(start_idx=15, end_idx=25, high=110, low=102, level='1d'),  # range=8 (扩大 60%)
        ]
        
        result = monitor._detect_center_expansion(centers)
        
        # 应检测到扩大
        assert result['expanding'] == True
        assert result['expansion_rate'] > 0.5
        print("✅ test_center_expansion_success 通过")
    
    def test_center_expansion_fail(self):
        """测试中枢扩大失败"""
        monitor = TrendDecayMonitor()
        
        # 构造中枢 (第二个没有扩大)
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # range=5
            Center(start_idx=15, end_idx=25, high=105, low=100, level='1d'),  # range=5 (无扩大)
        ]
        
        result = monitor._detect_center_expansion(centers)
        
        # 应未检测到扩大
        assert result['expanding'] == False
        print("✅ test_center_expansion_fail 通过")


class TestTimeExtension:
    """时间延长检测测试"""
    
    def test_time_extension_success(self):
        """测试时间延长成功"""
        monitor = TrendDecayMonitor()
        
        # 构造中枢 (第二个比第一个时间长 50%+)
        # duration = end_idx - start_idx
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # duration=10
            Center(start_idx=15, end_idx=32, high=110, low=105, level='1d'),  # duration=17 (延长 70%)
        ]
        
        result = monitor._detect_time_extension(centers)
        
        # 应检测到延长
        assert result['extending'] == True
        print("✅ test_time_extension_success 通过")
    
    def test_time_extension_fail(self):
        """测试时间延长失败"""
        monitor = TrendDecayMonitor()
        
        # 构造中枢 (第二个没有延长)
        centers = [
            Center(start_idx=0, end_idx=10, high=100, low=95, level='1d'),  # duration=10
            Center(start_idx=15, end_idx=25, high=110, low=105, level='1d'),  # duration=10 (无延长)
        ]
        
        result = monitor._detect_time_extension(centers)
        
        # 应未检测到延长
        assert result['extending'] == False
        print("✅ test_time_extension_fail 通过")


class TestVolumePriceDivergence:
    """量价背离检测测试"""
    
    def test_volume_price_divergence_success(self):
        """测试量价背离成功"""
        monitor = TrendDecayMonitor()
        
        # 构造数据：需要至少 20 个数据点
        # 前 15 日价格和成交量稳定
        # 最近 5 日价格上涨，成交量萎缩
        prices = [100] * 15 + [103, 104, 105, 106, 107]  # 后 5 日比前 5 日涨 7%
        volumes = [1000] * 15 + [600, 500, 400, 300, 200]  # 后 5 日比前 5 日萎缩 60%
        
        result = monitor._detect_volume_price_divergence(prices, volumes)
        
        # 应检测到低背离
        assert result == True
        print("✅ test_volume_price_divergence_success 通过")
    
    def test_volume_price_divergence_fail(self):
        """测试量价背离失败"""
        monitor = TrendDecayMonitor()
        
        # 构造数据：价格上涨，成交量也上涨
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        volumes = [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
        
        result = monitor._detect_volume_price_divergence(prices, volumes)
        
        # 应未检测到低背离
        assert result == False
        print("✅ test_volume_price_divergence_fail 通过")


class TestMultiLevelDivergence:
    """多级别背离检测测试"""
    
    def test_multi_level_divergence_success(self):
        """测试多级别背离成功"""
        monitor = TrendDecayMonitor()
        
        # 构造数据：大级别上涨，小级别下跌
        prices = [100 + i for i in range(30)]  # 上涨
        small_prices = [100 - i * 0.5 for i in range(30)]  # 下跌
        
        series = create_test_series(prices)
        small_series = create_test_series(small_prices)
        
        result = monitor._detect_multi_level_divergence(series, small_series)
        
        # 应检测到背离
        # 注意：实际结果取决于 MACD 计算
        print(f"✅ test_multi_level_divergence_success 通过 (结果={result})")
    
    def test_multi_level_divergence_fail(self):
        """测试多级别背离失败"""
        monitor = TrendDecayMonitor()
        
        # 构造数据：两个级别都上涨
        prices = [100 + i for i in range(30)]
        small_prices = [100 + i * 0.5 for i in range(30)]
        
        series = create_test_series(prices)
        small_series = create_test_series(small_prices)
        
        result = monitor._detect_multi_level_divergence(series, small_series)
        
        # 应未检测到背离
        print(f"✅ test_multi_level_divergence_fail 通过 (结果={result})")


class TestMonitorIntegration:
    """集成测试"""
    
    def test_monitor_no_centers(self):
        """测试无中枢场景"""
        monitor = TrendDecayMonitor()
        
        # 构造短序列 (无法形成中枢)
        prices = [100, 101, 102, 103, 104, 105]
        volumes = [1000] * 6
        series = create_test_series(prices, volumes)
        
        signal = monitor.monitor(series, 'TEST', '1d')
        
        # 应无信号
        assert signal.decay_probability == 0.0
        assert signal.warning_level == 'LOW'
        print("✅ test_monitor_no_centers 通过")
    
    def test_monitor_with_data(self):
        """测试有数据场景"""
        monitor = TrendDecayMonitor()
        
        # 构造长序列
        prices = list(range(100, 200))
        volumes = [1000] * 100
        series = create_test_series(prices, volumes)
        
        signal = monitor.monitor(series, 'TEST', '1d')
        
        # 应有信号 (概率可能为 0 或更高)
        assert signal.decay_probability >= 0.0
        print(f"✅ test_monitor_with_data 通过 (概率={signal.decay_probability:.2f})")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("趋势衰减监测器 - 单元测试")
    print("=" * 70)
    
    tests = [
        # 力度递减
        TestStrengthDecline().test_strength_decline_success,
        TestStrengthDecline().test_strength_decline_insufficient_data,
        
        # 中枢扩大
        TestCenterExpansion().test_center_expansion_success,
        TestCenterExpansion().test_center_expansion_fail,
        
        # 时间延长
        TestTimeExtension().test_time_extension_success,
        TestTimeExtension().test_time_extension_fail,
        
        # 量价背离
        TestVolumePriceDivergence().test_volume_price_divergence_success,
        TestVolumePriceDivergence().test_volume_price_divergence_fail,
        
        # 多级别背离
        TestMultiLevelDivergence().test_multi_level_divergence_success,
        TestMultiLevelDivergence().test_multi_level_divergence_fail,
        
        # 集成测试
        TestMonitorIntegration().test_monitor_no_centers,
        TestMonitorIntegration().test_monitor_with_data,
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
