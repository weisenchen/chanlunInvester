# EOSE (Eos Energy Enterprises) 美股缠论监控配置

**添加日期**: 2026-04-09  
**标的**: EOSE (NASDAQ: Eos Energy Enterprises, Inc.)  
**监控级别**: 30 分钟 + 日线双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | EOSE |
| **交易所** | NASDAQ (纳斯达克) |
| **公司** | Eos Energy Enterprises, Inc. |
| **行业** | 能源存储/电池技术 |
| **监控级别** | 30m + 1d |

---

## 🎯 监控功能

### 1. 实时买卖点监控

- **30 分钟级别**: 捕捉短期买卖点
- **日线级别**: 确认中期趋势方向
- **联动提醒**: 大小级别共振时优先推送

### 2. 背驰检测

- 日线背驰 → 30 分钟确认
- 30 分钟背驰 → 5 分钟确认 (可选)
- 多级别共振信号优先推送

### 3. Telegram 警报

警报将通过 OpenClaw 发送到 Telegram (Chat ID: 8365377574)

---

## 📁 配置文件

### monitor_all.py (主监控)

```python
SYMBOLS = [
    # 加股
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'levels': ['30m', '1d']},
    {'symbol': 'PAAS.TO', 'name': 'Pan American Silver', 'levels': ['30m', '1d']},
    {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['30m', '1d']},
    # 美股
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['30m', '1d']},
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d']},
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['30m', '1d']},
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['30m', '1d']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate
python test_eose_monitor.py
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep EOSE
```

### 查看多级别确认状态

```bash
python scripts/test_confirmation.py --symbol EOSE
```

---

## 📈 当前分析 (2026-04-09 11:31 EDT)

### 日线级别
- **最新价格**: 待获取
- **笔数**: 待计算
- **最新笔方向**: 待分析
- **MACD**: 待计算

### 30 分钟级别
- **最新价格**: 待获取
- **笔数**: 待计算
- **最新笔方向**: 待分析
- **MACD**: 待计算

### 联动状态
⏳ **初始配置** - 等待首次数据获取

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

# EOSE 监控已包含在现有配置中 (monitor_all.py)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 EOSE 30m 第一类买点 (背驰)
价格：$XXX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 EOSE 30m 第二类买点
价格：$XXX.XX
置信度：XX%
```

### 多级别共振
```
✅ EOSE 多级别共振
日线：背驰确认
30m: 第二类买点
置信度：高
```

---

## ⚠️ 注意事项

### 1. 交易时间
- 美股交易时间：09:30-16:00 ET (周一至周五)
- 盘前/盘后数据可能不完整

### 2. 数据延迟
- Yahoo Finance 数据可能有 15 分钟延迟
- 关键决策建议使用实时数据源

### 3. 节假日
- 美股休市日无数据 (感恩节、圣诞节等)
- 系统会自动跳过休市日

### 4. 财报季
- 财报发布前后波动可能加大
- 背驰信号可能失效，需谨慎

---

## 📞 故障排除

### 问题：收不到 EOSE 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep EOSE alerts.log

# 3. 测试数据获取
python test_eose_monitor.py
```

### 问题：数据获取失败

**解决**:
```bash
# 检查网络连接
curl -I https://finance.yahoo.com

# 检查 yfinance 安装
source venv/bin/activate
pip show yfinance
```

---

## 📚 相关文档

- [多级别背驰确认系统](SETUP_MULTI_LEVEL.md)
- [监控系统使用说明](MONITOR_USAGE.md)
- [缠论基础理论](docs/CHANLUN_MONITOR_DEV_PLAN.md)

---

**配置状态**: ⏳ 待配置  
**最后测试**: 待测试  
**下次自动汇报**: 16:00 ET (收盘报告)
