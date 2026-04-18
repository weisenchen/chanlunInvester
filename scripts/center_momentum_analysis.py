#!/usr/bin/env python3
"""
中枢动量分析集成脚本
缠论 v6.0 - 中枢动量模块

功能:
1. 对监控标的进行中枢动量分析
2. 输出多级别中枢状态
3. 生成趋势延续性评估

使用:
    python3 scripts/center_momentum_analysis.py [SYMBOL]
    
示例:
    python3 scripts/center_momentum_analysis.py EOSE
"""

import sys
import os
from datetime import datetime

# 添加路径
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(script_dir)
python_layer_dir = os.path.join(workspace_dir, 'python-layer')
sys.path.insert(0, python_layer_dir)
sys.path.insert(0, workspace_dir)

# 设置环境变量以便正确导入
os.environ['PYTHONPATH'] = python_layer_dir

# 延迟导入
def import_modules():
    from trading_system.center_momentum import (
        CenterMomentumAnalyzer, 
        format_center_analysis_report,
        CenterAnalysisResult,
        TrendDirection,
        MomentumStatus
    )
    from trading_system.center import CenterDetector
    from trading_system.segment import SegmentCalculator
    from trading_system.pen import PenCalculator
    from trading_system.fractal import FractalDetector
    return {
        'analyzer': CenterMomentumAnalyzer,
        'format_report': format_center_analysis_report,
        'CenterDetector': CenterDetector,
        'SegmentCalculator': SegmentCalculator,
        'PenCalculator': PenCalculator,
        'FractalDetector': FractalDetector,
    }


def calculate_fractals_simple(data):
    """简化版分型计算"""
    fractals = []
    for i in range(2, len(data) - 2):
        # 顶分型
        if (data['High'].iloc[i] > data['High'].iloc[i-1] and 
            data['High'].iloc[i] > data['High'].iloc[i-2] and
            data['High'].iloc[i] > data['High'].iloc[i+1] and
            data['High'].iloc[i] > data['High'].iloc[i+2]):
            fractals.append({'index': i, 'type': 'top', 'price': data['High'].iloc[i]})
        # 底分型
        elif (data['Low'].iloc[i] < data['Low'].iloc[i-1] and
              data['Low'].iloc[i] < data['Low'].iloc[i-2] and
              data['Low'].iloc[i] < data['Low'].iloc[i+1] and
              data['Low'].iloc[i] < data['Low'].iloc[i+2]):
            fractals.append({'index': i, 'type': 'bottom', 'price': data['Low'].iloc[i]})
    return fractals


def calculate_pivots_simple(data, fractals):
    """简化版笔计算"""
    if len(fractals) < 2:
        return []
    
    pivots = []
    for i in range(len(fractals) - 1):
        f1 = fractals[i]
        f2 = fractals[i + 1]
        
        # 顶底交替
        if f1['type'] != f2['type']:
            pivots.append({
                'start': f1,
                'end': f2,
                'direction': 'down' if f1['type'] == 'top' else 'up'
            })
    
    return pivots


def calculate_segments_simple(pivots):
    """简化版线段计算"""
    if len(pivots) < 2:
        return []
    
    segments = []
    i = 0
    while i < len(pivots) - 1:
        p1 = pivots[i]
        p2 = pivots[i + 1]
        
        # 同向笔构成线段
        if p1['direction'] == p2['direction']:
            # 检查是否有重叠
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
    
    return segments


def analyze_symbol_center_momentum(symbol: str, name: str, 
                                    data_1d=None, data_30m=None, 
                                    price=None) -> dict:
    """
    对单个标的进行中枢动量分析
    """
    result = {
        'symbol': symbol,
        'name': name,
        'price': price,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'levels': {}
    }
    
    # 导入模块
    try:
        mods = import_modules()
        CenterMomentumAnalyzer = mods['analyzer']
        CenterDetector = mods['CenterDetector']
    except Exception as e:
        print(f"⚠️ 模块导入失败：{e}")
        return result
    
    # 分析各级别
    for level_name, data in [("1d", data_1d), ("30m", data_30m)]:
        if data is None or len(data) < 30:
            continue
        
        try:
            # 计算缠论结构
            fractals = calculate_fractals_simple(data)
            pivots = calculate_pivots_simple(data, fractals)
            segments = calculate_segments_simple(pivots)
            
            if len(segments) < 3:
                continue
            
            # 检测中枢
            center_det = CenterDetector(min_segments=3)
            
            # 转换线段格式
            from trading_system.segment import Segment
            seg_objects = []
            for i, seg in enumerate(segments):
                seg_obj = Segment(
                    direction=seg['direction'],
                    start_idx=seg['start_idx'],
                    end_idx=seg['end_idx'],
                    start_price=seg['start_price'],
                    end_price=seg['end_price'],
                    amplitude=abs(seg['end_price'] - seg['start_price']),
                    fractals=[],
                    is_temp=False,
                    confirmed=True
                )
                seg_objects.append(seg_obj)
            
            centers = center_det.detect_centers(seg_objects)
            
            # 中枢动量分析
            analyzer = CenterMomentumAnalyzer(level=level_name)
            analysis = analyzer.analyze(centers, seg_objects, price)
            
            result['levels'][level_name] = {
                'centers_count': len(centers),
                'trend': analysis.trend_direction.value,
                'momentum': analysis.momentum_status.value,
                'momentum_score': analysis.momentum_score,
                'position': analysis.center_position.value,
                'continuation': analysis.continuation_probability,
                'reversal_risk': analysis.reversal_risk,
                'suggestion': analysis.suggestion,
                'confidence': analysis.confidence,
                'stage': analysis.trend_stage,
                'details': analysis.analysis_details
            }
            
        except Exception as e:
            print(f"⚠️ {level_name}级别分析失败：{e}")
            continue
    
    return result


def format_multi_level_report(results: list) -> str:
    """格式化多级别中枢动量报告"""
    lines = []
    lines.append("=" * 70)
    lines.append("📊 缠论 v6.0 - 中枢动量多级别分析报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    lines.append("=" * 70)
    lines.append("")
    
    for r in results:
        lines.append(f"【{r['symbol']} - {r['name']}】")
        lines.append(f"当前价格：${r['price']:.2f}")
        lines.append("")
        
        for level, data in r.get('levels', {}).items():
            level_name = "日线" if level == "1d" else "30 分钟"
            lines.append(f"  {level_name}级别:")
            lines.append(f"    中枢数量：{data['centers_count']}")
            lines.append(f"    趋势方向：{data['trend']}")
            lines.append(f"    动量状态：{data['momentum']} ({data['momentum_score']:+.1f})")
            lines.append(f"    当前位置：{data['position']}")
            lines.append(f"    趋势阶段：{data['stage']}")
            lines.append(f"    延续概率：{data['continuation']:.1f}%")
            lines.append(f"    反转风险：{data['reversal_risk']:.1f}%")
            lines.append(f"    操作建议：{data['suggestion']} (置信度：{data['confidence']:.1f}%)")
            lines.append("")
        
        lines.append("-" * 70)
        lines.append("")
    
    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 70)
    print("缠论 v6.0 - 中枢动量分析模块")
    print("=" * 70)
    print()
    
    # 获取标的
    symbol = sys.argv[1] if len(sys.argv) > 1 else "EOSE"
    
    # 导入数据获取模块
    try:
        from data_fetcher import get_stock_data, get_latest_price
    except ImportError:
        print("❌ 无法导入数据获取模块，使用测试数据")
        # 使用测试数据
        import pandas as pd
        import numpy as np
        
        # 生成模拟数据
        dates = pd.date_range('2026-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        data_1d = pd.DataFrame({
            'Open': prices,
            'High': prices + np.random.rand(100) * 2,
            'Low': prices - np.random.rand(100) * 2,
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        data_30m = data_1d.tail(30)  # 简化
        price = prices[-1]
        
        result = analyze_symbol_center_momentum(
            symbol=symbol,
            name="Test Symbol",
            data_1d=data_1d,
            data_30m=data_30m,
            price=price
        )
        
        report = format_multi_level_report([result])
        print(report)
        return
    
    print(f"分析标的：{symbol}")
    print()
    
    try:
        # 获取数据
        data_1d = get_stock_data(symbol, period="1y", interval="1d")
        data_30m = get_stock_data(symbol, period="5d", interval="30m")
        price = get_latest_price(symbol)
        
        if data_1d is None or data_30m is None:
            print("❌ 数据获取失败")
            return
        
        print(f"最新价格：${price:.2f}")
        print(f"日线数据：{len(data_1d)}条")
        print(f"30 分钟数据：{len(data_30m)}条")
        print()
        
        # 执行分析
        result = analyze_symbol_center_momentum(
            symbol=symbol,
            name=symbol,
            data_1d=data_1d,
            data_30m=data_30m,
            price=price
        )
        
        # 输出报告
        report = format_multi_level_report([result])
        print(report)
        
    except Exception as e:
        print(f"❌ 分析失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
