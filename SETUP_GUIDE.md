# 🚀 ChanLun Invester 本地部署指南

**缠论智能买卖点预警系统 - 本地化部署完成**

**部署日期**: 2026-03-18  
**版本**: v1.0 (基于 weisenchen/chanlunInvester)

---

## 📦 项目信息

**源码**: https://github.com/weisenchen/chanlunInvester.git  
**本地路径**: `/home/wei/.openclaw/workspace/chanlunInvester`

**核心特性**:
- 🦀 Rust + Python 混合核心引擎
- 📊 完整缠论实现：分型→笔→线段→中枢→买卖点
- 🔔 Telegram 实时预警
- 📈 Yahoo Finance 免费数据源
- 🔄 主备引擎故障转移

---

## ✅ 部署完成清单

### 1. 代码仓库
```bash
✅ Git 克隆完成
✅ 本地路径：/home/wei/.openclaw/workspace/chanlunInvester
```

### 2. Python 环境
```bash
✅ 虚拟环境：venv/
✅ 依赖安装：
   - grpcio >= 1.60.0
   - grpcio-tools >= 1.60.0
   - numpy >= 1.24.0
   - pandas >= 2.0.0
   - pyyaml >= 6.0
   - aiohttp >= 3.9.0
   - yfinance (实时数据)
```

### 3. 监控系统
```bash
✅ 监控脚本：monitor_all.py
✅ 监控标的：UVIX, XEG.TO, CVE.TO, CNQ.TO, PAAS.TO
✅ 监控级别：5m, 30m, 1d
✅ Telegram 预警：已配置
```

### 4. 自动化任务
```bash
✅ Cron 任务：每 15 分钟检查 (交易时段 9:30-16:00 ET)
✅ 盘前报告：每日 09:00 ET
✅ 日志文件：monitor.log, alerts.log
```

---

## 🎯 缠论核心实现

### 分析流程
```
K 线数据 → 分型检测 → 笔识别 → 线段划分 → 中枢检测 → 买卖点判断
   ↓          ↓          ↓          ↓          ↓          ↓
Yahoo    顶/底分型    新笔定义    特征序列    中枢区间   三类买卖点
Finance   Fractal      Pen      Segment     Center     BSP
```

### 买卖点检测

| 买卖点 | 缠论定义 | 系统实现 | 置信度 |
|--------|----------|----------|--------|
| **第一类买点** | 趋势背驰后，新低不创新低 | MACD 背驰检测 | high/medium |
| **第二类买点** | 回调不破前低 | 底分型对比 | medium |
| **第三类买点** | 中枢突破后回踩确认 | 🔄 开发中 | - |
| **第一类卖点** | 顶背驰后，新高不创新高 | MACD 背驰检测 | high/medium |
| **第二类卖点** | 反弹不过前高 | 顶分型对比 | medium |
| **第三类卖点** | 中枢跌破后回抽确认 | 🔄 开发中 | - |

---

## 📋 使用指南

### 手动分析
```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 分析单个标的
python3 launcher.py analyze UVIX --level 30m

# 分析多个级别
python3 launcher.py analyze CVE.TO --level 5m
python3 launcher.py analyze CVE.TO --level 30m
python3 launcher.py analyze CVE.TO --level 1d
```

### 实时监控
```bash
# 运行一次完整监控
python3 monitor_all.py

# 查看日志
tail -f monitor.log
tail -f alerts.log
```

### 命令行工具
```bash
# 列出所有可用命令
python3 launcher.py --help

# 分析命令
python3 launcher.py analyze <symbol> [--level <timeframe>]

# 监控命令
python3 launcher.py monitor <symbol> [--level <timeframe>] [--alert telegram]
```

---

## 🔔 预警系统

### Telegram 配置
- **Chat ID**: 8365377574
- **发送方式**: OpenClaw message tool
- **日志文件**: `alerts.log`

### 预警触发条件
- ✅ 第二类买点 (Buy2) - 回调不破前低
- ✅ 第二类卖点 (Sell2) - 反弹不过前高
- ✅ 第一类买点 (Buy1) - MACD 底背驰
- ✅ 第一类卖点 (Sell1) - MACD 顶背驰
- 🔄 第三类买卖点 - 开发中

### 预警示例
```
🟢 CVE.TO 缠论买卖点提醒

📊 信号：30m 级别第二类买点
💰 价格：$32.65
🎯 置信度：medium
📝 说明：回调不破前低 31.51, 当前价 32.65

⏰ 时间：2026-03-18 10:30
级别：30m
```

---

## ⏰ Cron 任务配置

### 当前 Cron 配置
```bash
# 缠论 Invester 监控 (每 15 分钟)
*/15 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlunInvester && source venv/bin/activate && python3 monitor_all.py >> /home/wei/.openclaw/workspace/chanlunInvester/monitor.log 2>&1

# 盘前报告 (每日 09:00 ET)
0 9 * * 1-5 cd /home/wei/.openclaw/workspace/chanlun && source venv/bin/activate && python3 premarket_report.py >> /home/wei/.openclaw/workspace/chanlun/premarket.log 2>&1

# 原有监控系统 (保留)
*/5 9-16 * * 1-5 ... monitor_uvix.py
*/30 9-15 * * 1-5 ... monitor_xeg.py
*/30 9-15 * * 1-5 ... monitor_cve.py
*/30 9-15 * * 1-5 ... monitor_cnq.py
*/30 9-15 * * 1-5 ... monitor_paas.py
```

### Cron 管理
```bash
# 查看当前任务
crontab -l

# 编辑任务
crontab -e

# 查看日志
tail -f /home/wei/.openclaw/workspace/chanlunInvester/monitor.log
```

---

## 📊 监控标的

| 标的 | 名称 | 监控级别 | 行业 |
|------|------|----------|------|
| **UVIX** | 波动率指数 | 5m, 30m | 金融/波动率 |
| **XEG.TO** | 加拿大能源 ETF | 30m, 1d | 能源 |
| **CVE.TO** | Cenovus Energy | 30m, 1d | 能源/石油 |
| **CNQ.TO** | Canadian Natural Resources | 30m, 1d | 能源/石油 |
| **PAAS.TO** | Pan American Silver | 30m, 1d | 贵金属/白银 |

---

## 🔧 配置文件

### config/default.yaml
```yaml
system:
  primary_engine: rust
  failover_enabled: true

pen:
  definition: new_3kline  # 新笔定义 (第 65 课)
  strict_validation: true

macd:
  fast_period: 12
  slow_period: 26
  signal_period: 9
```

### config/live.yaml
```yaml
environment: live
alerts:
  enabled: true
  channels:
    - type: telegram
    - type: console
    - type: file

risk:
  max_position_pct: 0.3
  stop_loss_pct: 0.05
  take_profit_pct: 0.10
```

---

## 📁 项目结构

```
chanlunInvester/
├── 📂 python-layer/           # Python 层
│   ├── 📂 trading_system/     # 交易系统核心
│   │   ├── kline.py          # K 线数据结构
│   │   ├── fractal.py        # 分型检测
│   │   ├── pen.py            # 笔识别
│   │   ├── segment.py        # 线段划分
│   │   ├── center.py         # 中枢检测
│   │   └── 📂 indicators/    # 技术指标
│   └── requirements.txt
│
├── 📂 rust-core/              # Rust 核心引擎
├── 📂 config/                 # 配置文件
│   ├── default.yaml
│   ├── live.yaml
│   └── macd_params.yaml
│
├── 📂 examples/               # 示例代码
│   ├── 📂 02_pen/
│   ├── 📂 03_segment/
│   ├── 📂 05_divergence/
│   ├── 📂 06_bsp1/
│   ├── 📂 07_bsp2/
│   └── 📂 08_bsp3/
│
├── 📂 scripts/                # 脚本工具
├── 📂 tests/                  # 测试用例
│
├── launcher.py                # 统一启动器
├── monitor_all.py             # 监控脚本 (新增)
├── alerts.log                 # 预警日志
├── monitor.log                # 监控日志
└── README.md
```

---

## 🧪 测试验证

### 运行测试
```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 测试分析功能
python3 launcher.py analyze UVIX --level 30m

# 测试监控功能
python3 monitor_all.py

# 查看结果
cat alerts.log | tail -20
```

### 预期输出
```
======================================================================
缠论智能监控系统 - ChanLun Invester
======================================================================
启动时间：2026-03-18 10:30:21
监控标的：5
======================================================================

📊 UVIX (波动率指数)
  [5m] 分型：33, 笔：27, 线段：2, 买卖点：0
  [30m] 分型：42, 笔：32, 线段：2, 买卖点：0

📊 CVE.TO (Cenovus Energy)
  [30m] 分型：34, 笔：26, 线段：2, 买卖点：1 ✅
  🎯 buy2: 30m 级别第二类买点 @ $32.65
```

---

## 🛠️ 故障排查

### 常见问题

**1. 数据获取失败**
```bash
# 检查 yfinance 安装
pip show yfinance

# 测试数据获取
python3 -c "import yfinance as yf; print(yf.Ticker('UVIX').history(period='5d'))"
```

**2. Telegram 预警不发送**
```bash
# 测试 OpenClaw message
openclaw message send --target "telegram:8365377574" -m "测试消息"

# 检查日志
cat alerts.log | tail -10
```

**3. Cron 任务不执行**
```bash
# 检查 Cron 状态
pgrep -x cron

# 查看 Cron 日志
grep CRON /var/log/syslog | tail -20
```

---

## 📈 后续优化

### Phase 1 (已完成) ✅
- [x] 代码仓库克隆
- [x] Python 环境配置
- [x] 监控脚本开发
- [x] Telegram 预警集成
- [x] Cron 自动化

### Phase 2 (计划中) 🔄
- [ ] Rust 核心引擎编译
- [ ] 第三类买卖点实现
- [ ] 中枢检测完善
- [ ] 回测框架集成
- [ ] Web Dashboard

### Phase 3 (未来) 🎯
- [ ] 实盘交易接口
- [ ] 多账户管理
- [ ] 风险控制模块
- [ ] 性能优化

---

## 📞 支持

**项目仓库**: https://github.com/weisenchen/chanlunInvester  
**本地文档**: `/home/wei/.openclaw/workspace/chanlunInvester/README.md`  
**缠论原文**: https://www.chanlun.com (缠中说禅博客)

---

**部署完成时间**: 2026-03-18 10:30 EDT  
**部署者**: ChanLun AI Agent  
**状态**: ✅ 运行中
