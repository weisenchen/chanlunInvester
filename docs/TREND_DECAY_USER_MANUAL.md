# 趋势衰减监测器 - 用户手册

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_decay_monitor.py`

---

## 📖 功能概述

趋势衰减监测器用于**实时监测趋势衰减**，提前 3-5 天预警趋势反转。

### 核心功能

1. **力度递减检测** (30% 权重)
   - 检测离开中枢的线段力度减弱
   - 力度下降 30% 触发预警

2. **中枢扩大检测** (20% 权重)
   - 检测中枢区间变大
   - 中枢扩大 50% 触发预警

3. **时间延长检测** (20% 权重)
   - 检测中枢形成时间变长
   - 时间延长 50% 触发预警

4. **量价背离检测** (15% 权重)
   - 检测价格上涨但成交量萎缩
   - 量价背离触发预警

5. **多级别背离检测** (15% 权重)
   - 检测大级别涨小级别跌
   - 多级别背离触发预警

### 预警级别

| 概率范围 | 预警级别 | 图标 | 含义 |
|---------|---------|------|------|
| ≥70% | CRITICAL | 🚨 | 严重预警 (3 天内反转) |
| ≥50% | HIGH | 🔴 | 高级预警 (5 天内反转) |
| ≥30% | MEDIUM | 🟡 | 中级预警 (7 天内反转) |
| <30% | LOW | 🟢 | 低级预警 (无明确反转) |

---

## 🔧 使用方法

### 基础用法

```python
from scripts.trend_decay_monitor import TrendDecayMonitor

# 创建监测器
monitor = TrendDecayMonitor()

# 监测信号
signal = monitor.monitor(series, 'AAPL', '1d')

# 格式化输出
print(monitor.format_signal(signal))
```

### 完整示例

```python
import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from scripts.trend_decay_monitor import TrendDecayMonitor

# 1. 获取数据
data = yf.Ticker('TSLA').history(period='60d', interval='1d')

# 2. 转换为 Kline 序列
klines = []
for idx, row in data.iterrows():
    kline = Kline(
        timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
        open=float(row['Open']),
        high=float(row['High']),
        low=float(row['Low']),
        close=float(row['Close']),
        volume=int(row.get('Volume', 0))
    )
    klines.append(kline)

series = KlineSeries(klines=klines, symbol='TSLA', timeframe='1d')

# 3. 监测信号
monitor = TrendDecayMonitor()
signal = monitor.monitor(series, 'TSLA', '1d')

# 4. 输出结果
print(monitor.format_signal(signal))
```

### 输出示例

```
======================================================================
📉 趋势衰减预警 - TSLA (1d)
======================================================================
时间：2026-04-16 19:00:00

衰减概率：75%
置信度：  85%
预警级别：🚨 CRITICAL

触发信号 (4 个):
   ✅ strength_decline
   ✅ center_expansion
   ✅ time_extension
   ✅ volume_price_divergence

力度递减：35.0%
中枢扩大：60.0%
时间延长：70.0%
量价背离：✅ 是
预估反转：3 天内
======================================================================
```

---

## 📋 参数说明

### TrendDecayMonitor 参数

无构造函数参数，使用默认配置。

### monitor() 方法参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `series` | KlineSeries | K 线序列 | ✅ |
| `symbol` | str | 股票代码 | ✅ |
| `level` | str | 级别 (1d, 30m, 5m) | ✅ |
| `small_level_series` | KlineSeries | 小级别 K 线序列 | ❌ |

### 配置参数 (可修改)

在 `trend_decay_monitor.py` 中：

```python
# 权重配置
self.weights = {
    'strength_decline': 0.30,
    'center_expansion': 0.20,
    'time_extension': 0.20,
    'volume_price_divergence': 0.15,
    'multi_level_divergence': 0.15,
}

# 阈值配置
self.thresholds = {
    'strength_decline_rate': -0.3,  # 力度下降 30%
    'center_expansion_rate': 0.5,    # 中枢扩大 50%
    'time_extension_rate': 0.5,      # 时间延长 50%
    'volume_decline_rate': -0.3,     # 成交量萎缩 30%
}
```

---

## 📊 输出说明

### TrendDecaySignal 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `symbol` | str | 股票代码 |
| `level` | str | 级别 |
| `decay_probability` | float | 衰减概率 (0-1) |
| `confidence` | float | 置信度 (0-1) |
| `signals` | List[str] | 触发信号列表 |
| `warning_level` | str | 预警级别 |
| `strength_decline_rate` | float | 力度递减率 |
| `center_expansion_rate` | float | 中枢扩大率 |
| `time_extension_rate` | float | 时间延长率 |
| `volume_price_divergence` | bool | 量价背离 |
| `multi_level_divergence` | bool | 多级别背离 |
| `days_to_reversal` | int | 预估反转天数 |

### 预警级别说明

| 级别 | 含义 | 操作建议 |
|------|------|---------|
| **CRITICAL** | 严重预警 | 立即减仓/离场 |
| **HIGH** | 高级预警 | 准备减仓 |
| **MEDIUM** | 中级预警 | 密切关注 |
| **LOW** | 低级预警 | 正常持有 |

---

## ⚠️ 注意事项

### 1. 数据要求

- **最少 K 线数**: 60 根 (用于中枢检测)
- **推荐 K 线数**: 100+ 根
- **中枢数量**: 至少 2 个中枢

### 2. 中枢检测限制

- 中枢形成需要至少 3 个线段
- 每线段需要至少 3 笔
- 低波动股票可能无法形成足够中枢

### 3. 预警解释

- **概率<30%**: 无明确衰减，正常持有
- **概率 30-50%**: 弱预警，密切关注
- **概率 50-70%**: 中预警，准备减仓
- **概率≥70%**: 强预警，立即减仓

### 4. 预估反转天数

- **CRITICAL**: 3 天内
- **HIGH**: 5 天内
- **MEDIUM**: 7 天内
- **LOW**: 无明确预估

---

## 🔍 故障排除

### 问题 1: 无预警信号

**可能原因**:
- 数据不足 (少于 60 根 K 线)
- 中枢数量不足 (少于 2 个)
- 市场处于强势趋势

**解决方案**:
- 增加历史数据
- 换用高波动股票
- 等待趋势衰减

### 问题 2: 预警过多

**可能原因**:
- 阈值设置过低
- 股票波动过大

**解决方案**:
- 调整阈值配置
- 增加信号过滤条件

### 问题 3: 预警不准确

**可能原因**:
- 市场突发消息
- 参数需要优化

**解决方案**:
- 结合基本面分析
- 优化阈值参数

---

## 📞 快速参考

### 一行代码监测

```python
signal = TrendDecayMonitor().monitor(series, 'TSLA', '1d')
```

### 批量监测

```python
monitor = TrendDecayMonitor()
for symbol in ['TSLA', 'NVDA', 'AMD']:
    signal = monitor.monitor(series, symbol, '1d')
    if signal.warning_level in ['HIGH', 'CRITICAL']:
        print(f"{symbol}: {signal.warning_level}")
```

### 回测

```bash
python scripts/backtest_trend_decay.py
```

---

## 📚 相关文档

- `CHANLUN_V2_DETAILED_PLAN.md` - v6.0 开发计划
- `PHASE2_PLAN.md` - Phase 2 开发计划
- `BACKTEST_RESULTS_PHASE2.md` - 回测结果报告 (待生成)

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 19:00 EDT  
**维护者**: ChanLun AI Agent
