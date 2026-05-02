# 缠论 (ChanLun) Knowledge Base

## 缠中说禅 — Complete Theoretical & Practical Reference

This document distills everything learned about 缠论 from the 108 lessons, practical implementation (Phase 1-3), and live testing on US stocks. It combines pure theory with real-world engineering experience.

---

## Table of Contents

1. [Theoretical Foundation](#1-theoretical-foundation)
2. [Pipeline Architecture](#2-pipeline-architecture)
3. [Detection Algorithms & Implementation](#3-detection-algorithms--implementation)
4. [Multi-Level Fusion](#4-multi-level-fusion)
5. [Alert System](#5-alert-system)
6. [Real Stock Analysis Results](#6-real-stock-analysis-results)
7. [Key Lessons & Edge Cases](#7-key-lessons--edge-cases)
8. [Configuration Reference](#8-configuration-reference)

---

## 1. Theoretical Foundation

### 1.1 K-Line Containment (K线包含处理) — Lesson 65/77

Two adjacent K-lines have containment when one's high-low range is entirely inside the other's.

**Rules:**
- Direction first: if `g_n >= g_{n-1}` → upward; if `d_n <= d_{n-1}` → downward
- Upward containment: merge → `[max(high), max(low)]`
- Downward containment: merge → `[min(high), min(low)]`
- Sequential: merge K1+K2, then compare with K3. NOT transitive.

**Practical note:** Single-pass containment works for most cases but can miss nested chains in high-volatility data. For production, consider iterative containment until no more mergers occur.

### 1.2 Fractal (分型) — Lesson 65/77/82

At least 3 consecutive K-lines (after containment processing):
- **Top fractal**: middle K-line's high is highest, with neighbors' highs lower
- **Bottom fractal**: middle K-line's low is lowest, with neighbors' lows higher

**Psychology (Lesson 82):** 1st=attempt, 2nd=strongest push, 3rd=exhaustion ("一而再、再而三，三而竭")

**Strong vs Weak:** A strong top fractal has the 2nd K-line with a long upper shadow and the 3rd unable to close above 50% of the 2nd's range. A weak one has the 1st as a big candle with 2nd/3rd as small candles — continuation pattern.

### 1.3 Pen (笔) — Lesson 65/77

A stroke connecting a top fractal and bottom fractal. Conditions:
1. One top + one bottom fractal (opposite types)
2. At least 1 K-line BETWEEN the two fractals (non-fractal)
3. Price validity: top's high > bottom's low
4. Must alternate (up → down → up → ...)

**Pen Uniqueness (Lesson 77):** Mathematically proven unique by contradiction. Algorithm: mark all fractals → for consecutive same-type, keep highest top/lowest bottom → adjacent opposite types form pens.

### 1.4 Segment (线段) — Lesson 65/67/77/78

- Minimum 3 pens, first 3 must overlap
- Odd number of pens (starts and ends with same direction)
- Destroyed only by opposite-direction segment
- Characteristic sequence: for up-segments, down-pens form the sequence
- **Two cases of destruction (Lesson 67):**
  - Case 1: no gap in characteristic seq → ends at fractal
  - Case 2: gap → must check next segment's characteristic seq for confirmation

### 1.5 Center (中枢) — Lesson 17/18/20

**Definition:** Overlapping range of ≥3 consecutive lower-level trend types.
Formula: `[max(low_a, low_b, low_c), min(high_a, high_b, high_c)]`
Standard notation: **ZG** = min(highs), **ZD** = max(lows)

**Types:**
- **Trend**: ≥2 non-overlapping same-direction centers
- **Range**: exactly 1 center
- **Extension**: more segments oscillate around same zone
- **Expansion**: two same-level centers touch → higher-level center

**Critical Theorem (Lesson 20):**
> `后GG < 前DD` = downtrend continuation; `后DD > 前GG` = uptrend continuation

### 1.6 All 6 Buy/Sell Points — Lesson 12/14/18/20/21

| Type | Condition | Prerequisite |
|------|-----------|-------------|
| **Buy1** | Downtrend deviation at new low with weaker momentum | ≥2 non-overlapping centers (trend) |
| **Sell1** | Uptrend deviation at new high with weaker momentum | ≥2 non-overlapping centers (trend) |
| **Buy2** | First pullback after Buy1, does NOT break prior low | Buy1 must have occurred |
| **Sell2** | First bounce after Sell1, does NOT break prior high | Sell1 must have occurred |
| **Buy3** | Price breaks above ZG, FIRST pullback stays above ZG | Confirmed center exists |
| **Sell3** | Price breaks below ZD, FIRST bounce stays below ZD | Confirmed center exists |

**Key theorem (Lesson 21):** Only 3 classes of guaranteed profitable points exist.
**Key theorem (Lesson 35):** Higher-level BSP must be a lower-level BSP of some sub-level.

### 1.7 Divergence (背驰) — Lesson 15/24/25

**Core rule: "没有趋势，没有背驰"** — only valid in trends, not ranges.

**Two methods:**
1. **Area method**: Compare MACD柱 area between two same-direction trend segments
2. **Force method**: area / time

**Standard 2-center trend MACD pattern (Lesson 24):**
1. First center: MACD黄白线 rises from below 0
2. Breakout: strongest segment
3. Second center: MACD黄白线 pulls back near 0
4. Final breakout: check if MACD黄白线 fails new high OR柱 area smaller → deviation

**Deviation → Trend Transition Theorem (Lesson 29):**
After deviation, three outcomes:
1. Last center extension (weakest)
2. Higher-level range
3. Higher-level reverse trend (strongest)

---

## 2. Pipeline Architecture

### 2.1 Data Flow

```
yfinance (free, no API key)
    │
    ▼
KlineSeries (150-500 bars per level)
    │
    ├── FractalDetector (分型)
    │       └── Containment → Top/Bottom Fractals
    │
    ├── PenCalculator (笔)
    │       └── Connected fractals → Pens
    │
    ├── SegmentCalculator (线段)
    │       └── ≥3 overlapping pens → Segments
    │
    ├── CenterDetector (中枢)
    │       └── ≥3 overlapping segments → Centers (ZG, ZD, GG, DD)
    │
    ├── MACDIndicator (MACD)
    │       └── DIF, DEA, Histogram
    │
    ├── DivergenceDetector (背驰) — Phase 2
    │       ├── Point method: MACD histogram at fractals
    │       ├── Area method: MACD柱 area between segments
    │       ├── DIF method: DIF 黄白线 comparison
    │       ├── Zero-pullback check: DIF回拉0轴
    │       └── Segment divergence (区间套): multi-level
    │
    ├── BSP Detection (买卖点)
    │       ├── Buy1/Sell1: trend + divergence
    │       ├── Buy2/Sell2: reversal structure + pullback
    │       └── Buy3/Sell3: center breakout + pullback
    │
    ├── Multi-Level Fusion
    │       └── Weighted scoring across timeframes
    │
    └── Alert Delivery
            └── Telegram Bot API (stdlib)
```

### 2.2 Data Windows (configurable in config.yaml)

| Level | Bars | Period | Coverage |
|-------|------|--------|----------|
| 5m | 200 | 5d | ~1 week |
| 30m | 300 | 30d | ~1 month |
| 1d | 500 | 1y | ~1 year |
| 1wk | 250 | 5y | ~5 years |

**Lesson learned:** 100 bars was insufficient for reliable segment detection. 500 daily bars gives enough structure for center detection in most stocks.

---

## 3. Detection Algorithms & Implementation

### 3.1 Divergence Detection (3 Methods)

**Point Method** (original, keep as fallback):
- Compare MACD histogram at the most recent two same-direction fractals
- Bullish: price new low, histogram higher → score proportional to relative difference
- Limitation: noisy; single-point comparison misses overall momentum shift

**Area Method** (第25课 — primary):
- Compare MACD柱 AREA between the two most recent same-direction segments
- Uses `abs(area)` for magnitude comparison (critical: down-segment histograms are negative)
- Bullish: `abs(area2) < abs(area1)` → less downward momentum in 2nd push
- Score: `(area1_abs - area2_abs) / area1_abs × 3`, capped at 5.0

**Pitfall:** Always use `abs()` for area comparison. Raw negative values give false negatives: `-11 >= -33` is True mathematically but means momentum is WEAKENING (divergence).

**DIF Method** (第24课 — 黄白线):
- Compare DIF values at two fractal points
- Bullish: DIF at new low > DIF at previous low (less negative)
- Standard 2-center pattern: deeply negative → rise toward 0 → less negative at second low

### 3.2 Zero-Pullback Check (黄白线回拉0轴)

Checks if DIF values pulled back near 0 during center formation. This is the "Standard 2-center MACD pattern" from Lesson 24.

**Implementation:** Find minimum absolute DIF value within a center's range. If `min_abs_dif < price_range × 0.3` → pullback confirmed. Gives +20% strength boost to BSP1.

### 3.3 Segment Divergence (区间套 — Lesson 27)

Checks for momentum weakening between the last two same-direction segments, regardless of center structure. This is a broader check that can detect divergence even when centers haven't formed.

**Implementation:**
- Up segments: if price went higher but area smaller → bearish
- Down segments: if price went lower but area less negative → bullish
- Contributes to divergence-aware fusion at 70% weight

### 3.4 Trend Confirmation

**Center non-overlap check (Lesson 20):**
- Downtrend: `c2.gg < c1.dd` (second center entirely below first)
- Uptrend: `c2.dd > c1.gg` (second center entirely above first)
- Trend strength: `gap / center_range`, capped at 3.0

**Segment direction alignment:**
- Segment-level flow must match center trend direction
- +15% strength boost when aligned

### 3.5 Buy2 Prerequisite (第21/32课)

Buy2 requires Buy1 to have occurred first. Since scans are stateless, the closest approximation is:

**Reversal structure check:**
- Buy2: last 2 segments must be `down → up`
- Sell2: last 2 segments must be `up → down`

This verifies the price structure shows a clear bottom → rise → pullback pattern, confirming Buy1 logically happened at the previous bottom.

### 3.6 Strength Calculation

| Signal | Formula | Range |
|--------|---------|-------|
| Buy1/Sell1 | `div_score × (1 + trend_strength × 0.3) × zero_pullback_bonus × segment_alignment_bonus` | 0.5-5.0 |
| Buy2/Sell2 | `2.0 × (1 - pullback_ratio × 0.5)` | 1.0-2.0 |
| Buy3/Sell3 | `3.0 × (1 - pullback_pct / threshold)` | 0.5-5.0 |

---

## 4. Multi-Level Fusion

### 4.1 Weighted Scoring

| Level | Direction Weight | Signal Weight |
|-------|-----------------|---------------|
| 5m | 1.0 | 2.0 |
| 30m | 2.0 | 3.0 |
| 1d | 3.0 | 5.0 |
| 1wk | 4.0 | 8.0 |

Score = Σ(direction × weight_dir) + Σ(signal_strength × weight_signal) for each level

### 4.2 Fusion Thresholds

| Score | Signal |
|-------|--------|
| ≥ +6.0 | STRONG_BUY |
| ≥ +3.0 | BUY |
| -3.0 to +3.0 | HOLD |
| ≤ -3.0 | SELL |
| ≤ -6.0 | STRONG_SELL |

### 4.3 Divergence-Aware Fusion (Phase 2)

When BSP1 is blocked by "no centers" (no trend), divergence is still tracked separately:
- `div_tracking['bullish_score']` and `bearish_score` are always computed
- Contributes to fusion at 30% weight via `weight_signal × divergence_score × 0.3`
- Displayed as `🟡 底背驰预警(无中枢)` / `🔶 顶背驰预警(无中枢)` in console output

---

## 5. Alert System

### 5.1 Delivery Pipeline

```
Pre-script (chanlun_bsp_scan.py)
  │  Runs yfinance + chanlun engine on all symbols
  │  Outputs JSON to stdout
  ▼
Hermes Cron Job (every 15 min, Mon-Fri 9AM-4PM)
  │  Reads JSON from pre-script
  │  Checks: market hours? has signals?
  ▼
Telegram Bot API (if signal found)
  │  Formatted Chinese alert with emoji
  ▼
Telegram:8365377574
```

### 5.2 Anti-Spam System

- **Min price change**: 0.3% between same-type alerts
- **Silence period**: 60 minutes per signal type per symbol per level
- **State file**: atomic write (tempfile → fsync → rename), auto-recovers from corruption
- **Cleanup**: 24-hour TTL on alert state entries

### 5.3 Alert Format

```
🟢 SMR 缠论买卖点提醒

📊 信号：第一类买点 (底背驰)
💰 价格：USD 12.12
🎯 置信度：high
📝 说明：底背驰(多方法融合): 点=1.2, 面积=2.8, DIF=2.2
📊 多级别联动：BUY (强度:+4.5)
  30m: 🟢 up (1个信号)
  1d: 🔴 down (0个信号)

⏰ 时间：2026-05-04 09:30
级别：30m
⚠️ 仅供参考，不构成投资建议
```

---

## 6. Real Stock Analysis Results

### 6.1 SMR (NuScale Power) — 2026-05-02

| Level | Segments | Centers | Divergence | BSP |
|-------|----------|---------|------------|-----|
| 30m | down→up | 0 | none | none |
| 1d | — | 0 | bullish (area 2.8, DIF 2.2) | none (no centers) |

**Fusion:** HOLD (+1.0) — conflicting levels
**Key insight:** Daily bullish divergence confirmed but no centers = no BSP1. This is where divergence-aware fusion adds value: the divergence is real but Buy1 is correctly blocked by theory.

### 6.2 INTC (Intel) — 2026-05-02

| Level | Segments | Centers | Divergence | BSP |
|-------|----------|---------|------------|-----|
| 30m | up→down | 0 | bearish (0.6) | none |
| 1d | up→up→up | 0 | none | none |
| 1wk | down→down→down | 0 | bearish (2.6) | none |

**Fusion:** SELL (-3.0)
**Key insight:** Strong weekly bearish divergence (point=5.0, area=3.0) against daily uptrend (DIF=11.32). Classic multi-level conflict. The weekly divergence is a major warning signal.

### 6.3 Key Pattern: PAAS.TO

**Fusion: BUY (+5.0)** — both 30m and 1d trending up. Cleanest BUY signal in the watchlist.

### 6.4 Key Pattern: IONQ & OKLO

**Fusion: SELL (-5.0)** — both levels trending down. OKLO also has bearish divergence on 30m.

---

## 7. Key Lessons & Edge Cases

### 7.1 "No Centers" Problem

The most common pattern across all tested stocks: **0 centers detected**. This happens because:
- SegmentCalculator produces long, clean segments without the ≥3-overlap required for centers
- Many stocks don't form clear consolidation zones (especially growth/volatile stocks)
- The 3-segment minimum for center formation is strict

**Implication:** Most BSP signals are blocked because BSP1 requires ≥2 centers (trend) and BSP3 requires ≥1 center. This is *theoretically correct* — 缠论 defines BSPs only in structured markets. But it means the system mostly produces no-signal results on trending stocks.

**Mitigation (Phase 2):** Divergence-aware fusion tracks divergence even without centers, providing early warnings.

### 7.2 Divergence Without Trends

The most counterintuitive finding: stocks can have multi-method divergence confirmed (area=2.8, DIF=2.2) but still fail BSP1 because no centers exist. This is correct per Lesson 15 ("没有趋势，没有背驰") but feels like a false negative.

**Resolution:** Divergence tracking as early warning (not BSP) is the correct approach. The divergence is logged and factored into fusion scoring, but not treated as a confirmed signal.

### 7.3 Area Method: abs() is Critical

**Bug found in Phase 2:** The initial area comparison used raw values (`area2 < area1`). For down-segments where histograms are negative, `-11 < -33` is False, causing false negatives. Fixed by using `abs(area)` for magnitude comparison.

**Rule:** Always compare absolute MACD柱 magnitudes. The sign indicates direction (bullish/bearish), magnitude indicates strength.

### 7.4 Data Window Size

- 100 bars for 1d (~3 months) is insufficient for reliable segment detection
- 500 bars for 1d (~1 year) works well
- For weekly analysis, need 200+ bars (~4 years)
- yfinance period mapping: 5d=5m, 30d=30m, 1y=1d, 5y=1wk

### 7.5 State File Corruption

The old `save_alert_state` wrote directly to a JSON file. If the process crashed mid-write, the file was corrupted, losing all alert history. Fixed with atomic write pattern: `tempfile.mkstemp` → `write` → `fsync` → `os.replace`.

### 7.6 Telegram Delivery Migration

- OpenClaw's `message send` subprocess was replaced with direct Telegram Bot API (stdlib `urllib.request`)
- Token auto-loads from `~/.hermes/.env` as fallback
- No subprocess → no shell injection risk, no PATH dependency, faster

### 7.7 Buy3/Sell3 Strength Explosion

**Old formula:** `strength = 3.0 + 1.0/pullback_pct` — when pullback is 0.1%, strength = 1003.0 (useless).
**New formula:** `strength = 3.0 × (1 - pullback_pct/threshold)`, capped at [0.5, 5.0] — sensible range.

---

## 8. Configuration Reference

### 8.1 config.yaml Structure

```yaml
telegram:
  chat_id: "8365377574"
  # bot_token from TELEGRAM_BOT_TOKEN env var or ~/.hermes/.env

symbols:
  - symbol: "SMR"
    name: "NuScale Power"
    levels: ["30m", "1d"]

data:
  count_per_level: {"5m": 200, "30m": 300, "1d": 500, "1wk": 250}
  period_map: {"5m": "5d", "30m": "30d", "1d": "1y", "1wk": "5y"}
  max_retries: 2
  retry_delay_seconds: 5

thresholds:
  "30m":
    bsp2_pct: 0.015
    bsp1_min_strength: 3.0
    min_distance: 0.008
    bsp3_pct: 0.03
    bsp3_klines: 5

fusion_weights:
  "30m": {direction: 2.0, signal: 3.0}
  "1d":  {direction: 3.0, signal: 5.0}

fusion:
  strong_buy: 6.0
  buy: 3.0
  strong_sell: -6.0
  sell: -3.0

antispam:
  min_price_change_pct: 0.003
  silence_period_minutes: 60
  state_ttl_hours: 24
```

### 8.2 File Map

| File | Purpose |
|------|---------|
| `config.yaml` | Configuration (symbols, thresholds, Telegram) |
| `monitor_all.py` | Production BSP scanner + alert delivery |
| `python-layer/trading_system/divergence.py` | DivergenceDetector (3 methods + zero-pullback) |
| `python-layer/trading_system/center.py` | Center detection (ZG, ZD, GG, DD) |
| `python-layer/trading_system/segment.py` | Segment calculation |
| `tests/test_bsp_detection.py` | 8 BSP unit tests |
| `tests/test_divergence_detection.py` | 11 divergence unit tests |
| `~/.hermes/scripts/chanlun_bsp_scan.py` | Cron pre-script (JSON output) |
| `~/.hermes/scripts/chanlun_daily_report.py` | Daily report cron pre-script |

### 8.3 Key Dependencies

- `yfinance` — free stock data (no API key)
- `pyyaml` — config parsing
- Standard library only for Telegram delivery (`urllib`)
- No databases, no message queues, no external services

---

## Appendix: Theory Reference

For the full 108-lesson theoretical extraction, see:
- `skill_view(name='chanlun-theory')` — Hermes skill
- `~/openclaw/workspace/chzhshch-108-plus/` — full lesson texts
- `docs/` in repo — analysis reports on individual stocks
