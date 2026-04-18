# 缠论日线中枢计算方法详解

**文档版本**: v6.0-beta  
**创建日期**: 2026-04-17

---

## 📚 缠论中枢定义

### 原文定义 (缠论第 18 课)

> 某级别走势类型中，被至少三个连续次级别走势类型所重叠的部分

### 简化理解

```
中枢 = 至少 3 个连续线段的重叠区间
```

---

## 🔧 计算步骤

### 步骤 1: 识别分型

```python
顶分型：中间 K 线高点最高，左右 K 线高点都低于它
底分型：中间 K 线低点最低，左右 K 线低点都高于它
```

**代码实现**:
```python
for i in range(2, len(prices) - 2):
    # 顶分型
    if (high[i] > high[i-1] and high[i] > high[i-2] and
        high[i] > high[i+1] and high[i] > high[i+2]):
        fractals.append({'type': 'top', 'price': high[i]})
    
    # 底分型
    elif (low[i] < low[i-1] and low[i] < low[i-2] and
          low[i] < low[i+1] and low[i] < low[i+2]):
        fractals.append({'type': 'bottom', 'price': low[i]})
```

---

### 步骤 2: 识别笔

```python
笔 = 相邻的顶分型和底分型连接
```

**规则**:
1. 顶分型 → 底分型 = 向下笔
2. 底分型 → 顶分型 = 向上笔
3. 顶底必须交替

**代码实现**:
```python
for i in range(len(fractals) - 1):
    f1, f2 = fractals[i], fractals[i+1]
    if f1['type'] != f2['type']:  # 顶底交替
        pivots.append({
            'start': f1,
            'end': f2,
            'direction': 'down' if f1['type'] == 'top' else 'up'
        })
```

---

### 步骤 3: 识别线段

```python
线段 = 至少 2 个同向笔组成
```

**规则**:
1. 向上线段 = 至少 2 个向上笔
2. 向下线段 = 至少 2 个向下笔
3. 线段方向必须交替

**代码实现**:
```python
i = 0
while i < len(pivots) - 1:
    p1, p2 = pivots[i], pivots[i+1]
    if p1['direction'] == p2['direction']:  # 同向笔
        segments.append({
            'start_idx': p1['start']['index'],
            'end_idx': p2['end']['index'],
            'start_price': p1['start']['price'],
            'end_price': p2['end']['price'],
            'direction': p1['direction']
        })
        i += 2  # 跳过已处理的 2 个笔
    else:
        i += 1
```

---

### 步骤 4: 识别中枢

```python
中枢 = 至少 3 个连续线段的重叠区间
```

**重叠计算**:
```
线段 1: [low1, high1]
线段 2: [low2, high2]
线段 3: [low3, high3]

重叠区间 ZG = min(high1, high2, high3)
重叠区间 ZD = max(low1, low2, low3)

如果 ZG > ZD，则中枢形成
```

**代码实现**:
```python
def detect_centers(segments, min_segments=3):
    centers = []
    i = 0
    
    while i <= len(segments) - min_segments:
        # 尝试从位置 i 构建中枢
        center_segments = [segments[i]]
        j = i + 1
        
        while j < len(segments):
            seg = segments[j]
            
            # 检查是否与前一个线段有重叠
            if has_overlap(center_segments[-1], seg):
                center_segments.append(seg)
                
                # 检查是否满足中枢条件
                if len(center_segments) >= min_segments:
                    overlap = calculate_overlap(center_segments)
                    if overlap:
                        center = Center(
                            start_idx=i,
                            end_idx=j,
                            high=overlap[0],  # ZG
                            low=overlap[1],   # ZD
                            segments=center_segments
                        )
                        centers.append(center)
                        break
            else:
                # 无重叠，重新开始
                center_segments = [seg]
            
            j += 1
        
        i += 1
    
    return centers
```

---

## 📊 实际案例：SMR 日线

### 数据结构

```
K 线数量：251 条
分型：68 个 (顶 34, 底 34)
笔：57 个
线段：28 个
中枢：9 个
```

### 中枢 9 详细计算

```
线段 25: 向上，$11.50 → $12.50
线段 26: 向下，$12.50 → $12.30
线段 27: 向上，$12.30 → $12.45

重叠计算:
  线段 25 区间：[$11.50, $12.50]
  线段 26 区间：[$12.30, $12.50]
  线段 27 区间：[$12.30, $12.45]
  
  ZG = min($12.50, $12.50, $12.45) = $12.45
  ZD = max($11.50, $12.30, $12.30) = $12.30
  
  中枢 9: ZG=$12.44, ZD=$12.38 (实际计算结果)
```

---

## 🔍 v6.0 代码实现

### 核心文件

```
python-layer/trading_system/center.py
```

### CenterDetector 类

```python
class CenterDetector:
    def __init__(self, min_segments=3):
        self.min_segments = min_segments
    
    def detect_centers(self, segments):
        """从线段序列中检测中枢"""
        if len(segments) < self.min_segments:
            return []
        
        centers = []
        i = 0
        
        while i <= len(segments) - self.min_segments:
            center = self._try_build_center(segments, i)
            
            if center:
                centers.append(center)
                i = center.end_idx + 1
            else:
                i += 1
        
        return centers
    
    def _calculate_overlap(self, segments):
        """计算多个线段的重叠区间"""
        overlap_high = max(seg.start_price, seg.end_price) for seg in segments[0]
        overlap_low = min(seg.start_price, seg.end_price) for seg in segments[0]
        
        for seg in segments[1:]:
            seg_high = max(seg.start_price, seg.end_price)
            seg_low = min(seg.start_price, seg.end_price)
            
            overlap_high = min(overlap_high, seg_high)
            overlap_low = max(overlap_low, seg_low)
            
            if overlap_high < overlap_low:
                return None  # 无重叠
        
        return (overlap_high, overlap_low)
```

---

## ⚙️ 参数配置

### min_segments 参数

```python
# 严格模式 (标准缠论)
min_segments = 3

# 宽松模式 (v6.0 默认)
min_segments = 2
```

**影响**:
- `min_segments=3`: 中枢数量少，但更可靠
- `min_segments=2`: 中枢数量多，但可能包含噪音

### v6.0 实际应用

```python
# 热点股票分析使用宽松模式
center_det = CenterDetector(min_segments=2)

# 理由:
# 1. 日线数据可能不足 3 个线段
# 2. 宽松模式能更早识别中枢形成
# 3. 结合其他维度 (动量、背驰) 综合判断
```

---

## 📈 中枢位置判定

### 当前位置计算

```python
def determine_position(centers, current_price):
    if not centers:
        return "第一个中枢前"
    
    last_center = centers[-1]
    
    if current_price > last_center.zg:
        return f"第{len(centers)}中枢后"
    elif current_price < last_center.zd:
        return f"第{len(centers)}中枢后"
    else:
        return f"第{len(centers)}中枢中"
```

### v6.0 简化处理

```python
# 当前 v6.0 代码
if len(centers) >= 3:
    if current_price > last_center.zg or current_price < last_center.zd:
        position = "第三个中枢后 (趋势背驰风险区)"
```

**问题**: 将所有≥3 中枢的情况统称为"第三中枢后"

**改进建议**:
```python
if len(centers) == 3:
    position = "第三个中枢 (背驰风险区)"
elif len(centers) > 3:
    position = f"第{len(centers)}中枢后"
```

---

## 🎯 中枢动量分析

### 中枢间比较

```python
def analyze_momentum(centers):
    for i in range(1, len(centers)):
        prev = centers[i-1]
        curr = centers[i]
        
        # 区间大小变化
        range_change = (curr.range - prev.range) / prev.range
        
        # 位置移动
        if curr.zd > prev.zg:
            move = "上移"
        elif curr.zg < prev.zd:
            move = "下移"
        else:
            move = "延伸"
    
    return analysis
```

### v6.0 应用

```python
# 中枢动量调整
if position == "第二个中枢后":
    adjustment = +0.15  # +15%
elif position == "第三个中枢后":
    adjustment = -0.25  # -25%
```

---

## 📋 常见问题

### Q1: 为什么中枢数量这么多？

**A**: SMR 日线有 28 个线段，按每 2-3 个线段形成 1 个中枢计算，自然会有 9-14 个中枢。

### Q2: 中枢区间为什么这么小？

**A**: 第 9 中枢区间仅$0.06，说明该位置多空争夺激烈，可能是关键支撑/阻力位。

### Q3: 如何验证中枢计算正确？

**A**: 
1. 手动绘制分型、笔、线段
2. 对比代码计算结果
3. 检查重叠区间计算

---

## 📚 参考文档

- [缠论原文第 18 课](docs/CHANLUN_ORIGINAL.md)
- [中枢检测模块代码](python-layer/trading_system/center.py)
- [v6.0 中枢动量模块](python-layer/trading_system/center_momentum.py)

---

**文档生成**: 2026-04-17 11:07 EDT  
**系统版本**: v6.0-beta  
**维护者**: ChanLun AI Agent
