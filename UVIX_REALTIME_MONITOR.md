# UVIX 实时买卖点监控系统

## 🚨 监控状态：**已启用**

**最后更新:** 2026-03-03 15:00 EST

---

## 📊 监控配置

| 项目 | 配置 |
|------|------|
| **标的** | UVIX (2x Long VIX Futures ETF) |
| **数据源** | Yahoo Finance (实时) |
| **监控级别** | 30 分钟 + 5 分钟 |
| **监控时段** | 美股交易时间 (9:30-16:00 ET) |
| **检查频率** | 正常：30 分钟 / 活跃：15 分钟 |
| **告警渠道** | Console + 日志 |

---

## 🔔 告警触发条件

**任一条件满足即发送警告:**

- ✅ **30 分钟级别** 出现第一/二/三类买卖点
- ✅ **5 分钟级别** 出现第一/二/三类买卖点
- ✅ 检测到背驰信号 (顶背驰/底背驰)
- ✅ 买卖点置信度 > 70%

---

## ⏰ 监控时间表 (美东时间)

| 时间 | 频率 | 说明 |
|------|------|------|
| **09:00** | 每日一次 | 盘前分析 |
| **09:30-16:00** | 每 30 分钟 | 正常交易时段监控 |
| **10:00-15:00** | 每 15 分钟 | 高活跃度时段加密监控 |
| **16:30** | 每日一次 | 盘后总结 |

---

## 📝 查看监控状态

### 快速检查
```bash
cd /home/wei/.openclaw/workspace/trading-system
./scripts/uvix_quick_check.sh
```

### 查看实时日志
```bash
# 监控日志
tail -f logs/uvix_cron.log

# 告警日志
tail -f logs/uvix_alerts.log
```

### 手动运行
```bash
python3 examples/uvix_monitor.py
```

---

## 🎯 当前状态

**最新检查:** 2026-03-03 14:59 EST

| 级别 | 买卖点 | 背驰 | 建议 |
|------|--------|------|------|
| **30m** | ❌ 无 | ❌ 无 | ⚪ HOLD |
| **5m** | ❌ 无 | ❌ 无 | ⚪ HOLD |

**总体状态:** 🟢 正常监控中，无买卖点信号

---

## 📈 历史告警记录

查看 `logs/uvix_alerts.log` 获取所有历史告警。

---

## 🔧 系统信息

- **监控脚本:** `examples/uvix_monitor.py`
- **Cron 配置:** 已启用
- **数据源:** Yahoo Finance (yfinance)
- **日志目录:** `logs/`
- **配置文件:** `config/uvix_cron.yaml`

---

## ⚠️ 注意事项

1. **仅在美股交易日运行** (周一至周五)
2. **自动识别美国节假日休市**
3. **买卖点出现时会立即发送提醒**
4. **实时数据依赖 Yahoo Finance**

---

## 📞 快速命令

```bash
# 查看当前状态
./scripts/uvix_quick_check.sh

# 查看监控日志
tail -f logs/uvix_cron.log

# 查看告警日志
tail -f logs/uvix_alerts.log

# 手动检查
python3 examples/uvix_monitor.py

# 重新配置 Cron
./scripts/enable_uvix_alerts.sh
```

---

**监控系统已就绪，随时准备捕捉买卖点！** 🎯
