#!/usr/bin/env python3
"""
SMR 日线中枢结构深度解析
为什么 SMR 日线被判定为在第三中枢后？
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
from trading_system.center import CenterDetector
from trading_system.segment import Segment


def fetch_data(symbol: str, period: str, interval: str):
    """获取数据"""
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval=interval)
    return history if len(history) > 0 else None


def detect_structure(prices):
    """检测缠论结构"""
    # 分型
    fractals = []
    for i in range(2, len(prices) - 2):
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': prices[i]})
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': prices[i]})
    
    # 笔
    pivots = []
    for i in range(len(fractals) - 1):
        f1, f2 = fractals[i], fractals[i+1]
        if f1['type'] != f2['type']:
            pivots.append({
                'start': f1, 'end': f2,
                'direction': 'down' if f1['type'] == 'top' else 'up'
            })
    
    # 线段
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
    
    return fractals, pivots, segments


def main():
    """主函数"""
    print("=" * 90)
    print("SMR 日线中枢结构深度解析")
    print("=" * 90)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    # 获取数据
    print("📈 获取 SMR 日线数据...")
    data = fetch_data("SMR", "1y", "1d")
    
    if data is None or len(data) < 30:
        print("❌ 数据不足")
        return
    
    prices = data['Close'].tolist()
    dates = data.index.tolist()
    current_price = prices[-1]
    current_date = dates[-1]
    
    print(f"数据范围：{dates[0].strftime('%Y-%m-%d')} 至 {current_date.strftime('%Y-%m-%d')}")
    print(f"K 线数量：{len(prices)}")
    print(f"当前价格：${current_price:.2f}")
    print()
    
    # 检测结构
    print("【缠论结构检测】")
    print("-" * 90)
    
    fractals, pivots, segments = detect_structure(prices)
    
    print(f"分型：{len(fractals)} (顶：{len([f for f in fractals if f['type']=='top'])}, 底：{len([f for f in fractals if f['type']=='bottom'])})")
    print(f"笔：{len(pivots)}")
    print(f"线段：{len(segments)}")
    print()
    
    # 创建 Segment 对象
    seg_objects = []
    for seg in segments:
        seg_objects.append(Segment(
            direction=seg['direction'], start_idx=seg['start_idx'], end_idx=seg['end_idx'],
            start_price=seg['start_price'], end_price=seg['end_price'],
            pen_count=2, feature_sequence=[], has_gap=False, confirmed=True
        ))
    
    # 检测中枢
    print("【中枢检测】")
    print("-" * 90)
    
    center_det = CenterDetector(min_segments=2)
    centers = center_det.detect_centers(seg_objects)
    
    print(f"中枢数量：{len(centers)}")
    print()
    
    # 详细分析每个中枢
    print("【中枢详细结构】")
    print("-" * 90)
    print()
    
    for i, center in enumerate(centers):
        print(f"中枢 {i+1}:")
        print(f"  位置：索引 {center.start_idx} - {center.end_idx}")
        print(f"  上沿 (ZG): ${center.zg:.2f}")
        print(f"  下沿 (ZD): ${center.zd:.2f}")
        print(f"  区间：${center.zg - center.zd:.2f}")
        print(f"  包含线段数：{len(center.segments)}")
        
        # 估算日期
        if center.start_idx < len(dates):
            start_date = dates[center.start_idx]
            end_date = dates[min(center.end_idx, len(dates)-1)]
            print(f"  时间：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        # 中枢前后走势
        if i == 0:
            print(f"  状态：第一个中枢")
        else:
            prev_center = centers[i-1]
            if center.zd > prev_center.zg:
                print(f"  状态：中枢上移 (上涨趋势)")
            elif center.zg < prev_center.zd:
                print(f"  状态：中枢下移 (下跌趋势)")
            else:
                print(f"  状态：中枢延伸 (震荡)")
        
        print()
    
    # 当前位置分析
    print("【当前位置分析】")
    print("-" * 90)
    print()
    
    if len(centers) >= 3:
        last_center = centers[-1]
        prev_center = centers[-2]
        
        print(f"最新中枢 (第{len(centers)}中枢):")
        print(f"  ZG: ${last_center.zg:.2f}")
        print(f"  ZD: ${last_center.zd:.2f}")
        print(f"  当前价格：${current_price:.2f}")
        print()
        
        # 判断当前位置
        if current_price > last_center.zg:
            print(f"✅ 当前价格在中枢上方 (${current_price:.2f} > ${last_center.zg:.2f})")
            print(f"   位置：第{len(centers)}中枢后")
        elif current_price < last_center.zd:
            print(f"✅ 当前价格在中枢下方 (${current_price:.2f} < ${last_center.zd:.2f})")
            print(f"   位置：第{len(centers)}中枢后")
        else:
            print(f"⚪ 当前价格在中枢内部 (${last_center.zd:.2f} < ${current_price:.2f} < ${last_center.zg:.2f})")
            print(f"   位置：第{len(centers)}中枢中")
        
        print()
        
        # 中枢演化分析
        print("【中枢演化分析】")
        print("-" * 90)
        print()
        
        for i in range(1, len(centers)):
            prev = centers[i-1]
            curr = centers[i]
            
            if curr.zd > prev.zg:
                move = "上移"
                distance = curr.zd - prev.zg
            elif curr.zg < prev.zd:
                move = "下移"
                distance = prev.zd - curr.zg
            else:
                move = "延伸"
                distance = 0
            
            print(f"中枢{i} → 中枢{i+1}: {move} (${distance:.2f})")
        
        print()
        
        # 为什么是第三中枢后
        print("【为什么判定为第三中枢后？】")
        print("-" * 90)
        print()
        
        if len(centers) == 3:
            print("✅ 中枢数量：3 个")
            print(f"✅ 当前价格：${current_price:.2f}")
            print(f"✅ 第 3 中枢 ZG: ${last_center.zg:.2f}, ZD: ${last_center.zd:.2f}")
            
            if current_price > last_center.zg or current_price < last_center.zd:
                print(f"✅ 当前价格在第 3 中枢外 → 判定为'第三中枢后'")
            else:
                print(f"⚪ 当前价格在第 3 中枢内 → 应判定为'第三中枢中'")
            
            print()
            print("缠论定义:")
            print("  第三中枢后：价格已经离开第三个中枢区间")
            print("  背驰风险：第三中枢后是趋势背驰的高发区域")
            print("  v6.0 调整：-25% (强制降级)")
        
        print()
        print("【v6.0 中枢动量调整】")
        print("-" * 90)
        print()
        print(f"中枢位置：第三个中枢后")
        print(f"v6.0 调整：-25% ⚠️")
        print(f"理由：第三中枢后，背驰风险高")
        print()
        
    else:
        print(f"中枢数量不足 3 个 (当前{len(centers)}个)")
        print("无法判定为'第三中枢后'")
    
    print("=" * 90)
    print("解析完成")
    print("=" * 90)


if __name__ == "__main__":
    main()
