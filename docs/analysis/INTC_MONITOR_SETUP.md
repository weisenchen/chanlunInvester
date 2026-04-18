# INTC (Intel Corporation) 美股缠论监控配置

**添加日期**: 2026-04-08  
**标的**: INTC (NASDAQ: Intel Corporation)  
**监控级别**: 30 分钟 + 日线双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | INTC |
| **交易所** | NASDAQ (纳斯达克) |
| **公司** | Intel Corporation |
| **行业** | 半导体/科技 |
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
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['30m', '1d']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate
python test_intc_monitor.py
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep INTC
```

### 查看多级别确认状态

```bash
python scripts/test_confirmation.py --symbol INTC
```

---

## 📈 当前分析 (2026-04-08 13:00 EDT)

### 日线级别
- **最新价格**: $58.60
- **笔数**: 17 笔
- **最新笔方向**: 向下 ⬇️
- **MACD**: DIF=1.78, DEA=0.35, MACD=2.85

### 30 分钟级别
- **最新价格**: $58.60
- **笔数**: 32 笔
- **最新笔方向**: 向上 ⬆️
- **MACD**: DIF=2.06, DEA=1.64, MACD=0.84

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

# INTC 监控已包含在现有配置中
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 INTC 30m 第一类买点 (背驰)
价格：$XX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 INTC 30m 第二类买点
价格：$XX.XX
置信度：XX%
```

### 多级别共振
```
✅ INTC 多级别共振
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
- Intel 财报通常在 1 月、4 月、7 月、10 月发布
- 财报发布前后波动可能加大
- 背驰信号可能失效，需谨慎

---

## 📞 故障排除

### 问题：收不到 INTC 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep INTC alerts.log

# 3. 测试数据获取
python test_intc_monitor.py
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
- [TEL 美股监控配置](TEL_MONITOR_SETUP.md)
- [GOOG 美股监控配置](GOOG_MONITOR_SETUP.md)
- [监控系统使用说明](MONITOR_USAGE.md)

---

## 📊 美股监控列表

| 标的 | 公司 | 级别 | 状态 |
|------|------|------|------|
| TEL | TE Connectivity | 30m + 1d | ✅ 运行中 |
| GOOG | Alphabet/Google | 1w + 1d | ✅ 运行中 |
| INTC | Intel | 30m + 1d | ✅ 新增 |

---

**配置状态**: ✅ **已启用**  
**多级别联动**: ✅ 日线 +30 分钟联动提醒已配置  
**最后测试**: 2026-04-13 15:43 EDT - 当前无背驰信号  
**下次自动汇报**: 16:00 ET (收盘报告)

---

## ✅ 联动提醒配置确认 (2026-04-13 验证)

### 多级别背驰确认系统

INTC 已加入多级别背驰确认系统 (`scripts/multi_level_confirmation.py`)

**配置**：
```python
{'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['1d', '30m']}
```

**联动逻辑**：
1. **日线背驰预警** → 触发第一阶段警报
2. **30 分钟第一类买卖点** → 触发第二阶段警报
3. **30 分钟第二类买卖点** → 触发第三阶段确认警报（可入场）

**确认窗口**：
- 日线背驰：48 小时内需要 30m 确认
- 30m 背驰：12 小时内需要次级别确认

### 当前状态 (2026-04-13 15:43 EDT)

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

### 📊 验证记录 (2026-04-13)

| 检查项 | 状态 |
|--------|------|
| monitor_all.py 配置 | ✅ 已配置 |
| multi_level_confirmation.py | ✅ 已配置 |
| 多级别背驰检测 | ✅ 正常运行 |
| Telegram 警报 | ✅ 推送正常 |
| 当前信号 | ⚪ 无背驰 |
