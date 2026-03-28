#!/usr/bin/env python3
"""
SQQQ 缠论多级别联动分析
基于缠论第 14 课 - 区间套定理
日线 +30 分钟 +5 分钟 三级联动
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system import ChanLunMonitor

def print_multi_level_analysis(symbol='SQQQ'):
    """打印多级别联动分析报告"""
    
    monitor = ChanLunMonitor()
    result = monitor.analyze(symbol, ['1d', '30m', '5m'])
    
    if not result:
        print('❌ 分析失败')
        return
    
    print('='*70)
    print(f'📊 {symbol} 缠论多级别联动分析报告')
    print('='*70)
    print()
    print(f'📅 分析时间：{result.timestamp}')
    print(f'💰 当前价格：${result.current_price:.2f}')
    print()
    
    # 1. 各级别分析
    print('='*70)
    print('📐 各级别走势分析')
    print('='*70)
    print()
    
    for timeframe in ['1d', '30m', '5m']:
        if timeframe not in result.levels:
            continue
        
        analysis = result.levels[timeframe]
        
        print(f'【{timeframe} 级别】')
        
        # 线段统计
        seg_up = analysis['segments']['up']
        seg_down = analysis['segments']['down']
        
        if seg_up > 0:
            print(f'  📈 向上线段：{seg_up}个')
        if seg_down > 0:
            print(f'  📉 向下线段：{seg_down}个')
        
        # 背驰检测
        if analysis.get('divergence') and analysis['divergence'].get('detected'):
            div = analysis['divergence']
            emoji = '🟢' if div['signal'] == 'buy' else '🔴'
            print(f'  {emoji} 背驰 detected: {div["type"]} (强度:{div["strength"]:.2f})')
        
        # 买卖点
        if analysis.get('buy_sell_points'):
            for bsp in analysis['buy_sell_points']:
                emoji = '🟢' if 'buy' in bsp['type_en'] else '🔴'
                print(f'  {emoji} {bsp["type"]} @ ${bsp["price"]:.2f}')
        
        print()
    
    # 2. 区间套定位
    print('='*70)
    print('🎯 区间套定位 (缠论第 14 课)')
    print('='*70)
    print()
    
    # 分析多级别共振
    print('信号强度计算:')
    print(f'  日线级别：{"上涨" if "+3.0" in str(result.reasoning) else "下跌"} (+3/-3)')
    print(f'  30 分钟级：{"上涨" if "30m 上涨" in str(result.reasoning) else "下跌"} (+2/-2)')
    print(f'  5 分钟级：{"上涨" if "5m 上涨" in str(result.reasoning) else "下跌"} (+1/-1)')
    print()
    print(f'当前信号强度：{result.strength:+.1f}')
    print(f'共振因素：{len(result.reasoning)}个')
    print()
    
    # 列出所有共振因素
    print('共振因素:')
    for reason in result.reasoning:
        print(f'  • {reason}')
    print()
    
    # 3. 交易信号
    print('='*70)
    print('💡 交易信号')
    print('='*70)
    print()
    
    signal_emoji = {
        'STRONG_BUY': '🟢🟢 强烈买入',
        'BUY': '🟢 买入',
        'HOLD': '⚪ 观望',
        'SELL': '🔴 卖出',
        'STRONG_SELL': '🔴🔴 强烈卖出'
    }
    
    signal_display = signal_emoji.get(result.signal, '⚪ 观望')
    print(f'{signal_display}')
    print(f'信号强度：{result.strength:+.1f}')
    print()
    
    # 4. 交易计划
    plan = monitor.generate_trading_plan(result)
    
    if plan['action'] != 'HOLD':
        print('='*70)
        print('💡 交易计划')
        print('='*70)
        print()
        print(f'入场价：${plan["entry"]:.2f}')
        print(f'止损价：${plan["stop_loss"]:.2f}')
        print(f'目标 1:  ${plan["target1"]:.2f}')
        print(f'目标 2:  ${plan["target2"]:.2f}')
        print(f'仓位：{plan["position_size"]}')
        print(f'风险收益比：1:{plan["risk_reward"]:.1f}')
        print()
    else:
        print('='*70)
        print('💡 操作建议')
        print('='*70)
        print()
        print('⚪ 当前无交易信号，等待多级别共振')
        print()
        print('建议:')
        print('  1. 等待信号强度≥4.0 再交易')
        print('  2. 关注 30 分钟级别走势转变')
        print('  3. 日线上涨 +30m 转涨=最佳买点')
        print()
    
    # 5. 缠论解读
    print('='*70)
    print('📚 缠论解读')
    print('='*70)
    print()
    
    # 分析走势类型
    if result.strength > 0:
        print('多头格局:')
        print('  • 日线上涨线段确立大方向')
        if '+2.0' in str(result.reasoning) or '30m 上涨' in str(result.reasoning):
            print('  • 30 分钟级别确认上涨')
        if '+1.0' in str(result.reasoning) or '5m 上涨' in str(result.reasoning):
            print('  • 5 分钟级别提供入场点')
        print()
        print('最佳买点:')
        print('  • 30 分钟底背驰 +5 分钟第一类买点')
        print('  • 信号强度≥6.0 为强烈买入')
    elif result.strength < 0:
        print('空头格局:')
        print('  • 30 分钟下跌线段主导')
        print('  • 日线上涨可能接近尾声')
        print()
        print('最佳卖点:')
        print('  • 30 分钟顶背驰 +5 分钟第一类卖点')
        print('  • 信号强度≤-6.0 为强烈卖出')
    else:
        print('震荡格局:')
        print('  • 多级别方向不一致')
        print('  • 等待明确信号')
        print()
    
    print()
    print('='*70)
    print('⚠️ 风险提示')
    print('='*70)
    print()
    print('• 缠论分析提高胜率，但不保证盈利')
    print('• SQQQ 是 3x 杠杆 ETF，波动极大')
    print('• 严格执行止损，每笔交易风险不超过 2%')
    print('• 多级别共振才交易 (信号强度≥4.0)')
    print('• 仅限日内交易，不可长期持有')
    print()

if __name__ == '__main__':
    print_multi_level_analysis('SQQQ')
