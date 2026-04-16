# 趋势反转预警器 - API 文档

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_reversal_warning.py`

---

## 📦 模块概览

趋势反转预警器模块提供趋势反转的自动预警功能。

### 核心类

| 类 | 用途 |
|------|------|
| `TrendReversalWarner` | 趋势反转预警器 |
| `TrendReversalSignal` | 反转信号数据类 |

### 依赖模块

```python
from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.center import CenterDetector
from trading_system.indicators import MACDIndicator
```

---

## 🔧 TrendReversalWarner

### 构造函数

```python
def __init__(self)
```

**参数**: 无

**返回值**: TrendReversalWarner 实例

**示例**:
```python
warner = TrendReversalWarner()
```

---

### warn() 方法

```python
def warn(self, 
         series: KlineSeries, 
         symbol: str, 
         level: str,
         small_level_series: Optional[KlineSeries] = None,
         large_level_series: Optional[KlineSeries] = None) -> TrendReversalSignal
```

**功能**: 预警趋势反转

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `series` | KlineSeries | - | K 线序列 (当前级别) |
| `symbol` | str | - | 股票代码 |
| `level` | str | - | 级别 (1d, 30m, 5m) |
| `small_level_series` | KlineSeries | None | 小级别 K 线序列 |
| `large_level_series` | KlineSeries | None | 大级别 K 线序列 |

**返回值**: `TrendReversalSignal` - 反转信号

**示例**:
```python
signal = warner.warn(series, 'TSLA', '1d')
print(signal.reversal_probability)  # 0.75
```

---

### 私有方法

#### _detect_multi_level_divergence()

```python
def _detect_multi_level_divergence(self, 
                                   series: KlineSeries,
                                   small_series: Optional[KlineSeries],
                                   large_series: Optional[KlineSeries]) -> bool
```

**功能**: 多级别背驰共振检测

**参数**:
- `series`: 当前级别 K 线序列
- `small_series`: 小级别 K 线序列
- `large_series`: 大级别 K 线序列

**返回值**: `bool` - 是否共振

**检测逻辑**:
```python
# 至少 2 个级别背驰 = 共振
divergence_count = sum([current_divergence, small_divergence, large_divergence])
return divergence_count >= 2
```

---

#### _detect_bsp3_failure()

```python
def _detect_bsp3_failure(self, 
                         fractals, 
                         pens, 
                         centers, 
                         macd_data) -> bool
```

**功能**: 第三类买卖点失败检测

**参数**:
- `fractals`: 分型列表
- `pens`: 笔列表
- `centers`: 中枢列表
- `macd_data`: MACD 数据

**返回值**: `bool` - 是否失败

**检测逻辑**:
```python
# buy3 失败：突破后迅速跌回
if last_center.zg > prev_center.zg:  # 中枢上移
    if current_price < 0:  # MACD 转负
        return True
```

---

#### _detect_center_upgrade()

```python
def _detect_center_upgrade(self, centers: List) -> bool
```

**功能**: 中枢升级完成检测

**参数**:
- `centers`: 中枢列表

**返回值**: `bool` - 是否升级

**检测逻辑**:
```python
# 中枢区间持续扩大
if ranges[-1] > ranges[-2] > ranges[-3]:
    return True
```

---

#### _detect_leading_indicator_divergence()

```python
def _detect_leading_indicator_divergence(self, 
                                         prices: List[float],
                                         volumes: List[int],
                                         macd_data) -> bool
```

**功能**: 先行指标背离检测

**参数**:
- `prices`: 价格列表
- `volumes`: 成交量列表
- `macd_data`: MACD 数据

**返回值**: `bool` - 是否背离

**检测逻辑**:
```python
# 价格新高但 MACD 和成交量未新高 = 背离
if price_new_high and (macd_not_new_high or volume_decline):
    return True
```

---

#### _calculate_confidence()

```python
def _calculate_confidence(self, 
                          probability: float, 
                          signal_count: int) -> float
```

**功能**: 计算置信度

**参数**:
- `probability`: 反转概率
- `signal_count`: 触发信号数量

**返回值**: `float` - 置信度 (0-1)

**计算逻辑**:
```python
base_confidence = probability
if signal_count >= 4:
    bonus = 0.15
elif signal_count >= 3:
    bonus = 0.10
elif signal_count >= 2:
    bonus = 0.05
else:
    bonus = 0.0

confidence = min(base_confidence + bonus, 1.0)
```

---

#### _get_warning_level()

```python
def _get_warning_level(self, probability: float) -> str
```

**功能**: 获取预警级别

**参数**:
- `probability`: 反转概率

**返回值**: `str` - 预警级别

**映射关系**:
| 概率 | 级别 |
|------|------|
| ≥70% | CRITICAL |
| ≥50% | HIGH |
| ≥30% | MEDIUM |
| <30% | LOW |

---

#### _estimate_days_to_reversal()

```python
def _estimate_days_to_reversal(self, probability: float) -> int
```

**功能**: 预估反转天数

**参数**:
- `probability`: 反转概率

**返回值**: `int` - 预估天数

**映射关系**:
| 概率 | 天数 |
|------|------|
| ≥70% | 3 天 |
| ≥50% | 5 天 |
| ≥30% | 7 天 |
| <30% | 0 天 |

---

#### _estimate_profit_preservation()

```python
def _estimate_profit_preservation(self, probability: float) -> float
```

**功能**: 预估利润保住率

**参数**:
- `probability`: 反转概率

**返回值**: `float` - 保住率 (0-1)

**映射关系**:
| 概率 | 保住率 |
|------|--------|
| ≥70% | 90% |
| ≥50% | 80% |
| ≥30% | 70% |
| <30% | 50% |

---

#### format_signal()

```python
def format_signal(self, signal: TrendReversalSignal) -> str
```

**功能**: 格式化信号输出

**参数**:
- `signal`: TrendReversalSignal 对象

**返回值**: `str` - 格式化的信号文本

**示例输出**:
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

## 📦 TrendReversalSignal

### 数据类属性

```python
@dataclass
class TrendReversalSignal:
    symbol: str                              # 股票代码
    level: str                               # 级别
    timestamp: datetime                      # 时间戳
    reversal_probability: float = 0.0        # 反转概率
    confidence: float = 0.0                  # 置信度
    signals: List[str] = field(default_factory=list)  # 触发信号
    warning_level: str = 'LOW'               # 预警级别
    multi_level_divergence: bool = False     # 多级别背驰
    bsp3_failure: bool = False               # 第三类买卖点失败
    center_upgrade: bool = False             # 中枢升级完成
    leading_indicator_divergence: bool = False  # 先行指标背离
    days_to_reversal: int = 0                # 预估反转天数
    profit_preservation_rate: float = 0.0    # 利润保住率
```

---

## 🔍 使用示例

### 示例 1: 基础预警

```python
from scripts.trend_reversal_warning import TrendReversalWarner

warner = TrendReversalWarner()
signal = warner.warn(series, 'TSLA', '1d')

if signal.warning_level in ['HIGH', 'CRITICAL']:
    print(f"预警：{signal.warning_level}")
    print(f"预估反转：{signal.days_to_reversal} 天内")
```

---

### 示例 2: 批量预警

```python
warner = TrendReversalWarner()
symbols = ['TSLA', 'NVDA', 'AMD']

for symbol in symbols:
    signal = warner.warn(series, symbol, '1d')
    if signal.reversal_probability >= 0.5:
        print(f"🔴 {symbol}: 反转预警")
```

---

### 示例 3: 带多级别数据

```python
# 获取三个级别数据
series_1d = get_series('TSLA', '1d')
series_30m = get_series('TSLA', '30m')
series_5m = get_series('TSLA', '5m')

warner = TrendReversalWarner()
signal = warner.warn(series_1d, 'TSLA', '1d', series_30m, series_5m)

if signal.multi_level_divergence:
    print(f"多级别背驰：{signal.warning_level}")
```

---

### 示例 4: 回测循环

```python
results = []
for i in range(60, len(series.klines)):
    partial_series = KlineSeries(klines=series.klines[:i+1])
    signal = warner.warn(partial_series, 'TSLA', '1d')
    
    if signal.warning_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
        results.append({
            'date': signal.timestamp,
            'probability': signal.reversal_probability,
            'warning_level': signal.warning_level
        })
```

---

## ⚠️ 注意事项

### 1. 数据要求

- 最少 60 根 K 线
- 推荐 100+ 根 K 线
- 至少 2 个中枢

### 2. 性能考虑

- 单次预警时间：~100ms
- 适合实时预警
- 回测时建议批量处理

### 3. 异常处理

```python
try:
    signal = warner.warn(series, 'TSLA', '1d')
except Exception as e:
    print(f"预警失败：{e}")
```

---

## 📚 相关文档

- `TREND_REVERSAL_USER_MANUAL.md` - 用户手册
- `PHASE3_ACCEPTANCE_REPORT.md` - Phase 3 验收报告
- `CHANLUN_V2_DETAILED_PLAN.md` - 开发计划

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 19:30 EDT  
**维护者**: ChanLun AI Agent
