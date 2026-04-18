# 中枢动量分析模块 - 缠论 v6.0

**版本**: v6.0-beta  
**创建日期**: 2026-04-17  
**状态**: ✅ 开发完成

---

## 📋 概述

中枢动量分析模块是缠论 v6.0 的核心功能之一，用于:

1. **判断趋势方向** - 上涨/下跌/震荡
2. **识别中枢序号** - 第几个中枢
3. **分析动量变化** - 增强/衰减/稳定
4. **评估趋势延续性** - 延续概率/反转风险

---

## 🎯 核心功能

### 1. 趋势方向判断

基于中枢位置移动判断趋势:

```
中枢依次上移 → 上涨趋势
中枢依次下移 → 下跌趋势
中枢重叠/无方向 → 震荡
```

**判断标准**:
- 60% 以上中枢上移 → 上涨
- 60% 以上中枢下移 → 下跌
- 其他 → 震荡

---

### 2. 中枢序号识别

识别当前处于第几个中枢:

| 位置 | 说明 | 操作含义 |
|------|------|---------|
| 第一个中枢前 | 趋势初现 | 观望/轻仓试单 |
| 第一个中枢 | 趋势确认中 | 等待突破 |
| 第一个中枢后 | 趋势延续 | 顺势操作 |
| 第二个中枢 | 趋势加强 | 加仓机会 |
| 第二个中枢后 | 趋势延续 | 持有 |
| 第三个中枢 | 背驰风险区 | 警惕反转 |
| 第三个中枢后 | 高背驰风险 | 准备离场 |
| 中枢延伸 | 级别扩张 | 重新评估 |

---

### 3. 动量变化分析

通过多维度分析动量状态:

**分析维度**:
1. **中枢区间变化** - 区间缩小=动量增强，区间扩大=动量减弱
2. **离开段动量** - 离开段 vs 进入段力度比较
3. **位置移动速度** - 中枢上移/下移的速度

**动量状态**:
- `INCREASING` (增强) - 分数 > 15
- `STABLE` (稳定) - 分数 -15 到 15
- `DECREASING` (衰减) - 分数 < -15

---

### 4. 趋势延续性评估

综合评估趋势延续概率和反转风险:

**影响因素**:
| 因素 | 延续概率影响 | 反转风险影响 |
|------|-------------|-------------|
| 第三中枢后 | -30% | +30% |
| 第一/二中枢后 | +15% | -15% |
| 动量增强 | +20% | -20% |
| 动量衰减 | -20% | +20% |
| 上涨趋势 | +10% | -10% |
| 下跌趋势 | -10% | +10% |
| 中枢延伸 | -15% | +15% |

---

## 📁 文件结构

```
chanlunInvester/
├── python-layer/trading_system/
│   └── center_momentum.py      # 中枢动量分析核心模块
├── scripts/
│   └── center_momentum_analysis.py  # 集成分析脚本
└── docs/
    └── CENTER_MOMENTUM_MODULE.md    # 本文档
```

---

## 🚀 使用方法

### 方法 1: 命令行分析

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester

# 分析单个标的
python3 scripts/center_momentum_analysis.py EOSE

# 分析多个标的
python3 scripts/center_momentum_analysis.py SMR
python3 scripts/center_momentum_analysis.py BABA
```

### 方法 2: Python API

```python
import sys
sys.path.insert(0, '/home/wei/.openclaw/workspace/chanlunInvester/python-layer')

from trading_system.center_momentum import (
    CenterMomentumAnalyzer,
    format_center_analysis_report
)
from trading_system.center import CenterDetector

# 1. 检测中枢
detector = CenterDetector(min_segments=3)
centers = detector.detect_centers(segments)

# 2. 执行中枢动量分析
analyzer = CenterMomentumAnalyzer(level="1d")
result = analyzer.analyze(centers, segments, current_price)

# 3. 格式化报告
report = format_center_analysis_report(result)
print(report)
```

### 方法 3: 集成到 monitor_all.py

在 `monitor_all.py` 中添加中枢动量分析:

```python
from python_layer.trading_system.center_momentum import CenterMomentumAnalyzer

# 在现有分析流程中添加
def analyze_with_center_momentum(symbol, data, price):
    # 1. 计算缠论结构
    fractals = calculate_fractals(data)
    pivots = calculate_pivots(data, fractals)
    segments = calculate_segments(pivots)
    
    # 2. 检测中枢
    detector = CenterDetector()
    centers = detector.detect_centers(segments)
    
    # 3. 中枢动量分析
    analyzer = CenterMomentumAnalyzer(level="1d")
    result = analyzer.analyze(centers, segments, price)
    
    return {
        'bsp': detect_buy_sell_points(...),
        'center_momentum': result
    }
```

---

## 📊 输出示例

### 单级别分析报告

```
======================================================================
📊 中枢动量分析报告 - 1d
======================================================================
当前价格：$115.00

【趋势判断】
  方向：上涨
  阶段：第二中枢阶段 - 趋势确认，动量衰减，上涨趋势
  位置：第二个中枢后

【动量分析】
  状态：衰减
  分数：-20.0

【中枢序列】
  第 1 中枢：ZG=106.00, ZD=104.00, 区间=2.00, 区间变化=+0.0%, 动量变化=-75.0%
  第 2 中枢：ZG=110.00, ZD=108.00, 区间=2.00, 区间变化=+0.0%, 动量变化=-75.0%

【趋势评估】
  延续概率：55.0%
  反转风险：45.0%

【操作建议】
  建议：持有观望
  置信度：55.0%

======================================================================
```

### 多级别分析报告

```
======================================================================
📊 缠论 v6.0 - 中枢动量多级别分析报告
生成时间：2026-04-17 07:23:17 EDT
======================================================================

【EOSE - Eos Energy Enterprises】
当前价格：$7.15

  日线级别:
    中枢数量：2
    趋势方向：上涨
    动量状态：衰减 (-15.0)
    当前位置：第二个中枢后
    趋势阶段：第二中枢阶段 - 趋势确认，动量衰减，上涨趋势
    延续概率：55.0%
    反转风险：45.0%
    操作建议：持有观望 (置信度：55.0%)

  30 分钟级别:
    中枢数量：3
    趋势方向：震荡
    动量状态：稳定 (5.0)
    当前位置：第三个中枢
    趋势阶段：第三中枢阶段 - 警惕背驰，震荡整理
    延续概率：40.0%
    反转风险：60.0%
    操作建议：警惕背驰/准备离场 (置信度：65.0%)

----------------------------------------------------------------------
```

---

## 🎯 实战应用

### 场景 1: 趋势跟踪

```
日线：第一中枢后，动量增强，延续概率 75%
30m: 第二中枢，动量稳定

操作：顺势做多，仓位 40-50%
止损：第一中枢下沿
目标：第三中枢形成
```

### 场景 2: 背驰预警

```
日线：第三中枢后，动量衰减，反转风险 70%
30m: 第三中枢，动量明显衰减

操作：减仓/止盈，准备离场
止损：移动至成本价
警惕：趋势反转
```

### 场景 3: 震荡市

```
日线：中枢延伸，趋势不明
30m: 多个中枢重叠，方向不明

操作：区间操作/观望
仓位：20-30%
策略：高抛低吸
```

---

## 📈 与 v5.3 对比

| 功能 | v5.3 | v6.0 | 提升 |
|------|------|------|------|
| 中枢检测 | ✅ 基础 | ✅ 增强 | 动量分析 |
| 趋势判断 | ❌ 无 | ✅ 自动 | 新增 |
| 动量评估 | ❌ 无 | ✅ 多维度 | 新增 |
| 背驰预警 | ✅ 价格背驰 | ✅ 中枢背驰 | 更准确 |
| 延续性评估 | ❌ 无 | ✅ 概率化 | 新增 |

---

## ⚙️ 配置参数

### CenterMomentumAnalyzer

```python
analyzer = CenterMomentumAnalyzer(
    level="1d"  # 分析级别：1w/1d/30m/5m
)
```

### 中枢检测

```python
detector = CenterDetector(
    min_segments=3  # 形成中枢的最少线段数
)
```

### 动量阈值

```python
# 动量状态判断阈值
INCREASING_THRESHOLD = 15   # > 15 为增强
DECREASING_THRESHOLD = -15  # < -15 为衰减
```

---

## 🔍 故障排除

### 问题 1: 无中枢检测

**原因**: 数据不足或线段太少

**解决**:
```
- 确保至少有 30 根 K 线
- 确保至少有 3 个线段
- 检查分型计算是否正确
```

### 问题 2: 趋势判断不准确

**原因**: 中枢数量太少

**解决**:
```
- 至少需要 2 个中枢才能判断趋势
- 使用更大级别 (如日线) 分析
- 结合多级别共振判断
```

### 问题 3: 动量分数异常

**原因**: 数据异常或计算错误

**解决**:
```
- 检查 K 线数据质量
- 检查线段计算
- 手动验证中枢区间
```

---

## 📚 相关文档

- [缠论中枢理论基础](docs/CHANLUN_MONITOR_DEV_PLAN.md)
- [中枢检测方法](python-layer/trading_system/center.py)
- [监控系统使用说明](MONITOR_USAGE.md)
- [v6.0 开发计划](CHANLUN_V2_DETAILED_PLAN.md)

---

## 🎓 缠论理论基础

### 中枢定义 (第 18 课)

> 某级别走势类型中，被至少三个连续次级别走势类型所重叠的部分

### 中枢延伸 (第 20 课)

> 中枢形成后，后续走势继续在中枢区间内震荡，超过 9 段则级别扩张

### 趋势背驰 (第 67 课)

> 第三个中枢后，趋势背驰概率显著增加

### 中枢与买卖点

- **第一类买卖点**: 趋势背驰点 (通常在第三中枢后)
- **第二类买卖点**: 第一类买卖点后的回调/反弹
- **第三类买卖点**: 中枢突破后的回抽确认

---

**文档版本**: v6.0-beta  
**最后更新**: 2026-04-17  
**维护者**: ChanLun AI Agent
