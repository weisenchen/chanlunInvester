# BABA (Alibaba Group) 美股缠论监控配置

**添加日期**: 2026-04-10  
**标的**: BABA (NYSE: Alibaba Group Holding Limited)  
**监控级别**: 日线 + 30 分钟双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | BABA |
| **交易所** | NYSE (纽约证券交易所) |
| **公司** | Alibaba Group Holding Limited |
| **行业** | 电子商务/科技/中概股 |
| **监控级别** | 1d + 30m |

---

## 🎯 监控功能

### 1. 日线 +30 分钟联动监控

- **日线级别**: 捕捉中期趋势和背驰信号
- **30 分钟级别**: 捕捉短期买卖点
- **联动提醒**: 大级别背驰 + 次级别确认时优先推送

### 2. 多级别背驰确认

```
日线背驰预警 → 30m 第一类买卖点 → 30m 第二类买卖点确认
   (观察)        (重点关注)          (入场信号)
```

### 3. Telegram 实时警报

警报将通过 OpenClaw 发送到 Telegram (Chat ID: 8365377574)

---

## 📁 配置文件更新

### monitor_all.py (主监控)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行一次完整监控

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate
python monitor_all.py
```

### 查看 BABA 特定信号

```bash
# 查看警报日志中的 BABA 信号
grep BABA alerts.log

# 运行多级别确认分析
python scripts/multi_level_confirmation.py --symbol BABA
```

### 查看实时数据

```bash
# 测试数据获取
python scripts/test_confirmation.py --symbol BABA
```

---

## 📈 信号类型示例

### 日线背驰预警
```
⚠️ BABA 日线背驰预警
价格：$XX.XX
背驰类型：底背驰/顶背驰
状态：等待 30m 确认
```

### 30 分钟第一类买点
```
🟢 BABA 30m 第一类买点 (背驰)
价格：$XX.XX
强度：0.XX
日线状态：背驰确认中
```

### 30 分钟第二类买点 (确认)
```
✅ BABA 多级别共振确认
日线：底背驰确认
30m: 第二类买点
置信度：高 (≥80%)
建议：关注入场机会
```

### 标准买卖点
```
🟢 BABA 30m 第二类买点
价格：$XX.XX
置信度：XX%
```

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

# BABA 监控已包含在现有配置中
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## ⚠️ 注意事项

### 1. 交易时间
- 美股交易时间：09:30-16:00 ET (周一至周五)
- 盘前/盘后数据可能不完整

### 2. 数据延迟
- Yahoo Finance 数据可能有 15 分钟延迟
- 关键决策建议使用实时数据源

### 3. 中概股特殊性
- BABA 为中概股，受中美关系和政策影响较大
- 财报通常在 2 月、5 月、8 月、11 月发布
- 财报发布前后波动可能加大，背驰信号需谨慎

### 4. 节假日
- 美股休市日无数据 (感恩节、圣诞节等)
- 中国节假日可能影响交易量

---

## 🔍 故障排除

### 问题：收不到 BABA 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log | grep BABA

# 2. 查看警报日志
grep BABA alerts.log

# 3. 测试数据获取
python scripts/test_confirmation.py --symbol BABA
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
- [INTC 美股监控配置](INTC_MONITOR_SETUP.md)
- [TEL 美股监控配置](TEL_MONITOR_SETUP.md)
- [GOOG 美股监控配置](GOOG_MONITOR_SETUP.md)
- [监控系统使用说明](MONITOR_USAGE.md)

---

## 📊 美股监控列表

| 标的 | 公司 | 级别 | 状态 |
|------|------|------|------|
| TEL | TE Connectivity | 1d + 30m | ✅ 运行中 |
| GOOG | Alphabet/Google | 1w + 1d | ✅ 运行中 |
| INTC | Intel | 1d + 30m | ✅ 运行中 |
| EOSE | Eos Energy | 1d + 30m | ✅ 运行中 |
| **BABA** | **Alibaba Group** | **1d + 30m** | ✅ **新增** |

---

## 📝 配置状态

| 项目 | 状态 |
|------|------|
| monitor_all.py | ✅ 已添加 |
| multi_level_confirmation.py | ✅ 已添加 |
| 配置文档 | ✅ 已创建 |
| 首次测试 | ⏳ 待执行 |

---

**配置状态**: ✅ 完成  
**配置时间**: 2026-04-10  
**下次自动汇报**: 09:00 ET (盘前报告)
