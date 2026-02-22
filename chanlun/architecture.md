# 缠论股票技术分析系统 - 软件架构设计文档

**项目名称:** 缠论 Invester (ChanLun Invester)  
**版本:** v1.0  
**基于:** 缠中说禅"教你炒股票"108 课  
**文档状态:** 初稿  
**创建日期:** 2026-02-22

---

## 目录

1. [系统概述](#1-系统概述)
2. [架构概览](#2-架构概览)
3. [核心模块设计](#3-核心模块设计)
4. [数据层设计](#4-数据层设计)
5. [API 设计](#5-api 设计)
6. [技术栈选型](#6-技术栈选型)
7. [部署架构](#7-部署架构)
8. [安全与性能](#8-安全与性能)
9. [开发路线图](#9-开发路线图)

---

## 1. 系统概述

### 1.1 项目背景

缠论 Invester 是一个基于缠中说禅"教你炒股票"108 课理论的股票技术分析系统。系统通过纯几何化的方法，对市场走势进行严格分类和当下判断，帮助投资者识别买卖点、控制风险。

### 1.2 核心功能

- **走势自动分析**: 自动识别分型、笔、线段、中枢
- **买卖点提示**: 实时识别三类买卖点并发出信号
- **背驰检测**: 多级别背驰自动判断
- **多周期联立**: 支持 1 分钟至月线的多级别分析
- **风险预警**: 走势从"能搞"变"不能搞"时立即预警

### 1.3 设计原则

1. **100% 符合缠论原文**: 所有算法严格遵循 108 课定义
2. **当下性**: 不做预测，只做当下分类和判断
3. **精确性**: 几何化定义，无歧义
4. **可扩展性**: 支持后续功能扩展和算法优化

---

## 2. 架构概览

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层 (UI)                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ K 线图展示  │ │ 买卖点标记 │ │ 多周期切换 │ │ 预警中心 │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    应用服务层 (Application)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ 走势分析服务 │ │ 买卖点服务  │ │ 风险预警服务    │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ 多周期联立  │ │ 区间套定位  │ │ 中枢震荡监控    │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    核心引擎层 (Core Engine)               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ 包含处理   │ │ 分型识别   │ │ 笔划分     │ │ 线段划分 │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│  │ 中枢识别   │ │ 背驰判断   │ │ 买卖点识别 │ │ 力度比较 │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据访问层 (Data Access)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ K 线数据仓库 │ │ 指标数据仓  │ │ 分析结果缓存    │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据源层 (Data Source)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │ 股票行情 API │ │ 指数数据 API│ │ 财务数据 API    │   │
│  └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 技术架构分层

| 层级 | 职责 | 技术选型 |
|------|------|----------|
| 表现层 | 图表展示、交互 | React/Vue + TradingView/ECharts |
| 应用层 | 业务逻辑、服务编排 | Node.js/Python FastAPI |
| 引擎层 | 核心算法 | Rust/C++ (高性能计算) |
| 数据层 | 数据存储、缓存 | PostgreSQL + Redis + ClickHouse |
| 基础设施 | 部署、监控 | Docker + Kubernetes + Prometheus |

---

## 3. 核心模块设计

### 3.1 包含处理模块 (Containment Processor)

**职责:** 处理 K 线包含关系，为后续分型判断做准备

**输入:** 原始 K 线序列 (Open, High, Low, Close)  
**输出:** 处理后无包含关系的 K 线序列

**算法流程:**
```python
def process_containment(klines, direction):
    """
    direction: 'up' (向上) 或 'down' (向下)
    """
    processed = [klines[0]]
    
    for i in range(1, len(klines)):
        prev = processed[-1]
        curr = klines[i]
        
        # 判断包含关系
        if is_contained(prev, curr):
            if direction == 'up':
                # 向上：取高高、低高
                merged = {
                    'high': max(prev['high'], curr['high']),
                    'low': max(prev['low'], curr['low'])
                }
            else:
                # 向下：取低低、高低
                merged = {
                    'high': min(prev['high'], curr['high']),
                    'low': min(prev['low'], curr['low'])
                }
            processed[-1] = merged
        else:
            # 更新方向
            direction = 'up' if curr['high'] > prev['high'] else 'down'
            processed.append(curr)
    
    return processed
```

**接口定义:**
```typescript
interface ContainmentProcessor {
  process(klines: KLine[], direction?: Direction): ProcessedKLine[];
  getDirection(klines: KLine[]): Direction;
}
```

### 3.2 分型识别模块 (Fractal Detector)

**职责:** 识别顶分型和底分型

**输入:** 处理后的 K 线序列  
**输出:** 分型列表 (类型、位置、高低点)

**算法流程:**
```python
def detect_fractals(klines):
    fractals = []
    
    for i in range(1, len(klines) - 1):
        prev = klines[i - 1]
        curr = klines[i]
        next_k = klines[i + 1]
        
        # 顶分型判断
        if (curr['high'] > prev['high'] and curr['high'] > next_k['high'] and
            curr['low'] > prev['low'] and curr['low'] > next_k['low']):
            fractals.append({
                'type': 'top',
                'index': i,
                'high': curr['high'],
                'low': curr['low'],
                'time': curr['time']
            })
        
        # 底分型判断
        elif (curr['low'] < prev['low'] and curr['low'] < next_k['low'] and
              curr['high'] < prev['high'] and curr['high'] < next_k['high']):
            fractals.append({
                'type': 'bottom',
                'index': i,
                'high': curr['high'],
                'low': curr['low'],
                'time': curr['time']
            })
    
    return fractals
```

**接口定义:**
```typescript
interface FractalDetector {
  detect(klines: ProcessedKLine[]): Fractal[];
  getTopFractals(): Fractal[];
  getBottomFractals(): Fractal[];
  validateFractal(fractal: Fractal, klines: ProcessedKLine[]): boolean;
}
```

### 3.3 笔划分模块 (Stroke Divider)

**职责:** 根据分型划分笔

**输入:** 分型列表  
**输出:** 笔列表 (起点、终点、方向)

**笔的成立条件 (新定义):**
1. 顶分型与底分型经过包含处理后，不允许共用 K 线
2. 顶分型中最高 K 线和底分型的最低 K 线之间 (不包括这两 K 线)，不考虑包含关系，至少有 3 根 (包括 3 根) 以上 K 线

**算法流程:**
```python
def divide_strokes(fractals):
    strokes = []
    
    # 交替取顶和底
    i = 0
    while i < len(fractals) - 1:
        start = fractals[i]
        
        # 寻找下一个相反类型的分型
        j = i + 1
        while j < len(fractals):
            end = fractals[j]
            
            # 检查是否符合笔的条件
            if is_valid_stroke(start, end, fractals):
                stroke = {
                    'start': start,
                    'end': end,
                    'direction': 'up' if end['type'] == 'top' else 'down',
                    'kline_count': count_klines_between(start, end)
                }
                strokes.append(stroke)
                i = j
                break
            
            j += 1
        
        if j >= len(fractals):
            break
    
    return strokes
```

**接口定义:**
```typescript
interface StrokeDivider {
  divide(fractals: Fractal[]): Stroke[];
  isValidStroke(start: Fractal, end: Fractal): boolean;
  getLastStroke(strokes: Stroke[]): Stroke | null;
}
```

### 3.4 线段划分模块 (Segment Divider)

**职责:** 根据特征序列划分线段

**输入:** 笔列表  
**输出:** 线段列表

**线段划分标准:**
1. 线段至少由三笔组成
2. 使用特征序列判断线段结束
3. 两种情况:
   - **第一种情况:** 特征序列分型无缺口，分型成立即线段结束
   - **第二种情况:** 特征序列分型有缺口，需要后续分型确认

**数据结构:**
```typescript
interface Segment {
  id: string;
  strokes: Stroke[];
  direction: 'up' | 'down';
  high: number;
  low: number;
  startTime: number;
  endTime: number;
  featureSequence: FeatureElement[];
  isConfirmed: boolean;
}

interface FeatureElement {
  high: number;
  low: number;
  index: number;
}
```

**接口定义:**
```typescript
interface SegmentDivider {
  divide(strokes: Stroke[]): Segment[];
  detectSegmentEnd(pendingSegment: Segment, currentStroke: Stroke): boolean;
  processFeatureSequence(strokes: Stroke[]): FeatureElement[];
}
```

### 3.5 中枢识别模块 (Center Identifier)

**职责:** 识别各级别中枢

**输入:** 线段列表  
**输出:** 中枢列表

**中枢定义:** 某级别走势类型中，被至少三个连续次级别走势类型所重叠的部分

**算法流程:**
```python
def identify_centers(segments):
    centers = []
    
    i = 0
    while i < len(segments) - 2:
        # 检查连续三段是否有重叠
        seg1 = segments[i]
        seg2 = segments[i + 1]
        seg3 = segments[i + 2]
        
        # 计算重叠区间
        overlap_start = max(seg1.low, seg2.low, seg3.low)
        overlap_end = min(seg1.high, seg2.high, seg3.high)
        
        if overlap_start < overlap_end:
            # 继续检查后续线段是否仍在中枢内
            j = i + 3
            while j < len(segments):
                seg = segments[j]
                if seg.high > overlap_start and seg.low < overlap_end:
                    j += 1
                else:
                    break
            
            center = {
                'segments': segments[i:j],
                'zg': overlap_end,  # 中枢高点
                'zd': overlap_start,  # 中枢低点
                'level': determine_level(segments[i:j]),
                'startTime': segments[i].startTime,
                'endTime': segments[j-1].endTime
            }
            centers.append(center)
            i = j
        else:
            i += 1
    
    return centers
```

**接口定义:**
```typescript
interface CenterIdentifier {
  identify(segments: Segment[]): Center[];
  getCenterLevel(center: Center): Level;
  isCenterCompleted(center: Center): boolean;
  getThirdBuyPoint(center: Center): BuyPoint | null;
}
```

### 3.6 背驰判断模块 (Divergence Detector)

**职责:** 判断趋势背驰和盘整背驰

**输入:** 走势段、MACD 数据  
**输出:** 背驰判断结果

**判断标准:**
1. 两段同向趋势
2. MACD 柱子面积比较
3. MACD 黄白线回拉 0 轴
4. 结合中枢判断

**接口定义:**
```typescript
interface DivergenceDetector {
  detectTrendDivergence(segmentA: Segment, segmentB: Segment, macd: MACDData): DivergenceResult;
  detectCenterDivergence(center: Center, leaveSegment: Segment, returnSegment: Segment): DivergenceResult;
  calculateMACDArea(macd: MACDData, start: number, end: number): number;
  isHuangBaiLineBackToZero(macd: MACDData): boolean;
}

interface DivergenceResult {
  hasDivergence: boolean;
  type: 'trend' | 'center';
  level: Level;
  confidence: number;  // 0-1
  macdAreaA: number;
  macdAreaB: number;
  priceCompare: {
    segmentA: { high: number; low: number };
    segmentB: { high: number; low: number };
  };
}
```

### 3.7 买卖点识别模块 (Buy/Sell Point Identifier)

**职责:** 识别三类买卖点

**买卖点定义:**

| 类型 | 买点 | 卖点 |
|------|------|------|
| 第一类 | 趋势背驰点 | 趋势顶背驰点 |
| 第二类 | 次级别回踩不破前低 | 次级别反弹不破前高 |
| 第三类 | 次级别回踩不破中枢 | 次级别反弹不破中枢 |

**接口定义:**
```typescript
interface BuySellPointIdentifier {
  identifyAllBuySellPoints(segments: Segment[], centers: Center[]): BuySellPoint[];
  identifyFirstBuyPoint(divergence: DivergenceResult): BuySellPoint | null;
  identifySecondBuyPoint(firstBuyPoint: BuySellPoint, strokes: Stroke[]): BuySellPoint | null;
  identifyThirdBuyPoint(center: Center, leaveSegment: Segment, returnSegment: Segment): BuySellPoint | null;
}

interface BuySellPoint {
  type: 'buy1' | 'buy2' | 'buy3' | 'sell1' | 'sell2' | 'sell3';
  price: number;
  time: number;
  level: Level;
  center?: Center;
  divergence?: DivergenceResult;
  isConfirmed: boolean;
  riskRewardRatio?: number;
}
```

### 3.8 区间套定位模块 (Interval Set Locator)

**职责:** 通过多级别区间套精确定位买卖点

**算法流程:**
```
大级别背驰段
    ↓
次级别背驰段 (在次级别图中找)
    ↓
次次级别背驰段
    ↓
...
    ↓
最低级别背驰段 (1 分钟或笔级别)
```

**接口定义:**
```typescript
interface IntervalSetLocator {
  locatePrecisePoint(largeLevelDivergence: DivergenceResult, 
                     levelChain: Level[]): PrecisePoint;
  getLevelChain(baseLevel: Level): Level[];
}

interface PrecisePoint {
  price: number;
  time: number;
  level: Level;
  confidence: number;
  range: {
    min: number;
    max: number;
  };
}
```

---

## 4. 数据层设计

### 4.1 数据模型

#### K 线数据表 (klines)
```sql
CREATE TABLE klines (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    level           VARCHAR(10) NOT NULL,  -- 1m, 5m, 30m, 1d, 1w, 1M
    open_time       TIMESTAMP NOT NULL,
    close_time      TIMESTAMP NOT NULL,
    open            DECIMAL(18, 4) NOT NULL,
    high            DECIMAL(18, 4) NOT NULL,
    low             DECIMAL(18, 4) NOT NULL,
    close           DECIMAL(18, 4) NOT NULL,
    volume          DECIMAL(18, 4) NOT NULL,
    amount          DECIMAL(18, 4),
    trade_count     INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, level, open_time)
);

CREATE INDEX idx_klines_symbol_level_time ON klines(symbol, level, open_time);
```

#### 分型数据表 (fractals)
```sql
CREATE TABLE fractals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    level           VARCHAR(10) NOT NULL,
    type            VARCHAR(10) NOT NULL,  -- top, bottom
    kline_index     INTEGER NOT NULL,
    high            DECIMAL(18, 4) NOT NULL,
    low             DECIMAL(18, 4) NOT NULL,
    time            TIMESTAMP NOT NULL,
    is_confirmed    BOOLEAN DEFAULT true,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 笔数据表 (strokes)
```sql
CREATE TABLE strokes (
    id                  BIGSERIAL PRIMARY KEY,
    symbol              VARCHAR(20) NOT NULL,
    level               VARCHAR(10) NOT NULL,
    direction           VARCHAR(10) NOT NULL,  -- up, down
    start_fractal_id    BIGINT REFERENCES fractals(id),
    end_fractal_id      BIGINT REFERENCES fractals(id),
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP NOT NULL,
    start_price         DECIMAL(18, 4) NOT NULL,
    end_price           DECIMAL(18, 4) NOT NULL,
    kline_count         INTEGER NOT NULL,
    is_confirmed        BOOLEAN DEFAULT true,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 线段数据表 (segments)
```sql
CREATE TABLE segments (
    id                  BIGSERIAL PRIMARY KEY,
    symbol              VARCHAR(20) NOT NULL,
    level               VARCHAR(10) NOT NULL,
    direction           VARCHAR(10) NOT NULL,
    start_stroke_id     BIGINT REFERENCES strokes(id),
    end_stroke_id       BIGINT REFERENCES strokes(id),
    stroke_count        INTEGER NOT NULL,
    high                DECIMAL(18, 4) NOT NULL,
    low                 DECIMAL(18, 4) NOT NULL,
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP NOT NULL,
    is_confirmed        BOOLEAN DEFAULT true,
    feature_sequence    JSONB,  -- 特征序列
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 中枢数据表 (centers)
```sql
CREATE TABLE centers (
    id                  BIGSERIAL PRIMARY KEY,
    symbol              VARCHAR(20) NOT NULL,
    level               VARCHAR(10) NOT NULL,
    zg                  DECIMAL(18, 4) NOT NULL,  -- 中枢高点
    zd                  DECIMAL(18, 4) NOT NULL,  -- 中枢低点
    gg                  DECIMAL(18, 4),  -- 最高
    dd                  DECIMAL(18, 4),  -- 最低
    segment_ids         BIGINT[] NOT NULL,
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP,
    status              VARCHAR(20) DEFAULT 'forming',  -- forming, completed, extended
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 买卖点数据表 (buy_sell_points)
```sql
CREATE TABLE buy_sell_points (
    id                  BIGSERIAL PRIMARY KEY,
    symbol              VARCHAR(20) NOT NULL,
    type                VARCHAR(10) NOT NULL,  -- buy1, buy2, buy3, sell1, sell2, sell3
    price               DECIMAL(18, 4) NOT NULL,
    time                TIMESTAMP NOT NULL,
    level               VARCHAR(10) NOT NULL,
    center_id           BIGINT REFERENCES centers(id),
    divergence_id       BIGINT,
    is_confirmed        BOOLEAN DEFAULT false,
    risk_reward_ratio   DECIMAL(5, 2),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 缓存设计

**Redis 缓存结构:**
```
# K 线数据缓存
klines:{symbol}:{level} -> sorted set (score=timestamp, value=json)

# 分析结果缓存
analysis:{symbol}:{level}:fractals -> list
analysis:{symbol}:{level}:strokes -> list
analysis:{symbol}:{level}:segments -> list
analysis:{symbol}:{level}:centers -> list
analysis:{symbol}:bsp -> sorted set (score=timestamp)

# 实时提醒
alerts:{user_id} -> list
```

### 4.3 数据存储策略

| 数据类型 | 存储方案 | 保留周期 |
|----------|----------|----------|
| 1 分钟 K 线 | ClickHouse | 3 个月 |
| 5/30 分钟 K 线 | ClickHouse | 1 年 |
| 日/周/月 K 线 | PostgreSQL | 永久 |
| 分析结果 | Redis + PostgreSQL | 永久 |
| 实时行情 | Redis | 当天 |

---

## 5. API 设计

### 5.1 RESTful API

#### 行情数据 API
```
GET /api/v1/klines
  ?symbol=000001.SZ
  &level=1m
  &start=2024-01-01T00:00:00Z
  &end=2024-01-01T23:59:59Z
  &limit=1000

Response:
{
  "data": [
    {
      "time": "2024-01-01T09:30:00Z",
      "open": 10.5,
      "high": 10.8,
      "low": 10.3,
      "close": 10.6,
      "volume": 1000000
    }
  ]
}
```

#### 走势分析 API
```
GET /api/v1/analysis/{symbol}
  ?level=30m
  &include=fractals,strokes,segments,centers,bsp

Response:
{
  "symbol": "000001.SZ",
  "level": "30m",
  "updateTime": "2024-01-01T15:00:00Z",
  "fractals": [...],
  "strokes": [...],
  "segments": [...],
  "centers": [...],
  "buySellPoints": [...],
  "trend": {
    "direction": "up",
    "strength": 0.75
  }
}
```

#### 买卖点信号 API
```
GET /api/v1/signals/bsp
  ?symbol=000001.SZ
  &type=buy1,buy2,buy3
  &status=unconfirmed,confirmed
  &since=2024-01-01T00:00:00Z

Response:
{
  "signals": [
    {
      "id": "bsp-001",
      "symbol": "000001.SZ",
      "type": "buy2",
      "price": 15.67,
      "time": "2024-01-01T10:30:00Z",
      "level": "30m",
      "isConfirmed": true,
      "description": "30 分钟级别第二类买点，次级别回踩不破前低"
    }
  ]
}
```

#### 预警订阅 API
```
POST /api/v1/alerts/subscribe
Content-Type: application/json

{
  "userId": "user-123",
  "symbol": "000001.SZ",
  "alertTypes": ["buy1", "buy2", "buy3", "divergence"],
  "channels": ["websocket", "email", "telegram"],
  "level": "30m"
}

Response:
{
  "subscriptionId": "sub-456",
  "status": "active"
}
```

### 5.2 WebSocket API

#### 实时行情推送
```
WS /ws/v1/market

Client → Server:
{
  "action": "subscribe",
  "channel": "klines",
  "params": {
    "symbol": "000001.SZ",
    "level": "1m"
  }
}

Server → Client:
{
  "channel": "klines",
  "data": {
    "symbol": "000001.SZ",
    "level": "1m",
    "kline": {...}
  }
}
```

#### 买卖点实时推送
```
Server → Client:
{
  "channel": "bsp",
  "data": {
    "symbol": "000001.SZ",
    "type": "buy1",
    "price": 16.23,
    "time": "2024-01-01T14:35:00Z",
    "urgency": "high",
    "message": "1 分钟级别第一类买点，趋势底背驰形成"
  }
}
```

---

## 6. 技术栈选型

### 6.1 核心引擎 (高性能计算)

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 算法实现 | Rust | 高性能、内存安全、并发友好 |
| 数值计算 | ndarray + Blas | 矩阵运算、统计分析 |
| 时间序列 | arrow | 高效时间序列处理 |

### 6.2 后端服务

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI (Python) | 高性能、异步、自动生成文档 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| API 网关 | Kong / Traefik | 路由、限流、认证 |

### 6.3 数据存储

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 时序数据 | ClickHouse | 高压缩、快速查询 |
| 关系数据 | PostgreSQL 15 | 事务支持、JSONB |
| 缓存 | Redis 7 | 低延迟、数据结构丰富 |

### 6.4 前端

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 框架 | React 18 + TypeScript | 类型安全、生态丰富 |
| 图表 | TradingView Lightweight Charts | 专业金融图表 |
| 状态管理 | Zustand | 轻量、简单 |

### 6.5 基础设施

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 容器化 | Docker | 环境一致性 |
| 编排 | Kubernetes | 自动扩缩容 |
| 监控 | Prometheus + Grafana | 指标监控 |
| 日志 | ELK Stack | 日志分析 |

---

## 7. 部署架构

### 7.1 生产环境架构

```
                              ┌─────────────┐
                              │   用户浏览器 │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │   CDN 静态资源│
                              └─────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                            Kubernetes 集群                               │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │  Ingress 控制器  │  │  API 网关 (Kong) │  │  WebSocket 网关  │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│           │                    │                    │                   │
│  ┌────────▼────────────────────▼────────────────────▼────────┐        │
│  │                    应用服务层 (Deployment)                 │        │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │        │
│  │  │ API 服务   │ │ WebSocket  │ │ 任务调度  │ │ 告警服务  │ │        │
│  │  │ ×3 副本    │ │ ×2 副本    │ │ ×2 副本    │ │ ×2 副本    │ │        │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ │        │
│  └───────────────────────────────────────────────────────────┘        │
│                                                                         │
│  ┌─────────▼─────────────────────────────────────┐                    │
│  │            核心引擎层 (StatefulSet)            │                    │
│  │  ┌───────────────┐  ┌───────────────┐        │                    │
│  │  │ 分析引擎      │  │ 实时监控引擎   │        │                    │
│  │  │ ×2 副本 (Rust)│  │ ×2 副本       │        │                    │
│  │  └───────────────┘  └───────────────┘        │                    │
│  └───────────────────────────────────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  PostgreSQL     │  │  ClickHouse     │  │  Redis Cluster  │
│  (主从复制)     │  │  (分布式)       │  │  (哨兵模式)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 7.2 资源需求估算

| 组件 | CPU | 内存 | 存储 |
|------|-----|------|------|
| API 服务 (×3) | 2 核 | 4GB | - |
| WebSocket (×2) | 2 核 | 4GB | - |
| 分析引擎 (×2) | 4 核 | 8GB | - |
| PostgreSQL | 4 核 | 16GB | 500GB SSD |
| ClickHouse | 8 核 | 32GB | 2TB NVMe |
| Redis | 2 核 | 8GB | - |

**总计:** ~40 核 CPU, ~120GB 内存，~2.5TB 存储

---

## 8. 安全与性能

### 8.1 安全设计

1. **API 认证:** JWT Token + OAuth2
2. **传输加密:** TLS 1.3
3. **数据脱敏:** 用户敏感信息加密存储
4. **访问控制:** RBAC 权限模型
5. **审计日志:** 所有操作记录可追溯

### 8.2 性能优化

1. **数据预计算:** 分型、笔、线段预先计算缓存
2. **增量更新:** 新 K 线到来时增量更新分析结果
3. **多级缓存:** 本地缓存 + Redis 缓存 + 数据库
4. **并行计算:** Rust 引擎多线程并行处理
5. **CDN 加速:** 静态资源和历史数据 CDN 分发

### 8.3 性能指标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 (P95) | < 100ms |
| WebSocket 延迟 | < 50ms |
| 买卖点识别延迟 | < 1 秒 |
| 系统可用性 | 99.9% |
| 数据准确性 | 100% (核心算法) |

---

## 9. 开发路线图

### Phase 1: 核心算法验证 (4 周)
- [ ] Rust 核心算法实现 (包含、分型、笔、线段)
- [ ] 单元测试覆盖率 > 90%
- [ ] 与手动标注数据对比验证
- [ ] 性能基准测试

### Phase 2: 数据层建设 (4 周)
- [ ] 数据库 Schema 设计与实现
- [ ] 历史 K 线数据导入
- [ ] 缓存层实现
- [ ] 数据同步工具

### Phase 3: 分析引擎开发 (6 周)
- [ ] 中枢识别模块
- [ ] 背驰判断模块
- [ ] 买卖点识别模块
- [ ] 区间套定位模块
- [ ] API 服务实现

### Phase 4: 用户界面 (6 周)
- [ ] K 线图表集成
- [ ] 买卖点标记展示
- [ ] 多周期切换
- [ ] 预警通知功能
- [ ] 用户配置管理

### Phase 5: 测试与优化 (4 周)
- [ ] 集成测试
- [ ] 性能压力测试
- [ ] 真实数据回测
- [ ] Bug 修复与优化

### Phase 6: 上线部署 (2 周)
- [ ] 生产环境部署
- [ ] 监控系统配置
- [ ] 文档完善
- [ ] 灰度发布

**总周期:** 约 26 周 (6 个月)

---

## 附录

### A. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 分型 | Fractal | 三 K 线组合，顶分型/底分型 |
| 笔 | Stroke | 相邻顶底分型连接 |
| 线段 | Segment | 至少三笔组成 |
| 中枢 | Center | 三段次级别走势重叠部分 |
| 背驰 | Divergence | 趋势力度衰竭 |
| 买卖点 | Buy/Sell Point | 第一/二/三类买卖点 |

### B. 参考资料

- 缠中说禅"教你炒股票"108 课原文
- chanlunskill.md (第 1-60 课总结)
- chanlunskill-61-108.md (第 61-108 课总结)
- GitHub: https://github.com/weisenchen/chanlunInvester

### C. 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-02-22 | 初稿完成 |

---

**文档结束**

---

**注意事项:**

1. 本架构设计基于缠论 108 课理论，所有算法实现需严格遵循原文定义
2. 系统不涉及具体的投资建议，仅提供技术分析工具
3. 实际开发过程中可能需要根据技术验证结果调整架构
4. 性能指标需在真实环境中持续监控和优化
