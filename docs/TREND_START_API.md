# 趋势起势检测器 - API 文档

**版本**: v1.0  
**日期**: 2026-04-16  
**模块**: `scripts/trend_start_detector.py`

---

## 📦 模块概览

趋势起势检测器模块提供趋势起势的自动检测功能。

### 核心类

| 类 | 用途 |
|------|------|
| `TrendStartDetector` | 趋势起势检测器 |
| `TrendStartSignal` | 起势信号数据类 |

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

## 🔧 TrendStartDetector

### 构造函数

```python
def __init__(self)
```

**参数**: 无

**返回值**: TrendStartDetector 实例

**示例**:
```python
detector = TrendStartDetector()
```

---

### detect() 方法

```python
def detect(self, 
           series: KlineSeries, 
           symbol: str, 
           level: str,
           small_level_series: Optional[KlineSeries] = None) -> TrendStartSignal
```

**功能**: 检测趋势起势信号

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `series` | KlineSeries | - | K 线序列 (当前级别) |
| `symbol` | str | - | 股票代码 |
| `level` | str | - | 级别 (1d, 30m, 5m) |
| `small_level_series` | KlineSeries | None | 小级别 K 线序列 (用于共振检测) |

**返回值**: `TrendStartSignal` - 起势信号

**示例**:
```python
signal = detector.detect(series, 'AAPL', '1d')
print(signal.start_probability)  # 0.75
```

---

### 私有方法

#### _center_breakout()

```python
def _center_breakout(self, prices: List[float], center) -> bool
```

**功能**: 中枢突破检测

**参数**:
- `prices`: 价格列表
- `center`: 中枢对象

**返回值**: `bool` - 是否突破

**检测条件**:
1. 价格突破中枢上沿 (ZG * 1.01)
2. 5 日涨幅≥3%

---

#### _momentum_acceleration()

```python
def _momentum_acceleration(self, macd_data) -> bool
```

**功能**: 动量加速检测

**参数**:
- `macd_data`: MACD 数据列表

**返回值**: `bool` - 是否动量加速

**检测条件**:
1. DIF 斜率>0.5
2. DEA 斜率>0.3
3. 金叉状态 (DIF>DEA)

---

#### _volume_expand()

```python
def _volume_expand(self, volumes: List[int]) -> float
```

**功能**: 量能放大检测

**参数**:
- `volumes`: 成交量列表

**返回值**: `float` - 成交量比率 (当前/20 日均量)

**检测条件**:
- 比率>1.5 (放量 50%)

---

#### _small_level_resonance()

```python
def _small_level_resonance(self, 
                           series: KlineSeries, 
                           small_series: KlineSeries) -> bool
```

**功能**: 小级别共振检测

**参数**:
- `series`: 当前级别 K 线序列
- `small_series`: 小级别 K 线序列

**返回值**: `bool` - 是否共振

**检测条件**:
- 两个级别都金叉

---

#### _ma_bullish()

```python
def _ma_bullish(self, prices: List[float]) -> bool
```

**功能**: 均线多头检测

**参数**:
- `prices`: 价格列表

**返回值**: `bool` - 是否多头排列

**检测条件**:
- MA5>MA10>MA20

---

#### _calculate_confidence()

```python
def _calculate_confidence(self, 
                          probability: float, 
                          signal_count: int) -> float
```

**功能**: 计算置信度

**参数**:
- `probability`: 起势概率
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

#### _get_action()

```python
def _get_action(self, probability: float) -> str
```

**功能**: 根据概率给出操作建议

**参数**:
- `probability`: 起势概率

**返回值**: `str` - 操作建议

**映射关系**:
| 概率 | 建议 |
|------|------|
| ≥70% | STRONG_ENTRY |
| ≥50% | ENTRY |
| ≥30% | WATCH |
| <30% | HOLD |

---

#### _get_position_ratio()

```python
def _get_position_ratio(self, 
                        probability: float, 
                        confidence: float) -> float
```

**功能**: 计算建议仓位

**参数**:
- `probability`: 起势概率
- `confidence`: 置信度

**返回值**: `float` - 建议仓位 (0-1)

**计算逻辑**:
```python
score = probability * 0.6 + confidence * 0.4

if score >= 0.8:
    return 0.7  # 70% 仓位
elif score >= 0.6:
    return 0.5  # 50% 仓位
elif score >= 0.4:
    return 0.3  # 30% 仓位
else:
    return 0.1  # 10% 仓位
```

---

#### _calculate_stop_loss()

```python
def _calculate_stop_loss(self, center, current_price: float) -> float
```

**功能**: 计算止损位

**参数**:
- `center`: 中枢对象
- `current_price`: 当前价格

**返回值**: `float` - 止损位

**计算公式**:
```python
stop_loss = center.zd * 0.98  # 中枢下沿 -2%
```

---

#### _calculate_take_profit()

```python
def _calculate_take_profit(self, 
                           center, 
                           current_price: float) -> float
```

**功能**: 计算止盈位

**参数**:
- `center`: 中枢对象
- `current_price`: 当前价格

**返回值**: `float` - 止盈位

**计算公式**:
```python
range_size = center.zg - center.zd
take_profit = current_price + range_size
```

---

#### format_signal()

```python
def format_signal(self, signal: TrendStartSignal) -> str
```

**功能**: 格式化信号输出

**参数**:
- `signal`: TrendStartSignal 对象

**返回值**: `str` - 格式化的信号文本

**示例输出**:
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

## 📦 TrendStartSignal

### 数据类属性

```python
@dataclass
class TrendStartSignal:
    symbol: str                    # 股票代码
    level: str                     # 级别
    timestamp: datetime            # 时间戳
    start_probability: float = 0.0 # 起势概率
    confidence: float = 0.0        # 置信度
    signals: List[str] = field(default_factory=list)  # 触发信号
    action: str = 'HOLD'           # 操作建议
    position_ratio: float = 0.0    # 建议仓位
    breakout_price: Optional[float] = None  # 突破价格
    center_zg: Optional[float] = None       # 中枢上沿
    center_zd: Optional[float] = None       # 中枢下沿
    volume_ratio: float = 1.0      # 成交量比率
    macd_status: str = 'unknown'   # MACD 状态
    stop_loss: Optional[float] = None       # 止损位
    take_profit: Optional[float] = None     # 止盈位
```

---

## 🔍 使用示例

### 示例 1: 基础检测

```python
from scripts.trend_start_detector import TrendStartDetector

detector = TrendStartDetector()
signal = detector.detect(series, 'AAPL', '1d')

if signal.start_probability >= 0.5:
    print(f"买入信号：{signal.action}")
    print(f"建议仓位：{signal.position_ratio*100:.0f}%")
```

---

### 示例 2: 批量检测

```python
detector = TrendStartDetector()
symbols = ['AAPL', 'TSLA', 'NVDA']

for symbol in symbols:
    signal = detector.detect(series, symbol, '1d')
    if signal.start_probability >= 0.7:
        print(f"🚀 {symbol}: 强烈入场")
```

---

### 示例 3: 带小级别共振

```python
# 获取两个级别数据
series_1d = get_series('AAPL', '1d')
series_30m = get_series('AAPL', '30m')

detector = TrendStartDetector()
signal = detector.detect(series_1d, 'AAPL', '1d', series_30m)

print(f"共振检测：{signal.signals}")
```

---

### 示例 4: 回测循环

```python
results = []
for i in range(60, len(series.klines)):
    partial_series = KlineSeries(klines=series.klines[:i+1])
    signal = detector.detect(partial_series, 'AAPL', '1d')
    
    if signal.start_probability >= 0.5:
        results.append({
            'date': signal.timestamp,
            'probability': signal.start_probability,
            'action': signal.action
        })
```

---

## ⚠️ 注意事项

### 1. 数据要求

- 最少 60 根 K 线
- 推荐 100+ 根 K 线
- 使用调整收盘价

### 2. 性能考虑

- 单次检测时间：~100ms
- 适合实时检测
- 回测时建议批量处理

### 3. 异常处理

```python
try:
    signal = detector.detect(series, 'AAPL', '1d')
except Exception as e:
    print(f"检测失败：{e}")
```

---

## 📚 相关文档

- `TREND_START_USER_MANUAL.md` - 用户手册
- `BACKTEST_RESULTS_PHASE1_2026-04-16.md` - 回测结果
- `CHANLUN_V2_DETAILED_PLAN.md` - 开发计划

---

**文档版本**: v1.0  
**最后更新**: 2026-04-16 18:35 EDT  
**维护者**: ChanLun AI Agent
