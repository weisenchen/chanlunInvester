# CVE.TO 缠论监控系统

## 功能
- ✅ 每 30 分钟自动分析 CVE.TO 的 **多级别** 走势
- ✅ 支持 **5 分钟、30 分钟、日线** 三个级别
- ✅ 检测缠论买卖点 (第一类、第二类、第三类)
- ✅ 发现信号时自动发送 Telegram 提醒

## 文件结构
```
chanlun/
├── monitor_cve.py          # 监控脚本
├── venv/                   # Python 虚拟环境
├── cve_analysis.json       # 最新分析结果
└── alerts.log              # 提醒日志
```

## 手动运行
```bash
cd /home/wei/.openclaw/workspace/chanlun
source venv/bin/activate
python3 monitor_cve.py
```

## 自动监控 (Cron)

### 添加 Cron 任务
```bash
crontab -e
```

### 市场时间每 30 分钟检查 (周一至周五 9:30-16:00 ET) ✅ 已配置
```cron
*/30 9-15 * * 1-5 cd /home/wei/.openclaw/workspace/chanlun && source venv/bin/activate && python3 monitor_cve.py >> /home/wei/.openclaw/workspace/chanlun/monitor.log 2>&1
```

### 盘后每日检查 (17:00 ET)
```cron
0 17 * * 1-5 cd /home/wei/.openclaw/workspace/chanlun && source venv/bin/activate && python3 monitor_cve.py >> /home/wei/.openclaw/workspace/chanlun/monitor.log 2>&1
```

### 更频繁的 5 分钟级别监控 (每 10 分钟)
```cron
*/10 9-15 * * 1-5 cd /home/wei/.openclaw/workspace/chanlun && source venv/bin/activate && python3 monitor_cve.py >> /home/wei/.openclaw/workspace/chanlun/monitor.log 2>&1
```

## 缠论买卖点检测逻辑

### 级别阈值配置

| 级别 | Buy2 阈值 | Buy1 背驰阈值 | Sell2 阈值 |
|------|----------|--------------|-----------|
| 5 分钟 | 1.5% | 2.0% | 1.5% |
| 30 分钟 | 2.0% | 3.0% | 2.0% |
| 日线 | 3.0% | 5.0% | 3.0% |

### 第一类买点 (Buy 1) 🟢
- 趋势背驰后，新低不创新低
- 价格创新低但跌幅很小 (低于阈值)
- 有反弹迹象 (价格从低点反弹>1%)
- **特点**: 左侧交易，风险较高但成本低

### 第二类买点 (Buy 2) 🟢
- 回调不破前低
- 最新底分型高于前一个底分型
- 价格回调到最近底分型附近 (阈值内)
- **特点**: 右侧交易，更安全可靠

### 第三类买点 (Buy 3) 🔵
- 中枢突破后回踩确认
- (需要更复杂的中枢检测逻辑 - 待实现)
- **特点**: 趋势确认后的买点

### 卖点 (Sell 1/2/3) 🔴
- 与买点逻辑相反
- 顶分型 + 背驰/不过前高

## 当前状态
- ✅ 脚本可运行
- ✅ 数据获取正常 (yfinance)
- ✅ 分型检测正常
- ✅ 多级别分析 (5m/30m/1d)
- ✅ Telegram 提醒已发送
- ✅ Cron 自动监控已配置
- ⚠️ 买卖点检测逻辑简化版
- ⚠️ 中枢检测待完善

## 下一步改进
1. 完善中枢 (center) 检测算法
2. 增加背驰 (divergence) 量化指标 (MACD/RSI)
3. 第三类买卖点检测
4. 添加更多股票监控 (自定义列表)
5. 增加持仓管理和止损提醒
