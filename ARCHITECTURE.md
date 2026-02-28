# Trading System Architecture - Rust + Python Hybrid

## Overview
A high-performance trading system implementing pen theory (笔理论) with dual architecture for reliability.

## Architecture Decision: Hybrid Rust + Python

### Why Dual Architecture?
1. **Rust (Primary)**: Performance-critical core trading logic, pen/segment calculations
2. **Python (Backup)**: Flexibility, rapid iteration, automatic failover
3. **Auto-switch**: Health monitoring switches to Python if Rust fails

### Communication Strategy
**Recommended: gRPC over FFI**
- Cleaner separation of concerns
- Easier testing and deployment
- Language-agnostic interface
- Built-in health checking
- Can run components independently

**Alternative: PyO3 (if tight coupling needed)**
- Lower latency
- Single process
- More complex build/deployment

## Project Structure

```
trading-system/
├── Cargo.toml                    # Rust workspace root
├── pyproject.toml                # Python package config
├── docker-compose.yml            # Multi-service orchestration
├── Dockerfile.rust               # Rust service container
├── Dockerfile.python             # Python service container
├── config/
│   ├── default.yaml              # Default configuration
│   └── macd_params.yaml          # MACD parameter presets
│
├── rust-core/                    # Rust trading engine
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs               # Library root
│   │   ├── main.rs              # Binary entry point
│   │   ├── kline/               # K-line data structures
│   │   │   ├── mod.rs
│   │   │   ├── types.rs         # OHLCV, TimeFrame enums
│   │   │   └── handler.rs       # Data ingestion
│   │   ├── pen/                 # Pen theory (笔) implementation
│   │   │   ├── mod.rs
│   │   │   ├── definition.rs    # New pen definition (3 K-lines)
│   │   │   ├── validator.rs     # Strict validation rules
│   │   │   └── calculator.rs    # Pen formation logic
│   │   ├── segment/             # Line segment (线段) division
│   │   │   ├── mod.rs
│   │   │   ├── feature_seq.rs   # Characteristic sequence
│   │   │   ├── divider.rs       # Segment division algorithm
│   │   │   └── strict_rules.rs  # Strict implementation
│   │   ├── indicators/          # Technical indicators
│   │   │   ├── mod.rs
│   │   │   ├── macd.rs          # Configurable MACD
│   │   │   └── mod.rs
│   │   ├── health/              # Health monitoring
│   │   │   ├── mod.rs
│   │   │   ├── monitor.rs       # Health checks
│   │   │   └── failover.rs      # Auto-switch logic
│   │   └── grpc/                # gRPC service implementation
│   │       ├── mod.rs
│   │       └── service.rs
│   │
├── python-layer/                 # Python integration & backup
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── trading_system/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── kline/               # Python K-line implementation
│   │   ├── pen/                 # Python pen theory (backup)
│   │   ├── segment/             # Python segment division
│   │   ├── indicators/          # Python indicators (TA-Lib wrapper)
│   │   └── grpc_client.py       # gRPC client/server
│   └── tests/
│
├── proto/                        # Protocol Buffers definitions
│   └── trading.proto             # Service interface definition
│
└── scripts/
    ├── build.sh                  # Build automation
    ├── test.sh                   # Test runner
    └── deploy.sh                 # Docker deployment
```

## Core Components

### 1. K-line Data Layer (Rust)
- Immutable OHLCV structures
- TimeFrame enum (1m, 5m, 15m, 1h, 4h, 1d, 1w)
- Efficient data ingestion from exchanges

### 2. Pen Theory Engine (Rust Primary, Python Backup)
**New Pen Definition (新笔):**
- Minimum 3 K-lines
- Strict top/bottom fractal validation
- No overlapping pens
- Gap handling rules

### 3. Segment Division (线段划分)
**Strict Feature Sequence Implementation:**
- Characteristic sequence construction
- Inclusion relationship handling (包含关系)
- Direction determination
- Segment completion criteria

### 4. MACD Indicator
**Configurable Parameters:**
- Fast EMA period (default: 12)
- Slow EMA period (default: 26)
- Signal EMA period (default: 9)
- Runtime configuration via YAML/JSON

### 5. Health Monitoring & Failover
- Heartbeat checks (Rust → Python)
- Latency monitoring
- Automatic switchover on failure
- Manual override capability
- State synchronization

## Data Flow

```
Exchange Data → K-line Handler → Pen Calculator → Segment Divider
                                            ↓
                                      MACD Indicator
                                            ↓
                                      Trading Signals → Output/Storage
                                            ↑
                                    Health Monitor (watchdog)
                                            ↕
                                    Python Backup (standby)
```

## Deployment (Docker)

### Development
```bash
docker-compose up --build
# Runs both Rust + Python services
# Health checks enabled
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
# Rust primary, Python standby
# Auto-failover enabled
```

## Configuration Example

```yaml
# config/default.yaml
system:
  primary_engine: rust
  failover_enabled: true
  health_check_interval_ms: 1000

macd:
  fast_period: 12
  slow_period: 26
  signal_period: 9

pen:
  definition: "new_3kline"  # new_3kline | traditional
  strict_validation: true

segment:
  feature_sequence_strict: true
  handle_inclusion: true

logging:
  level: info
  format: json
```

## Testing Strategy

1. **Unit Tests (Rust)**: `cargo test`
   - Pen formation rules
   - Segment division algorithms
   - MACD calculations

2. **Integration Tests**: Rust ↔ Python gRPC
   - Interface compatibility
   - Failover scenarios
   - Data consistency

3. **Property Tests**: QuickCheck (Rust)
   - Invariant validation
   - Edge cases

## Next Steps

1. ✅ Architecture design (current task)
2. Set up Rust workspace structure
3. Set up Python package structure
4. Define gRPC proto interfaces
5. Implement K-line data structures
6. Implement pen theory (new 3-Kline definition)
7. Implement feature sequence segment division
8. Build health monitoring system
9. Create Docker configuration
10. Write tests

## Technical Decisions Recorded

- **gRPC over FFI**: Cleaner architecture, easier deployment
- **Rust-first**: Performance for critical path
- **Python backup**: Flexibility and rapid iteration
- **No frontend**: CLI/API-only interface
- **Docker deployment**: Consistent environments
- **Configurable MACD**: Runtime parameter adjustment
