#!/usr/bin/env python3
"""
monitor_all.py v6.0 中枢动量整合补丁
使用方法：在 monitor_all.py 中导入此补丁模块

用法:
    from monitor_all_v6_patch import calculate_comprehensive_confidence_v6
    # 替换原有的 calculate_comprehensive_confidence 调用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from trading_system.center import CenterDetector
from trading_system.center_momentum_confidence import CenterMomentumConfidenceCalculator
from confidence_calculator import ComprehensiveConfidenceCalculator


def calculate_comprehensive_confidence_v6(symbol: str, signal: dict, level: str, 
                                           all_macd_data: dict = None,
                                           segments: list = None) -> dict:
    """
    v6.0 版本：整合中枢动量的综合可信度计算
    
    相比 v5.3 的新增功能:
    1. 自动检测中枢
    2. 应用中枢动量调整
    3. 背驰风险强制降级
    4. 返回中枢分析详情
    """
    try:
        calculator = ComprehensiveConfidenceCalculator()
        
        # 提取数据
        prices = signal.get('data', {}).get('prices', [])
        volumes = signal.get('data', {}).get('volumes', [])
        macd_data = signal.get('data', {}).get('macd_data', [])
        
        if not prices or len(prices) < 30:
            return {'final_confidence': 0.5, 'reliability_level': 'medium', 
                    'operation_suggestion': 'observe', 'error': '数据不足'}
        
        # 获取索引
        data = signal.get('data', {})
        div_start = data.get('prev_low_idx', data.get('prev_high_idx'))
        div_end = data.get('last_low_idx', data.get('last_high_idx'))
        
        # 【v6.0 新增】中枢检测
        centers = None
        center_momentum_result = None
        
        if segments:
            try:
                center_det = CenterDetector(min_segments=3)
                centers = center_det.detect_centers(segments)
                
                # 中枢动量分析
                if centers:
                    price = signal['price']
                    center_calc = CenterMomentumConfidenceCalculator()
                    center_momentum_result = center_calc.calculate(
                        symbol=symbol,
                        level=level,
                        price=price,
                        centers=centers,
                        segments=segments,
                        level_name=level
                    )
            except Exception as e:
                print(f"    ⚠️ 中枢检测失败：{e}")
        
        # 计算综合可信度 (v6.0: 传递 centers)
        result = calculator.calculate(
            symbol=symbol,
            signal_type=signal['type'].split()[0],
            level=level,
            price=signal['price'],
            prices=prices,
            volumes=volumes,
            macd_data=macd_data,
            chanlun_base_confidence=0.65 if signal['confidence'] == 'high' else 0.55,
            divergence_start_idx=div_start,
            divergence_end_idx=div_end,
            macd_1d=all_macd_data.get('1d') if all_macd_data else None,
            macd_30m=all_macd_data.get('30m') if all_macd_data else None,
            macd_5m=all_macd_data.get('5m') if all_macd_data else None,
            multi_level_confirmed=signal.get('resonance') == 'multi_level_confirmed',
            multi_level_count=2 if signal.get('resonance') == 'multi_level_confirmed' else 1,
            centers=centers,      # v6.0 新增
            segments=segments     # v6.0 新增
        )
        
        # 构建返回结果
        return_dict = {
            'final_confidence': result.final_confidence,
            'reliability_level': result.reliability_level.value,
            'operation_suggestion': result.operation_suggestion.value,
            'breakdown': result.breakdown,
            'analysis_summary': result.analysis_summary,
            'volume_verified': result.factors.volume_verified,
            'macd_divergence': result.factors.macd_divergence,
        }
        
        # 【v6.0 新增】中枢动量信息
        if center_momentum_result:
            return_dict['center_momentum'] = {
                'center_count': center_momentum_result.center_count,
                'center_position': center_momentum_result.center_position.value,
                'momentum_status': center_momentum_result.momentum_status.value,
                'adjustment': center_momentum_result.total_bonus,
                'divergence_risk': center_momentum_result.divergence_risk,
                'suggestion': center_momentum_result.suggestion,
            }
        
        return return_dict
        
    except Exception as e:
        import traceback
        print(f"    ❌ v6 可信度计算失败：{e}")
        traceback.print_exc()
        return {'final_confidence': 0.5, 'reliability_level': 'medium', 'error': str(e)}


def format_alert_v6(symbol: str, signal: dict, level: str, confidence: dict) -> str:
    """
    v6.0 警报格式：包含中枢动量信息
    """
    emoji = {'buy1': '🟢', 'buy2': '🟢', 'buy3': '🟢', 
             'sell1': '🔴', 'sell2': '🔴', 'sell3': '🔴'}.get(signal['type'].split()[0], '⚪')
    
    # 基础信息
    lines = []
    lines.append(f"{emoji} {symbol} {level}级别{signal['type']} @ ${signal['price']:.2f}")
    lines.append("")
    
    # 综合置信度 (v6.0: 显示调整)
    conf = confidence.get('final_confidence', 0.5) * 100
    rel = confidence.get('reliability_level', 'medium').upper()
    
    if 'center_momentum' in confidence:
        cm = confidence['center_momentum']
        adj = cm.get('adjustment', 0) * 100
        adj_str = f" ⬆️ +{adj:.0f}%" if adj > 0 else f" ⬇️ {adj:.0f}%" if adj < 0 else ""
        lines.append(f"综合置信度：{conf:.0f}% ({rel}){adj_str}")
    else:
        lines.append(f"综合置信度：{conf:.0f}% ({rel})")
    
    lines.append("")
    
    # 【v6.0 新增】中枢分析
    if 'center_momentum' in confidence:
        cm = confidence['center_momentum']
        lines.append("【中枢分析】")
        lines.append(f"  • 中枢数量：{cm.get('center_count', 0)}")
        lines.append(f"  • 当前位置：{cm.get('center_position', 'unknown')}")
        lines.append(f"  • 动量状态：{cm.get('momentum_status', 'unknown')}")
        
        # 背驰风险
        if cm.get('divergence_risk'):
            lines.append(f"  • ⚠️ 背驰风险：高")
        else:
            lines.append(f"  • ✅ 背驰风险：低")
        
        lines.append("")
    
    # 操作建议
    suggestion = confidence.get('operation_suggestion', 'OBSERVE')
    suggestion_map = {
        'STRONG_BUY': '强烈买入 (全仓)',
        'BUY': '买入 (正常仓位)',
        'LIGHT_BUY': '轻仓买入 (20-30%)',
        'OBSERVE': '观望',
        'AVOID': '避免'
    }
    lines.append(f"操作建议：{suggestion_map.get(suggestion, '观望')}")
    lines.append("")
    
    # 触发详情
    details = signal.get('trigger_details', {})
    if details:
        lines.append("【触发原因】")
        for k, v in details.items():
            if isinstance(v, float):
                lines.append(f"  • {k}: {v:.2f}")
            else:
                lines.append(f"  • {k}: {v}")
    
    return "\n".join(lines)
