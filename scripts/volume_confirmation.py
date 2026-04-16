#!/usr/bin/env python3
"""
成交量确认模块
Volume Confirmation Module

用于验证缠论买卖点的成交量配合情况

核心逻辑：
1. 背驰段缩量 → 力量衰竭
2. 确认段放量 → 资金入场
3. 量价背驰 → 高置信度信号
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class VolumeConfirmationResult:
    """成交量确认结果"""
    signal_type: str  # buy1, buy2, sell1, sell2
    level: str  # 5m, 30m, 1d
    
    # 背驰段成交量分析
    divergence_volume_ratio: float = 1.0  # 背驰段成交量比率
    divergence_shrink: bool = False  # 是否缩量
    divergence_shrink_percent: float = 0.0  # 缩量百分比
    
    # 确认段成交量分析
    confirmation_volume_ratio: float = 1.0  # 确认段成交量比率
    confirmation_expand: bool = False  # 是否放量
    confirmation_expand_percent: float = 0.0  # 放量百分比
    
    # 量价背驰分析
    price_volume_divergence: bool = False  # 是否量价背驰
    divergence_strength: str = "none"  # none, weak, medium, strong, very_strong
    
    # 综合评估
    verified: bool = False  # 是否验证通过
    confidence_boost: float = 0.0  # 置信度提升 (-0.2 到 +0.25)
    reliability_level: str = "low"  # very_low, low, medium, high, very_high
    
    # 详细信息
    details: Dict = None


class VolumeConfirmation:
    """成交量确认器"""
    
    def __init__(self):
        # 阈值配置
        self.SHRINK_THRESHOLD = 0.8  # 缩量阈值 (80%)
        self.EXPAND_THRESHOLD = 1.3  # 放量阈值 (130%)
        self.STRONG_SHRINK_THRESHOLD = 0.5  # 强缩量阈值 (50%)
        self.STRONG_EXPAND_THRESHOLD = 1.5  # 强放量阈值 (150%)
        
    def analyze_buy1_divergence(self, prices: List[float], volumes: List[float], 
                                 divergence_start_idx: int, divergence_end_idx: int) -> VolumeConfirmationResult:
        """
        分析第一类买点 (背驰点) 的成交量确认
        
        理想状态：背驰段缩量 → 力量衰竭
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            divergence_start_idx: 背驰段起始索引
            divergence_end_idx: 背驰段结束索引
        """
        result = VolumeConfirmationResult(
            signal_type='buy1',
            level='unknown',
            details={}
        )
        
        if len(prices) < 10 or len(volumes) < 10:
            result.details['error'] = '数据不足'
            return result
        
        # 获取背驰段成交量
        divergence_volumes = volumes[divergence_start_idx:divergence_end_idx+1]
        
        # 获取前一段成交量 (对比基准)
        prior_start = max(0, divergence_start_idx - 10)
        prior_volumes = volumes[prior_start:divergence_start_idx]
        
        if len(divergence_volumes) == 0 or len(prior_volumes) == 0:
            result.details['error'] = '成交量数据不足'
            return result
        
        # 计算成交量比率
        avg_divergence_volume = np.mean(divergence_volumes)
        avg_prior_volume = np.mean(prior_volumes)
        volume_ratio = avg_divergence_volume / avg_prior_volume if avg_prior_volume > 0 else 1.0
        
        result.divergence_volume_ratio = volume_ratio
        result.divergence_shrink = volume_ratio < self.SHRINK_THRESHOLD
        result.divergence_shrink_percent = (1 - volume_ratio) * 100
        
        # 量价背驰分析
        # 价格新低但成交量萎缩 = 量价背驰
        divergence_prices = prices[divergence_start_idx:divergence_end_idx+1]
        prior_prices = prices[prior_start:divergence_start_idx]
        
        price_lower = min(divergence_prices) < min(prior_prices)
        volume_shrink = volume_ratio < self.SHRINK_THRESHOLD
        
        result.price_volume_divergence = price_lower and volume_shrink
        
        # 背驰强度评估
        if volume_ratio < self.STRONG_SHRINK_THRESHOLD:
            result.divergence_strength = 'very_strong'
            result.confidence_boost = 0.25
        elif volume_ratio < self.SHRINK_THRESHOLD:
            result.divergence_strength = 'strong'
            result.confidence_boost = 0.15
        elif volume_ratio < 0.9:
            result.divergence_strength = 'medium'
            result.confidence_boost = 0.05
        elif volume_ratio > 1.2:
            result.divergence_strength = 'weak'
            result.confidence_boost = -0.15  # 放量下跌，警惕
        else:
            result.divergence_strength = 'none'
            result.confidence_boost = 0.0
        
        # 验证通过条件：缩量或量价背驰
        result.verified = result.divergence_shrink or result.price_volume_divergence
        
        # 可靠性等级
        if result.confidence_boost >= 0.20:
            result.reliability_level = 'very_high'
        elif result.confidence_boost >= 0.10:
            result.reliability_level = 'high'
        elif result.confidence_boost >= 0.0:
            result.reliability_level = 'medium'
        else:
            result.reliability_level = 'low'
        
        # 详细信息
        result.details = {
            'avg_divergence_volume': round(avg_divergence_volume, 2),
            'avg_prior_volume': round(avg_prior_volume, 2),
            'price_lower': price_lower,
            'volume_shrink': volume_shrink,
            'analysis': self._get_analysis_text(result)
        }
        
        return result
    
    def analyze_buy2_confirmation(self, prices: List[float], volumes: List[float],
                                   confirmation_start_idx: int, confirmation_end_idx: int,
                                   prior_low_idx: int) -> VolumeConfirmationResult:
        """
        分析第二类买点 (确认点) 的成交量确认
        
        理想状态：确认段放量 → 资金入场
        
        Args:
            prices: 价格序列
            volumes: 成交量序列
            confirmation_start_idx: 确认段起始索引
            confirmation_end_idx: 确认段结束索引
            prior_low_idx: 前低点的索引
        """
        result = VolumeConfirmationResult(
            signal_type='buy2',
            level='unknown',
            details={}
        )
        
        if len(prices) < 10 or len(volumes) < 10:
            result.details['error'] = '数据不足'
            return result
        
        # 获取确认段成交量
        confirmation_volumes = volumes[confirmation_start_idx:confirmation_end_idx+1]
        
        # 获取背驰段成交量 (对比基准)
        divergence_start = max(0, prior_low_idx - 10)
        divergence_volumes = volumes[divergence_start:prior_low_idx+1]
        
        if len(confirmation_volumes) == 0 or len(divergence_volumes) == 0:
            result.details['error'] = '成交量数据不足'
            return result
        
        # 计算成交量比率
        avg_confirmation_volume = np.mean(confirmation_volumes)
        avg_divergence_volume = np.mean(divergence_volumes)
        volume_ratio = avg_confirmation_volume / avg_divergence_volume if avg_divergence_volume > 0 else 1.0
        
        result.confirmation_volume_ratio = volume_ratio
        result.confirmation_expand = volume_ratio > self.EXPAND_THRESHOLD
        result.confirmation_expand_percent = (volume_ratio - 1) * 100
        
        # 量价配合分析
        # 价格上涨且成交量放大 = 健康上涨
        confirmation_prices = prices[confirmation_start_idx:confirmation_end_idx+1]
        divergence_prices = prices[divergence_start:prior_low_idx+1]
        
        price_higher = max(confirmation_prices) > max(divergence_prices)
        volume_expand = volume_ratio > self.EXPAND_THRESHOLD
        
        result.price_volume_divergence = price_higher and volume_expand  # 这里是正向配合
        
        # 确认强度评估
        if volume_ratio > self.STRONG_EXPAND_THRESHOLD:
            result.divergence_strength = 'very_strong'
            result.confidence_boost = 0.25
        elif volume_ratio > self.EXPAND_THRESHOLD:
            result.divergence_strength = 'strong'
            result.confidence_boost = 0.20
        elif volume_ratio > 1.1:
            result.divergence_strength = 'medium'
            result.confidence_boost = 0.10
        elif volume_ratio < 0.8:
            result.divergence_strength = 'weak'
            result.confidence_boost = -0.15  # 缩量上涨，警惕
        else:
            result.divergence_strength = 'none'
            result.confidence_boost = 0.05
        
        # 验证通过条件：放量或量价配合
        result.verified = result.confirmation_expand or result.price_volume_divergence
        
        # 可靠性等级
        if result.confidence_boost >= 0.20:
            result.reliability_level = 'very_high'
        elif result.confidence_boost >= 0.15:
            result.reliability_level = 'high'
        elif result.confidence_boost >= 0.05:
            result.reliability_level = 'medium'
        else:
            result.reliability_level = 'low'
        
        # 详细信息
        result.details = {
            'avg_confirmation_volume': round(avg_confirmation_volume, 2),
            'avg_divergence_volume': round(avg_divergence_volume, 2),
            'price_higher': price_higher,
            'volume_expand': volume_expand,
            'analysis': self._get_analysis_text(result)
        }
        
        return result
    
    def analyze_sell_signals(self, prices: List[float], volumes: List[float],
                              signal_type: str, start_idx: int, end_idx: int) -> VolumeConfirmationResult:
        """
        分析卖点信号的成交量确认
        
        卖点逻辑与买点相反：
        - 背驰段：缩量上涨 → 买盘衰竭
        - 确认段：放量下跌 → 抛压涌现
        """
        result = VolumeConfirmationResult(
            signal_type=signal_type,
            level='unknown',
            details={}
        )
        
        if len(prices) < 10 or len(volumes) < 10:
            result.details['error'] = '数据不足'
            return result
        
        signal_volumes = volumes[start_idx:end_idx+1]
        prior_start = max(0, start_idx - 10)
        prior_volumes = volumes[prior_start:start_idx]
        
        if len(signal_volumes) == 0 or len(prior_volumes) == 0:
            result.details['error'] = '成交量数据不足'
            return result
        
        avg_signal_volume = np.mean(signal_volumes)
        avg_prior_volume = np.mean(prior_volumes)
        volume_ratio = avg_signal_volume / avg_prior_volume if avg_prior_volume > 0 else 1.0
        
        if signal_type == 'sell1':
            # 第一类卖点：希望背驰段缩量上涨
            result.divergence_volume_ratio = volume_ratio
            result.divergence_shrink = volume_ratio < self.SHRINK_THRESHOLD
            result.divergence_shrink_percent = (1 - volume_ratio) * 100
            
            if volume_ratio < self.STRONG_SHRINK_THRESHOLD:
                result.divergence_strength = 'very_strong'
                result.confidence_boost = 0.25
            elif volume_ratio < self.SHRINK_THRESHOLD:
                result.divergence_strength = 'strong'
                result.confidence_boost = 0.15
            elif volume_ratio > 1.3:
                result.divergence_strength = 'weak'
                result.confidence_boost = -0.15
            else:
                result.divergence_strength = 'none'
                result.confidence_boost = 0.0
        else:  # sell2
            # 第二类卖点：希望确认段放量下跌
            result.confirmation_volume_ratio = volume_ratio
            result.confirmation_expand = volume_ratio > self.EXPAND_THRESHOLD
            result.confirmation_expand_percent = (volume_ratio - 1) * 100
            
            if volume_ratio > self.STRONG_EXPAND_THRESHOLD:
                result.divergence_strength = 'very_strong'
                result.confidence_boost = 0.25
            elif volume_ratio > self.EXPAND_THRESHOLD:
                result.divergence_strength = 'strong'
                result.confidence_boost = 0.20
            elif volume_ratio < 0.7:
                result.divergence_strength = 'weak'
                result.confidence_boost = -0.15
            else:
                result.divergence_strength = 'none'
                result.confidence_boost = 0.05
        
        result.verified = result.confidence_boost >= 0.0
        
        if result.confidence_boost >= 0.20:
            result.reliability_level = 'very_high'
        elif result.confidence_boost >= 0.10:
            result.reliability_level = 'high'
        elif result.confidence_boost >= 0.0:
            result.reliability_level = 'medium'
        else:
            result.reliability_level = 'low'
        
        result.details = {
            'avg_signal_volume': round(avg_signal_volume, 2),
            'avg_prior_volume': round(avg_prior_volume, 2),
            'volume_ratio': round(volume_ratio, 2),
            'analysis': self._get_analysis_text(result)
        }
        
        return result
    
    def _get_analysis_text(self, result: VolumeConfirmationResult) -> str:
        """生成分析文本"""
        if result.signal_type in ['buy1', 'sell1']:
            if result.divergence_strength == 'very_strong':
                return f"极强缩量 ({result.divergence_shrink_percent:.1f}%)，力量衰竭明显"
            elif result.divergence_strength == 'strong':
                return f"明显缩量 ({result.divergence_shrink_percent:.1f}%)，力量衰竭"
            elif result.divergence_strength == 'medium':
                return f"温和缩量 ({result.divergence_shrink_percent:.1f}%)，中性信号"
            elif result.divergence_strength == 'weak':
                return f"放量背驰，警惕假信号"
            else:
                return f"成交量无明显变化"
        else:  # buy2, sell2
            if result.divergence_strength == 'very_strong':
                return f"极强放量 (+{result.confirmation_expand_percent:.1f}%)，资金大举入场"
            elif result.divergence_strength == 'strong':
                return f"明显放量 (+{result.confirmation_expand_percent:.1f}%)，资金入场"
            elif result.divergence_strength == 'medium':
                return f"温和放量 (+{result.confirmation_expand_percent:.1f}%)，中性信号"
            elif result.divergence_strength == 'weak':
                return f"缩量确认，警惕假突破"
            else:
                return f"成交量无明显变化"


# ==================== 测试函数 ====================

def test_volume_confirmation():
    """测试成交量确认模块"""
    import random
    
    # 生成测试数据
    np.random.seed(42)
    
    # 模拟背驰段缩量场景
    prices = [100 - i * 0.5 + random.gauss(0, 1) for i in range(30)]
    volumes = [1000 + random.gauss(0, 100) for i in range(20)] + \
              [500 + random.gauss(0, 50) for i in range(10)]  # 后段缩量
    
    confirm = VolumeConfirmation()
    result = confirm.analyze_buy1_divergence(prices, volumes, 20, 29)
    
    print("=" * 60)
    print("成交量确认模块测试")
    print("=" * 60)
    print(f"信号类型：{result.signal_type}")
    print(f"背驰段成交量比率：{result.divergence_volume_ratio:.2f}")
    print(f"是否缩量：{result.divergence_shrink} ({result.divergence_shrink_percent:.1f}%)")
    print(f"量价背驰：{result.price_volume_divergence}")
    print(f"背驰强度：{result.divergence_strength}")
    print(f"置信度提升：{result.confidence_boost:+.2f}")
    print(f"可靠性等级：{result.reliability_level}")
    print(f"验证结果：{'✅ 通过' if result.verified else '❌ 未通过'}")
    print(f"分析：{result.details.get('analysis', 'N/A')}")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    test_volume_confirmation()
