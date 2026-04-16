# 全方位股票预警系统

**版本**: v1.0  
**创建日期**: 2026-04-14  
**系统定位**: 基本面 + 行业新闻 + 缠论技术 三位一体预警

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              全方位股票预警系统                          │
│         Comprehensive Stock Alert System                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   基本面     │  │   行业新闻   │  │   缠论技术   │ │
│  │   分析模块   │  │   监控模块   │  │   分析模块   │ │
│  │              │  │              │  │              │ │
│  │ • 营收增长   │  │ • 新闻抓取   │  │ • 买卖点检测 │ │
│  │ • 毛利率     │  │ • 情绪分析   │  │ • 背驰识别   │ │
│  │ • 机构持股   │  │ • 关键词匹配 │  │ • 级别联动   │ │
│  │ • 现金比率   │  │ • 重大事件   │  │ • 置信度计算 │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                            │
│                  ┌────────▼────────┐                   │
│                  │   综合预警引擎   │                   │
│                  │  Alert Engine   │                   │
│                  └────────┬────────┘                   │
│                           │                            │
│         ┌─────────────────┼─────────────────┐         │
│         │                 │                 │         │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐ │
│  │  警报级别    │  │  操作建议    │  │  Telegram    │ │
│  │  判定模块    │  │  生成模块    │  │  推送模块    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 三大维度指标

### 1. 基本面分析 (Fundamental Analysis) - 权重 35%

| 指标 | 权重 | 评分逻辑 |
|------|------|----------|
| **营收增长** | 30% | >50%→+0.3, >20%→+0.2, >0→+0.1, <-20%→-0.15 |
| **毛利率** | 25% | >70%→+0.25, >50%→+0.15, >30%→+0.08 |
| **机构持股** | 20% | >80%→+0.2, >50%→+0.12, >20%→+0.05 |
| **现金比率** | 15% | >2→+0.15, >1→+0.1, <0.3→-0.15 |
| **市值规模** | 10% | >1000 亿→+0.1, >100 亿→+0.05 |

**基本面警报类型**:
- 📈 **营收增长突破**: 增长率>50%
- 💰 **毛利率突破**: 毛利率>70%
- 🏦 **机构持股突破**: 机构持股>80%
- ⚠️ **现金流预警**: 现金比率<0.3

---

### 2. 行业新闻监控 (Industry News Monitoring) - 权重 25%

**正面关键词**:
```
beat, upgrade, growth, gain, surge, rally, bullish,
positive, strong, record, breakthrough, partnership, deal,
announce, launch, approve, success, win, contract, award
```

**负面关键词**:
```
miss, downgrade, loss, drop, plunge, crash, bearish,
negative, weak, warning, lawsuit, investigation, delay,
recall, fail, reject, cut, probe, fine, penalty
```

**新闻警报类型**:
- 📰 **重大利好新闻**: 24h 平均情绪>0.3 或 2+ 条重大利好
- ⚠️ **重大利空新闻**: 24h 平均情绪<-0.3 或 2+ 条重大利空
- 🔥 **新闻爆发**: 24h 新闻>20 条 (可能重大事件)

---

### 3. 缠论技术分析 (ChanLun Technical Analysis) - 权重 40%

**缠论信号类型**:
| 信号 | 含义 | 可靠性 |
|------|------|--------|
| **buy1** | 第一类买点 (背驰) | 高 |
| **buy2** | 第二类买点 (确认) | 非常高 |
| **buy3** | 第三类买点 (中枢突破) | 高 |
| **sell1** | 第一类卖点 (顶背驰) | 高 |
| **sell2** | 第二类卖点 (确认) | 非常高 |
| **sell3** | 第三类卖点 (中枢跌破) | 高 |

**增强置信度**: 结合行业趋势、基本面、消息面、资金流、波动率五维度调整

---

## 📈 综合得分计算

```
综合得分 = 基本面得分 × 35% + 新闻情绪得分 × 25% + 缠论置信度 × 40%
```

### 警报级别判定

| 级别 | 综合得分 | 图标 | 推送策略 |
|------|----------|------|----------|
| **CRITICAL** | ≥85% | 🚨 | 立即推送 + 高优先级 |
| **HIGH** | 70%-84% | 🔴 | 立即推送 |
| **MEDIUM** | 55%-69% | 🟡 | 正常推送 |
| **LOW** | 40%-54% | 🔵 | 仅记录，不推送 |
| **INFO** | <40% | ⚪ | 仅记录 |

---

## 💡 操作建议生成

| 综合得分 | 操作建议 | 仓位 | 止损策略 |
|----------|----------|------|----------|
| ≥80% | Strong Buy/Sell | 全仓 | 紧止损 (3-5%) |
| 70%-79% | Buy/Sell | 正常仓位 | 正常止损 (5-8%) |
| 55%-69% | Light Buy/Sell | 轻仓 | 宽止损 (8-12%) |
| 40%-54% | Observe | 观望 | N/A |
| <40% | Avoid | 避免 | N/A |

---

## 📁 系统文件

| 文件 | 说明 | 大小 |
|------|------|------|
| `scripts/comprehensive_alert_system.py` | 主系统脚本 | 25KB |
| `scripts/enhanced_confidence_analyzer.py` | 增强置信度模块 | 24KB |
| `config/enhanced_confidence.yaml` | 配置文件 | 5KB |
| `docs/COMPREHENSIVE_ALERT_SYSTEM.md` | 本文档 | - |

---

## 🚀 使用方法

### 1.  standalone 运行

```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 运行综合预警系统
python scripts/comprehensive_alert_system.py
```

### 2. 集成到现有监控系统

在 `monitor_all.py` 中调用：

```python
from comprehensive_alert_system import (
    ComprehensiveAlertEngine,
    send_alert,
    format_comprehensive_alert
)

# 检测到缠论信号后
engine = ComprehensiveAlertEngine()

alerts = engine.evaluate_comprehensive(
    symbol='IONQ',
    name='IonQ Inc',
    sector='quantum_computing',
    chanlun_signal={
        'type': 'buy1_divergence',
        'confidence': 0.75,
        'price': 12.50,
        'level': '30m'
    }
)

# 发送高级别警报
for alert in alerts:
    if alert.level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
        send_alert(alert)
```

### 3. Cron 定时任务

```bash
# 每 15 分钟运行一次 (交易时段)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && \
    venv/bin/python scripts/comprehensive_alert_system.py >> logs/comprehensive_alert.log 2>&1
```

---

## 📊 监控股票池

### 高优先级 (High Priority)
| 代码 | 名称 | 行业 |
|------|------|------|
| IONQ | IonQ Inc | 量子计算 |
| RKLB | Rocket Lab USA | 航天 |
| SMR | NuScale Power | 核能 |
| INTC | Intel Corporation | 半导体 |
| NVDA | NVIDIA Corporation | AI/芯片 |

### 中优先级 (Medium Priority)
| 代码 | 名称 | 行业 |
|------|------|------|
| RGTI | Rigetti Computing | 量子计算 |
| QBTS | D-Wave Quantum | 量子计算 |
| ENPH | Enphase Energy | 清洁能源 |
| FSLR | First Solar | 清洁能源 |
| MRNA | Moderna Inc | 生物科技 |

---

## 📋 警报示例

### CRITICAL 级别警报

```
🚨 IONQ 综合买入信号

📊 综合得分：88%
   基本面：75% (权重 35%)
   新闻面：82% (权重 25%)
   技术面：95% (权重 40%)

💡 操作建议:
💰 策略：STRONG BUY
📈 仓位：full
⏰ 时间：2026-04-14 14:30

─────────────────────────────
⚠️ 投资有风险，决策需谨慎
```

### HIGH 级别警报

```
🔴 RKLB 综合卖出信号

📊 综合得分：72%
   基本面：65% (权重 35%)
   新闻面：58% (权重 25%)
   技术面：85% (权重 40%)

💡 操作建议:
🔴 策略：SELL
📈 仓位：normal
⏰ 时间：2026-04-14 15:45

─────────────────────────────
⚠️ 投资有风险，决策需谨慎
```

---

## ⚠️ 注意事项

### 1. 数据延迟
- Yahoo Finance 数据可能有 15 分钟延迟
- 新闻情绪分析基于标题关键词，可能存在误差
- 基本面数据更新频率：季度 (财报)、实时 (股价)

### 2. 警报频率控制
- 同一信号 24 小时内不重复推送
- CRITICAL 级别警报不受频率限制
- 可通过配置调整频率阈值

### 3. 系统局限性
- 无法预测突发黑天鹅事件
- 新闻情绪分析可能受标题党影响
- 基本面数据对初创公司参考有限
- 缠论信号需要人工确认

### 4. 风险提示
- 本系统仅供参考，不构成投资建议
- 高波动股票风险极高，请谨慎决策
- 建议设置止损位，控制仓位
- 过往表现不代表未来结果

---

## 🔄 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-04-14 | 初始版本，整合三大维度预警 |

---

## 📚 相关文档

- [增强置信度系统](ENHANCED_CONFIDENCE_SYSTEM.md)
- [缠论监控系统使用说明](MONITOR_USAGE.md)
- [多级别背驰确认系统](SETUP_MULTI_LEVEL.md)
- [IONQ 监控配置](IONQ_MONITOR_SETUP.md)

---

**创建者**: ChanLun AI Agent  
**状态**: ✅ 已部署  
**测试**: 待实盘验证  
**推送渠道**: Telegram (Chat ID: 8365377574)
