#!/usr/bin/env python3
"""
UVIX 盘前预警脚本
Pre-market Alert for UVIX (30 minutes before market open)

在美股开盘前 30 分钟（9:00 EST）发送预警通知
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from uvix_monitor import fetch_uvix_data, ChanLunAnalyzer, send_alert


def generate_premarket_analysis():
    """生成盘前分析报告"""
    
    print("\n" + "="*70)
    print("UVIX 盘前预警 - Pre-market Alert")
    print("="*70)
    print(f"\n📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST")
    print(f"⏰ 距离开盘：30 分钟")
    
    # 获取数据
    print(f"\n[1] 获取隔夜数据...")
    
    series_30m = fetch_uvix_data('UVIX', count=200, timeframe='30m')
    series_5m = fetch_uvix_data('UVIX', count=200, timeframe='5m')
    
    print(f"    ✓ 30 分钟 K 线：{len(series_30m.klines)} 根")
    print(f"    ✓ 5 分钟 K 线：{len(series_5m.klines)} 根")
    
    # 分析
    print(f"\n[2] 缠论分析...")
    
    analyzer = ChanLunAnalyzer({
        'macd_params': {'fast': 12, 'slow': 26, 'signal': 9}
    })
    
    result_30m = analyzer.analyze(series_30m)
    result_5m = analyzer.analyze(series_5m)
    
    # 提取关键信息
    current_price = series_30m.klines[-1].close
    prev_close = series_30m.klines[-2].close if len(series_30m.klines) > 1 else current_price
    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    # 隔夜最高/最低
    overnight_high = max(k.high for k in series_5m.klines)
    overnight_low = min(k.low for k in series_5m.klines)
    
    # 买卖点检测
    bsp_30m = result_30m['analysis'].get('buy_sell_points', [])
    bsp_5m = result_5m['analysis'].get('buy_sell_points', [])
    
    divergence_30m = result_30m['analysis'].get('divergence', {})
    divergence_5m = result_5m['analysis'].get('divergence', {})
    
    # 生成报告
    print(f"\n[3] 生成盘前报告...")
    
    report = f"""
【UVIX 盘前预警】

📊 当前价格：${current_price:.2f}
📈 涨跌：{price_change:+.2f} ({price_change_pct:+.2f}%)

【隔夜走势】
🌙 最高：${overnight_high:.2f}
🌙 最低：${overnight_low:.2f}
📏 振幅：${overnight_high - overnight_low:.2f} ({(overnight_high - overnight_low) / overnight_low * 100:.2f}%)

【缠论分析】
30 分钟级别：{result_30m['operation_suggestion']['action']}
  • 分型：{result_30m['analysis']['fractals']['top']}顶 {result_30m['analysis']['fractals']['bottom']}底
  • 笔：{result_30m['analysis']['pens']['up']}向上 {result_30m['analysis']['pens']['down']}向下
  • 背驰：{'⚠️ 检测到' if divergence_30m.get('detected') else '✓ 无'}

5 分钟级别：{result_5m['operation_suggestion']['action']}
  • 分型：{result_5m['analysis']['fractals']['top']}顶 {result_5m['analysis']['fractals']['bottom']}底
  • 笔：{result_5m['analysis']['pens']['up']}向上 {result_5m['analysis']['pens']['down']}向下
  • 背驰：{'⚠️ 检测到' if divergence_5m.get('detected') else '✓ 无'}

【买卖点信号】
30 分钟：{'🟢' + bsp_30m[0]['type'] if bsp_30m else '⚪ 无'}
5 分钟：{'🟢' + bsp_5m[0]['type'] if bsp_5m else '⚪ 无'}

【今日策略】
{generate_strategy(result_30m, result_5m, current_price, overnight_high, overnight_low)}

⏰ 距离开盘：30 分钟
📊 监控已就绪
"""
    
    # 发送 Telegram
    print(f"\n[4] 发送预警通知...")
    send_alert(report, channels=['telegram', 'console'])
    
    # 保存报告
    report_file = Path(__file__).parent.parent / 'logs' / 'premarket_alerts.log'
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Pre-market Alert: {datetime.now().isoformat()}\n")
        f.write(f"Price: ${current_price:.2f}\n")
        f.write(f"Change: {price_change:+.2f} ({price_change_pct:+.2f}%)\n")
        f.write(f"Strategy: {result_30m['operation_suggestion']['action']} / {result_5m['operation_suggestion']['action']}\n")
    
    print(f"✓ 盘前预警完成")
    
    return {
        'timestamp': datetime.now().isoformat(),
        'price': current_price,
        'change': price_change,
        'change_pct': price_change_pct,
        'overnight_high': overnight_high,
        'overnight_low': overnight_low,
        'bsp_30m': len(bsp_30m),
        'bsp_5m': len(bsp_5m),
        'divergence_30m': divergence_30m.get('detected', False),
        'divergence_5m': divergence_5m.get('detected', False)
    }


def generate_strategy(result_30m, result_5m, current_price, high, low):
    """生成交易策略建议"""
    
    action_30m = result_30m['operation_suggestion']['action']
    action_5m = result_5m['operation_suggestion']['action']
    
    if action_30m == 'BUY' or action_5m == 'BUY':
        return f"""
🟢 多头策略
• 关注：${low:.2f} 支撑
• 突破：${high:.2f} 可加仓
• 止损：${low * 0.95:.2f} (-5%)
• 目标：${current_price * 1.10:.2f} (+10%)
"""
    elif action_30m == 'SELL' or action_5m == 'SELL':
        return f"""
🔴 空头策略
• 关注：${high:.2f} 阻力
• 跌破：${low:.2f} 可跟进
• 止损：${high * 1.05:.2f} (+5%)
• 目标：${current_price * 0.90:.2f} (-10%)
"""
    else:
        return f"""
⚪ 观望策略
• 等待：方向明确后再介入
• 关注：${low:.2f} - ${high:.2f} 区间
• 突破：向上突破${high:.2f} 看多
• 跌破：向下跌破${low:.2f} 看空
"""


if __name__ == '__main__':
    result = generate_premarket_analysis()
    
    # 输出 JSON 结果
    print(f"\n{'='*70}")
    print(f"JSON 结果:")
    print(f"{'='*70}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
