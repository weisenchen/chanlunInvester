# UVIX 缠论自动监控系统

## 🚨 功能说明

**实时监控 UVIX 5 分钟级别，买卖点出现后立即发送 Telegram 预警！**

---

## ⚡ 快速开始

### 1. 手动测试

```bash
cd /home/wei/.openclaw/workspace/trading-system
python3 scripts/test_uvix_alert.py
```

### 2. 运行一次检查

```bash
python3 scripts/uvix_auto_monitor.py
# 按 Ctrl+C 停止
```

### 3. 自动监控 (已设置)

Cron 任务已配置，**每 5 分钟自动检查一次**：

```cron
# 交易时段每 5 分钟检查
*/5 13-20 * * 1-5 python3 scripts/uvix_auto_monitor.py

# 盘前检查 (9:00 EST)
0 13 * * 1-5 python3 scripts/uvix_auto_monitor.py

# 盘后总结 (16:30 EST)
30 20 * * 1-5 python3 scripts/uvix_auto_monitor.py
```

---

## 📊 监控配置

**文件:** `scripts/uvix_auto_monitor.py`

```python
CONFIG = {
    'symbol': 'UVIX',              # 监控标的
    'timeframe': '5m',             # 5 分钟级别
    'check_interval_minutes': 5,   # 每 5 分钟检查一次
    'trading_hours': {
        'start': 9,                # 美东时间 9:30
        'end': 16                  # 美东时间 16:00
    },
    'alert_channels': ['telegram', 'console', 'file'],
    'min_confidence': 0.7,         # 最小置信度 70%
}
```

---

## 🔔 预警渠道

### 1. Telegram (实时推送)

买卖点出现后**立即**发送 Telegram 消息：

```
🟢 UVIX 缠论买卖点预警

📊 标的：UVIX
⏰ 时间：2026-03-18 10:25:01 EST

🎯 买入信号 - 第一类买点

💰 入场：$7.22
📈 置信度：90%
📝 类型：bottom_divergence

💡 交易计划
入场价：$7.22
止损价：$7.00 (-3%)
目标 1:  $7.44 (+3%)
目标 2:  $7.58 (+5%)
```

### 2. Console (控制台输出)

实时监控时在控制台显示预警信息。

### 3. File (文件记录)

所有预警保存到：
```
logs/uvix_auto_alerts.log
```

---

## 📈 预警类型

### 第一类买点 (🟢)

**触发条件:**
- 下跌线段背驰
- MACD 底背驰
- 置信度 ≥ 70%

**操作建议:**
- 入场：背驰点价格
- 止损：-3%
- 目标：+3% / +5%

### 第一类卖点 (🔴)

**触发条件:**
- 上涨线段背驰
- MACD 顶背驰
- 置信度 ≥ 70%

**操作建议:**
- 入场：背驰点价格
- 止损：+3%
- 目标：-3% / -5%

---

## 🔧 自定义配置

### 修改监控频率

编辑 `uvix_auto_monitor.py`:

```python
'check_interval_minutes': 5,  # 改为 10 = 每 10 分钟
```

### 修改监控级别

```python
'timeframe': '5m',  # 改为 '30m' = 30 分钟级别
```

### 修改置信度阈值

```python
'min_confidence': 0.7,  # 改为 0.8 = 80% 置信度
```

### 添加其他监控标的

复制脚本并修改：

```python
'symbol': 'TSLA',  # 监控特斯拉
```

---

## 📝 日志文件

### 预警日志

```bash
tail -f logs/uvix_auto_alerts.log
```

### 运行日志

```bash
tail -f logs/uvix_auto_monitor.log
```

### 查看今日预警

```bash
grep "$(date +%Y-%m-%d)" logs/uvix_auto_alerts.log
```

---

## ⚠️ 注意事项

### 1. Telegram 配置

确保 OpenClaw Telegram 频道已配置：

```bash
openclaw message send -t telegram -m "测试"
```

### 2. 交易时段

系统只在美东时间 9:30-16:00 监控：

- 周末不监控
- 盘后不监控
- 美国节假日不监控

### 3. 数据源

使用 Yahoo Finance 实时数据：

- 交易时段：实时延迟 (<5 分钟)
- 盘后：无数据

### 4. 风险提示

- ⚠️ UVIX 是**-2x VIX**产品，波动极大
- ⚠️ **必须使用止损**
- ⚠️ 每笔交易风险不超过 2%
- ⚠️ 本系统仅供参考，不构成投资建议

---

## 🎯 使用示例

### 示例 1: 立即检查一次

```bash
cd /home/wei/.openclaw/workspace/trading-system
python3 scripts/test_uvix_alert.py
```

### 示例 2: 持续监控 1 小时

```bash
timeout 3600 python3 scripts/uvix_auto_monitor.py
```

### 示例 3: 查看监控状态

```bash
ps aux | grep uvix_auto_monitor
```

### 示例 4: 停止所有监控

```bash
pkill -f uvix_auto_monitor
```

### 示例 5: 查看 Cron 状态

```bash
crontab -l | grep uvix
```

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 检查频率 | 每 5 分钟 |
| 分析时间 | <3 秒/次 |
| 预警延迟 | <10 秒 |
| 数据源 | Yahoo Finance |
| 缠论核心 | chanlunInvester |

---

## 🔗 相关资源

- **chanlunInvester:** https://github.com/weisenchen/chanlunInvester
- **缠论 108 课:** 第 12, 20, 24, 62, 65, 67 课
- **UVIX 产品:** -2x VIX 期货 ETF

---

## ✅ 系统状态

**当前配置:**
- ✅ 自动监控：已启用
- ✅ Telegram 预警：已配置
- ✅ 文件日志：已启用
- ✅ 交易时段检查：已设置
- ✅ 置信度过滤：70%

**下次检查:** 5 分钟后

---

**🚨 买卖点出现后，立即发送 Telegram 预警！**
