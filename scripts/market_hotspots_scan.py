#!/usr/bin/env python3
"""
缠论市场热点挖掘器
基于周线 + 日线级别分析，推荐投资标的
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from trading_system.weekly_analysis import WeeklyDailyAnalyzer

# 热门股票列表 (按板块分类)
MARKET_STOCKS = {
    # AI/芯片
    'AI/芯片': [
        'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM', 'MU',
        'AMAT', 'LRCX', 'KLAC', 'MRVL', 'NXPI'
    ],
    # 科技巨头
    '科技巨头': [
        'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN',
        'NFLX', 'CRM', 'ORCL', 'ADBE'
    ],
    # AI 应用
    'AI 应用': [
        'TSLA', 'PLTR', 'SNOW', 'PANW', 'CRWD',
        'ZS', 'NET', 'DDOG'
    ],
    # 半导体设备
    '半导体设备': [
        'ASML', 'TSM', 'AMAT', 'LRCX', 'KLAC',
        'TEL', 'APH'
    ],
    # ETF
    'ETF': [
        'QQQ', 'SPY', 'SOXX', 'SMH', 'XLK',
        'VGT', 'ARKK'
    ]
}

def print_stock_analysis(stock):
    """打印股票分析结果"""
    print(f"\n{'='*70}")
    print(f"{stock.symbol} ({stock.name})")
    print(f"{'='*70}")
    print(f"价格：${stock.price:.2f}")
    print(f"板块：{stock.sector}")
    print()
    
    # 信号
    signal_emoji = {
        'STRONG_BUY': '🟢🟢',
        'BUY': '🟢',
        'HOLD': '⚪',
        'SELL': '🔴',
        'STRONG_SELL': '🔴🔴'
    }
    
    print(f"周线信号：{signal_emoji.get(stock.weekly_signal, '⚪')} {stock.weekly_signal} ({stock.weekly_strength:+.1f})")
    print(f"日线信号：{signal_emoji.get(stock.daily_signal, '⚪')} {stock.daily_signal} ({stock.daily_strength:+.1f})")
    print(f"综合评分：{stock.combined_score:+.1f}")
    print()
    
    # 缠论分析
    print("📐 缠论分析:")
    for reason in stock.reasoning[:5]:
        print(f"  • {reason}")
    print()
    
    # 交易计划
    if stock.combined_score > 0:
        print("💡 交易计划:")
        print(f"  入场：${stock.entry_price:.2f}")
        print(f"  止损：${stock.stop_loss:.2f} (-{((stock.entry_price - stock.stop_loss) / stock.entry_price * 100):.1f}%)")
        print(f"  目标：${stock.target_price:.2f} (+{((stock.target_price - stock.entry_price) / stock.entry_price * 100):.1f}%)")
        print(f"  风险收益比：1:{((stock.target_price - stock.entry_price) / (stock.entry_price - stock.stop_loss)):.1f}")
    else:
        print("⚪ 观望，等待更明确信号")
    
    print()

def print_sector_analysis(sector):
    """打印板块分析结果"""
    print(f"\n{'='*70}")
    print(f"📊 板块：{sector.sector_name}")
    print(f"{'='*70}")
    print(f"股票数量：{sector.total_stocks}")
    print(f"强烈买入：{sector.strong_buy_count}只")
    print(f"买入机会：{sector.buy_count}只")
    print(f"平均强度：{sector.avg_strength:+.1f}")
    print(f"趋势：{sector.trend}")
    print()
    
    if sector.top_stocks:
        print("🏆 推荐股票:")
        for i, stock in enumerate(sector.top_stocks[:3], 1):
            print(f"  {i}. {stock.symbol} @ ${stock.price:.2f} (综合:{stock.combined_score:+.1f})")
    print()

def main():
    """主函数"""
    print('='*70)
    print('🔍 缠论市场热点挖掘器')
    print('📊 周线 + 日线级别分析')
    print('='*70)
    print()
    print(f'扫描时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'扫描板块：{len(MARKET_STOCKS)}个')
    total_stocks = sum(len(stocks) for stocks in MARKET_STOCKS.values())
    print(f'扫描股票：{total_stocks}只')
    print()
    
    # 创建分析器
    analyzer = WeeklyDailyAnalyzer()
    
    # 扫描所有股票
    print('='*70)
    print('📈 扫描市场...')
    print('='*70)
    
    all_stocks = []
    for sector_name, stock_list in MARKET_STOCKS.items():
        print(f'\n【{sector_name}】')
        for symbol in stock_list:
            result = analyzer.analyze_stock(symbol)
            if result:
                print(f'  {symbol}: ${result.price:.2f} | 综合:{result.combined_score:+.1f}')
                all_stocks.append(result)
    
    # 按综合评分排序
    all_stocks.sort(key=lambda x: x.combined_score, reverse=True)
    
    # 打印结果
    print()
    print('='*70)
    print('🏆 强烈推荐 (综合评分≥6.0)')
    print('='*70)
    
    strong_buys = [s for s in all_stocks if s.combined_score >= 6.0]
    
    if strong_buys:
        for i, stock in enumerate(strong_buys[:10], 1):
            print(f"\n{i}. {stock.symbol} ({stock.name})")
            print(f"   价格：${stock.price:.2f}")
            print(f"   板块：{stock.sector}")
            print(f"   综合评分：{stock.combined_score:+.1f}")
            print(f"   周线：{stock.weekly_signal} ({stock.weekly_strength:+.1f})")
            print(f"   日线：{stock.daily_signal} ({stock.daily_strength:+.1f})")
    else:
        print('⚪ 暂无强烈推荐股票')
    
    print()
    print('='*70)
    print('🟢 买入机会 (综合评分 4.0-6.0)')
    print('='*70)
    
    buys = [s for s in all_stocks if 4.0 <= s.combined_score < 6.0]
    
    if buys:
        for stock in buys[:10]:
            print(f"  • {stock.symbol} @ ${stock.price:.2f} (综合:{stock.combined_score:+.1f})")
    else:
        print('⚪ 暂无买入机会')
    
    # 板块分析
    print()
    print('='*70)
    print('📊 板块分析')
    print('='*70)
    
    sector_results = analyzer.analyze_sectors(MARKET_STOCKS)
    
    for sector in sector_results:
        print_sector_analysis(sector)
    
    # 保存结果
    import json
    
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'total_scanned': len(all_stocks),
        'strong_buy_count': len(strong_buys),
        'buy_count': len(buys),
        'top_recommendations': [
            {
                'symbol': s.symbol,
                'name': s.name,
                'price': s.price,
                'sector': s.sector,
                'combined_score': s.combined_score,
                'weekly_signal': s.weekly_signal,
                'daily_signal': s.daily_signal,
                'entry_price': s.entry_price,
                'stop_loss': s.stop_loss,
                'target_price': s.target_price
            }
            for s in strong_buys[:10]
        ],
        'sector_analysis': [
            {
                'sector': s.sector_name,
                'total_stocks': s.total_stocks,
                'strong_buy_count': s.strong_buy_count,
                'buy_count': s.buy_count,
                'avg_strength': s.avg_strength,
                'trend': s.trend
            }
            for s in sector_results
        ]
    }
    
    result_file = Path(__file__).parent.parent / 'logs' / f'market_hotspots_{datetime.now().strftime("%Y%m%d")}.json'
    result_file.parent.mkdir(exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f'\n📝 结果已保存：{result_file}')
    print()
    print('='*70)
    print('⚠️ 风险提示')
    print('='*70)
    print()
    print('• 缠论分析提高胜率，但不保证盈利')
    print('• 周线 + 日线共振信号更可靠')
    print('• 严格执行止损，每笔交易风险≤2%')
    print('• 综合评分≥6.0 为强烈推荐，≥4.0 为买入')
    print()

if __name__ == '__main__':
    main()
