# ChanLun Invester Examples

10 progressive examples demonstrating the ChanLun trading system.

## Quick Start

```bash
# All examples run from this directory
cd examples

# Example 1: Basic Fractal Recognition
python3 01_basic_fractal/main.py

# Example 4: MACD Divergence (requires server)
python3 04_macd_divergence/main.py

# Example 10: Full System Integration
python3 10_full_system/main.py
```

## Example Progression

### Phase 1: Foundation

| # | Example | Concept | ChanLun Lesson |
|---|---------|---------|----------------|
| 01 | Basic Fractal | 顶/底分型，containment | 62, 65 |
| 02 | Pen Detection | 新笔 (3-Kline definition) | 62, 65 |
| 03 | Segment Division | 特征序列，two-case judgment | 67 |

### Phase 2: Analysis

| # | Example | Concept | ChanLun Lesson |
|---|---------|---------|----------------|
| 04 | MACD Divergence | 背驰 detection | 15, 24, 27 |
| 05 | B/S Points | 1/2/3 买/卖 | 12, 20, 21, 53 |
| 06 | Multi-Level | 多级别联立 | 27, 61 |

### Phase 3: Strategies

| # | Example | Concept | Type |
|---|---------|---------|------|
| 07 | Center Analysis | 中枢 identification | 89, 90 |
| 08 | Trend Following | 1/2 buy in uptrend | Strategy |
| 09 | Mean Reversion | Divergence reversal | Strategy |
| 10 | Full System | Complete pipeline | Integration |

## Server Requirements

Examples 4-10 require the Rust gRPC server running:

```bash
# Build and run server
cd rust-core
cargo build --release
cargo run --bin trading-server

# Server listens on localhost:50051
```

## Learning Path

1. **Start with Example 1** - Understand fractals (foundation)
2. **Progress sequentially** - Each builds on previous
3. **Run Example 10 last** - Shows complete system
4. **Modify and experiment** - Change parameters, test patterns

## Key Concepts

- **分型 (Fractal)**: 3-K-line reversal patterns
- **笔 (Pen)**: Connected fractals, minimum 3 K-lines
- **线段 (Segment)**: Connected pens with feature sequences
- **背驰 (Divergence)**: Price vs MACD divergence
- **买卖点 (B/S Points)**: Optimal entry/exit points

## Next Steps

After completing all examples:
1. Review DEVELOPMENT_PLAN.md for advanced topics
2. Study chanlunskill.md for theory details
3. Implement custom strategies
4. Connect to live market data
