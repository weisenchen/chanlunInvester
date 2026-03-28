#!/usr/bin/env python3
"""
缠论热点股票筛选器
扫描热门股票，找出强烈买入机会 (信号强度≥6.0)
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system import ChanLunMonitor

# 当前热门股票列表
HOT_STOCKS = [
    # AI/芯片
    'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM',
    # 科技巨头
    'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN',
    # AI 应用
    'TSLA', 'PLTR', 'SNOW', 'CRM', 'ORCL',
    # 半导体设备
    'AMAT', 'LRCX', 'KLAC', 'MU',
    # ETF
    'QQQ', 'SPY', 'SOXX', 'SMH',
    # 杠杆 ETF (高风险)
    'SQQQ', 'TQQQ', 'UVIX', 'VIX'
]

def scan_hot_stocks():
    """扫描热门股票"""
    
    print('='*70)
    print('🔍 缠论热点股票筛选器 - 寻找强烈买入机会')
    print('='*70)
    print()
    print(f'扫描股票数：{len(HOT_STOCKS)}只')
    print(f'筛选条件：信号强度≥6.0 (STRONG_BUY)')
    print(f'扫描时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    monitor = ChanLunMonitor()
    strong_buy_list = []
    buy_list = []
    
    for i, symbol in enumerate(HOT_STOCKS, 1):
        print(f'[{i}/{len(HOT_STOCKS)}] 分析 {symbol}...', end=' ')
        
        try:
            result = monitor.analyze(symbol, ['1d', '30m', '5m'])
            
            if result:
                print(f'${result.current_price:.2f} | 信号：{result.signal} | 强度：{result.strength:+.1f}')
                
                if result.strength >= 6.0:
                    strong_buy_list.append({
                        'symbol': symbol,
                        'price': result.current_price,
                        'signal': result.signal,
                        'strength': result.strength,
                        'reasoning': result.reasoning
                    })
                elif result.strength >= 4.0:
                    buy_list.append({
                        'symbol': symbol,
                        'price': result.current_price,
                        'signal': result.signal,
                        'strength': result.strength,
                        'reasoning': result.reasoning
                    })
            else:
                print('❌ 分析失败')
        
        except Exception as e:
            print(f'❌ 错误：{str(e)[:50]}')
    
    print()
    print('='*70)
    print('📊 筛选结果')
    print('='*70)
    print()
    
    if strong_buy_list:
        print(f'🟢🟢 强烈买入 (信号强度≥6.0): {len(strong_buy_list)}只')
        print()
        
        for stock in sorted(strong_buy_list, key=lambda x: x['strength'], reverse=True):
            print(f"  {stock['symbol']}: ${stock['price']:.2f} | 强度：{stock['strength']:+.1f}")
            for reason in stock['reasoning'][:3]:  # 只显示前 3 个原因
                print(f"    • {reason}")
            print()
    else:
        print('⚪ 暂无强烈买入信号 (信号强度≥6.0)')
        print()
    
    if buy_list:
        print(f'🟢 买入机会 (信号强度≥4.0): {len(buy_list)}只')
        print()
        
        for stock in sorted(buy_list, key=lambda x: x['strength'], reverse=True):
            print(f"  {stock['symbol']}: ${stock['price']:.2f} | 强度：{stock['strength']:+.1f}")
        print()
    
    print('='*70)
    print('💡 操作建议')
    print('='*70)
    print()
    
    if strong_buy_list:
        print('🟢🟢 强烈关注以下股票:')
        for stock in strong_buy_list[:3]:
            print(f"  • {stock['symbol']} @ ${stock['price']:.2f} (强度:{stock['strength']:+.1f})")
        print()
        print('建议:')
        print('  1. 立即分析详细走势')
        print('  2. 设置价格预警')
        print('  3. 准备交易计划')
    elif buy_list:
        print('🟢 关注以下股票:')
        for stock in buy_list[:3]:
            print(f"  • {stock['symbol']} @ ${stock['price']:.2f} (强度:{stock['strength']:+.1f})")
        print()
        print('建议:')
        print('  1. 等待信号强度进一步提升')
        print('  2. 关注 30 分钟级别走势')
    else:
        print('⚪ 当前市场无强烈买入信号')
        print()
        print('建议:')
        print('  1. 继续观望')
        print('  2. 等待多级别共振')
        print('  3. 下次扫描：5 分钟后')
    
    print()
    print('='*70)
    print('⚠️ 风险提示')
    print('='*70)
    print()
    print('• 缠论分析提高胜率，但不保证盈利')
    print('• 信号强度≥6.0 为强烈买入，≥4.0 为买入')
    print('• 严格执行止损，每笔交易风险不超过 2%')
    print('• 多级别共振才交易')
    print()
    
    # 保存结果到文件
    report_file = Path(__file__).parent / 'hot_stocks_result.json'
    import json
    
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'total_scanned': len(HOT_STOCKS),
        'strong_buy_count': len(strong_buy_list),
        'buy_count': len(buy_list),
        'strong_buy_stocks': strong_buy_list,
        'buy_stocks': buy_list
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f'📝 结果已保存：{report_file}')
    print()

if __name__ == '__main__':
    scan_hot_stocks()
