# 成交量 + MACD 组合确认系统

**版本**: v1.0  
**创建日期**: 2026-04-16  
**系统定位**: 增强缠论买卖点的可信度评估

---

## 📊 系统概述

本系统整合**成交量**和**MACD 多维度分析**，为缠论买卖点提供综合可信度评估。

### 核心功能

| 模块 | 功能 | 文件 |
|------|------|------|
| **成交量确认** | 背驰段缩量、确认段放量验证 | `scripts/volume_confirmation.py` |
| **MACD 高级分析** | 零轴位置、柱状图面积、多周期共振 | `scripts/macd_advanced_analysis.py` |
| **综合可信度计算** | 整合多维度，输出综合置信度 | `scripts/confidence_calculator.py` |

---

## 🎯 五步高置信度交易流程

```
┌─────────────────────────────────────────────────────────┐
│           高置信度交易流程 (五步确认法)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1️⃣ 日线背驰出现     →  方向确立 🎯                    │
│       ↓                                                 │
│  2️⃣ 背驰段缩量       →  力量衰竭验证 ✅                │
│       ↓                                                 │
│  3️⃣ 30m 形成买卖点   →  时机确认 ⏰                    │
│       ↓                                                 │
│  4️⃣ 确认时放量       →  新资金入场验证 💰              │
│       ↓                                                 │
│  5️⃣ 多因素共振入场   →  高置信度执行 🚀                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 各维度权重配置

| 维度 | 权重 | 说明 |
|------|------|------|
| **缠论价格结构** | 35% | 基础得分 (分型→笔→线段→中枢→买卖点) |
| **成交量确认** | 15% | 背驰段缩量、确认段放量验证 |
| **MACD 多维度** | 20% | 零轴位置、柱状图面积、交叉分析 |
| **多级别确认** | 15% | 日线 +30m+5m 共振确认 |
| **外部因子** | 15% | 行业趋势、基本面、消息面 |

---

## 🚀 使用方法

### 方法 1: 单独运行测试

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 测试成交量确认模块
python scripts/volume_confirmation.py

# 测试 MACD 高级分析模块
python scripts/macd_advanced_analysis.py

# 测试综合可信度计算器
python scripts/confidence_calculator.py
```

### 方法 2: 在监控系统中调用

```python
from scripts.confidence_calculator import ComprehensiveConfidenceCalculator

# 初始化计算器
calculator = ComprehensiveConfidenceCalculator()

# 准备数据
prices = [...]      # 价格序列
volumes = [...]     # 成交量序列
macd_data = [...]   # MACD 数据

# 计算综合可信度
result = calculator.calculate(
    symbol='SMR',
    signal_type='buy1',
    level='30m',
    price=11.27,
    prices=prices,
    volumes=volumes,
    macd_data=macd_data,
    chanlun_base_confidence=0.65,
    divergence_start_idx=80,
    divergence_end_idx=99,
    multi_level_confirmed=True,
    multi_level_count=2,
    external_factors={
        'industry': 0.70,
        'fundamental': 0.60,
        'sentiment': 0.65,
    }
)

# 输出报告
print(calculator.format_report(result))

# 根据可靠性等级决策
if result.reliability_level.value in ['very_high', 'high']:
    send_telegram_alert(f"✅ 高可靠性信号：{result.confidence_percent}")
elif result.reliability_level.value == 'medium':
    send_telegram_alert(f"⚠️ 中等可靠性信号：{result.confidence_percent}")
else:
    print(f"❌ 低可靠性信号，跳过警报：{result.confidence_percent}")
```

### 方法 3: 单独使用成交量确认

```python
from scripts.volume_confirmation import VolumeConfirmation

confirm = VolumeConfirmation()

# 分析第一类买点 (背驰段缩量验证)
result = confirm.analyze_buy1_divergence(
    prices=prices,
    volumes=volumes,
    divergence_start_idx=80,
    divergence_end_idx=99
)

print(f"背驰段成交量比率：{result.divergence_volume_ratio:.2f}")
print(f"是否缩量：{result.divergence_shrink} ({result.divergence_shrink_percent:.1f}%)")
print(f"背驰强度：{result.divergence_strength}")
print(f"置信度提升：{result.confidence_boost:+.2f}")
print(f"分析：{result.details.get('analysis', 'N/A')}")
```

### 方法 4: 单独使用 MACD 高级分析

```python
from scripts.macd_advanced_analysis import MACDAdvancedAnalyzer

analyzer = MACDAdvancedAnalyzer()

# 零轴分析
zero_axis = analyzer.analyze_zero_axis(macd_data)
print(f"零轴位置：{zero_axis.position}")
print(f"趋势：{zero_axis.trend}")
print(f"分析：{zero_axis.analysis}")

# 柱状图面积背驰分析
area = analyzer.analyze_divergence_area(
    macd_data=macd_data,
    seg1_range=(70, 80),  # 第一段范围
    seg2_range=(90, 99),  # 第二段范围
    is_bull_divergence=True
)
print(f"面积比：{area.area_ratio:.2f}")
print(f"背驰强度：{area.divergence_strength}")
print(f"分析：{area.analysis}")

# 多周期 MACD 共振分析
resonance = analyzer.analyze_multi_level_resonance(
    macd_1d=macd_1d,
    macd_30m=macd_30m,
    macd_5m=macd_5m
)
print(f"共振类型：{resonance.resonance_type}")
print(f"综合置信度：{resonance.confidence:.2f}")
print(f"分析：{resonance.analysis}")
```

---

## 📊 输出示例

### 综合可信度报告

```
============================================================
📊 综合可信度分析报告
============================================================

🎯 信号信息
   标的：SMR
   类型：buy1
   级别：30m
   价格：$11.27

📈 各维度得分
   缠论基础：65.0% (权重 35%)
   成交量：  75.0% (权重 15%)  ← 缩量 28%，力量衰竭
   MACD:     80.0% (权重 20%)  ← 零轴下方 + 柱状图背驰
   多级别：  95.0% (权重 15%)  ← 日线 +30m 双级别共振
   外部因子：65.0% (权重 15%)

═══════════════════════════════════════
综合置信度：76%
可靠性等级：HIGH
操作建议：  BUY
═══════════════════════════════════════

📝 详细分析
   SMR 30m 第一类买点 @ $11.27 | 
   ✅ 成交量确认 (high) | 
   ✅ MACD 背驰 (high) | 
   零轴：below_zero | 
   共振：double_bull | 
   ✅ 多级别确认 (2 级别) | 
   综合：HIGH → BUY

生成时间：2026-04-16 12:49:05
============================================================
```

### Telegram 警报格式

```
🟢 SMR 30m 第一类买点 (背驰)

价格：$11.27
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 1. 日线背驰：$11.18 (04-13)
✅ 2. 背驰缩量：-28% (力量衰竭)
✅ 3. 30m 确认：buy1 形成
⚪ 4. 确认放量：等待中
✅ 5. 多因子共振：HIGH

📊 综合置信度：76%
可靠性等级：HIGH
操作建议：BUY (正常仓位)
止损位：$10.50 (-7%)

MACD:
  - 零轴：下方 (空头市场反弹)
  - 背驰：强 (面积比 0.42)
  - 共振：双级别 (1d+30m)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 投资有风险，决策需谨慎
```

---

## 📋 可靠性等级与操作建议

| 等级 | 置信度 | 操作建议 | 仓位 | 止损 |
|------|--------|----------|------|------|
| **VERY_HIGH** | ≥85% | Strong Buy/Sell | 全仓 | 紧 (3-5%) |
| **HIGH** | 70-84% | Buy/Sell | 正常 | 标准 (5-8%) |
| **MEDIUM** | 55-69% | Light Buy/Sell | 轻仓 | 宽 (8-12%) |
| **LOW** | 40-54% | Observe | 观望 | N/A |
| **VERY_LOW** | <40% | Avoid | 避免 | N/A |

---

## 🔍 成交量验证逻辑

### 第一类买点 (buy1)

| 状态 | 成交量比率 | 置信度提升 | 含义 |
|------|-----------|-----------|------|
| 极强缩量 | <0.5 | +0.25 | 力量衰竭明显 |
| 明显缩量 | 0.5-0.8 | +0.15 | 力量衰竭 |
| 温和缩量 | 0.8-0.9 | +0.05 | 中性信号 |
| 无明显变化 | 0.9-1.1 | 0.00 | 无显著特征 |
| 放量下跌 | >1.2 | -0.15 | 警惕假背驰 |

### 第二类买点 (buy2)

| 状态 | 成交量比率 | 置信度提升 | 含义 |
|------|-----------|-----------|------|
| 极强放量 | >1.5 | +0.25 | 资金大举入场 |
| 明显放量 | 1.3-1.5 | +0.20 | 资金入场 |
| 温和放量 | 1.1-1.3 | +0.10 | 中性信号 |
| 无明显变化 | 0.9-1.1 | +0.05 | 无显著特征 |
| 缩量上涨 | <0.8 | -0.15 | 警惕假突破 |

---

## 📐 MACD 多维度分析

### 零轴位置

| 位置 | 含义 | 置信度提升 |
|------|------|-----------|
| 零轴上方 | 多头市场 | +0.10 (买点) |
| 零轴下方 | 空头市场 | +0.10 (买点反弹) |
| 穿越零轴 | 趋势转换 | +0.05 |

### 柱状图面积背驰

| 面积比 | 背驰强度 | 置信度提升 |
|--------|---------|-----------|
| <0.3 | 极强背驰 | +0.25 |
| 0.3-0.5 | 强背驰 | +0.15 |
| 0.5-0.7 | 中背驰 | +0.05 |
| >0.7 | 弱背驰 | -0.10 |

### 多周期共振

| 共振类型 | 级别数 | 置信度 | 置信度提升 |
|---------|--------|--------|-----------|
| 三周期金叉 | 3 | 0.95 | +0.30 |
| 双周期多头 | 2 | 0.75 | +0.15 |
| 单周期多头 | 1 | 0.55 | +0.05 |

---

## ⚠️ 注意事项

### 1. 数据质量
- 需要至少 30 根 K 线才能进行有效分析
- 成交量数据必须为正数
- MACD 需要至少 26 根 K 线才能计算

### 2. 阈值调整
- 不同股票可能需要不同的成交量阈值
- 高波动股票 (如 IONQ, SMR) 可适当放宽阈值
- 可通过历史回测优化参数

### 3. 信号冲突
- 当成交量和 MACD 信号冲突时，综合置信度会降低
- 建议等待多因子共振后再入场

### 4. 局限性
- 无法预测突发黑天鹅事件
- 财报发布前后信号可能失效
- 高波动股票需谨慎使用

---

## 🔄 整合到现有系统

### 整合到 `monitor_all.py`

在买卖点检测后添加可信度计算：

```python
# 现有代码：检测买卖点
signals = detect_buy_sell_points(series, fractals, pens, segments, macd_data, level)

# 新增：计算综合可信度
from scripts.confidence_calculator import ComprehensiveConfidenceCalculator

calculator = ComprehensiveConfidenceCalculator()

for signal in signals:
    confidence_result = calculator.calculate(
        symbol=symbol,
        signal_type=signal['type'],
        level=level,
        price=signal['price'],
        prices=prices,
        volumes=volumes,
        macd_data=macd_data,
        chanlun_base_confidence=signal.get('confidence', 0.5),
        # ... 其他参数
    )
    
    # 更新信号置信度
    signal['comprehensive_confidence'] = confidence_result.final_confidence
    signal['reliability_level'] = confidence_result.reliability_level.value
    
    # 只推送高可靠性信号
    if confidence_result.reliability_level.value in ['very_high', 'high']:
        send_telegram_alert(format_alert(confidence_result))
```

---

## 📚 相关文档

- [增强置信度系统](ENHANCED_CONFIDENCE_SYSTEM.md)
- [全方位预警系统](COMPREHENSIVE_ALERT_SYSTEM.md)
- [缠论监控系统使用说明](MONITOR_USAGE.md)
- [多级别背驰确认系统](SETUP_MULTI_LEVEL.md)

---

## 🔄 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-04-16 | 初始版本，整合成交量 +MACD 综合可信度 |

---

**创建者**: ChanLun AI Agent  
**状态**: ✅ 已部署，待整合到 `monitor_all.py`  
**测试**: 模块测试通过，待实盘验证
