#!/usr/bin/env python3
"""
多级别背驰确认系统 - 快速测试脚本
测试当前市场的背驰确认状态
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python-layer"))
sys.path.insert(0, str(Path(__file__).parent))

from multi_level_confirmation import (
    MultiLevelMonitor, 
    ConfirmationManager,
    ConfirmationStage,
    SYMBOLS,
    LEVEL_CONFIG
)


def print_current_states():
    """打印当前所有确认状态"""
    manager = ConfirmationManager()
    
    print("\n" + "="*70)
    print("📋 当前背驰确认状态")
    print("="*70 + "\n")
    
    if not manager.states:
        print("暂无活跃的背驰确认状态")
        return
    
    stage_emoji = {
        ConfirmationStage.WAITING: "⚪",
        ConfirmationStage.PARENT_DIVERGENCE: "⚠️",
        ConfirmationStage.CHILD_BSP1: "🔍",
        ConfirmationStage.CHILD_BSP2: "✅",
        ConfirmationStage.CONFIRMED: "🎯",
        ConfirmationStage.FAILED: "❌",
    }
    
    for key, state in sorted(manager.states.items()):
        emoji = stage_emoji.get(state.stage, "❓")
        print(f"{emoji} {key}")
        print(f"   阶段：{state.stage.value}")
        print(f"   大级别：{state.parent_level}")
        print(f"   次级别：{state.child_level}")
        
        if state.parent_divergence:
            div = state.parent_divergence
            signal = "🟢 买" if div.signal_type == 'buy' else "🔴 卖"
            print(f"   大级别背驰：{signal} @ ${div.price:.2f} (强度:{div.strength:.2f})")
        
        if state.child_bsp1:
            bsp1 = state.child_bsp1
            signal = "🟢 买" if bsp1.signal_type == 'buy' else "🔴 卖"
            print(f"   次级别 BSP1: {signal} @ ${bsp1.price:.2f} (强度:{bsp1.strength:.2f})")
        
        if state.child_bsp2:
            bsp2 = state.child_bsp2
            print(f"   次级别 BSP2: 确认 @ ${bsp2['price']:.2f}")
        
        if state.confirmed_price:
            print(f"   ✅ 确认价格：${state.confirmed_price:.2f}")
        
        if state.notes:
            print(f"   📝 备注：{state.notes}")
        
        print()


def test_single_symbol(symbol: str):
    """测试单个标的"""
    print(f"\n{'='*70}")
    print(f"🔍 测试标的：{symbol}")
    print(f"{'='*70}\n")
    
    monitor = MultiLevelMonitor()
    
    # 获取监控配置
    symbol_config = next((s for s in SYMBOLS if s['symbol'] == symbol), None)
    if not symbol_config:
        print(f"❌ {symbol} 不在监控列表中")
        return
    
    # 分析所有级别
    results = {}
    for level in symbol_config['levels']:
        series = monitor.detector.fetch_data(symbol, level)
        if series:
            results[level] = monitor.detector.analyze_level(series)
            
            div = results[level]['divergence']
            if div:
                signal = "🟢 买" if div.signal_type == 'buy' else "🔴 卖"
                print(f"  {level}: {signal}背驰 @ ${div.price:.2f} (强度:{div.strength:.2f})")
            else:
                print(f"  {level}: 无背驰")
    
    # 检查确认状态
    monitor._check_confirmation(symbol, results)


def show_help():
    """显示帮助"""
    print("""
多级别背驰确认系统 - 快速测试

用法:
  python scripts/test_confirmation.py              # 查看所有状态
  python scripts/test_confirmation.py --symbol UVIX  # 测试单个标的
  python scripts/test_confirmation.py --help       # 显示帮助

示例:
  查看当前所有背驰确认状态
  测试 UVIX 的多级别背驰情况
""")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            show_help()
        elif sys.argv[1] == '--symbol':
            if len(sys.argv) > 2:
                test_single_symbol(sys.argv[2])
            else:
                print("❌ 请指定标的代码")
        else:
            print(f"❌ 未知参数：{sys.argv[1]}")
            show_help()
    else:
        print_current_states()
        
        print("\n" + "="*70)
        print("🔄 运行完整监控...")
        print("="*70)
        
        monitor = MultiLevelMonitor()
        monitor.run()
