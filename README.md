# Trading System - Rust + Python Hybrid Architecture

<div align="center">

**High-performance trading system implementing pen theory (笔理论) with automatic failover**

🦀 Rust Core &nbsp;•&nbsp; 🐍 Python Backup &nbsp;•&nbsp; 🔄 Auto-Switch &nbsp;•&nbsp; 🐳 Docker Ready

</div>

## 🎯 Project Overview

A production-ready trading system that implements **pen theory (笔理论)** with the new 3-K-line definition (新笔), strict line segment division (线段划分), and configurable MACD indicators. Built with a hybrid Rust + Python architecture for maximum performance and reliability.

### 📊 Default Data Source: Yahoo Finance

The system uses **Yahoo Finance** as the default data source for all market data:

- ✅ **Real-time prices** for US stocks, ETFs, and cryptocurrencies
- ✅ **Historical data** for backtesting and analysis
- ✅ **Multiple timeframes**: 5m, 30m, daily, weekly, monthly
- ✅ **No API key required** - free and unlimited
- ✅ **Automatic integration** with all monitoring and analysis tools

### Key Features

- ✅ **New Pen Definition**: 3 K-line minimum with strict fractal validation (新笔定义)
- ✅ **Strict Segment Division**: Feature sequence implementation (特征序列)
- ✅ **Center Detection**: Automatic center identification (中枢识别)
- ✅ **Configurable MACD**: Runtime-adjustable parameters (12/26/9 standard)
- ✅ **Dual Architecture**: Rust primary + Python automatic failover
- ✅ **Health Monitoring**: Continuous health checks with automatic switchover
- ✅ **Buy/Sell Points**: All 3 types auto-detected (三类买卖点)
- ✅ **Yahoo Finance Integration**: Default data source for real-time market data
- ✅ **Docker Deployment**: Ready for development and production
- ✅ **Security First**: Comprehensive .gitignore, no sensitive data in repo

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Trading System                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   Rust Engine    │ ──────► │  Python Engine   │          │
│  │   (Primary)      │ Health  │   (Backup)       │          │
│  │   Port: 50051    │ Check   │   Port: 50052    │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                              │                   │
│           └──────────┬───────────────────┘                   │
│                      │                                       │
│           ┌──────────▼───────────┐                          │
│           │  Failover Coordinator │                          │
│           │  (Auto-switch logic)  │                          │
│           └───────────────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Hybrid?

| Component              | Technology | Why                                        |
| ---------------------- | ---------- | ------------------------------------------ |
| **Core Trading Logic** | 🦀 Rust     | Performance, safety, concurrency           |
| **Integration Layer**  | 🐍 Python   | Flexibility, rapid iteration, ML libraries |
| **Communication**      | gRPC       | Language-agnostic, health checks built-in  |
| **Failover**           | Automatic  | Zero-downtime switching on failures        |

## 📊 Data Source

### Default: Yahoo Finance

The system uses **Yahoo Finance** as the default and primary data source:

**Why Yahoo Finance?**
- ✅ **Free** - No API key or subscription required
- ✅ **Real-time** - Live market data during trading hours
- ✅ **Comprehensive** - US stocks, ETFs, indices, cryptocurrencies
- ✅ **Historical** - Years of historical data for backtesting
- ✅ **Multiple timeframes** - 1m, 5m, 30m, daily, weekly, monthly
- ✅ **Easy to use** - Simple `yfinance` Python library

**Supported Assets:**
- US Stocks (AAPL, MSFT, TSLA, etc.)
- ETFs (SPY, QQQ, UVIX, VIX, etc.)
- Cryptocurrencies (BTC-USD, ETH-USD, etc.)
- Indices (^GSPC, ^DJI, ^IXIC, etc.)
- Futures and commodities

**Configuration:**
```yaml
# config/default.yaml
data:
  provider: yahoo_finance  # Default data source
  cache_enabled: false     # Real-time data
  update_interval: 60      # Update every 60 seconds
```

No API keys or credentials needed - just start using it!

---

## 📁 Project Structure

**Total:** 52 files (~6.5 MB)

```
trading-system/
├── README.md                 # Project overview
├── SECURITY.md               # Security guidelines ⭐
├── ARCHITECTURE.md           # System architecture
├── DEVELOPMENT_PLAN.md       # Development roadmap
├── QUICK_REFERENCE.md        # Quick reference
├── GANTT_CHART.md           # Project timeline
├── .gitignore                # Git ignore rules
├── launcher.py               # CLI tool
│
├── Cargo.toml                # Rust workspace config
├── docker-compose.yml        # Docker setup
├── docker-compose.prod.yml   # Production Docker
├── Dockerfile.rust           # Rust Dockerfile
├── Dockerfile.python         # Python Dockerfile
│
├── rust-core/                # 🦀 Rust Engine (10 files)
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs           # Library root
│       ├── main.rs          # Server binary
│       ├── kline/           # K-line data structures
│       ├── fractal/         # Fractal detection
│       ├── pen/             # Pen theory (新笔定义)
│       ├── segment/         # Segment division (特征序列)
│       ├── indicators/      # MACD indicators
│       ├── health/          # Health monitoring
│       └── grpc/            # gRPC service
│
├── python-layer/             # 🐍 Python Layer (9 files)
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── trading_system/
│       ├── __init__.py
│       ├── kline/           # K-line backup
│       ├── fractal/         # Fractal backup
│       ├── pen/             # Pen backup
│       ├── segment/         # Segment backup
│       ├── center/          # Center detection (中枢)
│       └── indicators/      # MACD indicators
│
├── proto/                    # Protocol Buffers
│   └── trading.proto        # gRPC service definition
│
├── config/                   # Configuration (3 files)
│   ├── default.yaml         # System configuration
│   ├── live.yaml            # Live trading config
│   └── macd_params.yaml     # MACD parameters
│
├── examples/                 # Working Examples (10 directories)
│   ├── 01_basic_fractal/    # Basic fractal identification
│   ├── 02_pen/              # Pen identification (笔)
│   ├── 03_segment/          # Segment division (线段)
│   ├── 04_center/           # Center detection (中枢)
│   ├── 05_divergence/       # Divergence detection (背驰)
│   ├── 06_bsp1/             # Type 1 Buy/Sell Points
│   ├── 07_bsp2/             # Type 2 Buy/Sell Points
│   ├── 08_bsp3/             # Type 3 Buy/Sell Points
│   ├── 09_interval_set/     # Interval Set (区间套)
│   └── 10_multi_level/      # Multi-level Analysis
│
├── tests/                    # Test Suite (4 files)
│   ├── test_fractal.py      # Fractal tests
│   ├── test_pen.py          # Pen tests
│   ├── test_segment.py      # Segment tests
│   └── test_integration.py  # Integration tests
│
└── scripts/                  # Automation Scripts (5 files)
    ├── build.sh             # Build all components
    ├── test.sh              # Run all tests
    ├── deploy.sh            # Docker deployment
    └── ...
```

## 🚀 Quick Start

### ⚙️ Prerequisites

- **Linux** (Tested on Ubuntu 22.04+)
- **Rust** 1.75+ (`rustup install stable`)
- **Python** 3.10+
- **Protobuf Compiler** (`apt install protobuf-compiler`)
- **Docker & Docker Compose** (Optional)

---

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/weisenchen/chanlunInvester.git
cd chanlunInvester

# Install Python dependencies (includes yfinance for Yahoo Finance data)
python3 -m venv venv
source venv/bin/activate
pip install -r python-layer/requirements.txt
```

**✅ Yahoo Finance is the default data source - no configuration needed!**

---

### 🐳 Option 1: Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

### 💻 Option 2: Local Development

```bash
# 1. Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r python-layer/requirements.txt

# 2. Build Rust core
./scripts/build.sh

# 3. Run tests
./scripts/test.sh
```

---

## 📖 Detailed Usage Examples

### 🧪 1. Running ChanLun Examples

**Example 2: Pen Identification (笔识别)**
```bash
cd /home/wei/.openclaw/workspace/trading-system
python3 examples/02_pen/main.py
```

**Example 3: Segment Division (线段划分)**
```bash
python3 examples/03_segment/main.py
```

**Example 5: Divergence Detection (背驰检测)**
```bash
python3 examples/05_divergence/main.py
```

**Example 6: Type 1 Buy/Sell Points (第一类买卖点)**
```bash
python3 examples/06_bsp1/main.py
```

---

### 📊 2. Real-time Monitoring

**Monitor UVIX (5-minute timeframe)**
```bash
python3 launcher.py monitor UVIX --level 5m
```

**Monitor Apple Stock (30-minute timeframe)**
```bash
python3 launcher.py monitor AAPL --level 30m
```

**Monitor Tesla (Daily timeframe)**
```bash
python3 launcher.py monitor TSLA --level day
```

**Monitor Bitcoin**
```bash
python3 launcher.py monitor BTC-USD --level 1h
```

**Monitor S&P 500 Index**
```bash
python3 launcher.py monitor ^GSPC --level day
```

---

### 🔍 3. Analysis Workflow

**Step 1: Fetch Real-time Data**
```bash
python3 launcher.py monitor UVIX --level 5m
```

**Output:**
```
[1] Starting real-time monitor...
    Symbol: UVIX
    Level:  5m

[2] Fetching data from Yahoo Finance...
    ✓ Fetched 100 K-lines
    Range: 2026-03-09 → 2026-03-13
    Price: $8.87

[3] Analyzing UVIX...
    ✓ Fractals: 39 (Top: 17, Bottom: 22)
    ✓ Pens: 28 (Up: 19, Down: 9)
    ✓ Segments: 2 (Up: 2, Down: 0)

Trading Signals
  ⚪ HOLD - No clear signal
     Current: UP segment
```

**Step 2: Run Detailed Example**
```bash
# For deeper analysis, run specific examples
python3 examples/05_divergence/main.py
```

**Step 3: Check for Buy/Sell Signals**
```bash
# Monitor will automatically detect and show signals
python3 launcher.py monitor UVIX --level 30m
```

---

### 🐳 4. Docker Deployment

**Start All Services**
```bash
cd /home/wei/.openclaw/workspace/trading-system
docker-compose up -d
```

**View Logs**
```bash
docker-compose logs -f
```

**Stop Services**
```bash
docker-compose down
```

**Production Deployment**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

### 🧪 5. Testing

**Run All Tests**
```bash
./scripts/test.sh
```

**Run Specific Test**
```bash
python3 tests/test_fractal.py
python3 tests/test_pen.py
python3 tests/test_segment.py
python3 tests/test_integration.py
```

**Test Output Example:**
```
======================================================================
Fractal Detection Module Tests
分型检测模块测试
======================================================================

Testing top fractal detection...
  ✓ Top fractal detection passed
Testing bottom fractal detection...
  ✓ Bottom fractal detection passed
Testing multiple fractals...
  ✓ Multiple fractals detection passed (3 fractals)

======================================================================
Test Results: 5 passed, 0 failed
======================================================================
```

---

### 🔧 6. Build & Development

**Build Rust Core**
```bash
./scripts/build.sh
```

**Install Python Dependencies**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r python-layer/requirements.txt
```

**Development Mode**
```bash
# Install in editable mode
pip install -e python-layer

# Run examples directly
python3 examples/02_pen/main.py
```

---

### 📈 7. Common Trading Scenarios

**Scenario 1: Day Trading UVIX**
```bash
# Monitor 5-minute chart for entry points
python3 launcher.py monitor UVIX --level 5m

# Run every 10 minutes during market hours
watch -n 600 python3 launcher.py monitor UVIX --level 5m
```

**Scenario 2: Swing Trading Stocks**
```bash
# Monitor daily chart for swing trades
python3 launcher.py monitor AAPL --level day

# Check 30-minute for precise entry
python3 launcher.py monitor AAPL --level 30m
```

**Scenario 3: Multi-timeframe Analysis**
```bash
# Start with daily for trend
python3 launcher.py monitor TSLA --level day

# Then 30-minute for setup
python3 launcher.py monitor TSLA --level 30m

# Finally 5-minute for entry
python3 launcher.py monitor TSLA --level 5m
```

---

### ⚙️ 8. Configuration

**View Current Configuration**
```bash
cat config/default.yaml
```

**Modify MACD Parameters**
```yaml
# config/default.yaml
macd:
  fast_period: 12      # Fast EMA
  slow_period: 26      # Slow EMA
  signal_period: 9     # Signal line
```

**Change Pen Definition**
```yaml
# config/default.yaml
chanlun:
  stroke_definition: new_3kline  # New 3-K-line definition
  segment_strict: true           # Strict segment division
```

---

### 📊 9. Data Management

**Clear Cache**
```bash
rm -rf ~/.cache/yfinance
```

**Export Analysis Results**
```bash
python3 launcher.py monitor UVIX --level 5m --output results.json
```

**View Logs**
```bash
tail -f logs/uvix_cron.log
tail -f logs/realtime_alerts.log
```

---

### 🆘 10. Troubleshooting

**Issue: No data returned**
```bash
# Check symbol is correct
python3 launcher.py monitor AAPL --level day

# Verify internet connection
ping yahoo.com

# Check yfinance installation
pip show yfinance
```

**Issue: Import errors**
```bash
# Reinstall dependencies
pip install -r python-layer/requirements.txt --force-reinstall
```

**Issue: Rust build fails**
```bash
# Update Rust
rustup update

# Clean and rebuild
cd rust-core
cargo clean
cargo build --release
```

---

### 🐳 Quick Start (with Docker)

The easiest way to get the full stack (Rust Core + Python Backup + Monitor) running:

```bash
# 1. Start core services
docker-compose up -d

# 2. Check logs
docker-compose logs -f
```

For the full failover-enabled setup:
```bash
docker-compose --profile backup --profile monitor up -d
```

---

### 💻 Local Deployment (Manual)

For development or direct host execution, follow these steps:

#### 1. Environment Setup
```bash
# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r python-layer/requirements.txt
pip install -e python-layer
```

#### 2. Build Components
Use the integrated build script to compile the Rust core and generate gRPC stubs:
```bash
./scripts/build.sh
```

#### 3. Run Components
Open two terminals (with virtualenv activated):

**Terminal 1: Rust Trading Engine (Primary)**
```bash
cd rust-core
cargo run --release
```

**Terminal 2: Python Integration Layer / Launcher**
```bash
# Use the unified launcher (see section below)
python launcher.py analyze 000001.SZ
```

---

### �️ Unified Launcher (`launcher.py`)

The project includes a powerful CLI tool to interact with all system features.

| Command    | Usage                                    | Description                               |
| ---------- | ---------------------------------------- | ----------------------------------------- |
| `analyze`  | `python launcher.py analyze <symbol>`    | Run ChanLun analysis on a symbol          |
| `examples` | `python launcher.py examples --list`     | List all available strategy examples      |
| `run`      | `python launcher.py examples --run <id>` | Run a specific example (e.g., `02`, `05`) |
| `server`   | `python launcher.py server`              | Start the API server                      |
| `monitor`  | `python launcher.py monitor <symbol>`    | Start real-time monitoring                |

**Example: Analyze 'Ping An Bank' (000001.SZ)**
```bash
python launcher.py analyze 000001.SZ --level 30m
```

---

### 📈 UVIX Monitor & Alerts

A specialized real-time monitor for UVIX is included in the `examples/` directory:
- **Location**: `examples/uvix_monitor.py`
- **Features**: 30m/5m multi-level analysis, Telegram alerts, CSV/JSON logging.
- **Documentation**: See [UVIX_MONITOR_README.md](examples/UVIX_MONITOR_README.md) for setup details.

---

## 📊 Configuration

### MACD Parameters
Edit `config/default.yaml`:
```yaml
macd:
  fast_period: 12      # Fast EMA period
  slow_period: 26      # Slow EMA period
  signal_period: 9     # Signal line period
```

### Pen Theory Logic
```yaml
pen:
  definition: new_3kline      # new_3kline | traditional
  strict_validation: true     # No overlapping pens
  min_klines_between_turns: 3
```

---

## 🧪 Testing

Run the full suite (Python + Rust + Examples):
```bash
./scripts/test.sh
```

Individual tests:
- **Rust**: `cd rust-core && cargo test`
- **Python**: `pytest tests/`

---

## � Roadmap & Status

### ✅ Completed (v1.0)
- [x] **Hybrid Architecture**: Rust performance + Python flexibility.
- [x] **Core Logic**: Full implementation of Pen (新笔) and Segment (线段).
- [x] **Indicators**: Optimized MACD and Fractal detection.
- [x] **Unified CLI**: Comprehensive launcher for all operations.
- [x] **Alert System**: Telegram integration for real-time signals.

### 🚧 In Progress
- [ ] Production-grade gRPC server implementation in Rust core.
- [ ] Persistent storage (PostgreSQL) for historical analysis.
- [ ] Real-time data connectors for US/China stock markets.

---

## 🤝 Contributing & License

1. Fork the repo.
2. Create a feature branch.
3. Submit a PR!

Licensed under **MIT**.

---

<div align="center">
**Built with ❤️ by Weisen**  
🦀 Rust + 🐍 Python + 🔄 Automatic Failover = 💪 Reliable Trading System
</div>
