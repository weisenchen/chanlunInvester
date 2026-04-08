# 多级别背驰确认系统 - 设置指南

**创建日期**: 2026-04-06  
**版本**: v1.0

---

## 🎯 系统功能

本系统实现了缠论的核心原理：**大级别背驰需要次级别确认**。

### 核心特性

1. **三阶段确认流程**
   - ⚠️ 第一阶段：大级别背驰预警
   - 🔍 第二阶段：次级别第一类买卖点
   - ✅ 第三阶段：次级别第二类买卖点（确认入场）

2. **级别递归监控**
   - 日线 (1d) → 30 分钟 (30m) 确认
   - 30 分钟 (30m) → 5 分钟 (5m) 确认

3. **智能超时处理**
   - 1d 背驰：48 小时内需要确认
   - 30m 背驰：12 小时内需要确认

4. **Telegram 实时通知**
   - 每个阶段自动推送
   - 包含详细分析数据

---

## 📁 文件结构

```
chanlunInvester/
├── scripts/
│   ├── multi_level_confirmation.py   # 主监控脚本
│   └── test_confirmation.py          # 测试/查看状态脚本
├── docs/
│   └── multi_level_confirmation.md   # 详细文档
├── .confirmation_state.json          # 状态文件（自动生成）
└── alerts.log                        # 警报日志
```

---

## 🚀 快速开始

### 1. 查看当前状态

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 查看所有背驰确认状态
python scripts/test_confirmation.py
```

**输出示例**：
```
⚠️ CVE.TO:1d
   阶段：parent_divergence
   大级别：1d 背驰预警
   次级别：30m 等待确认
   大级别背驰：🔴 卖 @ $32.95 (强度:0.83)
```

### 2. 运行完整监控

```bash
# 运行一次完整监控
python scripts/multi_level_confirmation.py
```

### 3. 添加定时任务（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（交易时段每 15 分钟检查）
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    scripts/multi_level_confirmation.py >> logs/multi_level.log 2>&1
```

---

## 📊 通知示例

### 第一阶段：大级别背驰预警

```
⚠️ 多级别背驰预警 🟢

📊 CVE.TO
🔸 级别：1d（大级别）
🔸 信号：第一类买点（背驰）
🔸 强度：0.65
🔸 价格：$36.94

📋 确认流程:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 等待 30m 级别第一类买点 ⏳
3️⃣ 等待 30m 级别第二类买点 ⏳

⏰ 确认窗口：48 小时
```

### 第二阶段：次级别第一类买卖点

```
🔍 次级别第一类买点 🟢

📊 CVE.TO
🔸 大级别：1d 背驰已确认
🔸 次级别：30m 第一类买点
🔸 强度：0.45
🔸 价格：$36.60

📋 确认流程:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 次级别第一类买点已出现 ✅
3️⃣ 等待次级别第二类买点 ⏳

💡 状态：重点关注，准备入场
```

### 第三阶段：确认入场

```
✅ 逆转确认！第二类买点 🟢

📊 CVE.TO
🔸 大级别：1d 背驰
🔸 次级别：30m 第二类买点
🔸 确认价格：$36.94
🔸 置信度：70%

📋 确认流程:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 次级别第一类买点已出现 ✅
3️⃣ 次级别第二类买点已确认 ✅

🎯 逆转确认完成！
💡 状态：可入场
```

---

## ⚙️ 配置选项

### 修改监控标的

编辑 `scripts/multi_level_confirmation.py`：

```python
SYMBOLS = [
    {'symbol': 'UVIX', 'name': '波动率指数', 'levels': ['1d', '30m', '5m']},
    {'symbol': 'XEG.TO', 'name': '加拿大能源 ETF', 'levels': ['1d', '30m']},
    # 添加更多标的...
]
```

### 调整背驰阈值

```python
LEVEL_CONFIG = {
    '1d': {
        'divergence_threshold': 0.3,  # 降低=更敏感，提高=更严格
        # ...
    },
    '30m': {
        'divergence_threshold': 0.25,
        # ...
    },
}
```

### 调整确认窗口

```python
LEVEL_CONFIG = {
    '1d': {
        'confirmation_window_hours': 48,  # 小时数
        # ...
    },
    '30m': {
        'confirmation_window_hours': 12,
        # ...
    },
}
```

---

## 🔍 常用命令

### 查看状态

```bash
# 查看所有确认状态
python scripts/test_confirmation.py

# 查看单个标的
python scripts/test_confirmation.py --symbol CVE.TO
```

### 手动触发监控

```bash
# 运行一次监控
python scripts/multi_level_confirmation.py

# 查看日志
tail -f alerts.log
```

### 清除状态

```bash
# 删除状态文件（重置所有确认状态）
rm .confirmation_state.json
```

---

## 📈 实战案例

### 成功案例：CVE.TO 日线背驰

```
时间线:
2026-04-02 14:15 - ⚠️ 1d 顶背驰预警 ($32.95, 强度 0.83)
2026-04-02 14:30 - 🔍 30m 顶背驰确认 ($32.80, 强度 0.55)
2026-04-02 15:00 - ✅ 30m 第二类卖点确认 ($33.10)

结果:
- 确认价格：$33.10
- 后续 3 日：$32.50 (-1.8%)
- 状态：✅ 成功
```

### 失败案例：超时未确认

```
时间线:
2026-04-01 10:00 - ⚠️ 30m 顶背驰预警
2026-04-01 10:00-22:00 - 🔍 等待 5m 确认
2026-04-01 22:00 - ⏰ 超时（12 小时）

结果:
- 状态：❌ FAILED
- 原因：强趋势中背驰失效
- 教训：小级别信号需更谨慎
```

---

## ⚠️ 注意事项

### 1. 数据延迟

Yahoo Finance 数据可能有 15 分钟延迟：
- 盘中信号仅供参考
- 关键决策建议使用实时数据源

### 2. 确认窗口

超时不代表一定失败：
- 可能是走势强劲延续
- 需要重新评估趋势强度

### 3. 小级别噪音

5m 级别频繁背驰是正常现象：
- 优先参考大级别信号
- 小级别仅用于精确入场

### 4. 重大消息

财报、经济数据发布时：
- 背驰信号可能失效
- 建议暂停自动交易

---

## 📖 理论基础

**缠中说禅核心原理**：

> "大级别的背驰，最终都要通过次级别的走势来确认。"

> "第一类买卖点是背驰点（左侧交易），第二类买卖点才是安全入场点（右侧交易）。"

**参考课程**：
- 《教你炒股票》第 24 课：背驰与级别
- 《教你炒股票》第 32 课：第二类买卖点
- 《教你炒股票》第 41 课：级别递归

---

## 🆘 故障排除

### 问题：收不到 Telegram 通知

**检查**：
1. OpenClaw 是否正常运行
2. Telegram 配置是否正确
3. 检查日志：`tail alerts.log`

### 问题：状态文件损坏

**解决**：
```bash
# 删除并重建
rm .confirmation_state.json
python scripts/multi_level_confirmation.py
```

### 问题：背驰检测不准确

**调整**：
```python
# 提高阈值（减少假信号）
'divergence_threshold': 0.5  # 默认 0.3

# 降低阈值（捕捉更多信号）
'divergence_threshold': 0.2  # 默认 0.3
```

---

## 📞 支持

- **详细文档**: `docs/multi_level_confirmation.md`
- **警报日志**: `alerts.log`
- **状态文件**: `.confirmation_state.json`

---

**作者**: ChanLun AI Agent  
**状态**: ✅ 生产就绪  
**最后更新**: 2026-04-06
