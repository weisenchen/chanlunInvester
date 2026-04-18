# 缠论中枢计算日期起点确定方法

**文档版本**: v6.0-beta  
**创建日期**: 2026-04-17

---

## 📅 日期起点的层次

中枢计算的日期起点有 5 个层次：

```
1. K 线数据起点 → 2. 分型起点 → 3. 笔起点 → 4. 线段起点 → 5. 中枢起点
```

---

## 1️⃣ K 线数据起点

### 确定方法

```python
# 根据分析级别获取足够的数据
levels_config = {
    '1w': {'period': '2y', 'interval': '1wk'},    # 周线：2 年数据
    '1d': {'period': '1y', 'interval': '1d'},     # 日线：1 年数据
    '30m': {'period': '10d', 'interval': '30m'},  # 30 分钟：10 天数据
    '5m': {'period': '2d', 'interval': '5m'},     # 5 分钟：2 天数据
}
```

### 数据量要求

| 级别 | 最少 K 线 | 推荐 K 线 | 时间范围 |
|------|---------|---------|---------|
| 周线 | 52 条 | 104 条 | 1-2 年 |
| 日线 | 30 条 | 250 条 | 1 年 |
| 30 分钟 | 30 条 | 130 条 | 10 天 |
| 5 分钟 | 30 条 | 390 条 | 2 天 |

### v6.0 实现

```python
def fetch_data(symbol, level):
    config = {
        '1w': {'period': '2y', 'interval': '1wk'},
        '1d': {'period': '1y', 'interval': '1d'},
        '30m': {'period': '10d', 'interval': '30m'},
    }
    
    ticker = yf.Ticker(symbol)
    history = ticker.history(
        period=config[level]['period'],
        interval=config[level]['interval']
    )
    
    return history
```

---

## 2️⃣ 分型起点

### 顶分型确定

```python
# 需要至少 5 根 K 线才能确定第一个分型
# 因为分型判断需要：左 2 + 中间 1 + 右 2 = 5 根 K 线

for i in range(2, len(prices) - 2):
    # 第 1 个可能的分型索引是 2 (第 3 根 K 线)
    # 但需要等到 i+2 (第 5 根 K 线) 才能确认
    if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
        prices[i] > prices[i+1] and prices[i] > prices[i+2]):
        fractals.append({'index': i, 'type': 'top'})
```

### 日期计算

```
假设 K 线数据从 2025-04-17 开始

第 1 根 K 线：2025-04-17 (索引 0)
第 2 根 K 线：2025-04-18 (索引 1)
第 3 根 K 线：2025-04-21 (索引 2)
第 4 根 K 线：2025-04-22 (索引 3)
第 5 根 K 线：2025-04-23 (索引 4)

第一个分型确认日期：2025-04-23 (索引 2 的分型需要索引 4 确认)
```

### v6.0 实现

```python
def detect_fractals(prices):
    fractals = []
    
    # 从索引 2 开始，到 len-2 结束
    # 确保左右各有 2 根 K 线用于确认
    for i in range(2, len(prices) - 2):
        # 顶分型
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
            prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            fractals.append({
                'index': i,
                'date': dates[i],
                'type': 'top',
                'price': prices[i]
            })
        # 底分型
        elif (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
              prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            fractals.append({
                'index': i,
                'date': dates[i],
                'type': 'bottom',
                'price': prices[i]
            })
    
    return fractals
```

---

## 3️⃣ 笔起点

### 笔的形成条件

```python
# 笔 = 相邻的顶分型和底分型连接
# 需要至少 2 个分型才能形成第 1 笔

def detect_pivots(fractals):
    pivots = []
    
    for i in range(len(fractals) - 1):
        f1 = fractals[i]      # 第 1 个分型
        f2 = fractals[i + 1]  # 第 2 个分型
        
        # 顶底必须交替
        if f1['type'] != f2['type']:
            pivots.append({
                'start': f1,
                'end': f2,
                'direction': 'down' if f1['type'] == 'top' else 'up',
                'start_date': f1['date'],
                'end_date': f2['date'],
            })
    
    return pivots
```

### 日期计算

```
第 1 个分型：2025-04-23 (顶)
第 2 个分型：2025-04-28 (底)

第 1 笔：2025-04-23 → 2025-04-28
起点日期：2025-04-23
终点日期：2025-04-28
```

---

## 4️⃣ 线段起点

### 线段的形成条件

```python
# 线段 = 至少 2 个同向笔
# 需要至少 3 个分型才能形成第 1 个线段

def detect_segments(pivots):
    segments = []
    i = 0
    
    while i < len(pivots) - 1:
        p1 = pivots[i]       # 第 1 个笔
        p2 = pivots[i + 1]   # 第 2 个笔
        
        # 同向笔才能形成线段
        if p1['direction'] == p2['direction']:
            segments.append({
                'start_idx': p1['start']['index'],
                'end_idx': p2['end']['index'],
                'start_date': p1['start']['date'],
                'end_date': p2['end']['date'],
                'start_price': p1['start']['price'],
                'end_price': p2['end']['price'],
                'direction': p1['direction']
            })
            i += 2  # 跳过已处理的 2 个笔
        else:
            i += 1
    
    return segments
```

### 日期计算

```
笔 1: 2025-04-23 → 2025-04-28 (向下)
笔 2: 2025-04-28 → 2025-05-02 (向下)

线段 1: 2025-04-23 → 2025-05-02
起点日期：2025-04-23 (笔 1 的起点)
终点日期：2025-05-02 (笔 2 的终点)
```

---

## 5️⃣ 中枢起点

### 中枢的形成条件

```python
# 中枢 = 至少 3 个连续线段的重叠区间
# 需要至少 6 个笔 (9 个分型) 才能形成第 1 个中枢

def detect_centers(segments, min_segments=3):
    centers = []
    
    for i in range(len(segments) - min_segments + 1):
        center_segments = segments[i:i + min_segments]
        
        # 计算重叠区间
        overlap = calculate_overlap(center_segments)
        
        if overlap:
            centers.append({
                'start_idx': center_segments[0]['start_idx'],
                'end_idx': center_segments[-1]['end_idx'],
                'start_date': center_segments[0]['start_date'],
                'end_date': center_segments[-1]['end_date'],
                'zg': overlap[0],
                'zd': overlap[1],
            })
    
    return centers
```

### 日期计算

```
线段 1: 2025-04-23 → 2025-05-02
线段 2: 2025-05-02 → 2025-05-08
线段 3: 2025-05-08 → 2025-05-15

中枢 1:
  起点日期：2025-04-23 (线段 1 起点)
  终点日期：2025-05-15 (线段 3 终点)
  ZG: $39.56
  ZD: $36.70
```

---

## 📊 SMR 日线实际案例

### 数据起点

```python
K 线数据：2025-04-17 至 2026-04-17 (251 条)
```

### 分型起点

```
第 1 个分型：2025-04-25 (索引 5)
  类型：底分型
  价格：$36.70
```

### 笔起点

```
第 1 笔：2025-04-25 → 2025-04-29
  方向：向上
  起点：$36.70
  终点：$39.56
```

### 线段起点

```
第 1 线段：2025-04-25 → 2025-04-30
  方向：向上
  起点：$36.70
  终点：$51.67
```

### 中枢起点

```
中枢 1:
  起点日期：2025-04-25
  终点日期：2025-04-29
  ZG: $39.56
  ZD: $36.70
  区间：$2.86
```

---

## ⚙️ v6.0 代码实现

### 完整流程

```python
def analyze_symbol(symbol, level):
    # 1. 获取 K 线数据
    data = fetch_data(symbol, level)
    prices = data['Close'].tolist()
    dates = data.index.tolist()
    
    print(f"K 线起点：{dates[0].strftime('%Y-%m-%d')}")
    print(f"K 线终点：{dates[-1].strftime('%Y-%m-%d')}")
    print(f"K 线数量：{len(prices)}")
    
    # 2. 检测分型
    fractals = detect_fractals(prices, dates)
    if fractals:
        print(f"\n第 1 个分型：{fractals[0]['date'].strftime('%Y-%m-%d')}")
        print(f"  类型：{fractals[0]['type']}")
        print(f"  价格：${fractals[0]['price']:.2f}")
    
    # 3. 检测笔
    pivots = detect_pivots(fractals)
    if pivots:
        print(f"\n第 1 笔：{pivots[0]['start_date'].strftime('%Y-%m-%d')} → {pivots[0]['end_date'].strftime('%Y-%m-%d')}")
        print(f"  方向：{pivots[0]['direction']}")
    
    # 4. 检测线段
    segments = detect_segments(pivots)
    if segments:
        print(f"\n第 1 线段：{segments[0]['start_date'].strftime('%Y-%m-%d')} → {segments[0]['end_date'].strftime('%Y-%m-%d')}")
        print(f"  方向：{segments[0]['direction']}")
    
    # 5. 检测中枢
    centers = detect_centers(segments)
    if centers:
        print(f"\n第 1 中枢：{centers[0]['start_date'].strftime('%Y-%m-%d')} → {centers[0]['end_date'].strftime('%Y-%m-%d')}")
        print(f"  ZG: ${centers[0]['zg']:.2f}")
        print(f"  ZD: ${centers[0]['zd']:.2f}")
```

---

## 📈 时间延迟分析

### 各级别确认延迟

| 级别 | 最少 K 线 | 确认延迟 | 说明 |
|------|---------|---------|------|
| 分型 | 5 条 | 2 根 K 线 | 需要左右各 2 根确认 |
| 笔 | 2 个分型 | 额外 2-5 根 | 等待第 2 个分型 |
| 线段 | 2 个同向笔 | 额外 2-5 根 | 等待第 2 个同向笔 |
| 中枢 | 3 个线段 | 额外 2-5 根 | 等待第 3 个线段 |

### 日线级别示例

```
K 线起点：2025-04-17

分型确认：2025-04-25 (+8 天)
笔形成：2025-04-29 (+12 天)
线段形成：2025-04-30 (+13 天)
中枢形成：2025-04-29 (+12 天)
```

---

## 🎯 常见问题

### Q1: 为什么第一个分型不是从第 1 根 K 线开始？

**A**: 分型需要左右各 2 根 K 线确认，所以第 1 个可能的分型索引是 2 (第 3 根 K 线)，但需要等到第 5 根 K 线才能确认。

### Q2: 数据量不足会怎样？

**A**: 
- <30 根 K 线：无法形成可靠中枢
- 30-60 根 K 线：可能形成 1-2 个中枢
- >250 根 K 线：可以形成多个中枢，分析更可靠

### Q3: 如何选择合适的数据范围？

**A**:
- 长线分析 (周线): 2 年数据
- 中线分析 (日线): 1 年数据
- 短线分析 (30m/5m): 10 天/2 天数据

---

## 📚 参考文档

- [中枢计算方法](CENTER_CALCULATION_EXPLAINED.md)
- [v6.0 中枢动量模块](../python-layer/trading_system/center_momentum.py)
- [缠论原文第 18 课](CHANLUN_ORIGINAL.md)

---

**文档生成**: 2026-04-17 11:11 EDT  
**系统版本**: v6.0-beta  
**维护者**: ChanLun AI Agent
