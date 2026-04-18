# IONQ (IonQ Inc) 美股缠论监控配置

**添加日期**: 2026-04-14  
**标的**: IONQ (NYSE: IonQ Inc)  
**监控级别**: 日线 + 30 分钟双级别联动

---

## 📊 标的基本信息

| 属性 | 值 |
|------|-----|
| **代码** | IONQ |
| **交易所** | NYSE (纽约证券交易所) |
| **公司** | IonQ Inc |
| **行业** | 科技/量子计算 (Quantum Computing) |
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
    {'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1d', '30m']},
]
```

### multi_level_confirmation.py (多级别确认)

```python
SYMBOLS = [
    # ... 其他标的
    {'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1d', '30m']},
]
```

---

## 🚀 测试方法

### 运行测试脚本

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 测试 IONQ 数据获取
python -c "import yfinance as yf; t=yf.Ticker('IONQ'); print(t.info.get('shortName', 'N/A'))"

# 查看多级别确认状态
python scripts/test_confirmation.py --symbol IONQ
```

### 查看实时数据

```bash
# 运行一次完整监控
python monitor_all.py

# 查看警报日志
tail -f alerts.log | grep IONQ
```

---

## ✅ 联动提醒配置确认

### 多级别背驰确认系统

IONQ 已加入多级别背驰确认系统 (`scripts/multi_level_confirmation.py`)

**配置**：
```python
{'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1d', '30m']}
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

## 📈 量子计算行业背景

### IonQ 公司简介
- **核心业务**: 量子计算机硬件和软件解决方案
- **技术路线**: 离子阱 (Trapped Ion) 量子计算
- **市场定位**: 纯量子计算上市公司
- **行业特点**: 高波动、高成长预期

### 交易注意事项
- 量子计算股票波动性较大
- 受行业消息和政策影响显著
- 背驰信号需结合行业趋势判断
- 适合高风险偏好投资者

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

# IONQ 监控已包含在现有配置中 (monitor_all.py)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    /home/wei/.openclaw/workspace/chanlunInvester/venv/bin/python3 \
    monitor_all.py >> logs/monitor.log 2>&1
```

---

## 🔍 常见信号类型

### 第一类买点 (背驰)
```
🟢 IONQ 30m 第一类买点 (背驰)
价格：$XXX.XX
强度：0.XX
```

### 第二类买点 (确认)
```
🟢 IONQ 30m 第二类买点
价格：$XXX.XX
置信度：XX%
```

### 多级别共振
```
✅ IONQ 多级别共振
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

### 4. 量子计算股特性
- IONQ 为高波动科技股
- 受行业新闻、政策、技术突破影响大
- 背驰信号需结合基本面判断
- 建议设置止损位

---

## 📞 故障排除

### 问题：收不到 IONQ 警报

**检查**:
```bash
# 1. 查看监控日志
tail logs/monitor.log

# 2. 查看警报日志
grep IONQ alerts.log

# 3. 测试数据获取
python -c "import yfinance as yf; t=yf.Ticker('IONQ'); print(t.history(period='5d'))"
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
- [RKLB 监控配置](RKLB_MONITOR_SETUP.md)
- [TECK 监控配置](TECK_MONITOR_SETUP.md)
- [监控系统使用说明](MONITOR_USAGE.md)

---

## 📊 美股监控列表

| 标的 | 公司 | 行业 | 级别 | 状态 |
|------|------|------|------|------|
| TEL | TE Connectivity | 科技/连接器 | 30m + 1d | ✅ 运行中 |
| GOOG | Alphabet/Google | 科技巨头 | 1w + 1d | ✅ 运行中 |
| INTC | Intel | 半导体 | 30m + 1d | ✅ 运行中 |
| EOSE | Eos Energy | 储能 | 30m + 1d | ✅ 运行中 |
| BABA | Alibaba | 电商/科技 | 1d + 30m | ✅ 运行中 |
| RKLB | Rocket Lab | 航天 | 1d + 30m | ✅ 运行中 |
| SMR | NuScale Power | 核能 | 1d + 30m | ✅ 运行中 |
| **IONQ** | **IonQ** | **量子计算** | **1d + 30m** | ✅ **新增** |

---

**配置状态**: ✅ **已启用**  
**多级别联动**: ✅ 日线 +30 分钟联动提醒已配置  
**最后信号**: 2026-04-14 - 初始配置完成  
**下次自动汇报**: 17:54 ET (收盘报告)
