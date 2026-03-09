# UVIX 缠论监控系统

**标的**: UVIX (Volatility Shares - 1.5x Long VIX)  
**类型**: 美股 - 波动率杠杆产品  
**监控级别**: 5 分钟 + 30 分钟  
**更新频率**: 每 5 分钟 (市场时间)

---

## 📊 关于 UVIX

UVIX 是 1.5 倍做多 VIX 短期期货 ETF，特点:
- **高波动性**: 适合缠论短线交易
- **均值回归**: VIX 产品具有均值回归特性
- **杠杆效应**: 1.5 倍放大 VIX 走势
- **适合级别**: 5m/30m 短线交易

---

## 🎯 监控功能

### 买卖点检测
| 类型 | 描述 | 置信度 |
|------|------|--------|
| 🟢 Buy1 | 第一类买点 (底背驰) | Low/High |
| 🟢 Buy2 | 第二类买点 (回调不破前低) | Medium |
| 🔴 Sell1 | 第一类卖点 (顶背驰) | High |
| 🔴 Sell2 | 第二类卖点 (反弹不过前高) | Medium |
| 🔵 Breakout | 突破前高/前低 | Medium |

### 阈值配置
| 级别 | Buy2 阈值 | Buy1 背驰 | Sell2 阈值 |
|------|----------|----------|-----------|
| 5 分钟 | 1.5% | 2.0% | 1.5% |
| 30 分钟 | 2.5% | 3.0% | 2.5% |

---

## 📁 文件结构

```
chanlun/
├── monitor_uvix.py           # UVIX 监控脚本
├── uvix_analysis.json        # 最新分析结果
├── uvix_alerts.log           # 提醒日志
└── uvix_monitor.log          # 运行日志
```

---

## 🚀 使用方式

### 手动运行
```bash
cd /home/wei/.openclaw/workspace/chanlun
source venv/bin/activate
python3 monitor_uvix.py
```

### 自动监控 (Cron)
```cron
# 市场时间每 5 分钟检查 (周一至周五 9:30-16:00 ET)
*/5 9-16 * * 1-5 cd /home/wei/.openclaw/workspace/chanlun && source venv/bin/activate && python3 monitor_uvix.py >> uvix_monitor.log 2>&1
```

---

## 📈 当前信号

查看最新分析结果:
```bash
cat uvix_analysis.json | jq .
```

查看提醒历史:
```bash
tail -50 uvix_alerts.log
```

---

## 🔔 Telegram 提醒

提醒格式:
```
🟢/🔴/🔵 UVIX 缠论买卖点提醒

📊 信号：[信号类型]
💰 价格：$[价格]
🎯 置信度：[low/medium/high]
📝 说明：[详细说明]

⏰ 时间：YYYY-MM-DD HH:MM
级别：[5m/30m]
```

---

## 📊 分析结果示例

```json
{
  "timestamp": "2026-03-09T09:35:44",
  "symbol": "UVIX",
  "levels": {
    "5m": {
      "current_price": 9.57,
      "daily_change": 12.19,
      "fractals_high": 7,
      "fractals_low": 7,
      "latest_top": 8.55,
      "latest_bottom": 8.38,
      "signals": [...]
    },
    "30m": {
      "current_price": 9.59,
      "daily_change": 49.72,
      "fractals_high": 11,
      "fractals_low": 16,
      "signals": [...]
    }
  },
  "total_signals": 4,
  "summary": {
    "buy_signals": 0,
    "sell_signals": 2,
    "breakout_signals": 2
  }
}
```

---

## ⚠️ 风险提示

1. **高波动性**: UVIX 是杠杆产品，波动剧烈
2. **损耗风险**: 期货展期有损耗，不适合长期持有
3. **止损建议**: 建议设置 5-10% 止损
4. **仓位控制**: 单只标的不超过总仓位 20%

---

## 🛠️ 故障排查

### 无法获取数据
```bash
# 检查 yfinance
python3 -c "import yfinance; print(yf.Ticker('UVIX').history(period='1d'))"
```

### Cron 不执行
```bash
# 检查 cron 日志
grep CRON /var/log/syslog | tail -20

# 检查 cron 状态
systemctl status cron
```

### 提醒不发送
```bash
# 检查提醒日志
tail -20 uvix_alerts.log

# 手动测试
python3 monitor_uvix.py
```

---

## 📝 日志位置

| 日志文件 | 内容 |
|----------|------|
| `uvix_monitor.log` | 脚本运行日志 |
| `uvix_alerts.log` | 买卖点提醒 |
| `uvix_analysis.json` | JSON 分析结果 |

---

**创建日期**: 2026-03-09  
**最后更新**: 2026-03-09  
**维护者**: ChanLun Monitoring System
