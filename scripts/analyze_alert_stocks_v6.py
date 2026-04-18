#!/usr/bin/env python3
"""
买卖点预警股票分析 - v6.0 中枢动量版
分析当前列入预警的股票
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.center import CenterDetector
from trading_system.center_momentum import CenterMomentumAnalyzer, CenterPosition, MomentumStatus
from trading_system.segment import Segment


# 当前预警股票 (从 monitor_all.py 检测)
ALERT_STOCKS = [
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'signal': 'sell1', 'price': 58.28, 'level': '30m'},
    {'symbol': 'AVGO', 'name': 'Broadcom (芯片)', 'signal': 'sell1', 'price': 141.94, 'level': '30m'},
    {'symbol': 'LRCX', 'name': 'Lam Research (半导体)', 'signal': 'sell1', 'price': 85.35, 'level': '30m'},
    {'symbol': 'SMR', 'name': 'NuScale (核能)', 'signal': 'buy1', 'price': 12.65, 'level': '1d'},
    {'symbol': 'IONQ', 'name': 'IonQ (量子计算)', 'signal': 'sell1', 'price': 44.97, 'level': '30m'},
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
    
    # 宽松处理
    if len(segments) < 2 and len(pivots) >= 2:
        for i in range(0, len(pivots) - 1, 2):
            p1, p2 = pivots[i], pivots[i+1]
            segments.append({
                'start_idx': p1['start']['index'], 'end_idx': p2['end']['index'],
                'start_price': p1['start']['price'], 'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
    
    return segments


def analyze_stock_v6(stock):
    """v6.0 分析单个股票"""
    symbol = stock['symbol']
    signal_type = stock['signal']
    signal_level = stock['level']
    
    # 获取数据
    if signal_level == '1d':
        data = fetch_data(symbol, '6mo', '1d')
    else:
        data = fetch_data(symbol, '10d', '30m')
    
    if data is None or len(data) < 30:
        return {'symbol': symbol, 'status': 'no_data'}
    
    prices = data['Close'].tolist()
    current_price = prices[-1]
    
    # 检测结构
    segments = detect_structure(prices)
    
    # 创建 Segment 对象
    seg_objects = []
    for seg in segments:
        seg_objects.append(Segment(
            direction=seg['direction'], start_idx=seg['start_idx'], end_idx=seg['end_idx'],
            start_price=seg['start_price'], end_price=seg['end_price'],
            pen_count=2, feature_sequence=[], has_gap=False, confirmed=True
        ))
    
    # 检测中枢
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    # v6.0 中枢动量分析
    if centers and len(seg_objects) >= 2:
        analyzer = CenterMomentumAnalyzer(level=signal_level)
        analysis = analyzer.analyze(centers, seg_objects, current_price)
        
        # 背驰风险检查
        divergence_risk = False
        if signal_type == 'sell1' and analysis.center_position == CenterPosition.AFTER_THIRD:
            divergence_risk = True
        if signal_type == 'buy1' and analysis.center_position == CenterPosition.AFTER_THIRD:
            divergence_risk = True
        
        return {
            'symbol': symbol,
            'name': stock['name'],
            'signal': signal_type,
            'signal_level': signal_level,
            'signal_price': stock['price'],
            'current_price': current_price,
            'status': 'ok',
            'centers': len(centers),
            'segments': len(segments),
            'analysis': analysis,
            'divergence_risk': divergence_risk,
        }
    else:
        return {
            'symbol': symbol,
            'name': stock['name'],
            'signal': signal_type,
            'signal_level': signal_level,
            'signal_price': stock['price'],
            'current_price': current_price,
            'status': 'no_center',
            'centers': 0,
            'segments': len(segments),
        }


def main():
    """主函数"""
    print("=" * 90)
    print("买卖点预警股票分析 - v6.0 中枢动量版")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print(f"预警股票：{len(ALERT_STOCKS)}只")
    print()
    
    results = []
    
    # 分析所有预警股票
    print("📊 v6.0 分析中...")
    print("-" * 90)
    
    for stock in ALERT_STOCKS:
        print(f"[{stock['symbol']}] {stock['name']}...", end=' ')
        result = analyze_stock_v6(stock)
        results.append(result)
        
        if result['status'] == 'ok':
            a = result['analysis']
            risk = "⚠️" if result['divergence_risk'] else "✅"
            print(f"{stock['signal']} @ ${result['signal_price']:.2f} | 中枢:{result['centers']}个 | {risk} {a.center_position.value}")
        elif result['status'] == 'no_center':
            print(f"{stock['signal']} @ ${result['signal_price']:.2f} | 中枢未形成")
        else:
            print(f"数据不足")
    
    print()
    print("=" * 90)
    print("【v6.0 背驰风险预警】")
    print("=" * 90)
    print()
    
    # 背驰风险股票
    divergence = [r for r in results if r.get('divergence_risk', False)]
    
    if divergence:
        for r in divergence:
            a = r['analysis']
            print(f"⚠️ {r['symbol']} ({r['name']})")
            print(f"   信号：{r['signal']} @ ${r['signal_price']:.2f}")
            print(f"   中枢位置：{a.center_position.value}")
            print(f"   背驰风险：{a.reversal_risk:.1f}%")
            print(f"   v6.0 建议：警惕背驰，准备离场")
            print()
    else:
        print("✅ 暂无高背驰风险股票")
        print()
    
    print("=" * 90)
    print("【v6.0 操作建议】")
    print("=" * 90)
    print()
    
    for r in results:
        if r['status'] != 'ok':
            continue
        
        a = r['analysis']
        signal = r['signal']
        
        # 根据信号类型和中枢位置给出建议
        print(f"{r['symbol']} ({r['name']})")
        print(f"   信号：{signal} @ ${r['signal_price']:.2f} (当前：${r['current_price']:.2f})")
        print(f"   中枢：{r['centers']}个 | 位置：{a.center_position.value}")
        print(f"   趋势：{a.trend_direction.value} | 动量：{a.momentum_status.value}")
        
        # v6.0 建议
        if signal == 'buy1':
            if a.center_position in [CenterPosition.AFTER_FIRST, CenterPosition.AFTER_SECOND]:
                print(f"   ✅ v6.0 建议：轻仓试多 (20-30%)")
                print(f"   理由：第{r['centers']}中枢后 buy1，可信度 +10-15%")
            elif a.center_position == CenterPosition.AFTER_THIRD:
                print(f"   ⚠️ v6.0 建议：观望 (背驰风险)")
                print(f"   理由：第三中枢后 buy1，强制降级至 40%")
            else:
                print(f"   ⚪ v6.0 建议：等待 30m 确认")
        elif signal == 'sell1':
            if a.center_position == CenterPosition.AFTER_THIRD:
                print(f"   ⚠️ v6.0 建议：减仓/离场")
                print(f"   理由：第三中枢后 sell1，背驰风险高")
            else:
                print(f"   ⚪ v6.0 建议：轻仓试空 (20-30%)")
        
        print()
    
    print("=" * 90)
    print("分析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
