#!/usr/bin/env python3
"""
市场热点股票分析报告 - v7.0 多级别版
生成详细 Markdown 报告

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
            advice['long_term'] = {'action': '买入', 'position': '40-60%', 'period': '3-12 个月', 'reason': f"周线成长期 (第{cycle.center_count}中枢)，{weekly['trend']}趋势"}
        elif cycle.stage == '诞生期':
            advice['long_term'] = {'action': '建仓', 'position': '30-50%', 'period': '6-12 个月', 'reason': f"周线诞生期 (第{cycle.center_count}中枢)，早期布局"}
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['long_term'] = {'action': '轻仓', 'position': '10-20%', 'period': '3-6 个月', 'reason': f"周线衰退期 (第{cycle.center_count}中枢)，风险已释放"}
        else:
            advice['long_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"周线{cycle.stage} (第{cycle.center_count}中枢)，{risk['risk_level']}风险"}
    
    # 中长线 (日线)
    if daily.get('status') == 'ok':
        cycle = daily['cycle']
        risk = daily['risk']
        
        if cycle.stage == '成长期':
            advice['medium_term'] = {'action': '参与', 'position': '30-50%', 'period': '1-12 周', 'reason': f"日线成长期 (第{cycle.center_count}中枢)，{daily['trend']}趋势"}
        elif cycle.stage == '诞生期':
            advice['medium_term'] = {'action': '试单', 'position': '20-30%', 'period': '2-8 周', 'reason': f"日线诞生期 (第{cycle.center_count}中枢)，趋势初现"}
        elif cycle.stage == '衰退期' and risk['adjustment'] > -0.1:
            advice['medium_term'] = {'action': '轻仓', 'position': '10-20%', 'period': '1-4 周', 'reason': f"日线衰退期 (第{cycle.center_count}中枢)，风险已释放"}
        else:
            advice['medium_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"日线{cycle.stage} (第{cycle.center_count}中枢)"}
    
    # 短线 (30 分钟)
    if intraday.get('status') == 'ok':
        cycle = intraday['cycle']
        risk = intraday['risk']
        
        if cycle.stage == '成长期':
            advice['short_term'] = {'action': '参与', 'position': '20-40%', 'period': '1-10 天', 'reason': f"30m 成长期 (第{cycle.center_count}中枢)，{intraday['trend']}趋势"}
        elif cycle.stage == '诞生期':
            advice['short_term'] = {'action': '试单', 'position': '10-30%', 'period': '1-5 天', 'reason': f"30m 诞生期 (第{cycle.center_count}中枢)"}
        else:
            advice['short_term'] = {'action': '观望', 'position': '0%', 'period': '-', 'reason': f"30m{cycle.stage} (第{cycle.center_count}中枢)"}
    
    return advice


def generate_report(results, output_path: str):
    """生成 Markdown 报告"""
    lines = []
    
    # 标题
    lines.append("# 市场热点股票分析报告 - v7.0 多级别版")
    lines.append("")
    lines.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**系统版本**: v7.0-beta")
    lines.append(f"**分析框架**: 按级别定义投资机会")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 分析框架
    lines.append("## 📊 分析框架")
    lines.append("")
    lines.append("| 级别 | 投资类型 | 持有周期 | 仓位建议 |")
    lines.append("|------|---------|---------|---------|")
    lines.append("| **周线** | 长线 | 3-12 个月 | 30-60% |")
    lines.append("| **日线** | 中长线 | 1-12 周 | 20-50% |")
    lines.append("| **30m** | 短线 | 1-10 天 | 10-40% |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 核心发现
    lines.append("## 🎯 核心发现")
    lines.append("")
    
    long_term_opps = [(r, get_investment_advice(r)) for r in results if r['weekly'] and r['weekly'].get('status') == 'ok' and get_investment_advice(r)['long_term']['action'] in ['买入', '建仓']]
    medium_term_opps = [(r, get_investment_advice(r)) for r in results if r['daily'] and r['daily'].get('status') == 'ok' and get_investment_advice(r)['medium_term']['action'] in ['参与', '试单']]
    short_term_opps = [(r, get_investment_advice(r)) for r in results if r['intraday'] and r['intraday'].get('status') == 'ok' and get_investment_advice(r)['short_term']['action'] in ['参与', '试单']]
    
    lines.append("```")
    lines.append(f"分析股票：{len(results)}只")
    lines.append(f"长线机会：{len(long_term_opps)}只 ({len(long_term_opps)/len(results)*100:.0f}%)")
    lines.append(f"中长线机会：{len(medium_term_opps)}只 ({len(medium_term_opps)/len(results)*100:.0f}%)")
    lines.append(f"短线机会：{len(short_term_opps)}只 ({len(short_term_opps)/len(results)*100:.0f}%)")
    lines.append("```")
    lines.append("")
    
    if len(long_term_opps) > 0 or len(medium_term_opps) > 0 or len(short_term_opps) > 0:
        lines.append("**整体评估**: ✅ **存在投资机会，可积极参与**")
    else:
        lines.append("**整体评估**: ⚠️ **市场整体处于调整期，谨慎为主**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 长线机会
    lines.append("## 🌟 长线投资机会 (周线级别)")
    lines.append("")
    
    if long_term_opps:
        lines.append("| 股票 | 周期阶段 | 中枢数 | 趋势 | 建议 | 仓位 |")
        lines.append("|------|---------|-------|------|------|------|")
        for r, advice in sorted(long_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            w = r['weekly']
            lines.append(f"| **{r['symbol']}** | {w['cycle'].stage} | 第{w['cycle'].center_count}中枢 | {w['trend']} | {advice['long_term']['action']} | {advice['long_term']['position']} |")
        lines.append("")
        
        # 详细说明
        for r, advice in sorted(long_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            w = r['weekly']
            lines.append(f"### {r['symbol']} ({r['name']})")
            lines.append("")
            lines.append(f"```")
            lines.append(f"周期阶段：{w['cycle'].stage} (第{w['cycle'].center_count}中枢)")
            lines.append(f"趋势方向：{w['trend']}")
            lines.append(f"背驰风险：{w['risk']['risk_level']} ({w['risk']['adjustment']*100:+.0f}%)")
            lines.append(f"评级：{w['rating']} ({w['rating_score']}分)")
            lines.append(f"```")
            lines.append("")
            lines.append(f"**建议**: {advice['long_term']['action']} {advice['long_term']['position']}")
            lines.append("")
            lines.append(f"**理由**: {advice['long_term']['reason']}")
            lines.append("")
            lines.append(f"**持有周期**: {advice['long_term']['period']}")
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("⚪ 暂无长线买入机会")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # 中长线机会
    lines.append("## 📈 中长线投资机会 (日线级别)")
    lines.append("")
    
    if medium_term_opps:
        lines.append("| 股票 | 周期阶段 | 中枢数 | 趋势 | 建议 | 仓位 |")
        lines.append("|------|---------|-------|------|------|------|")
        for r, advice in sorted(medium_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            d = r['daily']
            lines.append(f"| **{r['symbol']}** | {d['cycle'].stage} | 第{d['cycle'].center_count}中枢 | {d['trend']} | {advice['medium_term']['action']} | {advice['medium_term']['position']} |")
        lines.append("")
    else:
        lines.append("⚪ 暂无中长线参与机会")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 短线机会
    lines.append("## 📊 短线投资机会 (30 分钟级别)")
    lines.append("")
    
    if short_term_opps:
        lines.append("| 股票 | 周期阶段 | 中枢数 | 趋势 | 建议 | 仓位 |")
        lines.append("|------|---------|-------|------|------|------|")
        for r, advice in sorted(short_term_opps, key=lambda x: x[0]['composite_score'], reverse=True):
            i = r['intraday']
            lines.append(f"| **{r['symbol']}** | {i['cycle'].stage} | 第{i['cycle'].center_count}中枢 | {i['trend']} | {advice['short_term']['action']} | {advice['short_term']['position']} |")
        lines.append("")
    else:
        lines.append("⚪ 暂无短线参与机会")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 全部股票评级
    lines.append("## 📋 全部股票评级")
    lines.append("")
    lines.append("| 股票 | 周线 (长线) | 日线 (中长线) | 30m (短线) | 综合 |")
    lines.append("|------|-----------|------------|---------|------|")
    for r in sorted(results, key=lambda x: x['composite_score'], reverse=True):
        weekly_rating = r['weekly']['rating'] if r['weekly'] and r['weekly'].get('status') == 'ok' else '-'
        daily_rating = r['daily']['rating'] if r['daily'] and r['daily'].get('status') == 'ok' else '-'
        intraday_rating = r['intraday']['rating'] if r['intraday'] and r['intraday'].get('status') == 'ok' else '-'
        emoji = "🌟" if r['composite_score'] >= 70 else "✅" if r['composite_score'] >= 50 else "⚪"
        lines.append(f"| {emoji} **{r['symbol']}** | {weekly_rating} | {daily_rating} | {intraday_rating} | {r['composite_score']:.0f} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 投资策略总结
    lines.append("## 💡 投资策略总结")
    lines.append("")
    lines.append("### 当前市场状态")
    lines.append("")
    lines.append("```")
    lines.append(f"长线机会：{len(long_term_opps)}只")
    lines.append(f"中长线机会：{len(medium_term_opps)}只")
    lines.append(f"短线机会：{len(short_term_opps)}只")
    lines.append("```")
    lines.append("")
    
    # 建议配置
    total_score = sum(r['composite_score'] for r in results) / len(results) if results else 0
    if total_score >= 60:
        position_advice = "60-80%"
        strategy = "积极参与"
    elif total_score >= 50:
        position_advice = "40-60%"
        strategy = "选择性参与"
    else:
        position_advice = "20-40%"
        strategy = "谨慎观望"
    
    lines.append("### 建议配置")
    lines.append("")
    lines.append("```")
    lines.append(f"总仓位：{position_advice}")
    lines.append(f"策略：{strategy}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 风险提示
    lines.append("## ⚠️ 风险提示")
    lines.append("")
    lines.append("1. 本报告基于 v7.0 中枢动量分析，仅供参考")
    lines.append("2. 投资有风险，决策需谨慎")
    lines.append("3. 请结合个人风险承受能力进行投资")
    lines.append("4. 过往表现不代表未来收益")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 页脚
    lines.append("**报告生成**: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    lines.append("")
    lines.append("**系统版本**: v7.0-beta")
    lines.append("")
    lines.append("**分析师**: ChanLun AI Agent")
    lines.append("")
    lines.append("⚠️ **投资有风险，决策需谨慎**")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return output_path


def main():
    """主函数"""
    print("=" * 100)
    print("市场热点股票分析报告 - v7.0 多级别版")
    print("=" * 100)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    
    # 生成报告
    output_path = f"/home/wei/.openclaw/workspace/chanlunInvester/reports/HOT_STOCKS_V7_REPORT_{datetime.now().strftime('%Y-%m-%d_%H%M')}.md"
    generate_report(results, output_path)
    
    print(f"✅ 报告已生成：{output_path}")
    print()
    print("=" * 100)
    print("分析完成")
    print("=" * 100)


if __name__ == "__main__":
    main()
