# 趋势起势检测器 - 用户手册

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_start_detector.py`

---

## 📖 功能概述

趋势起势检测器用于**提前捕捉趋势起势**，领先于传统 buy1/buy2 信号。

### 核心功能

1. **中枢突破检测** (25% 权重)
   - 检测价格突破中枢上沿
   - 要求突破有力度 (5 日涨幅≥3%)

2. **动量加速检测** (20% 权重)
   - 检测 MACD 黄白线快速上升
   - 要求金叉状态

3. **量能放大检测** (20% 权重)
   - 检测成交量放大
   - 要求成交量>20 日均量 150%

4. **小级别共振检测** (15% 权重)
   - 检测多级别 MACD 同向
   - 要求大小级别都金叉

5. **均线多头检测** (10% 权重)
   - 检测均线多头排列
   - 要求短期>中期>长期

### 输出信号

| 概率范围 | 操作建议 | 建议仓位 |
|---------|---------|---------|
| ≥70% | STRONG_ENTRY | 70% |
| ≥50% | ENTRY | 50% |
| ≥30% | WATCH | 30% |
| <30% | HOLD | 10% |

---

## 🔧 使用方法

### 基础用法

```python
from scripts.trend_start_detector import TrendStartDetector

# 创建检测器
detector = TrendStartDetector()

# 检测信号
signal = detector.detect(series, 'AAPL', '1d')

# 格式化输出
print(detector.format_signal(signal))
```

### 完整示例

```python
import yfinance as yf
from trading_system.kline import Kline, KlineSeries
from scripts.trend_start_detector import TrendStartDetector

# 1. 获取数据
data = yf.Ticker('AAPL').history(period='60d', interval='1d')

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

series = KlineSeries(klines=klines, symbol='AAPL', timeframe='1d')

# 3. 检测信号
detector = TrendStartDetector()
signal = detector.detect(series, 'AAPL', '1d')

# 4. 输出结果
print(detector.format_signal(signal))
```

### 输出示例

```
======================================================================
📈 趋势起势信号 - AAPL (1d)
======================================================================
时间：2026-04-16 18:30:00

起势概率：75%
置信度：  85%

触发信号 (4 个):
   ✅ center_breakout
   ✅ momentum_acceleration
   ✅ volume_expand
   ✅ ma_bullish

操作建议：🚀 STRONG_ENTRY
建议仓位：70%

突破价格：$175.50
中枢上沿：$170.00
中枢下沿：$165.00
成交量比：2.50x
止损位：  $161.70
止盈位：  $181.00
======================================================================
```

---

## 📋 参数说明

### TrendStartDetector 参数

无构造函数参数，使用默认配置。

### detect() 方法参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `series` | KlineSeries | K 线序列 | ✅ |
| `symbol` | str | 股票代码 | ✅ |
| `level` | str | 级别 (1d, 30m, 5m) | ✅ |
| `small_level_series` | KlineSeries | 小级别 K 线序列 | ❌ |

### 配置参数 (可修改)

在 `trend_start_detector.py` 中：

```python
# 权重配置
self.weights = {
    'center_breakout': 0.25,
    'momentum_acceleration': 0.20,
    'volume_expand': 0.20,
    'small_level_resonance': 0.15,
    'ma_bullish': 0.10,
}

# 阈值配置
self.thresholds = {
    'breakout_tolerance': 0.01,  # 突破容差 1%
    'volume_expand_ratio': 1.5,   # 放量 50%
    'price_change_5d': 0.03,      # 5 日涨幅 3%
    'dif_slope': 0.5,             # DIF 斜率阈值
    'dea_slope': 0.3,             # DEA 斜率阈值
}
```

---

## 📊 输出说明

### TrendStartSignal 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `symbol` | str | 股票代码 |
| `level` | str | 级别 |
| `start_probability` | float | 起势概率 (0-1) |
| `confidence` | float | 置信度 (0-1) |
| `signals` | List[str] | 触发信号列表 |
| `action` | str | 操作建议 |
| `position_ratio` | float | 建议仓位 (0-1) |
| `breakout_price` | float | 突破价格 |
| `center_zg` | float | 中枢上沿 |
| `center_zd` | float | 中枢下沿 |
| `volume_ratio` | float | 成交量比率 |
| `stop_loss` | float | 止损位 |
| `take_profit` | float | 止盈位 |

### 操作建议说明

| 建议 | 含义 | 适用场景 |
|------|------|---------|
| **STRONG_ENTRY** | 强烈入场 | 概率≥70%，多信号共振 |
| **ENTRY** | 入场 | 概率≥50%，信号明确 |
| **WATCH** | 观察 | 概率≥30%，信号不明确 |
| **HOLD** | 持有/观望 | 概率<30%，无信号 |

---

## ⚠️ 注意事项

### 1. 数据要求

- **最少 K 线数**: 60 根 (用于中枢检测)
- **推荐 K 线数**: 100+ 根
- **数据质量**: 使用调整收盘价 (Adj Close)

### 2. 中枢检测限制

- 中枢形成需要至少 3 个线段
- 每线段需要至少 3 笔
- 低波动股票可能无法形成中枢

### 3. 信号解释

- **概率<30%**: 无明确信号，观望
- **概率 30-50%**: 弱信号，谨慎观察
- **概率 50-70%**: 中等信号，可轻仓
- **概率≥70%**: 强信号，可重仓

### 4. 止损止盈

- **止损位**: 中枢下沿 -2%
- **止盈位**: 当前价 + 中枢区间
- 建议根据实际波动率调整

---

## 🔍 故障排除

### 问题 1: 无信号产生

**可能原因**:
- 数据不足 (少于 60 根 K 线)
- 中枢未形成
- 市场处于震荡期

**解决方案**:
- 增加历史数据
- 换用高波动股票
- 等待市场趋势明确

### 问题 2: 信号过多

**可能原因**:
- 阈值设置过低
- 股票波动过大

**解决方案**:
- 调整阈值配置
- 增加信号过滤条件

### 问题 3: 胜率偏低

**可能原因**:
- 市场处于震荡期
- 止损设置不合理

**解决方案**:
- 增加市场状态判断
- 优化止损策略

---

## 📞 快速参考

### 一行代码检测

```python
signal = TrendStartDetector().detect(series, 'AAPL', '1d')
```

### 批量检测

```python
detector = TrendStartDetector()
for symbol in ['AAPL', 'TSLA', 'NVDA']:
    signal = detector.detect(series, symbol, '1d')
    if signal.start_probability >= 0.5:
        print(f"{symbol}: {signal.action}")
```

### 回测

```bash
python scripts/backtest_trend_start.py
```

---

## 📚 相关文档

- `CHANLUN_V2_DETAILED_PLAN.md` - v6.0 开发计划
- `PHASE1_VERIFICATION_CHECKLIST.md` - Phase 1 验收清单
- `BACKTEST_RESULTS_PHASE1_2026-04-16.md` - 回测结果报告

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 18:30 EDT  
**维护者**: ChanLun AI Agent
