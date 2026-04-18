# TEL (TE Connectivity) 美股缠论监控配置

**添加日期**: 2026-04-08  
**标的**: TEL (NYSE: TE Connectivity plc)  
**监控级别**: 30 分钟 + 日线双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | TEL |
| **交易所** | NYSE (纽约证券交易所) |
| **公司** | TE Connectivity plc |
| **行业** | 电子元件 |
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
    # ... 其他标的
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['30m', '1d']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate
python test_tel_monitor.py
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep TEL
```

### 查看多级别确认状态

```bash
python scripts/test_confirmation.py --symbol TEL
```

---

## 📈 当前分析 (2026-04-08 10:36 EDT)

### 日线级别
- **最新价格**: $223.01
- **笔数**: 20 笔
- **最新笔方向**: 向下 ⬇️
- **MACD**: DIF=-0.37, DEA=-3.05, MACD=5.37

### 30 分钟级别
- **最新价格**: $223.01
- **笔数**: 37 笔
- **最新笔方向**: 向上 ⬆️
- **MACD**: DIF=2.69, DEA=1.06, MACD=3.28

### 联动状态
⚠️ **级别不一致** - 日线向下，30m 向上，可能处于转折期

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

# 添加 TEL 监控 (已包含在现有配置中)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 TEL 30m 第一类买点 (背驰)
价格：$XXX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 TEL 30m 第二类买点
价格：$XXX.XX
置信度：XX%
```

### 多级别共振
```
✅ TEL 多级别共振
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

### 问题：收不到 TEL 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep TEL alerts.log

# 3. 测试数据获取
python test_tel_monitor.py
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

**配置状态**: ✅ 完成  
**最后测试**: 2026-04-08 10:36 EDT  
**下次自动汇报**: 16:00 ET (收盘报告)
