#!/usr/bin/env python3
"""
市场热点股票分析 - v6.0 中枢动量 + 多级别联动版
整合:
1. v6.0 中枢动量分析
2. 多级别联动分析 (周线 + 日线)
3. 综合可信度评估
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
        if len(history) == 0:
            return None
        return history
    except Exception:
        return None


def detect_structure(prices):
    """检测缠论结构 (宽松版)"""
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
    
    # 线段
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
    
    # 宽松处理
    if len(segments) < 2 and len(pivots) >= 2:
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


def create_seg_objects(segments):
    """创建 Segment 对象"""
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
    return seg_objects


def detect_centers(seg_objects, min_segments=2):
    """检测中枢"""
    center_det = CenterDetector(min_segments=min_segments)
    return center_det.detect_centers(seg_objects)


def analyze_multi_level(symbol: str):
    """
    多级别联动分析 (日线 +30m+5m)
    
    返回:
    - 各级别中枢状态
    - 多级别共振情况
    - 综合可信度
    """
    result = {
        'symbol': symbol,
        'levels': {},
        'multi_level_resonance': False,
        'resonance_type': 'none',
        'comprehensive_confidence': 0.0,
    }
    
    # 获取各级别数据 (周线 + 日线)
    levels_config = {
        '1w': {'period': '2y', 'interval': '1wk'},
        '1d': {'period': '1y', 'interval': '1d'},
    }
    
    for level, config in levels_config.items():
        data = fetch_data(symbol, config['period'], config['interval'])
        if data is None or len(data) < 30:
            result['levels'][level] = {'status': 'no_data'}
            continue
        
        prices = data['Close'].tolist()
        current_price = prices[-1]
        
        # 检测结构
        fractals, pivots, segments = detect_structure(prices)
        seg_objects = create_seg_objects(segments)
        centers = detect_centers(seg_objects)
        
        # v6.0 中枢动量分析
        if centers and len(seg_objects) >= 2:
            analyzer = CenterMomentumAnalyzer(level=level)
            analysis = analyzer.analyze(centers, seg_objects, current_price)
            
            result['levels'][level] = {
                'status': 'ok',
                'price': current_price,
                'centers': len(centers),
                'segments': len(segments),
                'analysis': analysis,
                'trend_direction': analysis.trend_direction.value,
                'momentum_status': analysis.momentum_status.value,
                'center_position': analysis.center_position.value,
            }
        else:
            result['levels'][level] = {
                'status': 'no_center',
                'price': current_price,
                'centers': 0,
                'segments': len(segments),
            }
    
    # 多级别共振分析
    result['multi_level_resonance'], result['resonance_type'] = analyze_resonance(result['levels'])
    
    # 综合可信度计算
    result['comprehensive_confidence'] = calculate_comprehensive_confidence(result)
    
    return result


def analyze_resonance(levels):
    """
    多级别共振分析 (周线 + 日线)
    
    共振条件:
    1. 周线 + 日线同向 → 强共振
    2. 仅单级别 → 无共振
    """
    if '1w' not in levels or '1d' not in levels:
        return False, 'none'
    
    week_data = levels['1w']
    day_data = levels['1d']
    
    if week_data.get('status') != 'ok' or day_data.get('status') != 'ok':
        return False, 'none'
    
    week_trend = week_data.get('trend_direction', 'unknown')
    day_trend = day_data.get('trend_direction', 'unknown')
    
    # 强共振：周线 + 日线同向 (非震荡)
    if week_trend == day_trend and week_trend != 'unknown' and week_trend != '震荡':
        return True, 'strong'
    
    # 普通共振：2 级别同向
    if week_trend == day_trend and week_trend != 'unknown':
        return True, 'normal'
    
    return False, 'none'


def calculate_comprehensive_confidence(result):
    """
    综合可信度计算 (周线 + 日线)
    
    整合:
    1. v6.0 中枢动量调整
    2. 多级别共振加成
    3. 中枢序号加成
    """
    base_confidence = 50.0
    
    # 周线权重 60% (大级别更重要)
    if result['levels'].get('1w', {}).get('status') == 'ok':
        week_analysis = result['levels']['1w'].get('analysis')
        if week_analysis:
            base_confidence += week_analysis.confidence * 0.6 - 30  # 归一化
    
    # 日线权重 40%
    if result['levels'].get('1d', {}).get('status') == 'ok':
        day_analysis = result['levels']['1d'].get('analysis')
        if day_analysis:
            base_confidence += day_analysis.confidence * 0.4 - 20
    
    # 多级别共振加成 (周线 + 日线)
    if result['multi_level_resonance']:
        resonance_bonus = {
            'strong': 20.0,    # 周线 + 日线同向
            'normal': 10.0,
        }
        base_confidence += resonance_bonus.get(result['resonance_type'], 0)
    
    # 中枢序号加成 (基于周线)
    if result['levels'].get('1w', {}).get('status') == 'ok':
        pos = result['levels']['1w'].get('center_position', '')
        if '第二' in pos:
            base_confidence += 15.0  # 周线第 2 中枢后，强信号
        elif '第一' in pos:
            base_confidence += 10.0
        elif '第三' in pos:
            base_confidence -= 25.0  # 周线第 3 中枢后，强背驰风险
    
    # 中枢序号加成 (基于日线)
    if result['levels'].get('1d', {}).get('status') == 'ok':
        pos = result['levels']['1d'].get('center_position', '')
        if '第二' in pos:
            base_confidence += 10.0
        elif '第一' in pos:
            base_confidence += 5.0
        elif '第三' in pos:
            base_confidence -= 15.0
    
    return max(0, min(100, base_confidence))


def main():
    """主函数"""
    print("=" * 90)
    print("市场热点股票分析 - v6.0 中枢动量 + 多级别联动版")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"热点股票池：{len(HOT_STOCKS)}只")
    print()
    
    results = []
    
    # 分析所有股票
    print("📊 多级别分析中...")
    print("-" * 90)
    
    for i, stock in enumerate(HOT_STOCKS, 1):
        print(f"[{i}/{len(HOT_STOCKS)}] {stock['symbol']:6} ({stock['name']:<20})...", end=' ')
        
        result = analyze_multi_level(stock['symbol'])
        result['name'] = stock['name']
        result['sector'] = stock['sector']
        results.append(result)
        
        # 快速状态
        day_status = result['levels'].get('1d', {})
        if day_status.get('status') == 'ok':
            trend = day_status.get('trend_direction', '?')[:2]
            centers = day_status.get('centers', 0)
            resonance = "✅" if result['multi_level_resonance'] else "⚪"
            print(f"日线{trend} | 中枢:{centers}个 | 共振:{resonance} | 置信度:{result['comprehensive_confidence']:.0f}%")
        else:
            print(f"数据不足")
    
    print()
    print("=" * 90)
    print("【v6.0 重点推荐 - 多级别共振 + 中枢动量】")
    print("=" * 90)
    print()
    
    # 筛选高置信度股票
    high_confidence = [r for r in results if r['comprehensive_confidence'] >= 60]
    high_confidence.sort(key=lambda x: x['comprehensive_confidence'], reverse=True)
    
    if high_confidence:
        for r in high_confidence[:5]:
            week_data = r['levels'].get('1w', {})
            day_data = r['levels'].get('1d', {})
            
            resonance_emoji = {"strong": "✅", "normal": "✔️"}.get(r['resonance_type'], "⚪")
            
            print(f"{resonance_emoji} {r['symbol']} ({r['name']})")
            print(f"   综合置信度：{r['comprehensive_confidence']:.0f}%")
            print(f"   多级别共振：{r['resonance_type']}")
            
            if week_data.get('status') == 'ok':
                print(f"   周线：{week_data.get('trend_direction', '?')} | 中枢:{week_data.get('centers', 0)}个 | {week_data.get('center_position', '?')}")
            
            if day_data.get('status') == 'ok':
                print(f"   日线：{day_data.get('trend_direction', '?')} | 中枢:{day_data.get('centers', 0)}个 | {day_data.get('center_position', '?')}")
            
            # 操作建议 (长线 + 短线)
            week_pos = week_data.get('center_position', '') if week_data.get('status') == 'ok' else ''
            day_pos = day_data.get('center_position', '') if day_data.get('status') == 'ok' else ''
            
            # 长线建议 (基于周线)
            if '第二' in week_pos or '第一' in week_pos:
                long_term = "✅ 长线关注"
                long_term_position = "30-50%"
            elif '第三' in week_pos:
                long_term = "⚠️ 长线规避"
                long_term_position = "0%"
            else:
                long_term = "⚪ 长线观望"
                long_term_position = "0-20%"
            
            # 短线建议 (基于日线)
            if '第二' in day_pos or '第一' in day_pos:
                short_term = "✅ 短线参与"
                short_term_position = "20-30%"
            elif '第三' in day_pos:
                short_term = "⚠️ 短线规避"
                short_term_position = "0%"
            else:
                short_term = "⚪ 短线观望"
                short_term_position = "0-20%"
            
            print(f"   长线建议：{long_term} (仓位{long_term_position})")
            print(f"   短线建议：{short_term} (仓位{short_term_position})")
            print()
    else:
        print("⚪ 暂无高置信度推荐 (≥60%)")
        print()
    
    print("=" * 90)
    print("【背驰风险预警 - v6.0 中枢动量】")
    print("=" * 90)
    print()
    
    # 筛选背驰风险股票
    divergence_risk = []
    for r in results:
        day_data = r['levels'].get('1d', {})
        if day_data.get('status') == 'ok':
            pos = day_data.get('center_position', '')
            if '第三' in pos or '延伸' in pos:
                reversal = day_data.get('analysis', None)
                if reversal and hasattr(reversal, 'reversal_risk'):
                    divergence_risk.append((r, reversal.reversal_risk))
    
    divergence_risk.sort(key=lambda x: x[1], reverse=True)
    
    if divergence_risk:
        for r, risk in divergence_risk:
            print(f"⚠️ {r['symbol']} ({r['name']})")
            print(f"   背驰风险：{risk:.1f}%")
            print(f"   中枢位置：{r['levels']['1d'].get('center_position', '?')}")
            print(f"   建议：警惕背驰，准备离场")
            print()
    else:
        print("✅ 暂无高背驰风险股票")
        print()
    
    print("=" * 90)
    print("【板块统计】")
    print("=" * 90)
    
    sectors = {}
    for r in results:
        sector = r['sector']
        if sector not in sectors:
            sectors[sector] = {'total': 0, 'high_conf': 0, 'resonance': 0, 'divergence': 0}
        sectors[sector]['total'] += 1
        if r['comprehensive_confidence'] >= 60:
            sectors[sector]['high_conf'] += 1
        if r['multi_level_resonance']:
            sectors[sector]['resonance'] += 1
        day_data = r['levels'].get('1d', {})
        if day_data.get('status') == 'ok' and '第三' in day_data.get('center_position', ''):
            sectors[sector]['divergence'] += 1
    
    for sector, stats in sectors.items():
        print(f"{sector}: {stats['total']}只 | 高置信:{stats['high_conf']} | 共振:{stats['resonance']} | 背驰:{stats['divergence']}")
    
    print()
    print("=" * 90)
    print("【长线 vs 短线投资建议】")
    print("=" * 90)
    print()
    
    # 长线投资标的 (基于周线)
    print("📈 长线投资标的 (周线级别)")
    print("-" * 90)
    
    long_term_buys = []
    long_term_avoids = []
    
    for r in results:
        week_data = r['levels'].get('1w', {})
        if week_data.get('status') != 'ok':
            continue
        
        week_analysis = week_data.get('analysis')
        if not week_analysis:
            continue
        
        pos = week_data.get('center_position', '')
        
        if '第二' in pos or '第一' in pos:
            if week_analysis.trend_direction.value == '上涨':
                long_term_buys.append((r, '✅ 上涨趋势'))
            else:
                long_term_buys.append((r, '⚪ 趋势未明'))
        elif '第三' in pos:
            long_term_avoids.append((r, week_analysis.reversal_risk))
    
    if long_term_buys:
        print("\n✅ 长线关注:")
        for r, note in long_term_buys:
            week_data = r['levels']['1w']
            week_analysis = week_data.get('analysis')
            print(f"   {r['symbol']} ({r['name']})")
            print(f"      周线：{week_data.get('center_position', '?')} | {week_analysis.trend_direction.value}")
            print(f"      建议：仓位 30-50% | 持有周期：3-12 个月")
            print(f"      状态：{note}")
    else:
        print("\n⚪ 暂无长线关注标的")
    
    if long_term_avoids:
        print("\n⚠️ 长线规避:")
        for r, risk in sorted(long_term_avoids, key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {r['symbol']} - 背驰风险{risk:.0f}%")
    else:
        print("\n✅ 无长线规避标的")
    
    print()
    print("-" * 90)
    print("📊 短线投资标的 (日线级别)")
    print("-" * 90)
    
    short_term_buys = []
    short_term_avoids = []
    
    for r in results:
        day_data = r['levels'].get('1d', {})
        if day_data.get('status') != 'ok':
            continue
        
        day_analysis = day_data.get('analysis')
        if not day_analysis:
            continue
        
        pos = day_data.get('center_position', '')
        
        if '第二' in pos or '第一' in pos:
            if day_analysis.momentum_status.value == '增强':
                short_term_buys.append((r, '✅ 动量增强'))
            else:
                short_term_buys.append((r, '⚪ 动量稳定'))
        elif '第三' in pos:
            short_term_avoids.append((r, day_analysis.reversal_risk))
    
    if short_term_buys:
        print("\n✅ 短线参与:")
        for r, note in short_term_buys[:5]:
            day_data = r['levels']['1d']
            day_analysis = day_data.get('analysis')
            print(f"   {r['symbol']} ({r['name']})")
            print(f"      日线：{day_data.get('center_position', '?')} | {day_analysis.momentum_status.value}")
            print(f"      建议：仓位 20-30% | 持有周期：1-10 天")
            print(f"      状态：{note}")
    else:
        print("\n⚪ 暂无短线参与标的")
    
    if short_term_avoids:
        print("\n⚠️ 短线规避:")
        for r, risk in sorted(short_term_avoids, key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {r['symbol']} - 背驰风险{risk:.0f}%")
    else:
        print("\n✅ 无短线规避标的")
    
    print()
    print("=" * 90)
    print("【投资策略总结】")
    print("=" * 90)
    print()
    
    # 综合策略
    total_long = len(long_term_buys)
    total_short = len(short_term_buys)
    total_avoid = len(long_term_avoids) + len(short_term_avoids)
    
    print(f"长线关注：{total_long}只 | 短线参与：{total_short}只 | 规避：{total_avoid}只")
    print()
    
    if total_long > 0 and total_short > 0:
        print("✅ 策略：长线 + 短线结合")
        print("   长线仓位：30-50% (持有 3-12 个月)")
        print("   短线仓位：20-30% (持有 1-10 天)")
        print("   总仓位：50-80%")
    elif total_long > 0:
        print("✅ 策略：长线为主")
        print("   长线仓位：30-50%")
        print("   短线仓位：0-20%")
        print("   总仓位：30-70%")
    elif total_short > 0:
        print("✅ 策略：短线为主")
        print("   长线仓位：0-20%")
        print("   短线仓位：20-30%")
        print("   总仓位：20-50%")
    else:
        print("⚪ 策略：观望为主")
        print("   建议仓位：0-20%")
        print("   理由：市场背驰风险高，等待清晰信号")
    
    print()
    print("=" * 90)
    print("分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
