#!/usr/bin/env python3
"""
测试 UVIX 预警系统
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'python-layer'))

from uvix_auto_monitor import fetch_data, analyze_chanlun, format_alert_message

print("\n🔍 测试 UVIX 预警系统\n")

# 获取数据
series = fetch_data('UVIX', '5m')
current_price = series.klines[-1].close
print(f"✓ 当前价格：${current_price:.2f}")

# 分析
results = analyze_chanlun(series)
print(f"✓ 分析完成")

# 检查买卖点
if results['buy_sell_points']:
    print(f"\n🚨 检测到买卖点！\n")
    message = format_alert_message(results, current_price)
    print(message)
else:
    print(f"\n⚪ 无买卖点信号")
    print(f"   分型：{results['fractals']['total']}个")
    print(f"   笔：{results['pens']['total']}个")
    print(f"   线段：{results['segments']['total']}个")
