#!/usr/bin/env python3
"""
多级别联动机会分析 - v7.0
识别周线末端 + 日元起势的黄金交叉机会
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.trend_segment import identify_trend_segments
from trading_system.center_cycle import CenterCycleAnalyzer, evaluate_cycle_divergence_risk


# 目标股票池 (可能处于周线末端 + 日元起势的股票)
TARGET_STOCKS = [
    {'symbol': 'SMR', 'name': 'NuScale (核能)'},
    {'symbol': 'IONQ', 'name': 'IonQ (量子计算)'},
    {'symbol': 'RGTI', 'name': 'Rigetti (量子计算)'},
    {'symbol': 'NVDA', 'name': 'NVIDIA (AI/芯片)'},
    {'symbol': 'TSLA', 'name': 'Tesla (电动车)'},
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
    """检测缠论结构"""
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


def analyze_multi_level(symbol: str, name: str):
    """多级别联动分析"""
    # 获取数据
    week_data = fetch_data(symbol, "2y", "1wk")
    day_data = fetch_data(symbol, "1y", "1d")
    
    if week_data is None or day_data is None:
        return None
    
    # 检测结构
    week_segments = detect_structure(week_data['Close'].tolist())
    day_segments = detect_structure(day_data['Close'].tolist())
    
    if not week_segments or not day_segments:
        return None
    
    # 识别趋势段
    week_trends = identify_trend_segments(week_segments)
    day_trends = identify_trend_segments(day_segments)
    
    if not week_trends or not day_trends:
        return None
    
    # 分析周期
    cycle_analyzer = CenterCycleAnalyzer()
    
    # 周线当前趋势段
    week_current = week_trends[-1]
    week_cycle = cycle_analyzer.analyze(week_current)
    week_risk = evaluate_cycle_divergence_risk(week_cycle)
    
    # 日线当前趋势段
    day_current = day_trends[-1]
    day_cycle = cycle_analyzer.analyze(day_current)
    day_risk = evaluate_cycle_divergence_risk(day_cycle)
    
    return {
        'symbol': symbol,
        'name': name,
        'weekly': {
            'trend': week_current.trend,
            'cycle': week_cycle,
            'risk': week_risk,
            'segment_count': len(week_trends),
        },
        'daily': {
            'trend': day_current.trend,
            'cycle': day_cycle,
            'risk': day_risk,
            'segment_count': len(day_trends),
        },
        'price': day_data['Close'].tolist()[-1],
    }


def evaluate_opportunity(result):
    """
    评估多级别联动机会
    
    黄金交叉机会:
    1. 周线下跌末端 (衰退期，第 4+ 中枢)
    2. 日线刚起势 (诞生期/成长期，第 1-2 中枢)
    3. 周线日线趋势可能即将同步向上
    """
    week = result['weekly']
    day = result['daily']
    
    opportunity_type = None
    opportunity_score = 0
    description = ""
    
    # 黄金交叉：周线末端 + 日元起势
    if (week['cycle'].stage == '衰退期' and week['cycle'].center_count >= 4 and week['trend'] == 'down') and \
       (day['cycle'].stage in ['诞生期', '成长期'] and day['cycle'].center_count <= 2):
        opportunity_type = '黄金交叉 (长线布局)'
        opportunity_score = 85
        description = "周线下跌末端 (第{} 中枢) + 日线刚起势 (第{} 中枢)，长线布局机会".format(
            week['cycle'].center_count, day['cycle'].center_count
        )
    
    # 白银机会：周线成长期 + 日线成长期
    elif (week['cycle'].stage == '成长期' and week['trend'] == 'up') and \
         (day['cycle'].stage == '成长期' and day['trend'] == 'up'):
        opportunity_type = '白银机会 (趋势共振)'
        opportunity_score = 75
        description = "周线日线同步成长期，趋势共振"
    
    # 青铜机会：周线诞生期 + 日线诞生期
    elif (week['cycle'].stage == '诞生期') and \
         (day['cycle'].stage in ['诞生期', '成长期']):
        opportunity_type = '青铜机会 (早期布局)'
        opportunity_score = 65
        description = "周线诞生期，早期布局机会"
    
    # 观望：周线成熟期
    if week['cycle'].stage == '成熟期':
        opportunity_type = '观望 (周线成熟期)'
        opportunity_score = 30
        description = "周线第 3 中枢，背驰高发区，观望"
    
    # 规避：周线日线双成熟期
    if week['cycle'].stage == '成熟期' and day['cycle'].stage == '成熟期':
        opportunity_type = '规避 (双成熟期)'
        opportunity_score = 10
        description = "周线日线均为成熟期，背驰风险高"
    
    # 计算建议仓位
    if opportunity_score >= 80:
        position = '50-70%'
        holding_period = '6-18 个月'
    elif opportunity_score >= 60:
        position = '30-50%'
        holding_period = '3-12 个月'
    elif opportunity_score >= 40:
        position = '10-30%'
        holding_period = '1-6 个月'
    else:
        position = '0-10%'
        holding_period = '观望'
    
    return {
        'type': opportunity_type,
        'score': opportunity_score,
        'description': description,
        'position': position,
        'holding_period': holding_period,
    }


def main():
    """主函数"""
    print("=" * 90)
    print("多级别联动机会分析 - v7.0")
    print("识别周线末端 + 日元起势的黄金交叉机会")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"目标股票：{len(TARGET_STOCKS)}只")
    print()
    
    results = []
    opportunities = []
    
    # 分析所有股票
    print("📊 多级别分析中...")
    print("-" * 90)
    
    for stock in TARGET_STOCKS:
        result = analyze_multi_level(stock['symbol'], stock['name'])
        if result:
            results.append(result)
            opp = evaluate_opportunity(result)
            opportunities.append((result, opp))
            
            print(f"[{result['symbol']}] 周线{result['weekly']['cycle'].stage} | 日线{result['daily']['cycle'].stage} | {opp['type']} (评分:{opp['score']})")
    
    print()
    print("=" * 90)
    print("【黄金交叉机会 - 周线末端 + 日元起势】")
    print("=" * 90)
    print()
    
    # 筛选黄金交叉机会
    golden_cross = [(r, o) for r, o in opportunities if o['score'] >= 80]
    
    if golden_cross:
        for result, opp in sorted(golden_cross, key=lambda x: x[1]['score'], reverse=True):
            print(f"🌟 {result['symbol']} ({result['name']})")
            print(f"   机会类型：{opp['type']}")
            print(f"   机会评分：{opp['score']}/100")
            print(f"   机会描述：{opp['description']}")
            print()
            print(f"   周线级别:")
            print(f"      趋势：{result['weekly']['trend']}")
            print(f"      周期：{result['weekly']['cycle'].stage} (第{result['weekly']['cycle'].center_count}中枢)")
            print(f"      背驰风险：{result['weekly']['risk']['risk_level']} ({result['weekly']['risk']['adjustment']*100:+.0f}%)")
            print()
            print(f"   日线级别:")
            print(f"      趋势：{result['daily']['trend']}")
            print(f"      周期：{result['daily']['cycle'].stage} (第{result['daily']['cycle'].center_count}中枢)")
            print(f"      背驰风险：{result['daily']['risk']['risk_level']} ({result['daily']['risk']['adjustment']*100:+.0f}%)")
            print()
            print(f"   操作建议:")
            print(f"      仓位：{opp['position']}")
            print(f"      持有周期：{opp['holding_period']}")
            print(f"      当前价格：${result['price']:.2f}")
            print()
            print("-" * 90)
            print()
    else:
        print("⚪ 暂无黄金交叉机会")
        print()
    
    print("=" * 90)
    print("【白银机会 - 趋势共振】")
    print("=" * 90)
    print()
    
    silver_opp = [(r, o) for r, o in opportunities if 60 <= o['score'] < 80]
    
    if silver_opp:
        for result, opp in sorted(silver_opp, key=lambda x: x[1]['score'], reverse=True):
            print(f"🥈 {result['symbol']} ({result['name']}) - {opp['type']} (评分:{opp['score']})")
            print(f"   描述：{opp['description']}")
            print(f"   建议：仓位{opp['position']} | 持有{opp['holding_period']}")
            print()
    else:
        print("⚪ 暂无白银机会")
        print()
    
    print("=" * 90)
    print("【观望/规避】")
    print("=" * 90)
    print()
    
    others = [(r, o) for r, o in opportunities if o['score'] < 60]
    
    if others:
        for result, opp in sorted(others, key=lambda x: x[1]['score'], reverse=True):
            print(f"⚪ {result['symbol']} - {opp['type']} (评分:{opp['score']})")
            print(f"   描述：{opp['description']}")
            print(f"   建议：仓位{opp['position']}")
            print()
    else:
        print("⚪ 无观望/规避标的")
        print()
    
    print("=" * 90)
    print("【SMR 深度分析】")
    print("=" * 90)
    print()
    
    # SMR 深度分析
    smr_result = next((r for r in results if r['symbol'] == 'SMR'), None)
    if smr_result:
        opp = evaluate_opportunity(smr_result)
        
        print("SMR (NuScale 核能) 多级别分析:")
        print()
        print("周线级别:")
        print(f"  趋势：{smr_result['weekly']['trend']}")
        print(f"  周期阶段：{smr_result['weekly']['cycle'].stage}")
        print(f"  中枢数量：第{smr_result['weekly']['cycle'].center_count}中枢")
        print(f"  背驰风险：{smr_result['weekly']['risk']['risk_level']} ({smr_result['weekly']['risk']['adjustment']*100:+.0f}%)")
        print(f"  趋势段数量：{smr_result['weekly']['segment_count']}个")
        print()
        print("日线级别:")
        print(f"  趋势：{smr_result['daily']['trend']}")
        print(f"  周期阶段：{smr_result['daily']['cycle'].stage}")
        print(f"  中枢数量：第{smr_result['daily']['cycle'].center_count}中枢")
        print(f"  背驰风险：{smr_result['daily']['risk']['risk_level']} ({smr_result['daily']['risk']['adjustment']*100:+.0f}%)")
        print(f"  趋势段数量：{smr_result['daily']['segment_count']}个")
        print()
        print("多级别联动评估:")
        print(f"  机会类型：{opp['type']}")
        print(f"  机会评分：{opp['score']}/100")
        print(f"  机会描述：{opp['description']}")
        print()
        print("操作建议:")
        print(f"  仓位：{opp['position']}")
        print(f"  持有周期：{opp['holding_period']}")
        print(f"  当前价格：${smr_result['price']:.2f}")
        print()
        print("投资逻辑:")
        print("  1. 周线下跌趋势末端 (衰退期，第{} 中枢)".format(smr_result['weekly']['cycle'].center_count))
        print("  2. 下行空间有限，可能接近底部")
        print("  3. 日线刚起势，短期趋势向好")
        print("  4. 长线布局机会，等待周线反转确认")
    
    print()
    print("=" * 90)
    print("分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
