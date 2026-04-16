# 趋势反转预警器 - 用户手册

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_reversal_warning.py`

---

## 📖 功能概述

趋势反转预警器用于**多信号共振预警趋势反转**，提前 3-5 天离场保住利润。

### 核心功能

1. **多级别背驰共振检测** (35% 权重)
   - 日线 +30m+5m 同时背驰
   - 至少 2 个级别背驰触发

2. **第三类买卖点失败检测** (20% 权重)
   - buy3/sell3 后迅速反转
   - MACD 转正/负信号

3. **中枢升级完成检测** (15% 权重)
   - 小中枢升级为大中枢
   - 中枢区间持续扩大

4. **先行指标背离检测** (15% 权重)
   - MACD/成交量先行背离
   - 价格新高但指标未新高

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
from scripts.trend_reversal_warning import TrendReversalWarner

# 创建预警器
warner = TrendReversalWarner()

# 预警信号
signal = warner.warn(series, 'TSLA', '1d')

# 格式化输出
print(warner.format_signal(signal))
```

### 完整示例

```python
import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from scripts.trend_reversal_warning import TrendReversalWarner

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

# 3. 预警信号
warner = TrendReversalWarner()
signal = warner.warn(series, 'TSLA', '1d')

# 4. 输出结果
print(warner.format_signal(signal))
```

### 输出示例

```
======================================================================
🔄 趋势反转预警 - TSLA (1d)
======================================================================
时间：2026-04-16 19:30:00

反转概率：75%
置信度：  85%
预警级别：🚨 CRITICAL

触发信号 (3 个):
   ✅ multi_level_divergence
   ✅ bsp3_failure
   ✅ leading_indicator_divergence

多级别背驰：✅ 是
第三类买卖点失败：✅ 是
先行指标背离：✅ 是
预估反转：3 天内
利润保住率：90%
======================================================================
```

---

## 📋 参数说明

### TrendReversalWarner 参数

无构造函数参数，使用默认配置。

### warn() 方法参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `series` | KlineSeries | K 线序列 | ✅ |
| `symbol` | str | 股票代码 | ✅ |
| `level` | str | 级别 (1d, 30m, 5m) | ✅ |
| `small_level_series` | KlineSeries | 小级别 K 线序列 | ❌ |
| `large_level_series` | KlineSeries | 大级别 K 线序列 | ❌ |

### 配置参数 (可修改)

在 `trend_reversal_warning.py` 中：

```python
# 权重配置
self.weights = {
    'multi_level_divergence': 0.35,
    'bsp3_failure': 0.20,
    'center_upgrade': 0.15,
    'leading_indicator_divergence': 0.15,
}

# 阈值配置
self.thresholds = {
    'divergence_threshold': 0.7,
    'bsp3_failure_threshold': 0.05,
    'confidence_bonus': 0.15,
}
```

---

## 📊 输出说明

### TrendReversalSignal 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `symbol` | str | 股票代码 |
| `level` | str | 级别 |
| `reversal_probability` | float | 反转概率 (0-1) |
| `confidence` | float | 置信度 (0-1) |
| `signals` | List[str] | 触发信号列表 |
| `warning_level` | str | 预警级别 |
| `multi_level_divergence` | bool | 多级别背驰 |
| `bsp3_failure` | bool | 第三类买卖点失败 |
| `center_upgrade` | bool | 中枢升级完成 |
| `leading_indicator_divergence` | bool | 先行指标背离 |
| `days_to_reversal` | int | 预估反转天数 |
| `profit_preservation_rate` | float | 利润保住率 |

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

- **最少 K 线数**: 60 根
- **推荐 K 线数**: 100+ 根
- **中枢数量**: 至少 2 个中枢

### 2. 中枢检测限制

- 中枢形成需要至少 2 个线段
- 每线段需要至少 2 笔
- 低波动股票可能无法形成足够中枢

### 3. 预警解释

- **概率<30%**: 无明确反转，正常持有
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
- 等待趋势反转

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

### 一行代码预警

```python
signal = TrendReversalWarner().warn(series, 'TSLA', '1d')
```

### 批量预警

```python
warner = TrendReversalWarner()
for symbol in ['TSLA', 'NVDA', 'AMD']:
    signal = warner.warn(series, symbol, '1d')
    if signal.warning_level in ['HIGH', 'CRITICAL']:
        print(f"{symbol}: {signal.warning_level}")
```

### 回测

```bash
python scripts/backtest_trend_reversal.py
```

---

## 📚 相关文档

- `CHANLUN_V2_DETAILED_PLAN.md` - v2.0 开发计划
- `PHASE3_PLAN.md` - Phase 3 开发计划
- `PHASE3_ACCEPTANCE_REPORT.md` - Phase 3 验收报告

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 19:30 EDT  
**维护者**: ChanLun AI Agent
