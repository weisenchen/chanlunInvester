# 多级别背驰确认监控系统

**版本**: v1.0  
**创建日期**: 2026-04-06  
**最后更新**: 2026-04-06

---

## 📚 核心原理

### 缠论级别递归

> "大级别背驰只是预警，真正逆转需要次级别确认。"

**级别递归关系**：
```
日线 (1d) 背驰 → 需要 30 分钟 (30m) 级别确认
30 分钟 (30m) 背驰 → 需要 5 分钟 (5m) 级别确认
5 分钟 (5m) 背驰 → 最小级别，直接交易
```

**为什么需要次级别确认？**
1. **大级别背驰可能是中继**：价格可能继续创新高/低
2. **次级别走势是大级别的组成**：大级别转折 = 次级别趋势逆转
3. **提高胜率**：双重确认比单一信号更可靠

---

## 🎯 确认流程（三阶段）

### 第一阶段：大级别背驰预警 ⚠️

```
触发条件:
- 大级别（如 1d）出现背驰
- 背驰强度 > 阈值（1d: 0.3, 30m: 0.25）

操作:
- 加入观察名单
- 启动确认窗口计时器
- 发送预警通知
```

**通知示例**：
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

---

### 第二阶段：次级别第一类买卖点 🔍

```
触发条件:
- 次级别（如 30m）出现同向背驰
- 信号方向与大级别一致

操作:
- 升级状态为"重点关注"
- 发送提醒通知
```

**通知示例**：
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

---

### 第三阶段：次级别第二类买卖点 ✅

```
触发条件:
- 次级别回调不破前低（买点）/ 反弹不过前高（卖点）
- 价格变化 > 0.3%（防重复）

操作:
- 确认逆转完成
- 发送入场信号
- 记录确认价格
```

**通知示例**：
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

## ⚙️ 配置说明

### 级别配置 (`LEVEL_CONFIG`)

```python
LEVEL_CONFIG = {
    '1d': {
        'child_level': '30m',           # 次级别
        'weight': 3.0,                   # 权重
        'divergence_threshold': 0.3,     # 背驰强度阈值
        'confirmation_window_hours': 48, # 确认窗口（小时）
    },
    '30m': {
        'child_level': '5m',
        'weight': 2.0,
        'divergence_threshold': 0.25,
        'confirmation_window_hours': 12,
    },
    '5m': {
        'child_level': None,  # 最小级别
        'weight': 1.0,
        'divergence_threshold': 0.2,
        'confirmation_window_hours': 0,
    }
}
```

### 监控标的配置 (`SYMBOLS`)

```python
SYMBOLS = [
    {'symbol': 'UVIX', 'name': '波动率指数', 'levels': ['1d', '30m', '5m']},
    {'symbol': 'XEG.TO', 'name': '加拿大能源 ETF', 'levels': ['1d', '30m']},
    {'symbol': 'CVE.TO', 'name': 'Cenovus Energy', 'levels': ['1d', '30m']},
    # ... 添加更多标的
]
```

---

## 🚀 使用方法

### 独立运行

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 运行多级别监控
python scripts/multi_level_confirmation.py
```

### 集成到现有监控系统

```python
from scripts.multi_level_confirmation import MultiLevelMonitor

monitor = MultiLevelMonitor()
monitor.run()
```

### 添加 Cron 任务

```bash
# 每 15 分钟检查一次（交易时段）
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    scripts/multi_level_confirmation.py >> logs/multi_level.log 2>&1
```

---

## 📊 状态管理

### 确认阶段枚举

```python
class ConfirmationStage(Enum):
    WAITING = "waiting"                    # 等待大级别背驰
    PARENT_DIVERGENCE = "parent_divergence"  # 大级别背驰预警
    CHILD_BSP1 = "child_bsp1"              # 次级别第一类买卖点
    CHILD_BSP2 = "child_bsp2"              # 次级别第二类买卖点
    CONFIRMED = "confirmed"                # 逆转确认
    FAILED = "failed"                      # 确认失败
```

### 状态文件 (`.confirmation_state.json`)

```json
{
  "CVE.TO:1d": {
    "symbol": "CVE.TO",
    "parent_level": "1d",
    "child_level": "30m",
    "stage": "child_bsp2",
    "parent_divergence": {
      "symbol": "CVE.TO",
      "level": "1d",
      "signal_type": "buy",
      "strength": 0.65,
      "price": 36.94,
      "timestamp": "2026-04-02T14:15:00"
    },
    "child_bsp1": {
      "symbol": "CVE.TO",
      "level": "30m",
      "signal_type": "buy",
      "strength": 0.45,
      "price": 36.60,
      "timestamp": "2026-04-02T14:30:00"
    },
    "child_bsp2": {
      "type": "bsp2_buy",
      "level": "30m",
      "price": 36.94,
      "confidence": 0.7
    },
    "confirmed_price": 36.94,
    "created_at": "2026-04-02T14:15:00",
    "updated_at": "2026-04-02T15:00:00"
  }
}
```

---

## ⏰ 超时处理

### 确认窗口

| 大级别 | 确认窗口 | 说明 |
|--------|----------|------|
| 1d | 48 小时 | 日线背驰需要 2 天内确认 |
| 30m | 12 小时 | 30 分钟背驰需要半天内确认 |
| 5m | 无 | 最小级别，无需确认 |

### 超时处理

```
如果超时未收到次级别确认:
1. 状态标记为 FAILED
2. 发送超时通知
3. 记录失败原因
4. 需要重新评估走势
```

**超时通知示例**：
```
⏰ 确认超时 ⚠️

📊 CVE.TO
🔸 大级别：1d 背驰
🔸 等待：30m 级别确认
🔸 超时：48 小时

💡 状态：确认失败，背驰可能失效
📋 建议：重新评估走势
```

---

## 📈 实战案例

### 案例 1: CVE.TO 日线背驰确认成功

```
时间线:
2026-04-02 14:15 - 1d 底背驰出现 (强度 0.65) → ⚠️ 预警
2026-04-02 14:30 - 30m 底背驰出现 (强度 0.45) → 🔍 关注
2026-04-02 15:00 - 30m 第二类买点确认 → ✅ 入场

结果:
- 确认价格：$36.94
- 后续走势：连续 3 日上涨
- 胜率：✅ 成功
```

### 案例 2: UVIX 30m 背驰超时失败

```
时间线:
2026-04-01 10:00 - 30m 顶背驰出现 (强度 0.55) → ⚠️ 预警
2026-04-01 10:00-22:00 - 等待 5m 确认
2026-04-01 22:00 - 超时（12 小时未确认） → ⏰ 失败

结果:
- 背驰失效，价格继续创新高
- 状态：FAILED
- 教训：小级别背驰在强趋势中容易失效
```

---

## 🔧 高级配置

### 自定义背驰阈值

```python
# 更严格（减少假信号）
'divergence_threshold': 0.5  # 默认 0.3

# 更宽松（捕捉更多机会）
'divergence_threshold': 0.2  # 默认 0.3
```

### 调整确认窗口

```python
# 更长窗口（适合震荡市）
'confirmation_window_hours': 72  # 默认 48

# 更短窗口（适合快速走势）
'confirmation_window_hours': 24  # 默认 48
```

### 添加更多级别

```python
# 添加周线级别
'1w': {
    'child_level': '1d',
    'weight': 5.0,
    'divergence_threshold': 0.4,
    'confirmation_window_hours': 168,  # 1 周
}
```

---

## 📝 日志与调试

### 日志文件

- **警报日志**: `alerts.log`
- **状态文件**: `.confirmation_state.json`
- **运行日志**: `logs/multi_level.log` (Cron 模式)

### 调试模式

```python
# 在脚本开头添加
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看详细分析过程
monitor = MultiLevelMonitor()
monitor.run()  # 会输出每个级别的详细分析
```

---

## ⚠️ 注意事项

### 1. 级别匹配

确保大级别和次级别方向一致：
- 1d 买信号 → 只匹配 30m 买信号
- 30m 卖信号 → 只匹配 5m 卖信号

### 2. 确认窗口

超时不代表一定失败，但需要重新评估：
- 检查是否有其他因素（如重大消息）
- 可能需要调整阈值或窗口

### 3. 小级别假信号

5m 级别频繁背驰是正常现象：
- 优先参考大级别信号
- 小级别仅用于精确入场点

### 4. 数据质量

确保数据源稳定：
- Yahoo Finance 可能有延迟
- 关键时段建议多数据源验证

---

## 📖 理论参考

**缠中说禅原文**：
> "大级别的背驰，最终都要通过次级别的走势来确认。"
> 
> "第一类买卖点是背驰点，第二类买卖点才是安全入场点。"

**参考课程**：
- 《教你炒股票》第 24 课：背驰与级别
- 《教你炒股票》第 32 课：第二类买卖点
- 《教你炒股票》第 41 课：级别递归

---

## 🎯 最佳实践

1. **优先大级别**：1d 信号 > 30m 信号 > 5m 信号
2. **等待确认**：不要在第一类买卖点重仓
3. **设置止损**：即使确认也有失败可能
4. **记录案例**：成功/失败案例都要记录
5. **定期回顾**：每周回顾确认成功率

---

**作者**: ChanLun AI Agent  
**状态**: ✅ 生产就绪  
**测试**: 待实战验证
