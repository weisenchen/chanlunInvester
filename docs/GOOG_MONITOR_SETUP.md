# GOOG (Alphabet/Google) 美股缠论监控配置

**添加日期**: 2026-04-08  
**标的**: GOOG (NASDAQ: Alphabet Inc. Class C)  
**监控级别**: 周线 (1w) + 日线 (1d) 双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | GOOG |
| **交易所** | NASDAQ (纳斯达克) |
| **公司** | Alphabet Inc. (Google) Class C |
| **行业** | 科技/互联网 |
| **监控级别** | 1w + 1d (周线 + 日线) |

---

## 🎯 监控功能

### 1. 大级别趋势监控

- **周线级别**: 捕捉中长期趋势方向
- **日线级别**: 确认短期走势
- **联动提醒**: 大小级别共振时优先推送

### 2. 背驰检测

- 周线背驰 → 日线确认 (168 小时确认窗口)
- 日线背驰 → 30 分钟确认 (48 小时确认窗口)
- 多级别共振信号优先推送

### 3. Telegram 警报

警报将通过 OpenClaw 发送到 Telegram (Chat ID: 8365377574)

---

## 📁 配置文件

### monitor_all.py (主监控)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
# 级别递归配置
LEVEL_CONFIG = {
    '1w': {
        'child_level': '1d',
        'weight': 4.0,
        'divergence_threshold': 0.35,
        'confirmation_window_hours': 168,  # 1 周
    },
    '1d': {
        'child_level': '30m',
        'weight': 3.0,
        'divergence_threshold': 0.3,
        'confirmation_window_hours': 48,  # 48 小时
    },
}

SYMBOLS = [
    # ... 其他标的
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate
python test_goog_monitor.py
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep GOOG
```

### 查看多级别确认状态

```bash
python scripts/test_confirmation.py --symbol GOOG
```

---

## 📈 当前分析 (2026-04-08 11:13 EDT)

### 周线级别
- **最新价格**: $313.95
- **K 线数**: 105 根 (2 年数据)
- **笔数**: 33 笔
- **最新笔方向**: 向下 ⬇️
- **MACD**: DIF=10.80, DEA=17.13, MACD=-12.67

### 日线级别
- **最新价格**: $313.95
- **K 线数**: 60 根
- **笔数**: 16 笔
- **最新笔方向**: 向上 ⬆️
- **MACD**: DIF=-2.59, DEA=-5.73, MACD=6.27

### 联动状态
⚠️ **级别不一致** - 周线向下，日线向上，可能处于转折期

---

## ⏰ 监控时间表

| 时间 (EDT) | 类型 | 状态 |
|-----------|------|------|
| 09:00 | 盘前报告 | ✅ 自动 |
| 09:30-16:00 | 实时监控 (每 15 分钟) | ✅ 自动 |
| 16:00 | 收盘报告 | ✅ 自动 |
| 20:00 | 盘后复盘 | ✅ 自动 |

---

## 📋 Cron 配置

```bash
# 编辑 crontab
crontab -e

# GOOG 监控已包含在现有配置中
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 GOOG 1d 第一类买点 (背驰)
价格：$XXX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 GOOG 1d 第二类买点
价格：$XXX.XX
置信度：XX%
```

### 周线背驰预警
```
⚠️ GOOG 1w 背驰预警
大级别：周线
次级别：等待日线确认
确认窗口：168 小时
```

### 多级别共振
```
✅ GOOG 多级别共振
周线：背驰确认
日线：第二类买点
置信度：高
```

---

## ⚠️ 注意事项

### 1. 交易时间
- 美股交易时间：09:30-16:00 ET (周一至周五)
- 周线 K 线在每周五收盘后完成

### 2. 数据延迟
- Yahoo Finance 数据可能有 15 分钟延迟
- 周线数据在周末更新

### 3. 节假日
- 美股休市日无数据 (感恩节、圣诞节等)
- 系统会自动跳过休市日

### 4. 财报季
- Google 财报通常在 1 月、4 月、7 月、10 月发布
- 财报发布前后波动可能加大
- 背驰信号可能失效，需谨慎

### 5. 大级别特性
- 周线信号更稳定，但频率低
- 日线信号更频繁，但噪音多
- 建议优先参考周线趋势方向

---

## 📞 故障排除

### 问题：收不到 GOOG 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep GOOG alerts.log

# 3. 测试数据获取
python test_goog_monitor.py
```

### 问题：周线数据获取失败

**解决**:
```bash
# 检查网络连接
curl -I https://finance.yahoo.com

# 检查 yfinance 安装
source venv/bin/activate
pip show yfinance

# 手动测试周线数据
python -c "import yfinance as yf; print(yf.Ticker('GOOG').history(period='2y', interval='1wk'))"
```

---

## 📚 相关文档

- [多级别背驰确认系统](SETUP_MULTI_LEVEL.md)
- [TEL 美股监控配置](TEL_MONITOR_SETUP.md)
- [监控系统使用说明](MONITOR_USAGE.md)
- [缠论基础理论](docs/CHANLUN_MONITOR_DEV_PLAN.md)

---

## 📊 美股监控列表

| 标的 | 公司 | 级别 | 状态 |
|------|------|------|------|
| TEL | TE Connectivity | 30m + 1d | ✅ 运行中 |
| GOOG | Alphabet/Google | 1w + 1d | ✅ 运行中 |

---

**配置状态**: ✅ 完成  
**最后测试**: 2026-04-08 11:13 EDT  
**下次自动汇报**: 16:00 ET (收盘报告)
