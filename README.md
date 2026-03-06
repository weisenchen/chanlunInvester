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

| Component | Technology | Why |
|-----------|-----------|-----|
| **Core Trading Logic** | 🦀 Rust | Performance, safety, concurrency |
| **Integration Layer** | 🐍 Python | Flexibility, rapid iteration, ML libraries |
| **Communication** | gRPC | Language-agnostic, health checks built-in |
| **Failover** | Automatic | Zero-downtime switching on failures |

## 📁 Project Structure

```
trading-system/
├── ARCHITECTURE.md           # Detailed architecture documentation
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

## 🚀 Quick Start

### Prerequisites

- **Rust** 1.75+ (`rustup install stable`)
- **Python** 3.10+ (`python3 --version`)
- **Docker** & **Docker Compose** (`docker --version`)
- **protobuf-compiler** (optional, for gRPC)

### Development

```bash
# 1. Build everything
./scripts/build.sh

# 2. Run tests
./scripts/test.sh

# 3. Start with Docker
docker-compose up

# Or with failover monitoring
docker-compose --profile backup --profile monitor up
```

### Production

```bash
# Deploy to production
./scripts/deploy.sh prod

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Configuration

### MACD Parameters

Edit `config/default.yaml`:

```yaml
macd:
  fast_period: 12      # Fast EMA period
  slow_period: 26      # Slow EMA period
  signal_period: 9     # Signal line period
```

Or use presets from `config/macd_params.yaml`:
- `standard` - Classic settings (12/26/9)
- `fast` - Shorter timeframes (8/17/9)
- `slow` - Longer timeframes (19/39/9)
- `scalping` - Very fast (6/13/5)

### Pen Theory

```yaml
pen:
  definition: new_3kline      # new_3kline | traditional
  strict_validation: true     # No overlapping pens
  min_klines_between_turns: 3
```

### Failover

```yaml
system:
  primary_engine: rust
  failover_enabled: true
  health_check_interval_ms: 1000

health:
  max_failures_before_switch: 3
  response_timeout_ms: 500
```

## 🔧 API Usage

### gRPC Endpoints

| Method | Description |
|--------|-------------|
| `SubmitKlines` | Submit OHLCV data for processing |
| `CalculatePens` | Calculate pens using pen theory |
| `CalculateSegments` | Calculate line segments |
| `GetMACD` | Get MACD indicator values |
| `HealthCheck` | Check service health |
| `GetStatus` | Get overall system status |

### Example (Python)

```python
import grpc
from trading.proto import trading_pb2
from trading.proto import trading_pb2_grpc

# Connect to Rust engine
channel = grpc.insecure_channel('localhost:50051')
stub = trading_pb2_grpc.TradingServiceStub(channel)

# Submit K-lines
klines = [
    trading_pb2.Kline(timestamp=1234567890, open=100, high=105, low=99, close=103, volume=1000),
    # ... more klines
]
response = stub.SubmitKlines(
    trading_pb2.SubmitKlinesRequest(
        symbol="BTC/USD",
        timeframe=trading_pb2.TimeFrame.TIMEFRAME_M5,
        klines=klines
    )
)

# Calculate pens
pens = stub.CalculatePens(
    trading_pb2.CalculatePensRequest(
        symbol="BTC/USD",
        timeframe=trading_pb2.TimeFrame.TIMEFRAME_M5,
        last_n=100
    )
)

print(f"Found {len(pens.pens)} pens")
```

## 🧪 Testing

```bash
# Run all tests
./scripts/test.sh

# Rust tests only
cd rust-core && cargo test

# Python tests only
cd python-layer && python -m pytest tests/
```

## 📖 Examples

Comprehensive examples demonstrating pen theory and buy/sell point identification:

| # | Example | Description | Run Command |
|---|---------|-------------|-------------|
| 02 | 笔识别 (新定义) | New 3-K-line pen definition with fractal detection | `python3 examples/02_pen/main.py` |
| 03 | 线段划分 | Line segment division with feature sequence analysis | `python3 examples/03_segment/main.py` |
| 05 | 背驰与买卖点 | Divergence detection and all 3 buy/sell point types | `python3 examples/05_divergence/main.py` |
| 06 | 第一类买卖点 | Type 1 B/S points (trend divergence) with risk/reward | `python3 examples/06_bsp1/main.py` |
| 07 | 第二类买卖点 | Type 2 B/S points (pullback confirmation) | `python3 examples/07_bsp2/main.py` |
| 08 | 第三类买卖点 | Type 3 B/S points (center breakout) | `python3 examples/08_bsp3/main.py` |
| 09 | 区间套定位 | Multi-level recursive positioning (interval set) | `python3 examples/09_interval_set/main.py` |

Each example includes:
- ✅ Complete algorithm implementation
- ✅ Sample data generation
- ✅ ASCII visualization
- ✅ JSON output
- ✅ Detailed Chinese/English documentation

## 📈 Current Status

### ✅ Completed (v1.0 - 2026-03-01)

- [x] Architecture design
- [x] Project structure setup
- [x] Rust core implementation (kline, pen, segment, indicators, health)
- [x] Python backup layer (kline, fractal, pen, segment, indicators)
- [x] gRPC proto definitions and interface
- [x] Docker configurations (dev + prod)
- [x] Build and deployment scripts
- [x] Health monitoring and auto-failover
- [x] Comprehensive example suite (7 examples, 3200+ lines)
- [x] Unit and integration tests

### 🚧 In Progress

- [ ] Production deployment testing
- [ ] Real market data integration
- [ ] Performance optimization

### 📋 TODO

- [ ] Add more technical indicators (RSI, KDJ, Bollinger Bands)
- [ ] Add data persistence layer (PostgreSQL/InfluxDB)
- [ ] Add backtesting framework
- [ ] Add real-time data feed integration

## 📚 Documentation

- **ARCHITECTURE.md** - Detailed system design
- **proto/trading.proto** - gRPC API reference
- **config/default.yaml** - Configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./scripts/test.sh`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

<div align="center">

**Built with ❤️ by Weisen**

🦀 Rust + 🐍 Python + 🔄 Automatic Failover = 💪 Reliable Trading System

</div>
