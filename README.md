# Trading System - Rust + Python Hybrid Architecture

<div align="center">

**High-performance trading system implementing pen theory (笔理论) with automatic failover**

🦀 Rust Core &nbsp;•&nbsp; 🐍 Python Backup &nbsp;•&nbsp; 🔄 Auto-Switch &nbsp;•&nbsp; 🐳 Docker Ready

</div>

## 🎯 Project Overview

A production-ready trading system that implements **pen theory (笔理论)** with the new 3-K-line definition (新笔), strict line segment division (线段划分), and configurable MACD indicators. Built with a hybrid Rust + Python architecture for maximum performance and reliability.

### Key Features

- ✅ **New Pen Definition**: 3 K-line minimum with strict fractal validation (新笔定义)
- ✅ **Strict Segment Division**: Feature sequence implementation (特征序列)
- ✅ **Center Detection**: Automatic center identification (中枢识别)
- ✅ **Configurable MACD**: Runtime-adjustable parameters (12/26/9 standard)
- ✅ **Dual Architecture**: Rust primary + Python automatic failover
- ✅ **Health Monitoring**: Continuous health checks with automatic switchover
- ✅ **Buy/Sell Points**: All 3 types auto-detected (三类买卖点)
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

### 🧪 Run Examples

```bash
# Example 2: Pen identification
python3 examples/02_pen/main.py

# Example 5: Divergence detection
python3 examples/05_divergence/main.py

# Example 6: Type 1 Buy/Sell Points
python3 examples/06_bsp1/main.py
```

---

### 📊 Monitor Symbols

```bash
# Monitor any symbol (real-time analysis)
python3 launcher.py monitor UVIX --level 5m

# Monitor with custom alert channel
python3 launcher.py monitor AAPL --level 30m --alert telegram
```

**Note:** Full UVIX real-time monitoring requires the dedicated module. The monitor command will run analysis with sample data for any symbol.

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
