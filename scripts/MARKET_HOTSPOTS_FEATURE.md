# 缠论市场热点挖掘功能

## ✅ 新功能完成

**完成时间:** 2026-03-28 16:02 EST  
**功能:** 周线 + 日线级别缠论分析  
**状态:** ✅ 已完成并测试

---

## 📊 功能说明

### 核心功能

1. **周线级别分析**
   - 识别大趋势方向
   - 检测周线级别背驰
   - 权重 60%

2. **日线级别分析**
   - 识别中期趋势
   - 检测日线级别背驰
   - 权重 40%

3. **综合评分系统**
   - 周线 60% + 日线 40%
   - 评分范围：-10 到 +10
   - ≥6.0: 强烈推荐
   - ≥4.0: 买入机会

4. **板块分析**
   - AI/芯片
   - 科技巨头
   - AI 应用
   - 半导体设备
   - ETF

---

## 🚀 使用方式

### 1. 市场热点扫描 (手动)

```bash
cd /home/wei/.openclaw/workspace/trading-system
PYTHONPATH=python-layer:$PYTHONPATH python3 scripts/market_hotspots_scan.py
```

**输出:**
- 所有扫描股票的综合评分
- 强烈推荐股票列表
- 买入机会列表
- 板块分析

### 2. 市场周报 (自动)

**时间:** 每周一早上 8:00 AM EST  
**渠道:** Telegram  
**内容:**
- 强烈推荐股票 (Top 5)
- 买入机会 (Top 5)
- 板块热度分析
- 操作建议

### 3. 市场热点扫描 (自动)

**时间:** 每周五下午 4:00 EST  
**内容:**
- 全市场扫描 (42 只股票)
- 板块分析
- 详细报告

---

## 📈 扫描股票池

### AI/芯片 (11 只)
NVDA, AMD, INTC, AVGO, QCOM, MU, AMAT, LRCX, KLAC, MRVL, NXPI

### 科技巨头 (9 只)
AAPL, MSFT, GOOGL, META, AMZN, NFLX, CRM, ORCL, ADBE

### AI 应用 (8 只)
TSLA, PLTR, SNOW, PANW, CRWD, ZS, NET, DDOG

### 半导体设备 (7 只)
ASML, TSM, AMAT, LRCX, KLAC, TEL, APH

### ETF (7 只)
QQQ, SPY, SOXX, SMH, XLK, VGT, ARKK

**总计:** 42 只热门股票

---

## 🎯 信号强度说明

### 综合评分

| 评分范围 | 信号 | 操作 |
|----------|------|------|
| **≥+6.0** | STRONG_BUY | 强烈推荐 |
| **≥+4.0** | BUY | 买入 |
| **-4.0 ~ +4.0** | HOLD | 观望 |
| **≤-4.0** | SELL | 卖出 |
| **≤-6.0** | STRONG_SELL | 强烈卖出 |

### 周线/日线信号

| 强度 | 信号 | 说明 |
|------|------|------|
| **≥+6.0** | STRONG_BUY | 强烈买入 |
| **≥+4.0** | BUY | 买入 |
| **-4.0~+4.0** | HOLD | 观望 |
| **≤-4.0** | SELL | 卖出 |

---

## 📊 测试结果

**测试时间:** 2026-03-28 16:02 EST

**扫描结果:**
- 扫描股票：42 只
- 强烈推荐：0 只
- 买入机会：0 只
- 观望：42 只

**当前市场状态:** 震荡整理，无明确方向

**表现较好股票:**
- AMD: +3.0
- INTC: +3.0
- GOOGL: +3.0
- LRCX: +3.0
- KLAC: +3.0
- ARKK: +3.0

**表现较差股票:**
- ZS: -8.1
- CRWD: -1.2
- META: -3.0
- CRM: -3.0

---

## 💡 操作建议

### 当前市场

**状态:** 震荡整理  
**策略:** 观望为主  
**关注:** 等待综合评分≥6.0 的股票

### 激进型

- 关注综合评分≥3.0 的股票
- 仓位：每只≤5%
- 止损：严格执行 5%

### 稳健型

- 等待综合评分≥6.0
- 关注 ETF (QQQ, SPY)
- 仓位：每只≤10%

### 保守型

- 继续观望
- 等待明确信号
- 现金为王

---

## ⏰ 自动推送时间

| 报告 | 时间 | 频率 |
|------|------|------|
| **市场周报** | 周一 8:00 AM | 每周 |
| **热点扫描** | 周五 4:00 PM | 每周 |
| **日报** | 交易日 9:00 AM | 每日 |

---

## 📝 日志文件

| 文件 | 用途 | 位置 |
|------|------|------|
| weekly_reports.log | 周报日志 | logs/weekly_reports.log |
| market_hotspots.log | 热点扫描日志 | logs/market_hotspots.log |
| weekly_report_*.json | 周报数据 | logs/weekly_report_*.json |
| market_hotspots_*.json | 热点数据 | logs/market_hotspots_*.json |

---

## 🔧 Cron 任务

```cron
# 缠论市场周报 - 每周一早上 8 点
0 12 * * 1 cd /home/wei/.openclaw/workspace/trading-system && python3 scripts/weekly_market_report.py >> logs/weekly_reports.log 2>&1

# 缠论市场热点扫描 - 每周五下午 4 点
0 20 * * 5 cd /home/wei/.openclaw/workspace/trading-system && python3 scripts/market_hotspots_scan.py >> logs/market_hotspots.log 2>&1
```

---

## 📄 相关文件

### Python 模块
- `python-layer/trading_system/weekly_analysis.py` - 周线/日线分析核心

### 脚本
- `scripts/market_hotspots_scan.py` - 市场热点扫描
- `scripts/weekly_market_report.py` - 周报生成

### 文档
- `scripts/MARKET_HOTSPOTS_FEATURE.md` - 本文档

---

## 🎯 下一步优化

### 短期 (1-2 周)
- [ ] 添加更多股票到扫描池
- [ ] 优化评分算法
- [ ] 添加历史回测

### 中期 (1 个月)
- [ ] 添加行业轮动分析
- [ ] 添加资金流向分析
- [ ] 添加情绪指标

### 长期 (3 个月)
- [ ] 机器学习模型优化评分
- [ ] 自动化交易系统
- [ ] 实时预警系统

---

## ⚠️ 风险提示

1. **缠论分析提高胜率，但不保证盈利**
2. **周线 + 日线共振信号更可靠**
3. **严格执行止损，每笔交易风险≤2%**
4. **综合评分≥6.0 为强烈推荐，≥4.0 为买入**
5. **市场有风险，投资需谨慎**

---

**功能完成时间:** 2026-03-28 16:02 EST  
**状态:** ✅ 已完成并测试  
**下次推送:** 下周一 8:00 AM (周报)
