#!/usr/bin/env python3
"""
EOSE (Eos Energy Enterprises) 缠论监控测试脚本
测试 30 分钟 + 日线双级别数据获取和分析
"""

import sys
sys.path.insert(0, '/home/wei/.openclaw/workspace/chanlunInvester')

from monitor_all import fetch_yahoo_data, analyze_symbol

def test_eose_monitor():
    """Test EOSE monitoring setup"""
    print("=" * 60)
    print("EOSE (Eos Energy Enterprises) 缠论监控测试")
    print("=" * 60)
    
    # Test 30-minute data
    print("\n📊 测试 30 分钟级别数据...")
    try:
        data_30m = fetch_yahoo_data('EOSE', timeframe='30m', count=100)
        if data_30m is not None and len(data_30m) > 0:
            print(f"✅ 30m 数据获取成功：{len(data_30m)} 条 K 线")
            print(f"   最新价格：${data_30m['close'].iloc[-1]:.2f}")
            print(f"   时间范围：{data_30m.index[0]} 至 {data_30m.index[-1]}")
        else:
            print("⚠️ 30m 数据为空或获取失败")
    except Exception as e:
        print(f"❌ 30m 数据获取失败：{e}")
    
    # Test daily data
    print("\n📊 测试日线级别数据...")
    try:
        data_1d = fetch_yahoo_data('EOSE', timeframe='1d', count=100)
        if data_1d is not None and len(data_1d) > 0:
            print(f"✅ 1d 数据获取成功：{len(data_1d)} 条 K 线")
            print(f"   最新价格：${data_1d['close'].iloc[-1]:.2f}")
            print(f"   时间范围：{data_1d.index[0]} 至 {data_1d.index[-1]}")
        else:
            print("⚠️ 1d 数据为空或获取失败")
    except Exception as e:
        print(f"❌ 1d 数据获取失败：{e}")
    
    # Test full symbol analysis
    print("\n🔍 测试 EOSE 完整分析...")
    try:
        symbol_config = {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['30m', '1d']}
        result = analyze_symbol(symbol_config)
        if result:
            print(f"✅ EOSE 分析完成")
            print(f"   分析级别：{result.get('levels_analyzed', 'N/A')}")
        else:
            print("⚠️ EOSE 分析结果为空")
    except Exception as e:
        print(f"❌ EOSE 分析失败：{e}")
    
    print("\n" + "=" * 60)
    print("✅ EOSE 监控测试完成")
    print("=" * 60)
    print("\n📋 配置摘要:")
    print("   标的：EOSE (Eos Energy Enterprises, Inc.)")
    print("   交易所：NASDAQ")
    print("   监控级别：30m + 1d 双级别联动")
    print("   警报渠道：Telegram (Chat ID: 8365377574)")
    print("\n📝 下一步:")
    print("   1. 运行 monitor_all.py 开始实时监控")
    print("   2. 查看 alerts.log 监控警报输出")
    print("   3. 查看 EOSE_MONITOR_SETUP.md 详细文档")

if __name__ == '__main__':
    test_eose_monitor()
