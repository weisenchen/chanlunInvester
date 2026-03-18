# UVIX Price Data Retrieval Flow

## 📊 Data Source: Yahoo Finance

**Library:** `yfinance` (Python Yahoo Finance API)

---

## 🔄 Data Flow

### Step 1: Create Ticker Object

```python
import yfinance as yf

# Create ticker for UVIX
uvix = yf.Ticker('UVIX')
```

**What happens:**
- Connects to Yahoo Finance API
- Initializes UVIX stock object
- Prepares for data fetch

---

### Step 2: Fetch Historical Data

```python
# Fetch 5 days of 5-minute data
history = uvix.history(period='5d', interval='5m')
```

**Parameters:**
- `period='5d'` - Last 5 trading days
- `interval='5m'` - 5-minute candlesticks

**Returns:**
- pandas DataFrame with OHLCV data
- ~370 bars (5 days × 78 bars/day)

---

### Step 3: Data Structure

```python
# DataFrame columns
['Open', 'High', 'Low', 'Close', 'Volume', 
 'Dividends', 'Stock Splits', 'Capital Gains']

# Index: DatetimeIndex with timezone
```

**Example Row:**
```
Timestamp: 2026-03-18 14:15:00-04:00
Open:      $8.14
High:      $8.27
Low:       $8.14
Close:     $8.19
Volume:    798,328
```

---

### Step 4: Extract Current Price

```python
# Get latest bar
latest = history.iloc[-1]
current_price = latest['Close']
```

**Result:**
- Current price: $8.19
- Timestamp: 2026-03-18 14:15:00 EST

---

### Step 5: Filter Today's Data

```python
from datetime import datetime

today = datetime.now().date()
today_data = history[history.index.date == today]
```

**Result:**
- Today's bars: 58 (from market open)
- Today's Open: $7.76
- Today's High: $8.40
- Today's Low: $7.71
- Current: $8.19

---

### Step 6: Convert to Kline Objects

```python
from trading_system.kline import Kline, KlineSeries

klines = []
for idx, row in history.iterrows():
    kline = Kline(
        timestamp=idx.to_pydatetime(),
        open=float(row['Open']),
        high=float(row['High']),
        low=float(row['Low']),
        close=float(row['Close']),
        volume=int(row['Volume'])
    )
    klines.append(kline)

series = KlineSeries(klines=klines, symbol='UVIX', timeframe='5m')
```

**Purpose:**
- Convert pandas DataFrame to Kline objects
- Compatible with ChanLun analysis modules

---

### Step 7: Data Validation

```python
# Validate data
if len(history) == 0:
    print("❌ Error: No data available")
    return None

# Validate prices
if open_price <= 0 or close_price <= 0:
    continue  # Skip invalid data

# Validate current price
current_price = klines[-1].close
if current_price <= 0:
    print("❌ Error: Invalid price")
    return None
```

**Validation Rules:**
- ✅ Data must exist
- ✅ Prices must be positive
- ✅ Current price must be valid

---

## 📝 Code Location

**File:** `scripts/uvix_auto_monitor.py`

**Function:** `fetch_data()`

```python
def fetch_data(symbol='UVIX', timeframe='5m', count=100):
    """获取实时数据 - 只使用 Yahoo Finance 真实数据"""
    ticker = yf.Ticker(symbol)
    
    # Fetch from Yahoo Finance
    history = ticker.history(period='5d', interval='5m')
    
    # Validate
    if len(history) == 0:
        return None
    
    # Convert to Klines
    klines = []
    for idx, row in history.iterrows():
        kline = Kline(
            timestamp=idx.to_pydatetime(),
            open=float(row['Open']),
            high=float(row['High']),
            low=float(row['Low']),
            close=float(row['Close']),
            volume=int(row['Volume'])
        )
        klines.append(kline)
    
    # Return KlineSeries
    return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
```

---

## 🔍 Real Data Example

**Execution Output:**
```
[Step 1] Create Yahoo Finance Ticker
  ✓ Ticker: UVIX

[Step 2] Fetch Historical Data
  ✓ Data fetched: 370 bars

[Step 3] Data Structure
  Columns: ['Open', 'High', 'Low', 'Close', 'Volume']

[Step 4] Latest Price Data
  Timestamp: 2026-03-18 14:15:00-04:00
  Open:   $8.14
  High:   $8.27
  Low:    $8.14
  Close:  $8.19
  Volume: 798,328

[Step 5] Today's Data Extraction
  Today's bars: 58
  Today's Open:   $7.76
  Today's High:   $8.40
  Today's Low:    $7.71
  Current Price:  $8.19

[Step 6] Data Validation
  ✅ Valid price data: $8.19
```

---

## ⚠️ Critical Fix (March 18, 2026)

**Problem:**
- Alert showed wrong price: $7.32
- Actual price range: $7.71 - $8.40

**Root Cause:**
- Code was using simulated data
- Not validating against real-time data

**Fix:**
```python
# BEFORE (WRONG)
base_price = 7.50  # Simulated!

# AFTER (CORRECT)
history = ticker.history(period='5d', interval='5m')
if len(history) == 0:
    return None  # No simulated data!
```

**Result:**
- ✅ All prices now from Yahoo Finance
- ✅ Real-time validation
- ✅ No more simulated data

---

## 📊 Data Update Frequency

| Interval | Update Frequency |
|----------|-----------------|
| **5m** | Every 5 minutes (during market hours) |
| **30m** | Every 30 minutes |
| **1d** | Once daily (after market close) |

**Market Hours:**
- Open: 9:30 AM EST
- Close: 4:00 PM EST
- After-hours: Limited data

---

## 🔗 API Documentation

**Yahoo Finance API:**
- Library: `yfinance`
- Docs: https://github.com/ranaroussi/yfinance
- Usage: `pip install yfinance`

**Data Coverage:**
- US Stocks: ✅ Full coverage
- ETFs: ✅ Full coverage
- Crypto: ✅ 24/7 coverage
- Indices: ✅ Full coverage

---

**🎯 All price data now comes directly from Yahoo Finance - NO simulation!**
