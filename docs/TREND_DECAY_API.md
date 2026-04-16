# 趋势衰减监测器 - API 文档

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_decay_monitor.py`

---

## 📦 模块概览

趋势衰减监测器模块提供趋势衰减的自动监测功能。

### 核心类

| 类 | 用途 |
|------|------|
| `TrendDecayMonitor` | 趋势衰减监测器 |
| `TrendDecaySignal` | 衰减信号数据类 |

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

## 🔧 TrendDecayMonitor

### 构造函数

```python
def __init__(self)
```

**参数**: 无

**返回值**: TrendDecayMonitor 实例

**示例**:
```python
monitor = TrendDecayMonitor()
```

---

### monitor() 方法

```python
def monitor(self, 
            series: KlineSeries, 
            symbol: str, 
            level: str,
            small_level_series: Optional[KlineSeries] = None) -> TrendDecaySignal
```

**功能**: 监测趋势衰减信号

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `series` | KlineSeries | - | K 线序列 (当前级别) |
| `symbol` | str | - | 股票代码 |
| `level` | str | - | 级别 (1d, 30m, 5m) |
| `small_level_series` | KlineSeries | None | 小级别 K 线序列 |

**返回值**: `TrendDecaySignal` - 衰减信号

**示例**:
```python
signal = monitor.monitor(series, 'TSLA', '1d')
print(signal.decay_probability)  # 0.75
```

---

### 私有方法

#### _detect_strength_decline()

```python
def _detect_strength_decline(self, 
                             centers: List, 
                             segments: List) -> Dict
```

**功能**: 力度递减检测

**参数**:
- `centers`: 中枢列表
- `segments`: 线段列表

**返回值**: `Dict` - 检测结果

**检测逻辑**:
```python
strengths = [calc_strength(seg) for seg in segments]
decline_rate = (strengths[-1] - strengths[-2]) / strengths[-2]

if decline_rate < -0.3:  # 力度下降 30%
    return {'declining': True, 'decline_rate': decline_rate}
```

---

#### _detect_center_expansion()

```python
def _detect_center_expansion(self, centers: List) -> Dict
```

**功能**: 中枢扩大检测

**参数**:
- `centers`: 中枢列表

**返回值**: `Dict` - 检测结果

**检测逻辑**:
```python
if centers[-1].range > centers[-2].range * 1.5:  # 扩大 50%
    return {'expanding': True, 'expansion_rate': ...}
```

---

#### _detect_time_extension()

```python
def _detect_time_extension(self, centers: List) -> Dict
```

**功能**: 时间延长检测

**参数**:
- `centers`: 中枢列表

**返回值**: `Dict` - 检测结果

**检测逻辑**:
```python
duration_last = centers[-1].end_idx - centers[-1].start_idx
duration_prev = centers[-2].end_idx - centers[-2].start_idx

if duration_last > duration_prev * 1.5:  # 延长 50%
    return {'extending': True, 'extension_rate': ...}
```

---

#### _detect_volume_price_divergence()

```python
def _detect_volume_price_divergence(self, 
                                    prices: List[float], 
                                    volumes: List[int]) -> bool
```

**功能**: 量价背离检测

**参数**:
- `prices`: 价格列表
- `volumes`: 成交量列表

**返回值**: `bool` - 是否背离

**检测逻辑**:
```python
# 最近 5 日价格 vs 前 5 日
recent_price_change = (prices[-1] - prices[-5]) / prices[-5]

# 最近 5 日成交量 vs 前 5 日
recent_vol_change = (sum(volumes[-5:]) - sum(volumes[-10:-5])) / sum(volumes[-10:-5])

# 价格上涨但成交量萎缩
if recent_price_change > 0.02 and recent_vol_change < -0.3:
    return True
```

---

#### _detect_multi_level_divergence()

```python
def _detect_multi_level_divergence(self, 
                                   series: KlineSeries, 
                                   small_series: KlineSeries) -> bool
```

**功能**: 多级别背离检测

**参数**:
- `series`: 当前级别 K 线序列
- `small_series`: 小级别 K 线序列

**返回值**: `bool` - 是否背离

**检测逻辑**:
```python
# 大级别金叉，小级别死叉 = 背离
big_bullish = macd[-1].dif > macd[-1].dea
small_bearish = small_macd[-1].dif < small_macd[-1].dea

if big_bullish and small_bearish:
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
- `probability`: 衰减概率
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
- `probability`: 衰减概率

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
def _estimate_days_to_reversal(self, 
                               probability: float, 
                               signal_count: int) -> int
```

**功能**: 预估反转天数

**参数**:
- `probability`: 衰减概率
- `signal_count`: 触发信号数量

**返回值**: `int` - 预估天数

**映射关系**:
| 概率 | 天数 |
|------|------|
| ≥70% | 3 天 |
| ≥50% | 5 天 |
| ≥30% | 7 天 |
| <30% | 0 天 |

---

#### format_signal()

```python
def format_signal(self, signal: TrendDecaySignal) -> str
```

**功能**: 格式化信号输出

**参数**:
- `signal`: TrendDecaySignal 对象

**返回值**: `str` - 格式化的信号文本

**示例输出**:
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

## 📦 TrendDecaySignal

### 数据类属性

```python
@dataclass
class TrendDecaySignal:
    symbol: str                        # 股票代码
    level: str                         # 级别
    timestamp: datetime                # 时间戳
    decay_probability: float = 0.0     # 衰减概率
    confidence: float = 0.0            # 置信度
    signals: List[str] = field(default_factory=list)  # 触发信号
    warning_level: str = 'LOW'         # 预警级别
    strength_decline_rate: float = 0.0 # 力度递减率
    center_expansion_rate: float = 0.0 # 中枢扩大率
    time_extension_rate: float = 0.0   # 时间延长率
    volume_price_divergence: bool = False  # 量价背离
    multi_level_divergence: bool = False   # 多级别背离
    days_to_reversal: int = 0          # 预估反转天数
```

---

## 🔍 使用示例

### 示例 1: 基础监测

```python
from scripts.trend_decay_monitor import TrendDecayMonitor

monitor = TrendDecayMonitor()
signal = monitor.monitor(series, 'TSLA', '1d')

if signal.warning_level in ['HIGH', 'CRITICAL']:
    print(f"预警：{signal.warning_level}")
    print(f"预估反转：{signal.days_to_reversal} 天内")
```

---

### 示例 2: 批量监测

```python
monitor = TrendDecayMonitor()
symbols = ['TSLA', 'NVDA', 'AMD']

for symbol in symbols:
    signal = monitor.monitor(series, symbol, '1d')
    if signal.decay_probability >= 0.5:
        print(f"🔴 {symbol}: 衰减预警")
```

---

### 示例 3: 带小级别共振

```python
# 获取两个级别数据
series_1d = get_series('TSLA', '1d')
series_30m = get_series('TSLA', '30m')

monitor = TrendDecayMonitor()
signal = monitor.monitor(series_1d, 'TSLA', '1d', series_30m)

if signal.multi_level_divergence:
    print(f"多级别背离：{signal.warning_level}")
```

---

### 示例 4: 回测循环

```python
results = []
for i in range(60, len(series.klines)):
    partial_series = KlineSeries(klines=series.klines[:i+1])
    signal = monitor.monitor(partial_series, 'TSLA', '1d')
    
    if signal.warning_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
        results.append({
            'date': signal.timestamp,
            'probability': signal.decay_probability,
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

- 单次监测时间：~100ms
- 适合实时监测
- 回测时建议批量处理

### 3. 异常处理

```python
try:
    signal = monitor.monitor(series, 'TSLA', '1d')
except Exception as e:
    print(f"监测失败：{e}")
```

---

## 📚 相关文档

- `TREND_DECAY_USER_MANUAL.md` - 用户手册
- `BACKTEST_RESULTS_PHASE2.md` - 回测结果 (待生成)
- `CHANLUN_V2_DETAILED_PLAN.md` - 开发计划

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 19:00 EDT  
**维护者**: ChanLun AI Agent
