#!/usr/bin/env python3
"""
市场热点股票分析 - v7.0 基于趋势段的中枢分析
整合:
1. 趋势段识别
2. 中枢周期动态计算
3. 背驰风险动态评估
4. 长线 + 短线投资建议
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.trend_segment import identify_trend_segments
from trading_system.center_cycle import CenterCycleAnalyzer, evaluate_cycle_divergence_risk


# 热点股票池
HOT_STOCKS = [
    {'symbol': 'NVDA', 'name': 'NVIDIA (AI/芯片)', 'sector': 'AI'},
    {'symbol': 'TSLA', 'name': 'Tesla (电动车)', 'sector': 'EV'},
    {'symbol': 'SMR', 'name': 'NuScale (核能)', 'sector': '能源'},
    {'symbol': 'IONQ', 'name': 'IonQ (量子计算)', 'sector': '量子'},
    {'symbol': 'RGTI', 'name': 'Rigetti (量子计算)', 'sector': '量子'},
    {'symbol': 'AMD', 'name': 'AMD (芯片)', 'sector': 'AI'},
    {'symbol': 'GOOG', 'name': 'Google (AI)', 'sector': 'AI'},
    {'symbol': 'MSFT', 'name': 'Microsoft (AI)', 'sector': 'AI'},
    {'symbol': 'META', 'name': 'Meta (AI)', 'sector': 'AI'},
    {'symbol': 'COIN', 'name': 'Coinbase (加密货币)', 'sector': '加密'},
    {'symbol': 'TQQQ', 'name': 'TQQQ (3 倍做多纳指)', 'sector': 'ETF'},
    {'symbol': 'SQQQ', 'name': 'SQQQ (3 倍做空纳指)', 'sector': 'ETF'},
]


def fetch_data(symbol: str, period: str, interval: str):
    """获取数据"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        return history if len(history) > 0 else None
    except Exception:
        return None


def detect_structure(prices):
    """检测缠论结构 (简化版)"""
    fractals = []
    for i in range(2, len(prices) - 2):
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': prices[i]})
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': prices[i]})
    
    pivots = []
    for i in range(len(fractals) - 1):
        f1, f2 = fractals[i], fractals[i+1]
        if f1['type'] != f2['type']:
            pivots.append({'start': f1, 'end': f2, 'direction': 'down' if f1['type'] == 'top' else 'up'})
    
    segments = []
    i = 0
    while i < len(pivots) - 1:
        p1, p2 = pivots[i], pivots[i+1]
        if p1['direction'] == p2['direction']:
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
            i += 2
        else:
            i += 1
    
    if len(segments) < 2 and len(pivots) >= 2:
        for i in range(0, len(pivots) - 1, 2):
            p1, p2 = pivots[i], pivots[i+1]
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
    
    return segments


def analyze_symbol_v7(symbol: str, name: str, sector: str):
    """v7.0 分析单个标的 (基于趋势段)"""
    # 获取周线和日线数据
    week_data = fetch_data(symbol, "2y", "1wk")
    day_data = fetch_data(symbol, "1y", "1d")
    
    result = {
        'symbol': symbol,
        'name': name,
        'sector': sector,
        'weekly': {'status': 'no_data', 'trend_segments': []},
        'daily': {'status': 'no_data', 'trend_segments': []},
    }
    
    # 分析周线
    if week_data is not None and len(week_data) >= 30:
        prices = week_data['Close'].tolist()
        segments = detect_structure(prices)
        trend_segments = identify_trend_segments(segments)
        
        # 分析每个趋势段的周期
        cycle_analyzer = CenterCycleAnalyzer()
        cycles = []
        for ts in trend_segments:
            cycle = cycle_analyzer.analyze(ts)
            risk = evaluate_cycle_divergence_risk(cycle)
            cycles.append({
                'cycle': cycle,
                'risk': risk,
            })
        
        result['weekly'] = {
            'status': 'ok',
            'price': prices[-1],
            'trend_segments': trend_segments,
            'cycles': cycles,
            'current_trend': trend_segments[-1] if trend_segments else None,
            'current_cycle': cycles[-1] if cycles else None,
        }
    
    # 分析日线
    if day_data is not None and len(day_data) >= 30:
        prices = day_data['Close'].tolist()
        segments = detect_structure(prices)
        trend_segments = identify_trend_segments(segments)
        
        cycle_analyzer = CenterCycleAnalyzer()
        cycles = []
        for ts in trend_segments:
            cycle = cycle_analyzer.analyze(ts)
            risk = evaluate_cycle_divergence_risk(cycle)
            cycles.append({
                'cycle': cycle,
                'risk': risk,
            })
        
        result['daily'] = {
            'status': 'ok',
            'price': prices[-1],
            'trend_segments': trend_segments,
            'cycles': cycles,
            'current_trend': trend_segments[-1] if trend_segments else None,
            'current_cycle': cycles[-1] if cycles else None,
        }
    
    return result


def main():
    """主函数"""
    print("=" * 90)
    print("市场热点股票分析 - v7.0 基于趋势段的中枢分析")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"热点股票池：{len(HOT_STOCKS)}只")
    print()
    
    results = []
    
    # 分析所有股票
    print("📊 v7.0 分析中...")
    print("-" * 90)
    
    for stock in HOT_STOCKS:
        print(f"[{stock['symbol']}] {stock['name']}...", end=' ')
        result = analyze_symbol_v7(stock['symbol'], stock['name'], stock['sector'])
        results.append(result)
        
        # 快速状态
        if result['weekly']['status'] == 'ok' and result['weekly']['current_cycle']:
            cycle = result['weekly']['current_cycle']['cycle']
            risk = result['weekly']['current_cycle']['risk']
            print(f"周线{cycle.stage} | 中枢{cycle.center_count}个 | {risk['risk_level']}风险 ({risk['adjustment']*100:+.0f}%)")
        else:
            print(f"数据不足")
    
    print()
    print("=" * 90)
    print("【v7.0 长线投资标的推荐 (周线级别)】")
    print("=" * 90)
    print()
    
    # 长线推荐 (基于周线)
    long_term_buys = []
    long_term_avoids = []
    
    for r in results:
        if r['weekly']['status'] != 'ok' or not r['weekly']['current_cycle']:
            continue
        
        cycle = r['weekly']['current_cycle']['cycle']
        risk = r['weekly']['current_cycle']['risk']
        
        if cycle.stage in ['诞生期', '成长期']:
            long_term_buys.append((r, cycle, risk))
        elif cycle.stage == '成熟期':
            long_term_avoids.append((r, cycle, risk, '背驰高发'))
        elif cycle.stage == '衰退期':
            long_term_avoids.append((r, cycle, risk, '趋势衰退'))
    
    if long_term_buys:
        print("✅ 长线关注 (诞生期/成长期):")
        for r, cycle, risk in long_term_buys[:5]:
            print(f"   {r['symbol']} ({r['name']})")
            print(f"      周线：{cycle.stage} | 第{cycle.center_count}中枢 | {cycle.trend_segment.trend}趋势")
            print(f"      背驰风险：{risk['risk_level']} ({risk['adjustment']*100:+.0f}%)")
            print(f"      建议：仓位 30-50% | 持有周期：3-12 个月")
            print()
    else:
        print("⚪ 暂无长线关注标的")
        print()
    
    if long_term_avoids:
        print("⚠️ 长线规避:")
        for r, cycle, risk, reason in sorted(long_term_avoids, key=lambda x: x[2]['adjustment'])[:5]:
            print(f"   {r['symbol']} - {reason} (调整{risk['adjustment']*100:+.0f}%)")
        print()
    
    print("=" * 90)
    print("【v7.0 短线投资标的推荐 (日线级别)】")
    print("=" * 90)
    print()
    
    # 短线推荐 (基于日线)
    short_term_buys = []
    short_term_avoids = []
    
    for r in results:
        if r['daily']['status'] != 'ok' or not r['daily']['current_cycle']:
            continue
        
        cycle = r['daily']['current_cycle']['cycle']
        risk = r['daily']['current_cycle']['risk']
        
        if cycle.stage in ['诞生期', '成长期']:
            short_term_buys.append((r, cycle, risk))
        elif cycle.stage == '成熟期':
            short_term_avoids.append((r, cycle, risk, '背驰高发'))
        elif cycle.stage == '衰退期':
            short_term_avoids.append((r, cycle, risk, '趋势衰退'))
    
    if short_term_buys:
        print("✅ 短线参与 (诞生期/成长期):")
        for r, cycle, risk in short_term_buys[:5]:
            print(f"   {r['symbol']} ({r['name']})")
            print(f"      日线：{cycle.stage} | 第{cycle.center_count}中枢 | {cycle.trend_segment.trend}趋势")
            print(f"      背驰风险：{risk['risk_level']} ({risk['adjustment']*100:+.0f}%)")
            print(f"      建议：仓位 20-30% | 持有周期：1-10 天")
            print()
    else:
        print("⚪ 暂无短线参与标的")
        print()
    
    if short_term_avoids:
        print("⚠️ 短线规避:")
        for r, cycle, risk, reason in sorted(short_term_avoids, key=lambda x: x[2]['adjustment'])[:5]:
            print(f"   {r['symbol']} - {reason} (调整{risk['adjustment']*100:+.0f}%)")
        print()
    
    print("=" * 90)
    print("【v7.0 vs v6.0 对比 - SMR 案例】")
    print("=" * 90)
    print()
    
    # SMR 案例对比
    smr_result = next((r for r in results if r['symbol'] == 'SMR'), None)
    if smr_result and smr_result['daily']['status'] == 'ok' and smr_result['daily']['current_cycle']:
        cycle = smr_result['daily']['current_cycle']['cycle']
        risk = smr_result['daily']['current_cycle']['risk']
        
        print("SMR (NuScale 核能):")
        print()
        print("v6.0 评估:")
        print("  中枢：第 9 中枢后 (连续计数)")
        print("  背驰风险：高 (-25%)")
        print("  建议：规避 ⚠️")
        print()
        print("v7.0 评估:")
        print(f"  趋势段：{len(smr_result['daily']['trend_segments'])}个")
        print(f"  当前趋势段：第{cycle.trend_segment.index}段 ({cycle.trend_segment.trend}趋势)")
        print(f"  中枢：第{cycle.center_count}中枢 (趋势段内独立计数)")
        print(f"  周期阶段：{cycle.stage}")
        print(f"  背驰风险：{risk['risk_level']} ({risk['adjustment']*100:+.0f}%)")
        print(f"  建议：{cycle.recommended_action}")
        print()
        print("改进点:")
        print("  ✅ 趋势段内独立计数 (更准确)")
        print("  ✅ 周期阶段动态评估 (更合理)")
        print("  ✅ 背驰风险递减 (第 4+ 中枢风险低于第 3 中枢)")
    
    print()
    print("=" * 90)
    print("分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
