# ChanLun Invester — 缠论智能监控系统

**缠论 (ChanLun/Pen Theory) Intelligent Trading System**

Real-time BSP (Buy/Sell Point) detection and alert system for US and Canadian stocks, powered by 缠论 Pen Theory.

## Quick Start

```bash
cd ~/.openclaw/workspace/chanlunInvester

# Full scan (all configured symbols)
python3 src/monitor_all.py

# Run tests
python3 tests/test_bsp_detection.py        # 8 BSP tests
python3 tests/test_divergence_detection.py  # 11 divergence tests
```

## Architecture

```
yfinance (free, no API key)
    │
    ▼
Python Engine (src/trading_system/)
    │
    ├── FractalDetector (分型)
    ├── PenCalculator (笔)
    ├── SegmentCalculator (线段)
    ├── CenterDetector (中枢)
    ├── DivergenceDetector (背驰) — 3 methods
    │   ├── Point method
    │   ├── Area method (MACD柱 area)
    │   └── DIF method (黄白线)
    ├── BSP Detection (买卖点) — all 6 types
    ├── Multi-Level Fusion (多级别联动)
    └── Telegram Alert Delivery
```

## Project Structure

```
src/                          # All source code
├── monitor_all.py            # Production BSP scanner + alert delivery
├── trading_system/           # Core engine (11 modules)
│   ├── kline.py              # K-line data structures
│   ├── fractal.py            # Fractal detection
│   ├── pen.py                # Pen calculation
│   ├── segment.py            # Segment detection
│   ├── center.py             # Center (中枢) detection
│   ├── divergence.py         # Multi-method divergence detection
│   ├── indicators.py         # MACD indicator
│   ├── monitor.py            # Analysis pipeline
│   ├── backtest.py           # Backtesting engine
│   ├── telegram_bot.py       # Telegram bot
│   └── weekly_analysis.py    # Weekly market analysis
├── launcher.py               # Launcher
└── premarket_report.py       # Premarket report script

config/                       # Configuration
├── config.yaml               # Symbols, thresholds, Telegram, fusion weights
├── default.yaml
├── live.yaml
└── macd_params.yaml

tests/                        # 19 unit tests
├── test_bsp_detection.py     # 8 BSP tests (all 6 types + conflict + structure)
├── test_divergence_detection.py  # 11 divergence tests
└── ...

docs/                         # Documentation and reports
scripts/                      # Utility scripts
```

## Features

### 6 BSP Types

| Type | Condition |
|------|-----------|
| **Buy1** | Downtrend deviation at new low with weaker momentum |
| **Sell1** | Uptrend deviation at new high with weaker momentum |
| **Buy2** | First pullback after Buy1, does NOT break prior low |
| **Sell2** | First bounce after Sell1, does NOT break prior high |
| **Buy3** | Price breaks above ZG, FIRST pullback stays above ZG |
| **Sell3** | Price breaks below ZD, FIRST bounce stays below ZD |

### Multi-Method Divergence (Phase 2)

- **Point method**: MACD histogram comparison at fractal points
- **Area method**: MACD柱 area comparison between same-direction segments
- **DIF method**: DIF 黄白线 comparison
- **Zero-pullback check**: DIF/DEA回拉0轴 during center formation
- **Segment divergence (区间套)**: Multi-level divergence between same-direction segments

### Real-Time Alerts

- Scans every 15 minutes during market hours (Mon-Fri 9AM-4PM)
- Telegram delivery via Hermes cron job
- Anti-spam: 60-min silence + 0.3% min price change
- Atomic state file (zero corruption risk)

### Multi-Level Fusion

Weighted scoring across timeframes:

| Level | Direction Weight | Signal Weight |
|-------|-----------------|---------------|
| 5m    | 1.0             | 2.0           |
| 30m   | 2.0             | 3.0           |
| 1d    | 3.0             | 5.0           |
| 1wk   | 4.0             | 8.0           |

## Configuration

Edit `config/config.yaml` to change symbols, thresholds, and Telegram settings:

```yaml
symbols:
  - symbol: "SMR"
    name: "NuScale Power"
    levels: ["30m", "1d"]
  - symbol: "TSLA"
    name: "Tesla Inc"
    levels: ["30m", "1d"]
  # ... add any symbol
```

## Tests

```bash
cd ~/.openclaw/workspace/chanlunInvester
python3 tests/test_bsp_detection.py           # 8 tests
python3 tests/test_divergence_detection.py    # 11 tests
```

All 19 tests pass with synthetic data and theory-compliant validation.

## Dependencies

- Python 3.10+
- `yfinance` — free stock data (no API key)
- `pyyaml` — config parsing
- Standard library only for Telegram delivery (`urllib`)

## Disclaimer

⚠️ 仅供参考，不构成投资建议。缠论分析基于技术指标，市场有风险，投资需谨慎。
