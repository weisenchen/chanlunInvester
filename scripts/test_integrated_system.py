#!/usr/bin/env python3
"""
整合系统测试脚本
Test Integrated Confidence System

测试成交量 + MACD 组合确认系统与 monitor_all.py 的整合
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

from trading_system.indicators import MACDIndicator
from volume_confirmation import VolumeConfirmation
from macd_advanced_analysis import MACDAdvancedAnalyzer
from confidence_calculator import ComprehensiveConfidenceCalculator


def test_full_workflow():
    """测试完整的买卖点检测 + 综合可信度计算流程"""
    
    print("=" * 70)
    print("整合系统测试 - 完整的买卖点检测 + 综合可信度计算")
    print("=" * 70)
    
    # 生成模拟数据
    np.random.seed(42)
    
    # 模拟下跌背驰场景
    # 第一段下跌
    prices_part1 = [100 - i * 0.3 + np.random.randn() * 0.5 for i in range(50)]
    # 反弹
    prices_part2 = [prices_part1[-1] + i * 0.2 + np.random.randn() * 0.5 for i in range(20)]
    # 第二段下跌 (新低但力度减弱)
    prices_part3 = [prices_part2[-1] - i * 0.15 + np.random.randn() * 0.5 for i in range(30)]
    
    prices = prices_part1 + prices_part2 + prices_part3
    
    # 模拟成交量 (背驰段缩量)
    volumes_part1 = [1000 + np.random.randn() * 200 for _ in range(50)]
    volumes_part2 = [800 + np.random.randn() * 150 for _ in range(20)]
    volumes_part3 = [500 + np.random.randn() * 100 for _ in range(30)]  # 缩量
    
    volumes = volumes_part1 + volumes_part2 + volumes_part3
    volumes = [max(100, v) for v in volumes]
    
    print(f"\n📊 测试数据")
    print(f"   价格序列：{len(prices)} 根 K 线")
    print(f"   成交量序列：{len(volumes)} 根 K 线")
    print(f"   价格范围：${min(prices):.2f} - ${max(prices):.2f}")
    
    # 计算 MACD
    macd = MACDIndicator(fast=12, slow=26, signal=9)
    macd_data = macd.calculate(prices)
    
    print(f"\n📈 MACD 计算完成")
    print(f"   最新 DIF: {macd_data[-1].dif:.3f}")
    print(f"   最新 DEA: {macd_data[-1].dea:.3f}")
    print(f"   最新柱状图：{macd_data[-1].histogram:.3f}")
    
    # 模拟背驰段索引
    div_start_idx = 50  # 第一段低点
    div_end_idx = 99    # 第二段低点 (背驰点)
    
    # 1. 成交量确认
    print(f"\n{'='*70}")
    print("1️⃣ 成交量确认分析")
    print(f"{'='*70}")
    
    volume_confirm = VolumeConfirmation()
    volume_result = volume_confirm.analyze_buy1_divergence(
        prices=prices,
        volumes=volumes,
        divergence_start_idx=div_start_idx,
        divergence_end_idx=div_end_idx
    )
    
    print(f"   背驰段成交量比率：{volume_result.divergence_volume_ratio:.2f}")
    print(f"   是否缩量：{volume_result.divergence_shrink} ({volume_result.divergence_shrink_percent:.1f}%)")
    print(f"   量价背驰：{volume_result.price_volume_divergence}")
    print(f"   背驰强度：{volume_result.divergence_strength}")
    print(f"   置信度提升：{volume_result.confidence_boost:+.2f}")
    print(f"   可靠性等级：{volume_result.reliability_level}")
    print(f"   分析：{volume_result.details.get('analysis', 'N/A')}")
    
    # 2. MACD 高级分析
    print(f"\n{'='*70}")
    print("2️⃣ MACD 多维度分析")
    print(f"{'='*70}")
    
    macd_analyzer = MACDAdvancedAnalyzer()
    
    # 零轴分析
    zero_axis = macd_analyzer.analyze_zero_axis(macd_data)
    print(f"\n【零轴位置】")
    print(f"   位置：{zero_axis.position}")
    print(f"   趋势：{zero_axis.trend}")
    print(f"   DIF: {zero_axis.dif_value:.3f}")
    print(f"   DEA: {zero_axis.dea_value:.3f}")
    print(f"   分析：{zero_axis.analysis}")
    
    # 柱状图面积背驰
    area_result = macd_analyzer.analyze_divergence_area(
        macd_data=macd_data,
        seg1_range=(40, 49),   # 第一段背驰
        seg2_range=(90, 99),   # 第二段背驰
        is_bull_divergence=True
    )
    print(f"\n【柱状图面积背驰】")
    print(f"   第一段面积：{area_result.area1:.4f}")
    print(f"   第二段面积：{area_result.area2:.4f}")
    print(f"   面积比：{area_result.area_ratio:.2f}")
    print(f"   背驰强度：{area_result.divergence_strength}")
    print(f"   置信度提升：{area_result.confidence_boost:+.2f}")
    print(f"   分析：{area_result.analysis}")
    
    # 3. 综合可信度计算
    print(f"\n{'='*70}")
    print("3️⃣ 综合可信度计算")
    print(f"{'='*70}")
    
    calculator = ComprehensiveConfidenceCalculator()
    
    result = calculator.calculate(
        symbol='SMR',
        signal_type='buy1',
        level='30m',
        price=prices[-1],
        prices=prices,
        volumes=volumes,
        macd_data=macd_data,
        chanlun_base_confidence=0.65,
        divergence_start_idx=div_start_idx,
        divergence_end_idx=div_end_idx,
        multi_level_confirmed=True,
        multi_level_count=2,
        external_factors={
            'industry': 0.70,
            'fundamental': 0.60,
            'sentiment': 0.65,
        }
    )
    
    print(f"\n📊 综合可信度报告")
    print(calculator.format_report(result))
    
    # 4. 模拟详细警报格式
    print(f"\n{'='*70}")
    print("4️⃣ 详细警报格式示例")
    print(f"{'='*70}")
    
    # 导入警报格式化函数
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from monitor_all import format_detailed_alert
    
    signal = {
        'type': 'buy1',
        'name': '30m 级别第一类买点 (背驰)',
        'price': prices[-1],
        'confidence': 'high',
        'description': f'底背驰：新低 {prices[div_end_idx]:.2f} vs 前低 {prices[div_start_idx]:.2f}',
        'trigger_details': {
            'condition': 'MACD 底背驰',
            'price_new_low': prices[div_end_idx],
            'price_prev_low': prices[div_start_idx],
            'macd_strength': f'{macd_data[div_end_idx].histogram / macd_data[div_start_idx].histogram * 100:.1f}%',
            'divergence': '价格新低但 MACD 未新低'
        },
        'data': {
            'prices': prices,
            'volumes': volumes,
            'macd_data': macd_data,
            'last_low_idx': div_end_idx,
            'prev_low_idx': div_start_idx
        },
        'resonance': 'multi_level_confirmed',
        'parent_signal': {
            'level': '1d',
            'type': 'buy1',
            'name': '1d 级别第一类买点 (背驰)'
        }
    }
    
    alert_message = format_detailed_alert(
        symbol='SMR',
        signal=signal,
        level='30m',
        confidence_result={
            'final_confidence': result.final_confidence,
            'reliability_level': result.reliability_level.value,
            'operation_suggestion': result.operation_suggestion.value,
            'breakdown': result.breakdown,
            'analysis_summary': result.analysis_summary,
            'volume_verified': volume_result.verified,
            'volume_reliability': volume_result.reliability_level,
            'macd_divergence': area_result.divergence_strength != 'none',
            'macd_reliability': area_result.divergence_strength,
            'macd_zero_axis': zero_axis.position,
            'macd_resonance': 'double_bull'
        }
    )
    
    print("\n" + alert_message)
    
    print(f"\n{'='*70}")
    print("✅ 测试完成")
    print(f"{'='*70}")
    
    return result


if __name__ == '__main__':
    test_full_workflow()
