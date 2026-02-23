# 缠论 Invester - 本地部署方案 (单机版)

**版本:** v2.1 (Local Edition)  
**目标:** 零成本启动，本地验证，逐步扩展  
**更新日期:** 2026-02-22

---

## 1. 设计原则

### 1.1 核心思路

**不租云端、不花冤枉钱、先验证再扩展**

```
开发阶段: 本地笔记本 → 验证有效 → 云端部署
          (0 成本)      (有收入)   (用利润扩展)
```

### 1.2 需求分析

**必须功能 (MVP):**
- ✅ 缠论算法计算 (分型、笔、线段、中枢、买卖点)
- ✅ K 线数据获取 (免费数据源)
- ✅ 本地数据库存储
- ✅ 简单 Web 界面查看
- ✅ 基础预警功能

**可选功能 (后期):**
- ⏸️ AI Agent (可本地跑开源模型)
- ⏸️ 多用户系统 (先服务自己)
- ⏸️ 订阅支付 (验证后再做)
- ⏸️ 高并发 (单机足够)

---

## 2. 技术架构 (简化版)

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                             │
│  ┌───────────────────┐  ┌───────────────────┐         │
│  │  Web UI (本地)     │  │  CLI/Python SDK   │         │
│  │  localhost:3000   │  │  本地调用          │         │
│  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    应用服务层 (单机)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  FastAPI Server (localhost:8000)                │   │
│  │  ├─ MCP 工具接口 (简化版)                        │   │
│  │  ├─ 用户认证 (SQLite)                           │   │
│  │  ├─ 配额管理 (内存/文件)                         │   │
│  │  └─ WebSocket 推送 (本地)                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    核心引擎层                             │
│  ┌───────────────────┐  ┌───────────────────┐         │
│  │  Rust 引擎        │  │  Python 包装器     │         │
│  │  (缠论算法)       │  │  (PyO3 绑定)       │         │
│  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据层 (本地)                          │
│  ┌───────────────────┐  ┌───────────────────┐         │
│  │  SQLite           │  │  本地文件系统      │         │
│  │  (业务数据)       │  │  (K 线缓存)         │         │
│  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    数据源 (免费)                          │
│  ┌───────────────────┐  ┌───────────────────┐         │
│  │  AKShare          │  │  Baostock         │         │
│  │  (免费行情)       │  │  (免费财经数据)    │         │
│  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 与云端架构对比

| 组件 | 云端架构 | 本地部署 (简化) | 差异 |
|------|----------|----------------|------|
| **部署环境** | Kubernetes 集群 | 单机/Docker | ✅ 简化 10 倍 |
| **数据库** | PostgreSQL+ClickHouse | SQLite | ✅ 零配置 |
| **缓存** | Redis Cluster | 内存/本地文件 | ✅ 无需额外服务 |
| **网关** | MCP Gateway (多副本) | FastAPI 单实例 | ✅ 合并功能 |
| **引擎** | Rust ×10 副本 | Rust 单进程 | ✅ 同核心 |
| **认证** | OAuth2+JWT | SQLite 用户表 | ✅ 简化 |
| **配额** | Redis 计数 | JSON 文件 | ✅ 简化 |

---

## 3. 硬件需求

### 3.1 最低配置

| 组件 | 要求 | 说明 |
|------|------|------|
| **CPU** | 4 核 | 现代笔记本标配 |
| **内存** | 8GB | Rust+Python+ 浏览器 |
| **存储** | 50GB SSD | K 线数据 + 数据库 |
| **网络** | 普通宽带 | 下载行情数据 |

### 3.2 推荐配置

| 组件 | 要求 | 说明 |
|------|------|------|
| **CPU** | 8 核+ | 并行计算更快 |
| **内存** | 16GB | 多任务不卡顿 |
| **存储** | 256GB SSD | 存储更多历史数据 |
| **网络** | 50Mbps+ | 实时数据流畅 |

### 3.3 功耗估算

```
笔记本电脑运行:
- CPU 占用：~30% (闲时) → ~80% (计算时)
- 内存占用：~4GB
- 功耗：~30W (普通笔记本)
- 电费：~¥50/月 (24 小时运行)
```

---

## 4. 软件栈 (100% 免费开源)

### 4.1 核心软件

| 组件 | 技术选型 | 许可 | 成本 |
|------|----------|------|------|
| **操作系统** | Windows/Mac/Linux | - | ¥0 |
| **Python** | 3.11+ | PSF | ¥0 |
| **Rust** | 1.75+ | MIT/Apache | ¥0 |
| **数据库** | SQLite 3 | Public Domain | ¥0 |
| **Web 框架** | FastAPI | MIT | ¥0 |
| **前端** | React + Vite | MIT | ¥0 |
| **图表** | TradingView Light Charts | Apache 2.0 | ¥0 |
| **数据源** | AKShare + Baostock | 开源 | ¥0 |

### 4.2 可选软件

| 组件 | 技术选型 | 用途 | 成本 |
|------|----------|------|------|
| **Docker** | Docker Desktop | 容器化部署 | ¥0 |
| **AI 模型** | Ollama + Qwen | 本地 AI Agent | ¥0 |
| **任务调度** | APScheduler | 定时任务 | ¥0 |

---

## 5. 目录结构

```
chanlun-local/
├── README.md              # 项目说明
├── requirements.txt       # Python 依赖
├── Cargo.toml            # Rust 依赖
├── docker-compose.yml    # Docker 部署 (可选)
│
├── core/                 # Rust 核心引擎
│   ├── src/
│   │   ├── lib.rs
│   │   ├── fractal.rs    # 分型计算
│   │   ├── stroke.rs     # 笔划分
│   │   ├── segment.rs    # 线段划分
│   │   ├── center.rs     # 中枢识别
│   │   └── divergence.rs # 背驰判断
│   └── Cargo.toml
│
├── backend/              # Python 后端
│   ├── main.py           # FastAPI 入口
│   ├── mcp_tools/        # MCP 工具实现
│   │   ├── klines.py
│   │   ├── analyze.py
│   │   ├── bsp.py
│   │   └── alerts.py
│   ├── engine/           # Rust 引擎绑定
│   │   └── chanlun_engine.py
│   ├── data/             # 数据源
│   │   ├── akshare_client.py
│   │   └── baostock_client.py
│   ├── database/         # 数据库操作
│   │   ├── sqlite_db.py
│   │   └── models.py
│   ├── auth/             # 认证
│   │   └── simple_auth.py
│   └── requirements.txt
│
├── frontend/             # React 前端
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── KChart.tsx      # K 线图
│   │   │   ├── BSPList.tsx     # 买卖点列表
│   │   │   └── AlertPanel.tsx  # 预警面板
│   │   └── api/                # API 调用
│   │       └── client.ts
│   └── vite.config.ts
│
├── data/                 # 本地数据
│   ├── klines/           # K 线缓存
│   ├── db.sqlite         # SQLite 数据库
│   └── config.json       # 配置文件
│
├── scripts/              # 工具脚本
│   ├── download_klines.py  # 下载历史数据
│   ├── backup_db.sh        # 备份数据库
│   └── start.sh            # 启动脚本
│
└── tests/                # 测试
    ├── test_engine.py
    └── test_mcp.py
```

---

## 6. 核心模块实现

### 6.1 Rust 核心引擎 (简化版)

```rust
// core/src/lib.rs
use pyo3::prelude::*;

mod fractal;
mod stroke;
mod segment;
mod center;
mod divergence;

#[pyclass]
pub struct ChanLunEngine {
    config: EngineConfig,
}

#[pymethods]
impl ChanLunEngine {
    #[new]
    fn new() -> Self {
        ChanLunEngine {
            config: EngineConfig::default(),
        }
    }
    
    /// 分析走势结构
    fn analyze(&self, klines: Vec<KLine>) -> AnalysisResult {
        let fractals = fractal::detect(&klines);
        let strokes = stroke::divide(&fractals);
        let segments = segment::divide(&strokes);
        let centers = center::identify(&segments);
        
        AnalysisResult {
            fractals,
            strokes,
            segments,
            centers,
        }
    }
    
    /// 查询买卖点
    fn query_bsp(&self, segments: Vec<Segment>, centers: Vec<Center>) -> Vec<BuySellPoint> {
        let mut bsp_list = Vec::new();
        
        // 第一类买卖点 (背驰)
        for i in 1..segments.len() {
            if let Some(divergence) = divergence::check(&segments[i-1], &segments[i]) {
                if divergence.confidence > 0.8 {
                    bsp_list.push(BuySellPoint::new(
                        "buy1",
                        segments[i].low,
                        segments[i].end_time,
                    ));
                }
            }
        }
        
        // 第二类买卖点 (回踩)
        for i in 2..segments.len() {
            if segments[i].direction == "up" && 
               segments[i].low > segments[i-2].low {
                bsp_list.push(BuySellPoint::new(
                    "buy2",
                    segments[i].low,
                    segments[i].end_time,
                ));
            }
        }
        
        // 第三类买卖点 (回踩中枢)
        for center in &centers {
            if let Some(bsp) = center.check_third_buy(&segments) {
                bsp_list.push(bsp);
            }
        }
        
        bsp_list
    }
}
```

### 6.2 Python 后端 (FastAPI)

```python
# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
from datetime import datetime
import json

from engine.chanlun_engine import ChanLunEngine
from mcp_tools.klines import get_klines
from mcp_tools.bsp import query_buy_sell_points
from mcp_tools.alerts import subscribe_alert
from data.akshare_client import AKShareClient

app = FastAPI(title="ChanLun Invester (Local)")

# CORS (允许本地前端访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化引擎
engine = ChanLunEngine()
data_client = AKShareClient()

# 数据库初始化
def init_db():
    conn = sqlite3.connect("data/db.sqlite")
    cursor = conn.cursor()
    
    # 用户表 (简化版，先服务自己)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 配额表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotas (
            user_id INTEGER,
            quota_type TEXT,
            used_count INTEGER DEFAULT 0,
            limit_count INTEGER,
            reset_date DATE,
            PRIMARY KEY (user_id, quota_type)
        )
    """)
    
    # 买卖点记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bsp_records (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            type TEXT,
            price REAL,
            time TIMESTAMP,
            level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup():
    init_db()

# MCP 工具接口
@app.post("/api/mcp/tools/call")
async def mcp_call_tool(tool: str, args: dict):
    """统一 MCP 工具调用接口"""
    
    tools = {
        "get_klines": get_klines,
        "analyze_structure": analyze_structure,
        "query_buy_sell_points": query_buy_sell_points,
        "subscribe_alert": subscribe_alert,
    }
    
    if tool not in tools:
        raise HTTPException(status_code=404, detail=f"Tool {tool} not found")
    
    # 配额检查 (简化版)
    await check_quota(tool)
    
    # 调用工具
    result = await tools[tool](**args)
    
    # 记录使用
    await record_usage(tool)
    
    return {"content": result, "isError": False}

# 行情数据接口
@app.get("/api/klines/{symbol}")
async def get_klines_api(
    symbol: str,
    level: str = "1d",
    start: str = None,
    end: str = None,
    limit: int = 1000
):
    """获取 K 线数据"""
    klines = await data_client.get_klines(
        symbol=symbol,
        level=level,
        start=start,
        end=end,
        limit=limit
    )
    return klines

# 买卖点查询接口
@app.get("/api/bsp/{symbol}")
async def get_bsp_api(symbol: str, level: str = "30m"):
    """查询买卖点"""
    bsp_list = await query_buy_sell_points(
        symbol=symbol,
        level=level,
        type=["buy1", "buy2", "buy3", "sell1", "sell2", "sell3"]
    )
    return bsp_list

# 预警接口
@app.post("/api/alerts/subscribe")
async def subscribe_alert_api(
    symbol: str,
    condition: dict,
    user_id: int = 1  # 简化版，默认用户 1
):
    """订阅预警"""
    # 检查配额
    used = await get_alert_count(user_id)
    if used >= 5:  # 免费版 5 只股票
        raise HTTPException(
            status_code=429,
            detail="Alert quota exceeded. Max 5 for free plan."
        )
    
    alert_id = await subscribe_alert(
        user_id=user_id,
        symbol=symbol,
        condition=condition
    )
    return {"alert_id": alert_id}

# 配额查询接口
@app.get("/api/user/quota")
async def get_quota(user_id: int = 1):
    """查询用户配额状态"""
    return {
        "bsp_query": {"used": 2, "limit": 3, "period": "month"},
        "alerts": {"used": 3, "limit": 5, "period": "permanent"},
        "api_call": {"used": 150, "limit": 1000, "period": "day"}
    }

# 启动命令
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6.3 配额管理 (简化版)

```python
# backend/auth/quota.py
import json
from datetime import datetime, timedelta
from pathlib import Path

QUOTA_FILE = Path("data/quotas.json")

QUOTA_LIMITS = {
    "free": {
        "bsp_query": {"limit": 3, "period": "month"},
        "alerts": {"limit": 5, "period": "permanent"},
        "api_call": {"limit": 1000, "period": "day"},
        "backtest": {"limit": 0, "period": "month"},
    },
    "pro": {
        "bsp_query": {"limit": -1},  # -1 = unlimited
        "alerts": {"limit": 50},
        "api_call": {"limit": 10000, "period": "day"},
        "backtest": {"limit": 10, "period": "month"},
    },
    "enterprise": {
        "bsp_query": {"limit": -1},
        "alerts": {"limit": -1},
        "api_call": {"limit": -1},
        "backtest": {"limit": -1},
    }
}

async def check_quota(tool: str, user_plan: str = "free"):
    """检查配额"""
    quotas = QUOTA_LIMITS.get(user_plan, QUOTA_LIMITS["free"])
    
    if tool not in quotas:
        return  # 无限制
    
    limit = quotas[tool].get("limit", 0)
    if limit == -1:
        return  # 无限
    
    # 读取当前使用
    usage = await get_usage(user_plan, tool)
    
    if usage >= limit:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "tool": tool,
                "used": usage,
                "limit": limit,
                "upgrade_hint": "Upgrade to pro for unlimited access"
            }
        )

async def record_usage(user_plan: str, tool: str, count: int = 1):
    """记录使用"""
    usage = await get_usage(user_plan, tool)
    usage += count
    
    # 写入文件
    quotas = load_quotas()
    quotas[user_plan][tool] = usage
    save_quotas(quotas)

def load_quotas() -> dict:
    """加载配额文件"""
    if not QUOTA_FILE.exists():
        return {"free": {}, "pro": {}, "enterprise": {}}
    
    with open(QUOTA_FILE, "r") as f:
        return json.load(f)

def save_quotas(quotas: dict):
    """保存配额文件"""
    QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUOTA_FILE, "w") as f:
        json.dump(quotas, f, indent=2)
```

### 6.4 数据下载工具

```python
# scripts/download_klines.py
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import time

def download_daily_data(symbol: str, start_date: str, end_date: str):
    """下载日线数据"""
    print(f"Downloading {symbol} from {start_date} to {end_date}")
    
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"  # 前复权
    )
    
    # 保存到数据库
    conn = sqlite3.connect("data/db.sqlite")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS klines_daily (
            symbol TEXT,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            PRIMARY KEY (symbol, date)
        )
    """)
    
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO klines_daily 
            (symbol, date, open, high, low, close, volume, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            row["日期"],
            row["开盘"],
            row["最高"],
            row["最低"],
            row["收盘"],
            row["成交量"],
            row["成交额"]
        ))
    
    conn.commit()
    conn.close()
    print(f"Downloaded {len(df)} records")

def download_all_stocks():
    """下载全市场股票数据"""
    # 获取所有股票代码
    stock_list = ak.stock_info_a_code_name()
    
    for _, row in stock_list.iterrows():
        symbol = row["code"]
        download_daily_data(
            symbol=symbol,
            start_date="20200101",
            end_date=datetime.now().strftime("%Y%m%d")
        )
        time.sleep(0.5)  # 避免请求过快

if __name__ == "__main__":
    # 下载特定股票
    download_daily_data("000001", "20200101", datetime.now().strftime("%Y%m%d"))
    
    # 或下载全市场
    # download_all_stocks()
```

---

## 7. 部署方案

### 7.1 方案 A: 直接运行 (最简单)

```bash
# 1. 克隆项目
git clone https://github.com/weisenchen/chanlunInvester.git
cd chanlunInvester/chanlun-local

# 2. 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 3. 编译 Rust 引擎
cd core
cargo build --release

# 4. 安装 Python 依赖
cd ../backend
pip install -r requirements.txt

# 5. 安装前端依赖
cd ../frontend
npm install

# 6. 启动后端
cd ../backend
python main.py

# 7. 另开终端，启动前端
cd frontend
npm run dev

# 访问 http://localhost:3000
```

### 7.2 方案 B: Docker 部署 (推荐)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/db.sqlite
      - RUST_BACKTRACE=1
    restart: unless-stopped
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
  
  # 可选：本地 AI Agent (需要 8GB+ 内存)
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama-data:/root/.ollama
    restart: unless-stopped
    profiles:
      - ai
```

```bash
# 一键启动
docker-compose up -d

# 启动 AI 功能 (可选)
docker-compose --profile ai up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 7.3 方案 C: 一键脚本

```bash
#!/bin/bash
# scripts/install.sh

echo "🚀 ChanLun Invester 本地版安装脚本"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# 检查 Rust
if ! command -v rustc &> /dev/null; then
    echo "⚠️  Rust not found. Installing..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# 安装依赖
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

echo "📦 Installing Node dependencies..."
cd ../frontend
npm install

# 编译 Rust
echo "🔨 Building Rust engine..."
cd ../core
cargo build --release

# 初始化数据库
echo "🗄️  Initializing database..."
cd ../backend
python -c "from main import init_db; init_db()"

# 下载示例数据
echo "📥 Downloading sample data..."
python ../scripts/download_klines.py

echo "✅ Installation complete!"
echo ""
echo "启动命令:"
echo "  cd backend && python main.py  # 启动后端"
echo "  cd frontend && npm run dev    # 启动前端"
echo "  访问 http://localhost:3000"
```

---

## 8. 成本分析

### 8.1 零成本启动

| 项目 | 云端方案 | 本地方案 | 节省 |
|------|----------|----------|------|
| **服务器** | ¥1,200/月 | ¥0 | ¥1,200 |
| **数据库** | ¥400/月 | ¥0 | ¥400 |
| **存储** | ¥200/月 | ¥0 (本地硬盘) | ¥200 |
| **带宽** | ¥300/月 | ¥0 | ¥300 |
| **其他** | ¥200/月 | ¥0 | ¥200 |
| **合计** | ¥2,300/月 | ¥50/月 (电费) | **¥2,250/月** |

**年度节省：¥27,000**

### 8.2 时间成本

| 任务 | 云端部署 | 本地部署 |
|------|----------|----------|
| ** setup** | 2-3 天 | 2-3 小时 |
| **运维** | 持续投入 | 几乎为零 |
| **调试** | 远程排查 | 本地直接调试 |

---

## 9. 功能对比

### 9.1 本地版 vs 云端版

| 功能 | 本地版 | 云端版 | 说明 |
|------|--------|--------|------|
| **缠论算法** | ✅ 完整 | ✅ 完整 | 同核心 |
| **K 线数据** | ✅ 免费源 | ✅ 多数据源 | 本地用 AKShare |
| **买卖点识别** | ✅ 完整 | ✅ 完整 | 同算法 |
| **预警推送** | ✅ 本地 | ✅ WebSocket | 本地用轮询 |
| **Web 界面** | ✅ 简化版 | ✅ 完整版 | 功能相同 |
| **API 访问** | ✅ 本地 | ✅ 公网 | 本地限 localhost |
| **AI Agent** | ⚠️ 可选 | ✅ 完整 | 本地需 Ollama |
| **多用户** | ❌ 单用户 | ✅ 多用户 | 本地服务自己 |
| **订阅支付** | ❌ 无 | ✅ Stripe | 验证后再做 |
| **高并发** | ❌ 单机 | ✅ 集群 | 本地足够 |
| **数据隔离** | ❌ 本地 | ✅ 多租户 | 本地无需 |

### 9.2 何时升级到云端？

**升级信号:**
- ✅ 有稳定付费用户 (>10 人)
- ✅ 月收入 > ¥5,000/月
- ✅ 需要 24 小时在线服务
- ✅ 多用户并发访问
- ✅ 需要公网 API 访问

**升级路径:**
```
本地验证 → 小规模云端 (1 台服务器) → 完整云端架构
(0-3 个月)  (月收入>5k)           (月收入>20k)
```

---

## 10. 开发路线图

### Phase 1: 核心引擎 (2 周)

- [ ] Rust 引擎编译通过
- [ ] 分型、笔、线段算法验证
- [ ] Python 绑定测试
- [ ] 单元测试覆盖

### Phase 2: 后端服务 (2 周)

- [ ] FastAPI 框架搭建
- [ ] MCP 工具接口实现
- [ ] SQLite 数据库集成
- [ ] 配额管理系统

### Phase 3: 数据源 (1 周)

- [ ] AKShare 集成
- [ ] 历史数据下载工具
- [ ] 增量更新机制

### Phase 4: 前端界面 (2 周)

- [ ] React 项目搭建
- [ ] TradingView 图表集成
- [ ] 买卖点展示
- [ ] 预警面板

### Phase 5: 本地验证 (持续)

- [ ] 自己使用测试
- [ ] 策略回测验证
- [ ] 实盘模拟测试
- [ ] bug 修复和优化

**总周期: 7 周 (约 2 个月)**

---

## 11. 风险与缓解

### 11.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Rust 编译失败 | 高 | 提供预编译二进制 |
| 数据源不稳定 | 中 | 多数据源备份 |
| 本地性能不足 | 低 | 优化算法、限制数据量 |

### 11.2 使用风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 电脑故障数据丢失 | 高 | 定期备份到云盘 |
| 忘记运行服务 | 中 | 设置开机自启 |
| 网络安全 | 中 | 仅监听 localhost |

---

## 12. 总结

### 12.1 核心优势

1. **零成本启动** - 无需租用服务器
2. **快速验证** - 当天安装当天用
3. **数据可控** - 本地存储，隐私安全
4. **低维护** - 无需运维，专注产品
5. **平滑升级** - 验证后可迁移云端

### 12.2 行动建议

**本周:**
1. 克隆项目，安装依赖
2. 编译 Rust 引擎
3. 下载示例数据
4. 启动测试

**本月:**
1. 自己日常使用
2. 发现并修复 bug
3. 优化用户体验
4. 验证策略有效性

**下阶段:**
- 有效果 → 考虑小规模云端部署
- 无效 → 调整策略，无金钱损失

### 12.3 第一性原理

**不要为了部署而部署，要为了验证而部署。**

在没验证策略有效性之前，每一分云端投入都是浪费。
先用本地版验证，有收入后再云端，这是最稳妥的路径。

---

**文档结束**

---

**快速开始:**

```bash
# 安装
git clone https://github.com/weisenchen/chanlunInvester.git
cd chanlunInvester/chanlun-local
bash scripts/install.sh

# 启动
cd backend && python main.py
cd frontend && npm run dev

# 访问
http://localhost:3000
```

**最后更新:** 2026-02-22  
**版本:** v2.1 Local Edition  
**许可:** MIT License
