# 防重复警报修复说明

**日期**: 2026-04-03  
**问题**: 休市期间价格不变，导致每 15 分钟重复发送相同警报

---

## 🐛 问题描述

### 现象
```
2026-04-02T16:45:02 - CVE.TO 30m 第二类买点 @ $36.94
2026-04-03T09:00:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 相同价格
2026-04-03T09:15:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 重复
2026-04-03T09:30:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 重复
2026-04-03T09:45:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 重复
2026-04-03T10:00:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 重复
2026-04-03T10:15:02 - CVE.TO 30m 第二类买点 @ $36.94  ← 重复
```

### 根本原因
1. **休市期间数据不更新** - Yahoo Finance 在休市时返回最后收盘价
2. **缺少去重机制** - 监控系统每次扫描都发送警报，不管信号是否相同
3. **无价格变化检测** - 即使价格完全相同也触发警报

---

## ✅ 解决方案

### 三重过滤机制

| 机制 | 参数 | 说明 |
|------|------|------|
| **价格变化检测** | `MIN_PRICE_CHANGE = 0.3%` | 价格变化 < 0.3% 不触发新警报 |
| **信号去重** | Key: `symbol:type:level` | 相同标的 + 信号类型 + 级别视为同一信号 |
| **静默期** | `SILENCE_PERIOD = 60 分钟` | 同一信号至少间隔 60 分钟才再次警报 |

### 工作流程

```
扫描到信号
    ↓
检查是否首次出现？ → 是 → 发送警报
    ↓ 否
检查价格变化？ → ≥0.3% → 发送警报
    ↓ <0.3%
跳过 (价格未显著变化)
    ↓
检查静默期？ → 已过 60 分钟 → 发送警报
    ↓ 未过
跳过 (静默期内)
```

---

## 🔧 代码修改

### 新增配置
```python
# 防重复警报设置
MIN_PRICE_CHANGE = 0.003  # 最小价格变化 0.3%
SILENCE_PERIOD_MINUTES = 60  # 静默期 60 分钟
ALERT_STATE_FILE = ".alert_state.json"  # 状态文件
```

### 新增函数

1. **`load_alert_state()`** - 加载警报状态
2. **`save_alert_state()`** - 保存警报状态
3. **`should_send_alert()`** - 检查是否应该发送警报
4. **`update_alert_state()`** - 更新警报状态（含 24 小时自动清理）

### 修改函数

**`send_telegram_alert()`** - 添加防重复检查
```python
# 发送前检查
signal_type = signal['type'].replace(' (背驰)', '')
if not should_send_alert(symbol, signal_type, level, signal['price']):
    continue  # 跳过重复警报

# 发送成功后更新状态
update_alert_state(symbol, signal_type, level, signal['price'])
```

---

## 📊 状态文件格式

`.alert_state.json` 示例:
```json
{
  "alerts": {
    "CVE.TO:buy2:30m": {
      "price": 36.94,
      "time": "2026-04-03T10:15:02.123456",
      "symbol": "CVE.TO",
      "signal_type": "buy2",
      "level": "30m"
    },
    "UVIX:buy1:5m": {
      "price": 8.53,
      "time": "2026-04-02T14:30:02.600959",
      "symbol": "UVIX",
      "signal_type": "buy1",
      "level": "5m"
    }
  }
}
```

**自动清理**: 超过 24 小时的记录会被自动删除

---

## 🧪 测试场景

### 场景 1: 价格不变 (休市)
```
10:00 - CVE.TO buy2 @ $36.94 → ✅ 发送
10:15 - CVE.TO buy2 @ $36.94 → ⏭️ 跳过 (价格变化 0%)
10:30 - CVE.TO buy2 @ $36.94 → ⏭️ 跳过 (价格变化 0%)
```

### 场景 2: 价格显著变化
```
10:00 - CVE.TO buy2 @ $36.94 → ✅ 发送
10:15 - CVE.TO buy2 @ $37.05 → ✅ 发送 (变化 0.3%+)
```

### 场景 3: 静默期后
```
10:00 - CVE.TO buy2 @ $36.94 → ✅ 发送
11:00 - CVE.TO buy2 @ $36.94 → ✅ 发送 (静默期已过)
```

### 场景 4: 不同信号类型
```
10:00 - CVE.TO buy2 @ $36.94 → ✅ 发送
10:15 - CVE.TO sell2 @ $37.20 → ✅ 发送 (不同信号类型)
```

---

## 📝 使用说明

### 调整参数

编辑 `monitor_all.py`:
```python
# 更敏感 (0.1% 变化就警报)
MIN_PRICE_CHANGE = 0.001

# 更宽松 (30 分钟静默期)
SILENCE_PERIOD_MINUTES = 30

# 更严格 (1% 变化 + 120 分钟静默)
MIN_PRICE_CHANGE = 0.01
SILENCE_PERIOD_MINUTES = 120
```

### 手动清除状态

```bash
# 清除所有警报状态 (重置所有信号)
rm /home/wei/.openclaw/workspace/chanlunInvester/.alert_state.json

# 查看当前状态
cat /home/wei/.openclaw/workspace/chanlunInvester/.alert_state.json
```

---

## ✅ 验证步骤

1. **语法检查**
   ```bash
   python3 -m py_compile monitor_all.py
   ```

2. **手动运行测试**
   ```bash
   cd /home/wei/.openclaw/workspace/chanlunInvester
   ./venv/bin/python3 monitor_all.py
   ```

3. **观察日志**
   ```bash
   tail -f alerts.log
   ```

4. **检查状态文件**
   ```bash
   cat .alert_state.json
   ```

---

## 📌 预期效果

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 休市 8 小时 | ~32 条重复警报 | 1 条 (首次) |
| 震荡市 (±0.2%) | 每 15 分钟警报 | 静默 |
| 趋势市 (±1%) | 每 15 分钟警报 | 每小时 1 条 |
| 信号反转 | 正常 | 正常 |

**预计减少警报量**: 80-90% (休市/震荡市)

---

**修复完成**: 2026-04-03  
**版本**: v5.0.1  
**状态**: ✅ 待验证
