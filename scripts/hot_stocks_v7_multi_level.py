#!/usr/bin/env python3
"""
市场热点股票分析 - v7.0 多级别版
按级别定义投资机会:
- 周线级别 → 长线投资 (持有 3-12 个月)
- 日线级别 → 中长线投资 (持有 1-12 周)
- 30 分钟级别 → 短线投资 (持有 1-10 天)
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
    {'symbol': 'OKLO', 'name': 'Oklo (核能)', 'sector': '能源'},
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


def analyze_level(level_name: str, data, min_klines: int):
    """分析单个级别"""
    if data is None or len(data) < min_klines:
        return {'status': 'no_data', 'level': level_name}
    
    prices = data['Close'].tolist()
    segments = detect_structure(prices)
    
    if not segments:
        return {'status': 'no_segments', 'level': level_name}
    
    trend_segments = identify_trend_segments(segments)
    
    if not trend_segments:
        return {'status': 'no_trend', 'level': level_name, 'segments': len(segments)}
    
    cycle_analyzer = CenterCycleAnalyzer()
    current_trend = trend_segments[-1]
    current_cycle = cycle_analyzer.analyze(current_trend)
    current_risk = evaluate_cycle_divergence_risk(current_cycle)
    
    # 投资评级
    if current_cycle.stage in ['诞生期', '成长期']:
        rating = '买入'
        rating_score = 80 if current_cycle.stage == '成长期' else 70
    elif current_cycle.stage == '成熟期':
        rating = '观望'
        rating_score = 40
    else:  # 衰退期
        rating = '观望'
        rating_score = 50 if current_risk['adjustment'] > -0.1 else 30
    
    return {
        'status': 'ok',
        'level': level_name,
        'price': prices[-1],
        'trend': current_trend.trend,
        'cycle': current_cycle,
        'risk': current_risk,
        'rating': rating,
        'rating_score': rating_score,
    }


def analyze_symbol(symbol: str, name: str, sector: str):
    """多级别分析单个股票"""
    result = {
        'symbol': symbol,
        'name': name,
        'sector': sector,
        'weekly': None,
        'daily': None,
        'intraday': None,
    }
    
    # 获取数据
    week_data = fetch_data(symbol, "2y", "1wk")
    day_data = fetch_data(symbol, "1y", "1d")
    min30_data = fetch_data(symbol, "10d", "30m")
    
    # 分析各级别
    result['weekly'] = analyze_level('周线', week_data, 30)
    result['daily'] = analyze_level('日线', day_data, 60)
    result['intraday'] = analyze_level('30 分钟', min30_data, 30)
    
    # 综合评分
    scores = []
    if result['weekly'] and result['weekly'].get('status') == 'ok':
        scores.append(result['weekly']['rating_score'])
    if result['daily'] and result['daily'].get('status') == 'ok':
        scores.append(result['daily']['rating_score'])
    if result['intraday'] and result['intraday'].get('status') == 'ok':
        scores.append(result['intraday']['rating_score'])
    
    result['composite_score'] = sum(scores) / len(scores) if scores else 0
    
    return result


def get_investment_advice(result):
    """根据各级别分析给出投资建议"""
    weekly = result.get('weekly', {})
    daily = result.get('daily', {})
    intraday = result.get('intraday', {})
    
    advice = {
        'long_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
        'medium_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
        'short_term': {'action': '观望', 'position': '0%', 'period': '-', 'reason': ''},
    }
    
    # 长线 (周线)
    if weekly.get('status') == 'ok':
        cycle = weekly['cycle']
        risk = weekly['risk']
        
        if cycle.stage == '成长期':
            advice['long_term'] = {
                'action': '买入',
                'position': '40-60%',
                'period': '3-12 个月',
                'reason': f"周线成长期 (第{cycle.center_count}中枢)，{weekly['trend']}趋势",
            }
        elif cycle.stage == '诞生期':
            advice['long_term'] = {
                'action': '建仓',
                'position': '30-50%',
                'period': '6-12 个月',
                'reason': f"周线诞生期 (第{cycle.center_count}中枢)，早期布局",
            }
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['long_term'] = {
                'action': '轻仓',
                'position': '10-20%',
                'period': '3-6 个月',
                'reason': f"周线衰退期 (第{cycle.center_count}中枢)，风险已释放",
            }
        else:
            advice['long_term'] = {
                'action': '观望',
                'position': '0%',
                'period': '-',
                'reason': f"周线{cycle.stage} (第{cycle.center_count}中枢)，{risk['risk_level']}风险",
            }
    
    # 中长线 (日线)
    if daily.get('status') == 'ok':
        cycle = daily['cycle']
        risk = daily['risk']
        
        if cycle.stage == '成长期':
            advice['medium_term'] = {
                'action': '参与',
                'position': '30-50%',
                'period': '1-12 周',
                'reason': f"日线成长期 (第{cycle.center_count}中枢)，{daily['trend']}趋势",
            }
        elif cycle.stage == '诞生期':
            advice['medium_term'] = {
                'action': '试单',
                'position': '20-30%',
                'period': '2-8 周',
                'reason': f"日线诞生期 (第{cycle.center_count}中枢)，趋势初现",
            }
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['medium_term'] = {
                'action': '轻仓',
                'position': '10-20%',
                'period': '1-4 周',
                'reason': f"日线衰退期 (第{cycle.center_count}中枢)，风险已释放",
            }
        else:
            advice['medium_term'] = {
                'action': '观望',
                'position': '0%',
                'period': '-',
                'reason': f"日线{cycle.stage} (第{cycle.center_count}中枢)",
            }
    
    # 短线 (30 分钟)
    if intraday.get('status') == 'ok':
        cycle = intraday['cycle']
        risk = intraday['risk']
        
        if cycle.stage == '成长期':
            advice['short_term'] = {
                'action': '参与',
                'position': '20-40%',
                'period': '1-10 天',
                'reason': f"30m 成长期 (第{cycle.center_count}中枢)，{intraday['trend']}趋势",
            }
        elif cycle.stage == '诞生期':
            advice['short_term'] = {
                'action': '试单',
                'position': '10-30%',
                'period': '1-5 天',
                'reason': f"30m 诞生期 (第{cycle.center_count}中枢)",
            }
        else:
            advice['short_term'] = {
                'action': '观望',
                'position': '0%',
                'period': '-',
                'reason': f"30m{cycle.stage} (第{cycle.center_count}中枢)",
            }
    
    return advice


def main():
    """主函数"""
    print("=" * 100)
    print("市场热点股票分析 - v7.0 多级别版")
    print("按级别定义投资机会：周线 (长线) | 日线 (中长线) | 30m (短线)")
    print("=" * 100)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"热点股票池：{len(HOT_STOCKS)}只")
    print()
    
    results = []
    
    # 分析所有股票
    print("📊 多级别分析中...")
    print("-" * 100)
    
    for stock in HOT_STOCKS:
        result = analyze_symbol(stock['symbol'], stock['name'], stock['sector'])
        results.append(result)
        
        # 快速状态
        weekly_status = result['weekly']['rating'] if result['weekly'] and result['weekly'].get('status') == 'ok' else '-'
        daily_status = result['daily']['rating'] if result['daily'] and result['daily'].get('status') == 'ok' else '-'
        intraday_status = result['intraday']['rating'] if result['intraday'] and result['intraday'].get('status') == 'ok' else '-'
        
        print(f"[{result['symbol']:6}] 周线:{weekly_status:^6} | 日线:{daily_status:^6} | 30m:{intraday_status:^6} | 综合:{result['composite_score']:.0f}")
    
    print()
    print("=" * 100)
    print("【🌟 长线投资机会 - 周线级别 (持有 3-12 个月)】")
    print("=" * 100)
    print()
    
    # 长线机会 (周线买入/建仓)
    long_term_opps = []
    for r in results:
        if r['weekly'] and r['weekly'].get('status') == 'ok':
            advice = get_investment_advice(r)
            if advice['long_term']['action'] in ['买入', '建仓']:
                long_term_opps.append((r, advice))
    
    if long_term_opps:
        for r, advice in sorted(long_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            print(f"🌟 {r['symbol']} ({r['name']})")
            print(f"   长线建议：{advice['long_term']['action']} {advice['long_term']['position']}")
            print(f"   持有周期：{advice['long_term']['period']}")
            print(f"   理由：{advice['long_term']['reason']}")
            print()
    else:
        print("⚪ 暂无长线买入机会")
        print()
    
    print("=" * 100)
    print("【🥈 中长线投资机会 - 日线级别 (持有 1-12 周)】")
    print("=" * 100)
    print()
    
    # 中长线机会 (日线参与/试单)
    medium_term_opps = []
    for r in results:
        if r['daily'] and r['daily'].get('status') == 'ok':
            advice = get_investment_advice(r)
            if advice['medium_term']['action'] in ['参与', '试单']:
                medium_term_opps.append((r, advice))
    
    if medium_term_opps:
        for r, advice in sorted(medium_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            print(f"🥈 {r['symbol']} ({r['name']})")
            print(f"   中长线建议：{advice['medium_term']['action']} {advice['medium_term']['position']}")
            print(f"   持有周期：{advice['medium_term']['period']}")
            print(f"   理由：{advice['medium_term']['reason']}")
            print()
    else:
        print("⚪ 暂无中长线参与机会")
        print()
    
    print("=" * 100)
    print("【📊 短线投资机会 - 30 分钟级别 (持有 1-10 天)】")
    print("=" * 100)
    print()
    
    # 短线机会 (30m 参与/试单)
    short_term_opps = []
    for r in results:
        if r['intraday'] and r['intraday'].get('status') == 'ok':
            advice = get_investment_advice(r)
            if advice['short_term']['action'] in ['参与', '试单']:
                short_term_opps.append((r, advice))
    
    if short_term_opps:
        for r, advice in sorted(short_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            print(f"📊 {r['symbol']} ({r['name']})")
            print(f"   短线建议：{advice['short_term']['action']} {advice['short_term']['position']}")
            print(f"   持有周期：{advice['short_term']['period']}")
            print(f"   理由：{advice['short_term']['reason']}")
            print()
    else:
        print("⚪ 暂无短线参与机会")
        print()
    
    print("=" * 100)
    print("【SMR 多级别深度分析】")
    print("=" * 100)
    print()
    
    # SMR 深度分析
    smr_result = next((r for r in results if r['symbol'] == 'SMR'), None)
    if smr_result:
        advice = get_investment_advice(smr_result)
        
        print("SMR (NuScale 核能) 多级别分析:")
        print()
        
        if smr_result['weekly'] and smr_result['weekly'].get('status') == 'ok':
            w = smr_result['weekly']
            print(f"周线级别 (长线 3-12 个月):")
            print(f"  趋势：{w['trend']}")
            print(f"  周期：{w['cycle'].stage} (第{w['cycle'].center_count}中枢)")
            print(f"  背驰风险：{w['risk']['risk_level']} ({w['risk']['adjustment']*100:+.0f}%)")
            print(f"  评级：{w['rating']} ({w['rating_score']}分)")
            print(f"  建议：{advice['long_term']['action']} {advice['long_term']['position']}")
            print(f"  理由：{advice['long_term']['reason']}")
            print()
        
        if smr_result['daily'] and smr_result['daily'].get('status') == 'ok':
            d = smr_result['daily']
            print(f"日线级别 (中长线 1-12 周):")
            print(f"  趋势：{d['trend']}")
            print(f"  周期：{d['cycle'].stage} (第{d['cycle'].center_count}中枢)")
            print(f"  背驰风险：{d['risk']['risk_level']} ({d['risk']['adjustment']*100:+.0f}%)")
            print(f"  评级：{d['rating']} ({d['rating_score']}分)")
            print(f"  建议：{advice['medium_term']['action']} {advice['medium_term']['position']}")
            print(f"  理由：{advice['medium_term']['reason']}")
            print()
        
        if smr_result['intraday'] and smr_result['intraday'].get('status') == 'ok':
            i = smr_result['intraday']
            print(f"30 分钟级别 (短线 1-10 天):")
            print(f"  趋势：{i['trend']}")
            print(f"  周期：{i['cycle'].stage} (第{i['cycle'].center_count}中枢)")
            print(f"  背驰风险：{i['risk']['risk_level']} ({i['risk']['adjustment']*100:+.0f}%)")
            print(f"  评级：{i['rating']} ({i['rating_score']}分)")
            print(f"  建议：{advice['short_term']['action']} {advice['short_term']['position']}")
            print(f"  理由：{advice['short_term']['reason']}")
            print()
        
        print("综合投资建议:")
        print(f"  综合评分：{smr_result['composite_score']:.0f}/100")
        print(f"  长线：{advice['long_term']['action']} {advice['long_term']['position']} ({advice['long_term']['period']})")
        print(f"  中长线：{advice['medium_term']['action']} {advice['medium_term']['position']} ({advice['medium_term']['period']})")
        print(f"  短线：{advice['short_term']['action']} {advice['short_term']['position']} ({advice['short_term']['period']})")
    
    print()
    print("=" * 100)
    print("分析完成")
    print("=" * 100)


if __name__ == "__main__":
    main()
