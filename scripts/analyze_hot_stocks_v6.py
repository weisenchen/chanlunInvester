#!/usr/bin/env python3
"""
市场热点股票分析 - v6.0 中枢动量版
分析当前市场热点股票的中枢趋势和买卖点
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator
from trading_system.center_momentum import CenterMomentumAnalyzer, CenterPosition, MomentumStatus, TrendDirection
from trading_system.center_momentum_confidence import CenterMomentumConfidenceCalculator


# 热点股票池 (科技/量子/AI/能源)
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
]


def fetch_data(symbol: str, period: str = "1mo", interval: str = "1d"):
    """获取数据"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        if len(history) == 0:
            return None
        return history
    except Exception as e:
        return None


def detect_structure(prices):
    """检测缠论结构 (宽松版 - min_segments=2)"""
    # 分型
    fractals = []
    for i in range(2, len(prices) - 2):
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
            prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': prices[i]})
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
              prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': prices[i]})
    
    # 笔
    pivots = []
    for i in range(len(fractals) - 1):
        f1, f2 = fractals[i], fractals[i+1]
        if f1['type'] != f2['type']:
            pivots.append({'start': f1, 'end': f2, 'direction': 'down' if f1['type'] == 'top' else 'up'})
    
    # 线段 (宽松版 - 允许 2 个笔形成线段)
    segments = []
    i = 0
    while i < len(pivots) - 1:
        p1, p2 = pivots[i], pivots[i+1]
        if p1['direction'] == p2['direction']:
            segments.append({
                'start_idx': p1['start']['index'],
                'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'],
                'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
            i += 2
        else:
            i += 1
    
    # 如果线段不足，使用笔作为近似
    if len(segments) < 2 and len(pivots) >= 2:
        # 使用连续的笔作为线段的近似
        for i in range(0, len(pivots) - 1, 2):
            p1, p2 = pivots[i], pivots[i+1]
            segments.append({
                'start_idx': p1['start']['index'],
                'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'],
                'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
    
    return fractals, pivots, segments


def analyze_symbol_v6(symbol: str, name: str, sector: str):
    """v6.0 分析单个标的"""
    data = fetch_data(symbol, "3mo", "1d")
    if data is None or len(data) < 30:
        return None
    
    prices = data['Close'].tolist()
    current_price = prices[-1]
    
    # 检测结构
    fractals, pivots, segments = detect_structure(prices)
    
    # 创建 Segment 对象
    from trading_system.segment import Segment
    seg_objects = []
    for seg in segments:
        seg_objects.append(Segment(
            direction=seg['direction'],
            start_idx=seg['start_idx'],
            end_idx=seg['end_idx'],
            start_price=seg['start_price'],
            end_price=seg['end_price'],
            pen_count=2,
            feature_sequence=[],
            has_gap=False,
            confirmed=True
        ))
    
    # 检测中枢 (min_segments=2)
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    # v6.0 中枢动量分析
    if centers and len(seg_objects) >= 2:
        analyzer = CenterMomentumAnalyzer(level="1d")
        analysis = analyzer.analyze(centers, seg_objects, current_price)
        
        return {
            'symbol': symbol,
            'name': name,
            'sector': sector,
            'price': current_price,
            'centers': centers,
            'analysis': analysis,
            'structure': {
                'fractals': len(fractals),
                'pivots': len(pivots),
                'segments': len(segments),
            }
        }
    else:
        return {
            'symbol': symbol,
            'name': name,
            'sector': sector,
            'price': current_price,
            'centers': [],
            'analysis': None,
            'structure': {
                'fractals': len(fractals),
                'pivots': len(pivots),
                'segments': len(segments),
            }
        }


def main():
    """主函数"""
    print("=" * 80)
    print("市场热点股票分析 - v6.0 中枢动量版")
    print("=" * 80)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"热点股票池：{len(HOT_STOCKS)}只")
    print()
    
    results = []
    
    # 分析所有热点股票
    print("📊 分析中...")
    print("-" * 80)
    
    for stock in HOT_STOCKS:
        result = analyze_symbol_v6(stock['symbol'], stock['name'], stock['sector'])
        if result:
            results.append(result)
            status = "✅" if result['analysis'] else "⚪"
            print(f"{status} {result['symbol']:6} ${result['price']:>8.2f} | 中枢：{len(result['centers'])}个 | 线段：{result['structure']['segments']}个")
    
    print()
    print("=" * 80)
    print("【v6.0 中枢动量分析详情】")
    print("=" * 80)
    print()
    
    # 有中枢的股票详细分析
    for r in [x for x in results if x['analysis']]:
        a = r['analysis']
        
        # 趋势方向徽章
        trend_emoji = {"上涨": "📈", "下跌": "📉", "震荡": "➡️"}.get(a.trend_direction.value, "⚪")
        
        # 中枢位置徽章
        pos_emoji = "✅" if a.center_position.value in ['第一个中枢后', '第二个中枢后'] else "⚠️" if "第三" in a.center_position.value else "⚪"
        
        print(f"{pos_emoji} {r['symbol']} ({r['name']})")
        print(f"   价格：${r['price']:.2f} {trend_emoji} {a.trend_direction.value}")
        print(f"   中枢：{len(a.centers)}个 | 位置：{a.center_position.value}")
        print(f"   动量：{a.momentum_status.value} ({a.momentum_score:+.1f})")
        print(f"   延续概率：{a.continuation_probability:.1f}% | 反转风险：{a.reversal_risk:.1f}%")
        print(f"   操作建议：{a.suggestion} (置信度：{a.confidence:.1f}%)")
        print()
    
    # 无中枢的股票
    no_center = [x for x in results if not x['analysis']]
    if no_center:
        print("=" * 80)
        print("【中枢尚未形成】")
        print("=" * 80)
        for r in no_center:
            print(f"⚪ {r['symbol']} ({r['name']}) - 线段：{r['structure']['segments']}个 | 等待中枢形成")
        print()
    
    # 热点板块统计
    print("=" * 80)
    print("【热点板块统计】")
    print("=" * 80)
    
    sectors = {}
    for r in results:
        sector = r['sector']
        if sector not in sectors:
            sectors[sector] = {'total': 0, 'with_center': 0, 'trending': 0}
        sectors[sector]['total'] += 1
        if r['analysis']:
            sectors[sector]['with_center'] += 1
            if r['analysis'].trend_direction.value == '上涨':
                sectors[sector]['trending'] += 1
    
    for sector, stats in sectors.items():
        print(f"{sector}: {stats['total']}只 | 有中枢：{stats['with_center']} | 上涨趋势：{stats['trending']}")
    
    print()
    print("=" * 80)
    print("【重点推荐】")
    print("=" * 80)
    
    # 推荐：第二中枢后 + 上涨趋势 + 高延续概率
    recommendations = []
    for r in results:
        if r['analysis']:
            a = r['analysis']
            score = 0
            if a.center_position.value in ['第二个中枢后', '第二个中枢']:
                score += 3
            elif a.center_position.value in ['第一个中枢后', '第一个中枢']:
                score += 2
            if a.trend_direction.value == '上涨':
                score += 2
            if a.momentum_status.value == '增强':
                score += 2
            if a.continuation_probability > 70:
                score += 2
            if score >= 5:
                recommendations.append((r, score))
    
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    if recommendations:
        for r, score in recommendations[:5]:
            a = r['analysis']
            print(f"🌟 {r['symbol']} ({r['name']}) - 评分：{score}")
            print(f"   位置：{a.center_position.value} | 趋势：{a.trend_direction.value}")
            print(f"   建议：{a.suggestion} | 置信度：{a.confidence:.1f}%")
            print()
    else:
        print("⚪ 暂无高置信度推荐，市场处于震荡期")
    
    print("=" * 80)
    print("分析完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
