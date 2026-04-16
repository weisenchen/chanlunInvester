#!/usr/bin/env python3
"""
增强置信度系统集成示例
Enhanced Confidence System Integration Example

演示如何将增强置信度分析整合到现有缠论监控系统中
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

from enhanced_confidence_analyzer import (
    EnhancedConfidenceAnalyzer,
    EnhancedConfidence,
    STOCK_SECTOR_MAP,
    IndustrySector
)


# ==================== 集成配置 ====================

# 哪些股票需要启用增强置信度分析
ENHANCED_STOCKS = [
    'IONQ', 'RGTI', 'QBTS',  # 量子计算
    'RKLB', 'SMR', 'EOSE',   # 航天/能源
    'MRNA', 'BNTX',          # 生物科技
    'ENPH', 'SEDG',          # 清洁能源
]

# 可靠性等级对应的操作策略
RELIABILITY_ACTIONS = {
    'very_high': {
        'send_alert': True,
        'priority': 'HIGH',
        'position_size': 'full',  # 全仓
        'stop_loss': 'tight',     # 紧止损
    },
    'high': {
        'send_alert': True,
        'priority': 'NORMAL',
        'position_size': 'normal',  # 正常仓位
        'stop_loss': 'normal',
    },
    'medium': {
        'send_alert': True,
        'priority': 'LOW',
        'position_size': 'light',  # 轻仓
        'stop_loss': 'wide',
    },
    'low': {
        'send_alert': False,
        'priority': 'NONE',
        'position_size': 'none',
        'stop_loss': 'N/A',
        'note': '建议观望',
    },
    'very_low': {
        'send_alert': False,
        'priority': 'NONE',
        'position_size': 'none',
        'stop_loss': 'N/A',
        'note': '避免参与',
    },
}


# ==================== 集成函数 ====================

def should_use_enhanced_analysis(symbol: str) -> bool:
    """判断是否需要对某股票使用增强置信度分析"""
    # 高波动、行业敏感型股票使用增强分析
    return symbol in ENHANCED_STOCKS or symbol in STOCK_SECTOR_MAP


def analyze_signal_enhanced(symbol: str, signal_type: str, 
                           chanlun_confidence: float, 
                           price: float) -> dict:
    """
    对缠论信号进行增强置信度分析
    
    Args:
        symbol: 股票代码
        signal_type: 缠论信号类型 (buy1, buy2, sell1, sell2 等)
        chanlun_confidence: 缠论原始置信度 (0-1)
        price: 当前价格
    
    Returns:
        包含增强分析结果的字典
    """
    result = {
        'symbol': symbol,
        'signal_type': signal_type,
        'price': price,
        'chanlun_confidence': chanlun_confidence,
        'use_enhanced': should_use_enhanced_analysis(symbol),
    }
    
    if not result['use_enhanced']:
        # 传统股票，直接使用缠论置信度
        result['final_confidence'] = chanlun_confidence
        result['reliability_level'] = _simple_reliability(chanlun_confidence)
        result['action'] = RELIABILITY_ACTIONS[result['reliability_level']]
        return result
    
    # 高波动股票，使用增强分析
    analyzer = EnhancedConfidenceAnalyzer()
    enhanced = analyzer.analyze(symbol, signal_type, chanlun_confidence)
    
    result['enhanced_analysis'] = {
        'industry_score': enhanced.industry_score,
        'fundamental_score': enhanced.fundamental_score,
        'sentiment_score': enhanced.sentiment_score,
        'capital_flow_score': enhanced.capital_flow_score,
        'volatility_adjustment': enhanced.volatility_adjustment,
        'weighted_score': enhanced.weighted_score,
    }
    
    result['final_confidence'] = enhanced.final_confidence
    result['reliability_level'] = enhanced.reliability_level
    result['action'] = RELIABILITY_ACTIONS[enhanced.reliability_level]
    result['report'] = analyzer.generate_report(enhanced)
    
    return result


def _simple_reliability(confidence: float) -> str:
    """简单可靠性等级 (传统股票)"""
    if confidence >= 0.85:
        return 'very_high'
    elif confidence >= 0.70:
        return 'high'
    elif confidence >= 0.55:
        return 'medium'
    elif confidence >= 0.40:
        return 'low'
    else:
        return 'very_low'


def format_enhanced_alert(result: dict) -> str:
    """格式化增强置信度警报消息"""
    symbol = result['symbol']
    signal = result['signal_type']
    price = result['price']
    final_conf = result['final_confidence']
    reliability = result['reliability_level']
    action = result['action']
    
    # 可靠性图标
    icons = {
        'very_high': '✅',
        'high': '🟢',
        'medium': '⚠️',
        'low': '❌',
        'very_low': '⛔'
    }
    icon = icons.get(reliability, '⚪')
    
    # 基础消息
    message = f"""{icon} {symbol} 缠论信号 (增强分析)

📊 信号：{signal}
💰 价格：USD {price:.2f}
🎯 最终置信度：{final_conf:.0f}%
📈 可靠性：{reliability.upper()}"""
    
    # 如果是高波动股票，添加增强指标详情
    if result.get('use_enhanced') and 'enhanced_analysis' in result:
        ea = result['enhanced_analysis']
        message += f"""

🔍 增强指标:
   行业趋势：{ea['industry_score']:.2f}
   基本面：{ea['fundamental_score']:.2f}
   消息面：{ea['sentiment_score']:.2f}
   资金流：{ea['capital_flow_score']:.2f}
   波动调整：{ea['volatility_adjustment']:.2f}"""
    
    # 操作建议
    message += f"""

💡 操作建议:
   仓位：{action.get('position_size', 'N/A')}
   止损：{action.get('stop_loss', 'N/A')}"""
    
    if 'note' in action:
        message += f"\n   备注：{action['note']}"
    
    return message


def integrate_with_monitor(symbol: str, signals: list, level: str):
    """
    与现有监控系统集成
    
    在 monitor_all.py 的 send_telegram_alert 函数中调用此函数
    """
    results = []
    
    for signal in signals:
        signal_type = signal.get('type', 'unknown').replace(' (背驰)', '')
        confidence = signal.get('confidence', 0.5)
        price = signal.get('price', 0)
        
        # 增强分析
        result = analyze_signal_enhanced(symbol, signal_type, confidence, price)
        results.append(result)
        
        # 根据可靠性决定是否发送警报
        if result['action'].get('send_alert', False):
            message = format_enhanced_alert(result)
            # 调用现有的 Telegram 发送函数
            # send_telegram_message(message, priority=result['action']['priority'])
            print(f"📤 发送警报：{symbol} {signal_type}")
            print(message)
        else:
            print(f"🔇 跳过警报：{symbol} {signal_type} (可靠性：{result['reliability_level']})")
    
    return results


# ==================== 测试入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("增强置信度系统集成测试")
    print("=" * 60)
    
    # 测试 IONQ (高波动股票)
    print("\n📊 测试：IONQ (量子计算)")
    result = analyze_signal_enhanced(
        symbol='IONQ',
        signal_type='buy1_divergence',
        chanlun_confidence=0.75,
        price=12.50
    )
    print(format_enhanced_alert(result))
    
    # 测试 INTC (传统半导体，不启用增强分析)
    print("\n📊 测试：INTC (半导体)")
    result = analyze_signal_enhanced(
        symbol='INTC',
        signal_type='buy2',
        chanlun_confidence=0.70,
        price=62.00
    )
    print(format_enhanced_alert(result))
    
    # 测试 RKLB (航天，高波动)
    print("\n📊 测试：RKLB (航天)")
    result = analyze_signal_enhanced(
        symbol='RKLB',
        signal_type='buy1_divergence',
        chanlun_confidence=0.80,
        price=8.50
    )
    print(format_enhanced_alert(result))
