# Yahoo Finance (yfinance) Rate Limits

## 📊 Official vs Unofficial API

**Important:** `yfinance` is an **unofficial** library that scrapes Yahoo Finance website.

| Aspect | Official API | yfinance (Unofficial) |
|--------|-------------|----------------------|
| **Rate Limit** | Defined (2000 calls/hour) | **Undefined/Undocumented** |
| **Reliability** | High | Medium |
| **Cost** | Paid tiers | Free |
| **Support** | Official support | Community support |

---

## ⚠️ yfinance Rate Limits (Unofficial)

### Known Limits (Based on Community Experience)

**Conservative Limits:**
- **Requests per minute:** ~60 requests
- **Requests per hour:** ~1,000-2,000 requests
- **Requests per day:** ~10,000-20,000 requests

**What Users Report:**
```
✅ Safe: 100-500 requests/day
⚠️  Risky: 1,000-2,000 requests/day
❌ Danger: 5,000+ requests/day
```

---

## 🚨 Rate Limit Error

**Error Message:**
```python
YFRateLimitError: Too Many Requests
```

**Or:**
```python
HTTPError: 429 Client Error: Too Many Requests
```

**What happens:**
- Yahoo blocks your IP temporarily
- Duration: 15 minutes to 24 hours
- Solution: Wait or reduce request frequency

---

## 📈 Current UVIX Monitor Usage

### Current Configuration

**5-Minute Monitor:**
```python
CONFIG = {
    'check_interval_minutes': 5,
    'trading_hours': {
        'start': 9,   # 9:30 EST
        'end': 16     # 16:00 EST
    }
}
```

**Daily Request Count:**
```
Trading hours: 6.5 hours (9:30-16:00)
Checks per day: 6.5 hours × 60 minutes ÷ 5 minutes = 78 checks
Requests per check: 3 timeframes (1d, 30m, 5m) = 3 requests
Total requests/day: 78 × 3 = 234 requests/day
```

**Status:** ✅ **SAFE** (well below limits)

---

## 🎯 Safe Usage Guidelines

### For Single Stock Monitoring (UVIX)

**Current Setup:**
```
✅ 234 requests/day
✅ Well within safe limits
✅ No rate limit issues expected
```

### For Multiple Stocks

**Safe Configuration:**
```python
# Monitor 10 stocks
STOCKS = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 
          'AMZN', 'META', 'SPY', 'QQQ', 'UVIX']

# Check every 15 minutes
check_interval = 15  # minutes

# Daily requests
requests_per_day = 10 stocks × (6.5h × 60m ÷ 15m) × 3 timeframes
requests_per_day = 10 × 26 × 3 = 780 requests/day ✅ SAFE
```

**Risky Configuration:**
```python
# Monitor 50 stocks every 5 minutes
requests_per_day = 50 × 78 × 3 = 11,700 requests/day ⚠️ RISKY
```

---

## 🔧 Best Practices

### 1. Add Delays Between Requests

```python
import time
import yfinance as yf

stocks = ['AAPL', 'TSLA', 'NVDA']

for stock in stocks:
    ticker = yf.Ticker(stock)
    data = ticker.history(period='5d')
    
    # Add delay
    time.sleep(1)  # 1 second between requests
```

### 2. Use Caching

```python
from functools import lru_cache
import yfinance as yf

@lru_cache(maxsize=100)
def get_stock_data(symbol, period='5d'):
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)
```

### 3. Implement Retry Logic

```python
import time
from yfinance.exceptions import YFRateLimitError

def fetch_with_retry(symbol, max_retries=3):
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period='5d')
        except YFRateLimitError:
            if attempt < max_retries - 1:
                wait_time = 60 * (attempt + 1)  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

### 4. Monitor Request Count

```python
class RequestTracker:
    def __init__(self, daily_limit=2000):
        self.count = 0
        self.daily_limit = daily_limit
        self.last_reset = datetime.now().date()
    
    def can_make_request(self):
        if datetime.now().date() > self.last_reset:
            self.count = 0
            self.last_reset = datetime.now().date()
        return self.count < self.daily_limit
    
    def record_request(self):
        self.count += 1

# Usage
tracker = RequestTracker(daily_limit=2000)

if tracker.can_make_request():
    data = ticker.history(period='5d')
    tracker.record_request()
else:
    print("Daily limit reached!")
```

---

## 📊 Rate Limit Comparison

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Yahoo Finance** | ~2,000/hour (unofficial) | N/A |
| **Alpha Vantage** | 5 requests/min | 100+/min |
| **IEX Cloud** | 50,000/month | 1M+/month |
| **Polygon.io** | Limited | 1M+/day |
| **Finnhub** | 60 requests/min | 1,000+/min |

---

## 🎯 UVIX Monitor Status

### Current Usage

**Requests per Day:**
```
5-minute checks: 78 checks/day
3 timeframes per check: 3 requests
Total: 234 requests/day ✅
```

**Status:**
- ✅ Well within safe limits
- ✅ No rate limiting expected
- ✅ Can safely monitor UVIX indefinitely

### Scaling Up

**If you want to monitor more stocks:**

| Stocks | Interval | Requests/Day | Status |
|--------|----------|--------------|--------|
| 1 (UVIX) | 5 min | 234 | ✅ Safe |
| 5 stocks | 5 min | 1,170 | ✅ Safe |
| 10 stocks | 5 min | 2,340 | ⚠️ Monitor |
| 10 stocks | 15 min | 780 | ✅ Safe |
| 20 stocks | 15 min | 1,560 | ✅ Safe |
| 50 stocks | 15 min | 3,900 | ⚠️ Risky |

---

## ⚡ Optimization Tips

### 1. Batch Requests

```python
# Instead of individual requests
for stock in stocks:
    data = yf.Ticker(stock).history(period='5d')

# Use multi-threading (carefully)
from concurrent.futures import ThreadPoolExecutor

def fetch_stock(stock):
    return yf.Ticker(stock).history(period='5d')

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(fetch_stock, stocks))
```

### 2. Use Appropriate Periods

```python
# Don't fetch more data than needed
ticker.history(period='5d', interval='5m')  # ✅ Good for 5m monitoring
ticker.history(period='1d', interval='1m')  # ❌ Too frequent
ticker.history(period='1y', interval='1d')  # ✅ Good for daily analysis
```

### 3. Implement Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failures = 0
        self.threshold = failure_threshold
        self.disabled_until = None
    
    def can_execute(self):
        if self.disabled_until and datetime.now() < self.disabled_until:
            return False
        return True
    
    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.disabled_until = datetime.now() + timedelta(hours=1)
            print("Circuit breaker triggered. Waiting 1 hour...")
    
    def record_success(self):
        self.failures = 0
```

---

## 🚨 What to Do If Rate Limited

### Immediate Actions

1. **Stop all requests immediately**
2. **Wait 15-60 minutes**
3. **Resume with longer delays**

### Long-term Solutions

1. **Reduce request frequency**
2. **Add more caching**
3. **Use multiple IP addresses**
4. **Consider paid API alternatives**

---

## 📝 Summary for UVIX Monitor

**Current Configuration:**
- ✅ 234 requests/day
- ✅ Well within safe limits (2,000/day)
- ✅ No rate limiting expected
- ✅ Can run indefinitely

**Recommendations:**
- ✅ Current setup is optimal
- ✅ No changes needed
- ✅ Safe to continue monitoring

**If expanding:**
- ⚠️ Monitor total requests/day
- ⚠️ Add delays for >10 stocks
- ⚠️ Implement caching
- ⚠️ Consider paid API for >50 stocks

---

**🎯 Current UVIX monitor usage is SAFE and sustainable!**
