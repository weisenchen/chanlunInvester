#!/usr/bin/env python3
"""
综合置信度引擎 - 单元测试
Comprehensive Confidence Engine - Unit Tests
"""

import sys
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from trading_system.kline import Kline, KlineSeries
from scripts.comprehensive_confidence_engine import ComprehensiveConfidenceEngine, ComprehensiveSignal


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


class TestComprehensiveConfidenceCalculation:
    """综合置信度计算测试"""
    
    def test_calculate_comprehensive_confidence(self):
        """测试综合置信度计算"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试不同置信度组合
        confidence = engine._calculate_comprehensive_confidence(0.8, 0.7, 0.6)
        
        # 简单平均：(0.8 + 0.7 + 0.6) / 3 = 0.7
        assert abs(confidence - 0.7) < 0.01
        print("✅ test_calculate_comprehensive_confidence 通过")
    
    def test_calculate_comprehensive_confidence_bounds(self):
        """测试综合置信度边界"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试边界值
        confidence_max = engine._calculate_comprehensive_confidence(1.0, 1.0, 1.0)
        confidence_min = engine._calculate_comprehensive_confidence(0.0, 0.0, 0.0)
        
        # 应限制在 0-1 范围
        assert confidence_max == 1.0
        assert confidence_min == 0.0
        print("✅ test_calculate_comprehensive_confidence_bounds 通过")


class TestRecommendation:
    """操作建议测试"""
    
    def test_get_recommendation(self):
        """测试操作建议获取"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试不同置信度的建议
        assert engine._get_recommendation(0.9) == 'STRONG_BUY'
        assert engine._get_recommendation(0.7) == 'BUY'
        assert engine._get_recommendation(0.5) == 'HOLD'
        assert engine._get_recommendation(0.3) == 'SELL'
        assert engine._get_recommendation(0.1) == 'STRONG_SELL'
        print("✅ test_get_recommendation 通过")


class TestPositionRatio:
    """仓位建议测试"""
    
    def test_get_position_ratio(self):
        """测试仓位建议获取"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试不同置信度的仓位
        assert engine._get_position_ratio(0.9) == 0.8
        assert engine._get_position_ratio(0.7) == 0.6
        assert engine._get_position_ratio(0.5) == 0.4
        assert engine._get_position_ratio(0.3) == 0.2
        assert engine._get_position_ratio(0.1) == 0.0
        print("✅ test_get_position_ratio 通过")


class TestRiskLevel:
    """风险等级测试"""
    
    def test_get_risk_level(self):
        """测试风险等级获取"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试不同置信度的风险等级
        assert engine._get_risk_level(0.8) == 'LOW'
        assert engine._get_risk_level(0.6) == 'MEDIUM'
        assert engine._get_risk_level(0.4) == 'HIGH'
        print("✅ test_get_risk_level 通过")


class TestConfidenceRange:
    """置信度区间测试"""
    
    def test_get_confidence_range(self):
        """测试置信度区间获取"""
        engine = ComprehensiveConfidenceEngine()
        
        # 测试不同置信度的区间
        assert engine._get_confidence_range(0.9) == 'VERY_HIGH'
        assert engine._get_confidence_range(0.7) == 'HIGH'
        assert engine._get_confidence_range(0.5) == 'MEDIUM'
        assert engine._get_confidence_range(0.3) == 'LOW'
        assert engine._get_confidence_range(0.1) == 'VERY_LOW'
        print("✅ test_get_confidence_range 通过")


class TestEngineIntegration:
    """集成测试"""
    
    def test_evaluate_short_series(self):
        """测试短序列评估"""
        engine = ComprehensiveConfidenceEngine()
        
        # 构造短序列 (无法形成中枢)
        prices = [100, 101, 102, 103, 104, 105]
        volumes = [1000] * 6
        series = create_test_series(prices, volumes)
        
        signal = engine.evaluate(series, 'TEST', '1d')
        
        # 应有综合信号 (即使无中枢)
        assert signal.comprehensive_confidence >= 0.0
        assert signal.recommendation in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        print(f"✅ test_evaluate_short_series 通过 (置信度={signal.comprehensive_confidence:.2f})")
    
    def test_evaluate_long_series(self):
        """测试长序列评估"""
        engine = ComprehensiveConfidenceEngine()
        
        # 构造长序列
        prices = list(range(100, 200))
        volumes = [1000] * 100
        series = create_test_series(prices, volumes)
        
        signal = engine.evaluate(series, 'TEST', '1d')
        
        # 应有综合信号
        assert signal.comprehensive_confidence >= 0.0
        assert signal.recommendation in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        print(f"✅ test_evaluate_long_series 通过 (置信度={signal.comprehensive_confidence:.2f})")


class TestSignalFormatting:
    """信号格式化测试"""
    
    def test_format_signal(self):
        """测试信号格式化"""
        engine = ComprehensiveConfidenceEngine()
        
        # 创建测试信号
        signal = ComprehensiveSignal(
            symbol='TEST',
            level='1d',
            timestamp=datetime.now(),
            comprehensive_confidence=0.75,
            recommendation='BUY',
            position_ratio=0.6,
            start_confidence=0.8,
            decay_confidence=0.7,
            reversal_confidence=0.75,
            risk_level='MEDIUM',
            confidence_range='HIGH'
        )
        
        # 格式化输出
        output = engine.format_signal(signal)
        
        # 检查输出包含关键信息
        assert 'TEST' in output
        assert '75%' in output
        assert 'BUY' in output
        assert '60%' in output
        print("✅ test_format_signal 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("综合置信度引擎 - 单元测试")
    print("=" * 70)
    
    tests = [
        # 综合置信度计算
        TestComprehensiveConfidenceCalculation().test_calculate_comprehensive_confidence,
        TestComprehensiveConfidenceCalculation().test_calculate_comprehensive_confidence_bounds,
        
        # 操作建议
        TestRecommendation().test_get_recommendation,
        
        # 仓位建议
        TestPositionRatio().test_get_position_ratio,
        
        # 风险等级
        TestRiskLevel().test_get_risk_level,
        
        # 置信度区间
        TestConfidenceRange().test_get_confidence_range,
        
        # 集成测试
        TestEngineIntegration().test_evaluate_short_series,
        TestEngineIntegration().test_evaluate_long_series,
        
        # 信号格式化
        TestSignalFormatting().test_format_signal,
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
