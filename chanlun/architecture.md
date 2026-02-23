# 缠论 Invester - AI-Native MCP 架构设计文档

**项目名称:** 缠论 Invester (ChanLun Invester)  
**版本:** v2.0 (AI-Native MCP Edition)  
**基于:** 缠中说禅"教你炒股票"108 课  
**架构模式:** AI-Native + MCP (Model Context Protocol)  
**创建日期:** 2026-02-22  
**更新日期:** 2026-02-22

---

## 目录

1. [架构愿景](#1-架构愿景)
2. [MCP 架构概览](#2-mcp 架构概览)
3. [核心模块设计](#3-核心模块设计)
4. [AI Agent 系统](#4-ai-agent 系统)
5. [订阅与配额管理](#5-订阅与配额管理)
6. [数据层设计](#6-数据层设计)
7. [API 与 MCP 工具](#7-api 与 mcp 工具)
8. [技术栈选型](#8-技术栈选型)
9. [部署架构](#9-部署架构)
10. [开发路线图](#10-开发路线图)

---

## 1. 架构愿景

### 1.1 从"工具"到"平台"的演进

**chanlun-pro (传统工具):**
```
用户 → GUI 界面 → 单体应用 → 数据库
```

**ChanLun Invester (AI-Native 平台):**
```
用户/AI Agent → MCP 协议 → 微服务集群 → 多模态数据
```

### 1.2 核心设计理念

1. **AI-Native First** - 为 AI Agent 设计，而非仅为人类用户
2. **MCP Protocol** - 基于 Model Context Protocol 的标准化接口
3. **Composable** - 可组合的工具和服务
4. **Scalable** - 从单机到集群的无缝扩展
5. **Monetizable** - 内建订阅和配额管理

### 1.3 使用场景

#### 场景 1: 散户投资者 (自然语言交互)
```
用户： "帮我看看 000001 现在有什么买卖点"
    ↓
AI Agent → MCP: query_buy_sell_points(symbol="000001.SZ")
    ↓
返回： "30 分钟级别第二类买点形成于 14:30，价格 16.23 元"
```

#### 场景 2: 量化开发者 (API 集成)
```python
from mcp_client import MCPClient

client = MCPClient()
bsp = await client.call_tool("query_buy_sell_points", {
    "symbol": "000001.SZ",
    "level": "30m",
    "type": ["buy1", "buy2", "buy3"]
})
```

#### 场景 3: 机构客户 (私有化部署)
```
内部系统 → MCP Gateway → 本地 ChanLun 服务
                  ↓
            数据隔离 + 定制开发
```

---

## 2. MCP 架构概览

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Clients)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Web App     │ │ Mobile App  │ │ CLI/SDK     │ │ AI Agents │ │
│  │ (React)     │ │ (Flutter)   │ │ (Python)    │ │ (LLM)     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MCP Protocol (JSON-RPC over WebSocket/HTTP)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Gateway (入口网关)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ 身份验证     │ │ 配额检查     │ │ 限流控制     │ │ 路由转发  │ │
│  │ (JWT/OAuth) │ │ (Redis)     │ │ (Token Bucket)│ │ (gRPC)   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gRPC (内部通信)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     MCP Server 集群                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              MCP Tools (标准化接口)                      │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │   │
│  │  │ 行情数据   │ │ 走势分析   │ │ 买卖点     │ │ 预警订阅 │ │   │
│  │  │ klines    │ │ analyze   │ │ bsp       │ │ alerts  │ │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │   │
│  │  │ 策略回测   │ │ 实盘交易   │ │ 风险监控   │ │ 用户管理 │ │   │
│  │  │ backtest  │ │ trade     │ │ risk      │ │ user    │ │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └─────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent 系统                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ 分析 Agent   │ │ 监控 Agent   │ │ 交易 Agent   │ │ 学习 Agent │ │
│  │ (Analysis)  │ │ (Monitor)   │ │ (Trading)   │ │ (Learning)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                                                                       │
│  每个 Agent 可通过 MCP 调用工具，也可与其他 Agent 协作                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      核心引擎层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Rust 引擎   │ │ Python 服务 │ │ 算法库       │ │ 缓存层    │ │
│  │ (高性能)    │ │ (业务逻辑)  │ │ (缠论算法)  │ │ (Redis)   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      数据层                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ PostgreSQL  │ │ ClickHouse  │ │ Redis       │ │ S3        │ │
│  │ (业务数据)  │ │ (时序数据)  │ │ (缓存)      │ │ (文件)    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 MCP 协议设计

**基于 JSON-RPC 2.0 over WebSocket/HTTP:**

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "query_buy_sell_points",
    "arguments": {
      "symbol": "000001.SZ",
      "level": "30m",
      "type": ["buy1", "buy2", "buy3"]
    }
  }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "content": [
      {
        "type": "buy2",
        "price": 16.23,
        "time": "2026-02-22T14:30:00Z",
        "confirmed": true
      }
    ],
    "isError": false
  }
}
```

### 2.3 MCP 工具清单

| 工具名称 | 功能 | 配额影响 |
|----------|------|----------|
| `get_klines` | 获取 K 线数据 | 计入 API 调用 |
| `analyze_structure` | 走势结构分析 | 计入分析次数 |
| `query_buy_sell_points` | 查询买卖点 | **计入预警配额** |
| `subscribe_alert` | 订阅价格/买卖点预警 | 计入监控股票数 |
| `backtest_strategy` | 策略回测 | 计入回测次数 |
| `execute_trade` | 实盘交易 (仅企业版) | - |
| `get_user_quota` | 查询用户配额状态 | 免费 |
| `list_tools` | 列出可用工具 | 免费 |

---

## 3. 核心模块设计

### 3.1 MCP Gateway

**职责:** 请求入口、身份验证、配额检查、限流、路由

**技术栈:** Node.js + Fastify + Redis

```typescript
// MCP Gateway 核心逻辑
interface MCPGateway {
  // 身份验证
  authenticate(token: string): Promise<User>;
  
  // 配额检查
  checkQuota(user: User, tool: string): Promise<QuotaStatus>;
  
  // 限流
  rateLimit(user: User): Promise<void>;
  
  // 路由到 MCP Server
  route(request: MCPRequest, server: MCPServer): Promise<MCPResponse>;
  
  // 记录使用
  recordUsage(user: User, tool: string, cost: number): Promise<void>;
}
```

**中间件链:**
```
Request → Authentication → Rate Limit → Quota Check → Logging → Route → Response
```

### 3.2 MCP Server

**职责:** MCP 工具实现、业务逻辑、协调核心引擎

**技术栈:** Python FastAPI + gRPC

```python
class MCPServer:
    def __init__(self):
        self.tools = {
            "query_buy_sell_points": self.query_bsp,
            "subscribe_alert": self.subscribe_alert,
            "get_klines": self.get_klines,
            # ... 其他工具
        }
    
    async def call_tool(self, name: str, arguments: dict) -> MCPResult:
        if name not in self.tools:
            raise ToolNotFoundError(f"Tool {name} not found")
        
        tool_func = self.tools[name]
        return await tool_func(**arguments)
    
    async def query_bsp(self, symbol: str, level: str, type: List[str]) -> MCPResult:
        # 调用核心引擎
        result = await self.engine.query_buy_sell_points(symbol, level, type)
        return MCPResult(content=result)
```

### 3.3 核心引擎 (Rust)

**职责:** 高性能缠论算法计算

**技术栈:** Rust + PyO3 (Python 绑定)

```rust
// Rust 核心引擎接口
#[pyclass]
pub struct ChanLunEngine {
    // 引擎配置
    config: EngineConfig,
}

#[pymethods]
impl ChanLunEngine {
    // 计算分型、笔、线段
    pub fn analyze_structure(&self, klines: Vec<KLine>) -> AnalysisResult {
        // 并行计算
        let fractals = self.detect_fractals(&klines);
        let strokes = self.divide_strokes(&fractals);
        let segments = self.divide_segments(&strokes);
        
        AnalysisResult {
            fractals,
            strokes,
            segments,
        }
    }
    
    // 识别中枢
    pub fn identify_centers(&self, segments: Vec<Segment>) -> Vec<Center> {
        segments.par_iter()  // 并行迭代
            .map(|s| self.compute_center(s))
            .collect()
    }
    
    // 背驰检测
    pub fn detect_divergence(&self, segment_a: &Segment, segment_b: &Segment) -> DivergenceResult {
        // MACD 力度比较
        let macd_area_a = self.calculate_macd_area(segment_a);
        let macd_area_b = self.calculate_macd_area(segment_b);
        
        DivergenceResult {
            has_divergence: macd_area_b < macd_area_a * 0.8,
            confidence: self.calculate_confidence(segment_a, segment_b),
        }
    }
}
```

### 3.4 AI Agent 系统

**职责:** 智能交互、多 Agent 协作、自然语言理解

**技术栈:** LangChain + LLM (GPT-4/Claude/本地模型)

```python
class ChanLunAgent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
        self.tools = self._load_mcp_tools()
        
    async def chat(self, user_message: str) -> str:
        # 1. 理解用户意图
        intent = await self.llm.parse_intent(user_message)
        
        # 2. 选择合适的 MCP 工具
        tool_name = self._select_tool(intent)
        
        # 3. 调用 MCP 工具
        result = await self.mcp.call_tool(tool_name, intent.args)
        
        # 4. 生成自然语言回复
        response = await self.llm.generate_response(user_message, result)
        
        return response

# 多 Agent 协作
class MultiAgentSystem:
    def __init__(self):
        self.agents = {
            "analyst": AnalysisAgent(),
            "monitor": MonitorAgent(),
            "trader": TradingAgent(),
            "learner": LearningAgent(),
        }
    
    async def collaborate(self, task: str) -> str:
        # 任务分解
        subtasks = await self.planner.decompose(task)
        
        # 分配给不同 Agent
        results = await asyncio.gather(
            *[self.agents[sub.agent].execute(sub.task) for sub in subtasks]
        )
        
        # 汇总结果
        return await self.synthesizer.synthesize(results)
```

---

## 4. AI Agent 系统

### 4.1 Agent 类型

| Agent | 职责 | MCP 工具使用 |
|-------|------|-------------|
| **分析 Agent** | 走势分解、买卖点识别 | `analyze_structure`, `query_bsp` |
| **监控 Agent** | 实时监控、预警推送 | `subscribe_alert`, `get_market_status` |
| **交易 Agent** | 策略执行、订单管理 | `execute_trade`, `get_position` |
| **学习 Agent** | 回测优化、策略迭代 | `backtest_strategy`, `get_performance` |

### 4.2 Agent 协作流程

```
用户请求: "帮我找到所有 30 分钟级别形成第二类买点的股票，并回测的策略"
    ↓
Planner Agent: 分解为 3 个子任务
    ↓
1. 分析 Agent: 扫描全市场，找出 30 分钟 buy2 的股票列表
2. 学习 Agent: 对这些股票进行历史回测
3. 监控 Agent: 设置价格预警
    ↓
Synthesizer Agent: 汇总结果，生成报告
    ↓
返回用户：股票列表 + 回测结果 + 预警设置确认
```

### 4.3 Agent 配置

```yaml
agents:
  analyst:
    model: claude-3-opus
    tools:
      - analyze_structure
      - query_buy_sell_points
      - get_klines
    quota:
      max_requests_per_hour: 100
  
  monitor:
    model: gpt-4-turbo
    tools:
      - subscribe_alert
      - get_market_status
    quota:
      max_active_alerts: 50
  
  trader:
    model: claude-3-sonnet
    tools:
      - execute_trade
      - get_position
      - cancel_order
    quota:
      max_trades_per_day: 100
    security:
      require_confirmation: true
```

---

## 5. 订阅与配额管理

### 5.1 订阅层级

```sql
CREATE TYPE subscription_plan AS ENUM ('free', 'pro', 'developer', 'enterprise');

CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id),
    plan            subscription_plan NOT NULL,
    status          VARCHAR(20) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end   TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    stripe_subscription_id VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 配额定义

```yaml
quota_config:
  free:
    bsp_query:
      limit: 3
      period: month
    alert_subscription:
      limit: 5
      period: permanent
    api_call:
      limit: 1000
      period: day
    backtest:
      limit: 0
      period: month
  
  pro:
    bsp_query:
      limit: -1  # -1 = unlimited
      period: month
    alert_subscription:
      limit: 50
      period: permanent
    api_call:
      limit: 10000
      period: day
    backtest:
      limit: 10
      period: month
  
  developer:
    bsp_query:
      limit: -1
      period: month
    alert_subscription:
      limit: 100
      period: permanent
    api_call:
      limit: 50000
      period: day
    backtest:
      limit: 100
      period: month
  
  enterprise:
    bsp_query:
      limit: -1
    alert_subscription:
      limit: -1
    api_call:
      limit: -1
    backtest:
      limit: -1
```

### 5.3 配额检查中间件

```python
from fastapi import Request, HTTPException
from functools import wraps

async def quota_check(tool_name: str):
    """MCP 工具配额检查装饰器"""
    
    async def middleware(request: Request, call_next):
        # 获取用户
        user = request.state.user
        
        # 获取配额配置
        quota_config = await get_quota_config(user.plan, tool_name)
        
        # -1 表示无限
        if quota_config.limit == -1:
            return await call_next(request)
        
        # 检查已用额度
        used = await get_usage_count(user.id, tool_name, quota_config.period)
        
        if used >= quota_config.limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "tool": tool_name,
                    "used": used,
                    "limit": quota_config.limit,
                    "period": quota_config.period,
                    "upgrade_url": "/billing/upgrade"
                }
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 记录使用
        await increment_usage(user.id, tool_name)
        
        return response
    
    return middleware
```

### 5.4 使用统计

```python
class UsageTracker:
    async def record(self, user_id: str, tool: str, cost: int = 1):
        """记录工具使用"""
        await redis.incrby(f"usage:{user_id}:{tool}:current", cost)
        await redis.incr(f"usage:{user_id}:{tool}:total")
        
        # 写入数据库 (异步)
        await db.execute(
            "INSERT INTO usage_logs (user_id, tool, cost) VALUES ($1, $2, $3)",
            user_id, tool, cost
        )
    
    async def get_remaining(self, user_id: str, tool: str) -> int:
        """获取剩余配额"""
        plan = await get_user_plan(user_id)
        limit = get_quota_limit(plan, tool)
        
        if limit == -1:
            return -1  # unlimited
        
        used = await redis.get(f"usage:{user_id}:{tool}:current")
        return limit - (used or 0)
```

---

## 6. 数据层设计

### 6.1 数据库 Schema

```sql
-- K 线数据表 (ClickHouse)
CREATE TABLE klines (
    symbol      String,
    level       String,
    time        DateTime,
    open        Decimal64(4),
    high        Decimal64(4),
    low         Decimal64(4),
    close       Decimal64(4),
    volume      Decimal64(4),
    amount      Decimal64(4),
    
    INDEX idx_symbol_time (symbol, time)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(time)
ORDER BY (symbol, level, time);

-- 分析结果表 (PostgreSQL)
CREATE TABLE analysis_results (
    id              UUID PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    level           VARCHAR(10) NOT NULL,
    analysis_type   VARCHAR(50) NOT NULL,  -- fractals, strokes, segments, centers
    result          JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP,
    
    INDEX idx_symbol_level (symbol, level),
    INDEX idx_created (created_at)
);

-- 买卖点表
CREATE TABLE buy_sell_points (
    id              UUID PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    type            VARCHAR(10) NOT NULL,  -- buy1, buy2, buy3, sell1, sell2, sell3
    price           DECIMAL(18, 4) NOT NULL,
    time            TIMESTAMP NOT NULL,
    level           VARCHAR(10) NOT NULL,
    center_id       UUID REFERENCES centers(id),
    is_confirmed    BOOLEAN DEFAULT false,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户订阅表
CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(id),
    plan            VARCHAR(20) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    current_period_start  TIMESTAMP,
    current_period_end    TIMESTAMP,
    stripe_id       VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 使用配额表
CREATE TABLE usage_quotas (
    id              UUID PRIMARY KEY,
    user_id         UUID NOT NULL,
    quota_type      VARCHAR(50) NOT NULL,
    used_count      INTEGER DEFAULT 0,
    limit_count     INTEGER,
    reset_date      TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, quota_type)
);
```

### 6.2 缓存策略

```yaml
cache_config:
  klines:
    backend: redis
    ttl: 300  # 5 分钟
    key_pattern: "klines:{symbol}:{level}"
  
  analysis:
    backend: redis
    ttl: 3600  # 1 小时
    key_pattern: "analysis:{symbol}:{level}:{type}"
  
  user_quota:
    backend: redis
    ttl: 60  # 1 分钟
    key_pattern: "quota:{user_id}"
```

### 6.3 数据流

```
实时行情 → Kafka → Stream Processor → ClickHouse
                                    ↓
                              Analysis Engine
                                    ↓
                              Redis Cache
                                    ↓
                              PostgreSQL (结果)
```

---

## 7. API 与 MCP 工具

### 7.1 MCP 工具定义

```typescript
// MCP Tool Schema
interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, {
      type: string;
      description: string;
      required?: boolean;
    }>;
  };
  quotaCost?: number;
}

// 工具注册
const tools: MCPTool[] = [
  {
    name: "query_buy_sell_points",
    description: "查询指定股票的买卖点信息",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "股票代码，如 000001.SZ"
        },
        level: {
          type: "string",
          description: "分析级别：1m, 5m, 30m, 1d, 1w, 1M",
          enum: ["1m", "5m", "30m", "1d", "1w", "1M"]
        },
        type: {
          type: "array",
          items: { type: "string", enum: ["buy1", "buy2", "buy3", "sell1", "sell2", "sell3"] },
          description: "买卖点类型"
        }
      }
    },
    quotaCost: 1  // 消耗 1 次买卖点查询配额
  },
  {
    name: "get_klines",
    description: "获取 K 线数据",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        level: { type: "string" },
        start: { type: "string", format: "date-time" },
        end: { type: "string", format: "date-time" },
        limit: { type: "integer", maximum: 10000 }
      }
    },
    quotaCost: 1  // 消耗 1 次 API 调用配额
  },
  // ... 其他工具
];
```

### 7.2 REST API

```yaml
openapi: 3.0.0
info:
  title: ChanLun Invester API
  version: 2.0.0

paths:
  /api/v2/mcp/tools:
    get:
      summary: 列出可用 MCP 工具
      operationId: listTools
      security:
        - BearerAuth: []
      responses:
        200:
          description: 工具列表
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/MCPTool'
  
  /api/v2/mcp/tools/call:
    post:
      summary: 调用 MCP 工具
      operationId: callTool
      security:
        - BearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MCPCallRequest'
      responses:
        200:
          description: 工具执行结果
        429:
          description: 配额超限
  
  /api/v2/user/quota:
    get:
      summary: 查询用户配额状态
      operationId: getUserQuota
      security:
        - BearerAuth: []
      responses:
        200:
          description: 配额状态
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuotaStatus'
```

### 7.3 WebSocket 实时推送

```typescript
// WebSocket 连接
const ws = new WebSocket("wss://api.chanlun-invester.com/mcp");

// 订阅买卖点预警
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  method: "subscribe",
  params: {
    channel: "buy_sell_points",
    filter: {
      symbol: "000001.SZ",
      type: ["buy1", "buy2", "buy3"]
    }
  }
}));

// 接收推送
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.method === "buy_sell_points/alert") {
    console.log("新买卖点:", message.params.data);
  }
};
```

---

## 8. 技术栈选型

### 8.1 完整技术栈

| 层级 | 组件 | 技术选型 |
|------|------|----------|
| **客户端** | Web App | React 18 + TypeScript + TradingView |
| | Mobile App | Flutter (iOS/Android) |
| | SDK | Python + TypeScript |
| **网关** | MCP Gateway | Node.js 20 + Fastify |
| | 认证 | JWT + OAuth2 |
| | 限流 | Redis Token Bucket |
| **服务层** | MCP Server | Python 3.11 + FastAPI |
| | AI Agent | LangChain + Claude/GPT-4 |
| | 任务队列 | Celery + Redis |
| **引擎层** | 核心算法 | Rust 1.75 + PyO3 |
| | 数值计算 | ndarray + Blas |
| **数据层** | 关系数据库 | PostgreSQL 15 |
| | 时序数据库 | ClickHouse 23 |
| | 缓存 | Redis 7 Cluster |
| | 对象存储 | MinIO / S3 |
| **基础设施** | 容器化 | Docker + Kubernetes |
| | 服务网格 | Istio |
| | 监控 | Prometheus + Grafana |
| | 日志 | ELK Stack |
| | CI/CD | GitHub Actions + ArgoCD |

### 8.2 成本估算 (月)

| 服务 | 配置 | 数量 | 单价 | 小计 |
|------|------|------|------|------|
| **Kubernetes** | 4 核 8GB | 5 | $80 | $400 |
| **ClickHouse** | 8 核 16GB | 3 | $200 | $600 |
| **PostgreSQL** | 4 核 8GB | 2 | $100 | $200 |
| **Redis** | 2 核 4GB | 3 | $50 | $150 |
| **存储** | 1TB SSD | 1 | $100 | $100 |
| **带宽** | 1TB | 1 | $100 | $100 |
| **合计** | - | - | - | **$1,550/月** |

---

## 9. 部署架构

### 9.1 生产环境架构

```
                              ┌─────────────┐
                              │   用户请求   │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │ CloudFlare  │
                              │ (DDoS/CDN)  │
                              └──────┬──────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                         Kubernetes 集群 (AWS/GCP)                        │
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │  Ingress (TLS)  │  │ MCP Gateway     │  │ WebSocket Gateway│        │
│  │  ×3 副本         │  │ ×5 副本          │  │ ×3 副本           │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│           │                    │                    │                   │
│  ┌────────▼────────────────────▼────────────────────▼────────┐        │
│  │                    服务网格 (Istio)                        │        │
│  └────────┬────────────────────┬────────────────────┬────────┘        │
│           │                    │                    │                   │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐        │
│  │ MCP Server      │  │ AI Agent        │  │ 后台任务        │        │
│  │ ×10 副本         │  │ ×5 副本          │  │ (Celery) ×5     │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│           │                    │                    │                   │
│  ┌────────▼─────────────────────────────────────────▼────────┐        │
│  │                    核心引擎 (Rust)                         │        │
│  │                    ×10 副本                                │        │
│  └───────────────────────────────────────────────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  PostgreSQL     │  │  ClickHouse     │  │  Redis Cluster  │
│  (主从 +PgBouncer)│  │  (分布式 3 节点)  │  │  (哨兵 3 节点)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 9.2 扩缩容策略

```yaml
# HPA (Horizontal Pod Autoscaler) 配置
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### 9.3 多可用区部署

```
区域：us-east-1
├── 可用区 A (主)
│   ├── Kubernetes 节点 ×5
│   ├── PostgreSQL 主库
│   └── Redis 主节点
├── 可用区 B (备)
│   ├── Kubernetes 节点 ×3
│   ├── PostgreSQL 从库
│   └── Redis 从节点
└── 可用区 C (备)
    ├── Kubernetes 节点 ×2
    └── ClickHouse 节点 ×3
```

---

## 10. 开发路线图

### Phase 1: 基础架构 (4 周) ✅

- [x] MCP 协议定义
- [x] 商业模式设计
- [ ] MCP Gateway 实现
- [ ] 基础 MCP 工具 (klines, analyze)
- [ ] 用户认证系统

### Phase 2: 核心功能 (6 周)

- [ ] 缠论算法封装 (Rust → Python)
- [ ] 买卖点识别工具
- [ ] 订阅与配额系统
- [ ] Stripe 支付集成
- [ ] 免费版上线 MVP

### Phase 3: AI Agent (6 周)

- [ ] LangChain 集成
- [ ] 分析 Agent 开发
- [ ] 监控 Agent 开发
- [ ] 自然语言接口
- [ ] Pro 版发布

### Phase 4: 高级功能 (8 周)

- [ ] 回测框架
- [ ] 数据下载模块
- [ ] 预警系统 (WebSocket)
- [ ] 监控 Agent 完善
- [ ] Developer 版发布

### Phase 5: 企业级 (8 周)

- [ ] 私有化部署方案
- [ ] 实盘交易接口
- [ ] 机构 Dashboard
- [ ] 专属支持体系
- [ ] Enterprise 版发布

### Phase 6: 生态建设 (持续)

- [ ] SDK 完善 (Python/TS)
- [ ] 开发者文档
- [ ] 合作伙伴计划
- [ ] 社区运营
- [ ] 应用市场

---

## 11. 风险与缓解

### 11.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Rust 引擎性能不达标 | 高 | 低 | 早期性能测试、优化热点 |
| MCP 协议兼容性 | 中 | 中 | 严格遵循规范、版本管理 |
| AI Agent 准确性 | 高 | 中 | 人工审核、置信度阈值 |

### 11.2 商业风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 获客成本过高 | 高 | 中 | 内容营销、社区运营 |
| 付费转化率低 | 高 | 中 | 优化免费体验、限时优惠 |
| 竞品价格战 | 中 | 低 | 差异化、技术优势 |

### 11.3 合规风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 投资建议资质 | 高 | 中 | 免责声明、不提供投资建议 |
| 数据隐私 | 高 | 中 | GDPR 合规、数据加密 |
| 支付合规 | 中 | 低 | 正规支付渠道、税务合规 |

---

## 12. 关键指标 (KPI)

### 12.1 技术指标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 (P95) | < 100ms |
| WebSocket 延迟 | < 50ms |
| 系统可用性 | 99.9% |
| 买卖点识别准确率 | > 85% (回测) |

### 12.2 业务指标

| 指标 | 第 1 年目标 |
|------|------------|
| 注册用户 | 10,000 |
| 付费用户 | 200 (2% 转化) |
| MRR | ¥40 万 |
| 毛利率 | > 60% |

---

## 总结

### 架构优势

1. **AI-Native** - 为 AI Agent 时代设计
2. **MCP 标准化** - 易于集成和扩展
3. **内建商业化** - 订阅和配额管理原生支持
4. **高性能** - Rust 核心引擎
5. **可扩展** - Kubernetes 微服务架构

### 下一步

1. **本周:** MCP Gateway 原型
2. **下周:** 基础 MCP 工具实现
3. **2 周后:** 免费版 MVP 上线

---

**文档结束**

**最后更新:** 2026-02-22  
**作者:** ChanLun Invester Team  
**版本:** v2.0 (AI-Native MCP)
