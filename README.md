# Trading System - Rust + Python Hybrid Architecture

<div align="center">

**High-performance trading system implementing pen theory (笔理论) with automatic failover**

🦀 Rust Core &nbsp;•&nbsp; 🐍 Python Backup &nbsp;•&nbsp; 🔄 Auto-Switch &nbsp;•&nbsp; 🐳 Docker Ready

</div>

## 🎯 Project Overview

A production-ready trading system that implements **pen theory (笔理论)** with the new 3-K-line definition (新笔), strict line segment division (线段划分), and configurable MACD indicators. Built with a hybrid Rust + Python architecture for maximum performance and reliability.

### Key Features

- ✅ **New Pen Definition**: 3 K-line minimum with strict fractal validation
- ✅ **Strict Segment Division**: Feature sequence implementation with inclusion handling
- ✅ **Configurable MACD**: Runtime-adjustable parameters (fast/slow/signal periods)
- ✅ **Dual Architecture**: Rust primary + Python automatic failover
- ✅ **Health Monitoring**: Continuous health checks with automatic switchover
- ✅ **Docker Deployment**: Ready for development and production
- ✅ **No Frontend**: CLI/API-only interface for backend integration

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

```
chanlunInvester/
├── Cargo.toml                # Rust workspace configuration
├── docker-compose.yml        # Development Docker setup
├── docker-compose.prod.yml   # Production Docker setup
├── Dockerfile.rust           # Rust container build
├── Dockerfile.python         # Python container build
│
├── rust-core/                # 🦀 Rust Trading Engine
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs           # Library root
│       ├── main.rs          # Server binary
│       ├── kline/           # K-line data structures
│       ├── pen/             # Pen theory implementation
│       ├── segment/         # Line segment division
│       ├── indicators/      # MACD and other indicators
│       ├── health/          # Health monitoring
│       └── grpc/            # gRPC service
│
├── python-layer/             # 🐍 Python Backup & Integration
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── trading_system/
│       ├── __init__.py
│       ├── kline/           # Python K-line (backup)
│       ├── pen/             # Python pen theory (backup)
│       ├── segment/         # Python segment (backup)
│       └── indicators/      # Python indicators (TA-Lib)
│
├── proto/                    # Protocol Buffers
│   └── trading.proto        # gRPC service definition
│
├── config/                   # Configuration files
│   ├── default.yaml         # System configuration
│   └── macd_params.yaml     # MACD parameter presets
│
└── scripts/                  # Automation scripts
    ├── build.sh             # Build everything
    ├── test.sh              # Run all tests
    └── deploy.sh            # Docker deployment
```

## 🚀 Deployment & Usage

### ⚙️ Prerequisites

- **Linux** (Tested on Ubuntu 22.04+)
- **Rust** 1.75+ (`rustup install stable`)
- **Python** 3.10+
- **Protobuf Compiler** (`apt install protobuf-compiler`)
- **Docker & Docker Compose** (Optional, for containerized deployment)

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
