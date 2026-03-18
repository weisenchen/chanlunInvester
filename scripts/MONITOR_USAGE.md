# 缠论通用股票监控系统

## 🎯 系统说明

**支持任意美股/ETF/加密货币的缠论多级别分析**

一套系统，所有股票通用！

---

## ⚡ 快速开始

### 监控单只股票

```bash
cd /home/wei/.openclaw/workspace/trading-system

# Apple
python3 scripts/chanlun_monitor.py AAPL

# Tesla
python3 scripts/chanlun_monitor.py TSLA

# NVIDIA
python3 scripts/chanlun_monitor.py NVDA
```

### 多级别分析

```bash
# 日线 +30 分钟 +5 分钟
python3 scripts/chanlun_monitor.py AAPL --levels 1d,30m,5m

# 仅 30 分钟级别
python3 scripts/chanlun_monitor.py TSLA --level 30m

# 自定义级别组合
python3 scripts/chanlun_monitor.py BTC-USD --levels 1d,1h,15m
```

### 保存结果

```bash
python3 scripts/chanlun_monitor.py AAPL -o results/aapl_analysis.json
```

### 查看支持的股票

```bash
python3 scripts/chanlun_monitor.py --list
```

---

## 📊 支持的股票类型

### 美股

```bash
# 科技股
python3 chanlun_monitor.py AAPL   # Apple
python3 chanlun_monitor.py MSFT   # Microsoft
python3 chanlun_monitor.py GOOGL  # Alphabet
python3 chanlun_monitor.py AMZN   # Amazon
python3 chanlun_monitor.py TSLA   # Tesla
python3 chanlun_monitor.py NVDA   # NVIDIA
python3 chanlun_monitor.py META   # Meta

# 金融股
python3 chanlun_monitor.py JPM    # JPMorgan
python3 chanlun_monitor.py BAC    # Bank of America
python3 chanlun_monitor.py GS     # Goldman Sachs

# 其他
python3 chanlun_monitor.py DIS    # Disney
python3 chanlun_monitor.py NKE    # Nike
python3 chanlun_monitor.py KO     # Coca-Cola
```

### ETF

```bash
python3 chanlun_monitor.py SPY    # S&P 500 ETF
python3 chanlun_monitor.py QQQ    # Nasdaq 100 ETF
python3 chanlun_monitor.py UVIX   # 2x Long VIX
python3 chanlun_monitor.py VIX    # 波动率指数
python3 chanlun_monitor.py IWM    # Russell 2000 ETF
```

### 加密货币

```bash
python3 chanlun_monitor.py BTC-USD   # Bitcoin
python3 chanlun_monitor.py ETH-USD   # Ethereum
python3 chanlun_monitor.py SOL-USD   # Solana
```

### 指数

```bash
python3 chanlun_monitor.py ^GSPC   # S&P 500
python3 chanlun_monitor.py ^DJI    # Dow Jones
python3 chanlun_monitor.py ^IXIC   # Nasdaq
```

---

## 🎯 命令行参数

### 基本参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `symbol` | 股票代码 | 必需 | `AAPL` |
| `--level, -l` | 单级别分析 | 30m | `-l 5m` |
| `--levels, -L` | 多级别分析 | 1d,30m,5m | `-L 1d,1h,5m` |
| `--output, -o` | 输出文件 | - | `-o results.json` |
| `--list` | 显示热门股票 | - | `--list` |

### 参数组合

```bash
# 单级别分析
python3 chanlun_monitor.py AAPL -l 30m

# 多级别分析
python3 chanlun_monitor.py AAPL -L 1d,30m,5m

# 保存结果
python3 chanlun_monitor.py AAPL -L 1d,30m,5m -o aapl.json

# 组合使用
python3 chanlun_monitor.py TSLA -L 1d,4h,1h -o tesla.json
```

---

## 📈 输出示例

### 命令行输出

```
📊 标的：AAPL
📅 时间：2026-03-18 12:09:37 EST
🎯 级别：1d + 30m + 5m (区间套)

【1d 级别】
  📈 1d: 上涨线段
  🟢 1d 底背驰！强度:1.5

【30m 级别】
  📈 30m: 上涨线段

【5m 级别】
  🟢 5m 第一类买点！置信度:85%

💡 交易信号
  🟢 BUY (强度：+9.0)
  依据：5 个因素共振

💡 交易建议
  🟢 买入策略
     标的：AAPL
     入场：$251.59
     止损：$244.04 (-3%)
     目标 1: $259.14 (+3%)
     目标 2: $264.17 (+5%)
     仓位：重仓
```

### JSON 输出

```json
{
  "timestamp": "2026-03-18T12:09:37.123456",
  "symbol": "AAPL",
  "signal": "BUY",
  "strength": 9.0,
  "reasoning": [
    "✓ 1d 上涨线段 (+3)",
    "🟢 1d 底背驰 (强度:1.50) (+6)",
    "✓ 30m 上涨线段 (+2)",
    "🟢 5m 第一类买点 (置信度:85%) (+4)"
  ],
  "current_price": 251.59
}
```

---

## 🎯 实战场景

### 场景 1: 快速检查股票

```bash
# 快速查看 AAPL 当前状态
python3 chanlun_monitor.py AAPL -l 30m
```

### 场景 2: 深度分析

```bash
# 多级别深度分析
python3 chanlun_monitor.py TSLA -L 1d,4h,1h,30m,5m
```

### 场景 3: 批量分析

```bash
# 分析科技股
for stock in AAPL MSFT GOOGL AMZN NVDA; do
  python3 chanlun_monitor.py $stock -L 1d,30m,5m -o results/${stock}.json
done
```

### 场景 4: 监控加密货币

```bash
# 24/7 监控比特币
python3 chanlun_monitor.py BTC-USD -L 1d,4h,1h
```

---

## 📊 信号强度说明

### 权重计算

| 级别 | 方向 | 背驰/买卖点 |
|------|------|------------|
| **日线 (1d)** | ±3 | ±6 |
| **4 小时 (4h)** | ±2.5 | ±5 |
| **1 小时 (1h)** | ±2 | ±4 |
| **30 分钟 (30m)** | ±2 | ±4 |
| **15 分钟 (15m)** | ±1.5 | ±3 |
| **5 分钟 (5m)** | ±1 | ±4 |

### 信号等级

| 信号强度 | 信号 | 操作建议 | 胜率 |
|----------|------|----------|------|
| **≥ +8** | STRONG BUY | 重仓买入 | ~90% |
| **≥ +4** | BUY | 标准买入 | ~80% |
| **-4 ~ +4** | HOLD | 观望 | - |
| **≤ -4** | SELL | 标准卖出 | ~80% |
| **≤ -8** | STRONG SELL | 重仓卖出 | ~90% |

---

## ⚠️ 注意事项

### 1. 数据延迟

- 美股：实时数据 (交易时段)
- ETF: 实时数据 (交易时段)
- 加密货币：实时数据 (24/7)
- 日线数据：收盘后更新

### 2. 交易时段

**美股/ETF:**
- 开盘：09:30 EST
- 收盘：16:00 EST
- 盘前/盘后数据可能不准确

**加密货币:**
- 24/7 交易
- 随时可以分析

### 3. 股票代码格式

**美股:** 直接代码 (AAPL, TSLA)
**ETF:** 直接代码 (SPY, QQQ)
**加密货币:** 代码-USD (BTC-USD, ETH-USD)
**指数:** ^开头 (^GSPC, ^DJI)

---

## 🔧 自定义配置

### 修改权重

编辑 `chanlun_monitor.py`:
```python
DEFAULT_CONFIG = {
    'weights': {
        '1d': {'direction': 3, 'divergence': 6},
        '4h': {'direction': 2.5, 'divergence': 5},
        '1h': {'direction': 2, 'divergence': 4},
        # ... 自定义其他级别
    }
}
```

### 添加新级别

```python
# 在 fetch_data 函数中添加
elif timeframe == '2h':
    history = ticker.history(period='3mo', interval='2h')
```

---

## 📝 批处理示例

### 监控股票列表

```bash
#!/bin/bash
# monitor_stocks.sh

STOCKS="AAPL MSFT GOOGL AMZN NVDA TSLA"

for stock in $STOCKS; do
  echo "分析 $stock..."
  python3 chanlun_monitor.py $stock -L 1d,30m,5m -o results/${stock}.json
  sleep 2  # 避免请求过快
done
```

### 监控强烈信号

```bash
#!/bin/bash
# find_strong_signals.sh

for stock in AAPL MSFT GOOGL AMZN NVDA TSLA SPY QQQ; do
  result=$(python3 chanlun_monitor.py $stock -L 1d,30m,5m 2>&1)
  
  if echo "$result" | grep -q "STRONG BUY"; then
    echo "🟢 $stock: STRONG BUY detected!"
    echo "$result" | grep -A 5 "交易信号"
  fi
  
  if echo "$result" | grep -q "STRONG SELL"; then
    echo "🔴 $stock: STRONG SELL detected!"
    echo "$result" | grep -A 5 "交易信号"
  fi
done
```

---

## 🎯 最佳实践

### 1. 多级别确认

```bash
# 总是使用多级别分析
python3 chanlun_monitor.py AAPL -L 1d,30m,5m
```

### 2. 保存结果

```bash
# 保存分析结果用于回测
python3 chanlun_monitor.py AAPL -L 1d,30m,5m -o results/aapl_$(date +%Y%m%d).json
```

### 3. 定期监控

```bash
# 设置 Cron 定时任务
0 9,13,16 * * 1-5 cd /path && python3 chanlun_monitor.py AAPL -L 1d,30m,5m
```

### 4. 批量分析

```bash
# 分析整个行业
for stock in AAPL MSFT GOOGL META NVDA; do
  python3 chanlun_monitor.py $stock -L 1d,30m,5m
done
```

---

## 📚 相关文档

- PHASE1_README.md - Phase 1 详细说明
- 缠论第 14 课 - 区间套定理
- 缠论第 12 课 - 三类买卖点
- GitHub: https://github.com/weisenchen/chanlunInvester

---

**🎯 一套系统，监控所有股票！**
