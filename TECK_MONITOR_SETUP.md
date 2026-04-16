# TECK (Teck Resources Limited) 美股缠论监控配置

**添加日期**: 2026-04-06  
**标的**: TECK (NYSE: Teck Resources Limited)  
**监控级别**: 日线 + 30 分钟双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | TECK |
| **交易所** | NYSE (纽约证券交易所) |
| **公司** | Teck Resources Limited |
| **行业** | 材料/矿业 (铜、锌、煤炭) |
| **监控级别** | 1d + 30m |

---

## 🎯 监控功能

### 1. 实时买卖点监控

- **日线级别**: 捕捉中期趋势方向
- **30 分钟级别**: 捕捉短期买卖点
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
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'SMR', 'name': 'NuScale Power Corporation (美股)', 'levels': ['1d', '30m']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 测试 TECK 数据获取
python -c "import yfinance as yf; t=yf.Ticker('TECK'); print(t.info.get('shortName', 'N/A'))"

# 查看多级别确认状态
python scripts/test_confirmation.py --symbol TECK
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep TECK
```

---

## ✅ 联动提醒配置确认

### 多级别背驰确认系统

TECK 已加入多级别背驰确认系统 (`scripts/multi_level_confirmation.py`)

**配置**：
```python
{'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['1d', '30m']}
```

**联动逻辑**：
1. **日线背驰预警** → 触发第一阶段警报
2. **30 分钟第一类买卖点** → 触发第二阶段警报
3. **30 分钟第二类买卖点** → 触发第三阶段确认警报（可入场）

**确认窗口**：
- 日线背驰：48 小时内需要 30m 确认
- 30m 背驰：12 小时内需要次级别确认

### 当前状态 (2026-04-14)

| 级别 | 背驰状态 | 信号 |
|------|----------|------|
| 日线 (1d) | ⚪ 无背驰 | 观望 |
| 30 分钟 (30m) | ⚪ 无背驰 | 观望 |

**联动状态**: ⚪ 等待背驰信号

### 警报推送

当检测到联动信号时，Telegram 将收到以下类型的警报：

1. **⚠️ 多级别背驰预警** - 日线背驰出现
2. **🔍 次级别第一类买卖点** - 30m 确认中
3. **✅ 逆转确认！第二类买卖点** - 联动完成，可入场

### 实时监控

- **交易时段**: 每 15 分钟自动检查 (09:30-16:00 ET)
- **Cron 任务**: 已配置
- **日志**: `logs/multi_level.log`

---

## 📈 历史信号回顾

### 最近 10 条 TECK 警报

| 时间 | 信号类型 | 价格 |
|------|----------|------|
| 4/10 13:30 | 1d 买点 2 | $56.05 |
| 4/10 13:15 | 30m 卖点 2 | $56.11 |
| 4/10 12:15 | 1d 买点 2 | $56.22 |
| 4/10 11:00 | 30m 卖点 2 | $56.34 |
| 4/9 15:00 | 30m 卖点 2 | $54.73 |
| 4/9 13:45 | 30m 卖点 2 | $55.03 |
| 4/8 14:45 | 30m 卖点 2 | $55.70 |
| 4/7 13:30 | 30m 卖点 2 | $51.72 |
| 4/7 12:30 | 1d 买点 2 | $51.92 |
| 4/7 11:15 | 1d 买点 2 | $51.50 |

**信号特征**: 
- 4/7-4/10 期间频繁出现 30m 卖点 2 与 1d 买点 2 交替
- 显示日线级别底部震荡，30m 级别反复试探
- 当前价格 ~$56 附近，需等待明确共振信号

---

## ⏰ 监控时间表

| 时间 (EDT) | 事件 | 状态 |
|-----------|------|------|
| 09:00 | 盘前报告 | ✅ 自动 |
| 09:30-16:00 | 实时监控 (每 15 分钟) | ✅ 自动 |
| 16:00 | 收盘报告 | ✅ 自动 |
| 17:54 | 盘后复盘 | ✅ 自动 |

---

## 📋 Cron 配置

```bash
# 编辑 crontab
crontab -e

# TECK 监控已包含在现有配置中 (monitor_all.py)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 TECK 30m 第一类买点 (背驰)
价格：$XXX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 TECK 30m 第二类买点
价格：$XXX.XX
置信度：XX%
```

### 多级别共振
```
✅ TECK 多级别共振
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

### 4. 商品周期股特性
- TECK 为矿业股，受大宗商品价格影响大
- 铜、锌、煤炭价格波动会影响走势
- 背驰信号需结合商品周期判断

---

## 📞 故障排除

### 问题：收不到 TECK 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep TECK alerts.log

# 3. 测试数据获取
python -c "import yfinance as yf; t=yf.Ticker('TECK'); print(t.history(period='5d'))"
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
- [SMR 监控配置](SMR_MONITOR_SETUP.md)
- [PAAS.TO 监控配置](PAAS_MONITOR_SETUP.md)
- [监控系统使用说明](MONITOR_USAGE.md)

---

## 📊 加拿大股票监控列表

| 标的 | 公司 | 行业 | 级别 | 状态 |
|------|------|------|------|------|
| CNQ.TO | Canadian Natural Resources | 能源 | 30m + 1d | ✅ 运行中 |
| PAAS.TO | Pan American Silver | 贵金属 | 30m + 1d | ✅ 运行中 |
| TECK | Teck Resources | 矿业 | 30m + 1d | ✅ 运行中 |

---

**配置状态**: ✅ **已启用**  
**多级别联动**: ✅ 日线 +30 分钟联动提醒已配置  
**最后信号**: 2026-04-10 13:30 - 1d 买点 2 @ $56.05  
**下次自动汇报**: 17:54 ET (收盘报告)
