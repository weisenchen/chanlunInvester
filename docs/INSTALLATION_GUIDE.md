# 缠论监控系统 - 完整安装指南

## 📦 系统要求

- **操作系统:** Linux / macOS / Windows (WSL)
- **Python:** 3.10+
- **Rust:** 1.75+ (可选，用于高性能核心)
- **内存:** 最少 2GB
- **存储:** 最少 1GB

---

## 🚀 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/weisenchen/chanlunInvester.git
cd chanlunInvester
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r python-layer/requirements.txt
```

**requirements.txt 内容:**
```txt
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
```

### 3. (可选) 安装 Rust 核心

```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 编译 Rust 核心
cd rust-core
cargo build --release
```

### 4. 验证安装

```bash
# 测试 Python 核心
PYTHONPATH=python-layer:$PYTHONPATH python3 -c "
from trading_system import ChanLunMonitor
print('✅ Python Core 安装成功')
"

# 测试命令行工具
python3 scripts/chanlun_monitor.py --help
```

---

## 📱 Telegram Bot 配置

### 方法 1: 使用 OpenClaw (推荐)

如果你已经在使用 OpenClaw，Telegram 集成已经配置好：

```python
from trading_system import send_alert

# 发送预警
send_alert("🟢 AAPL 第一类买点 detected!", chat_id="your_chat_id")
```

### 方法 2: 自建 Telegram Bot

#### 步骤 1: 创建 Bot

1. 在 Telegram 搜索 **@BotFather**
2. 发送 `/newbot`
3. 按提示设置 Bot 名称和用户名
4. 保存 Bot Token (类似：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 步骤 2: 获取 Chat ID

1. 在 Telegram 搜索 **@userinfobot**
2. 发送 `/start`
3. 它会回复你的 Chat ID (类似：`123456789`)

#### 步骤 3: 配置 Bot

编辑 `config/telegram_config.py`:
```python
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID = "123456789"
```

#### 步骤 4: 测试 Bot

```python
from trading_system import ChanLunBot

bot = ChanLunBot(token="YOUR_BOT_TOKEN")
bot.send_message("YOUR_CHAT_ID", "🤖 Bot 测试成功！")
```

---

## 🖥️ 命令行工具使用

### 1. 股票分析

```bash
# 基本分析
python3 scripts/chanlun_monitor.py AAPL

# 指定级别
python3 scripts/chanlun_monitor.py TSLA --level 30m

# 多级别分析
python3 scripts/chanlun_monitor.py NVDA --levels 1d,30m,5m

# 保存结果
python3 scripts/chanlun_monitor.py MSFT -o results/msft.json
```

### 2. 历史回测

```bash
# 基本回测
python3 scripts/backtest.py AAPL

# 自定义参数
python3 scripts/backtest.py TSLA \
  --start 2025-01-01 \
  --end 2026-03-21 \
  --capital 50000 \
  --report results/tsla_backtest.json

# 调整策略
python3 scripts/backtest.py NVDA \
  --threshold 3.0 \
  --stop-loss 0.05 \
  --take-profit 0.08
```

### 3. 实时监控

```bash
# 启动监控管理器
cd scripts
./monitor_manager.sh start

# 查看状态
./monitor_manager.sh status

# 查看日志
./monitor_manager.sh logs

# 停止监控
./monitor_manager.sh stop
```

---

## 📱 Telegram Bot 命令使用

### 基本命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `/start` | 欢迎信息 | `/start` |
| `/help` | 帮助信息 | `/help` |
| `/status` | 监控状态 | `/status` |
| `/analyze` | 股票分析 | `/analyze AAPL` |
| `/monitor` | 开始监控 | `/monitor UVIX` |
| `/alerts` | 查看预警 | `/alerts` |
| `/settings` | 查看设置 | `/settings` |

### 使用示例

**1. 分析股票:**
```
User: /analyze AAPL
Bot: 📊 AAPL 缠论分析
    
    🎯 信号：BUY
    📈 强度：+6.5
    💰 价格：$250.00
    
    📐 分析详情:
    • 日线上涨线段 (+3)
    • 30 分钟底背驰 (+4)
    
    ⚠️ 仅供参考，不构成投资建议
```

**2. 开始监控:**
```
User: /monitor UVIX
Bot: ✅ 已开始监控 UVIX
    
    监控设置:
    • 频率：每 5 分钟
    • 级别：5m, 30m, 1d
    • 预警：Telegram 推送
    • 置信度：≥70%
    
    当检测到买卖点时，我会立即通知您!
```

**3. 查看预警:**
```
User: /alerts
Bot: 🚨 最新预警
    
    🔴 UVIX 第一类卖点
    价格：$8.10
    时间：2026-03-18 14:24
    置信度：90%
```

---

## ⚙️ 配置选项

### 监控配置

编辑 `python-layer/trading_system/monitor.py`:
```python
DEFAULT_CONFIG = {
    'timeframes': ['1d', '30m', '5m'],  # 分析级别
    'min_confidence': 0.7,               # 最小置信度
    'weights': {
        '1d': {'direction': 3.0, 'divergence': 6.0},
        '30m': {'direction': 2.0, 'divergence': 4.0},
        '5m': {'direction': 1.0, 'divergence': 4.0}
    }
}
```

### 回测配置

编辑 `python-layer/trading_system/backtest.py`:
```python
config = BacktestConfig(
    symbol='AAPL',
    start_date='2025-01-01',
    end_date='2026-12-31',
    initial_capital=100000,
    position_size_pct=0.1,    # 10% 仓位
    stop_loss_pct=0.03,       # 3% 止损
    take_profit_pct=0.05,     # 5% 止盈
    signal_threshold=4.0      # 信号强度阈值
)
```

### Cron 配置 (定时任务)

```bash
crontab -e
```

添加以下内容:
```cron
# UVIX 实时监控 (每 5 分钟)
*/5 13-20 * * 1-5 cd /path/to/chanlunInvester && python3 scripts/uvix_auto_monitor.py >> logs/uvix_cron.log 2>&1

# 多级别分析 (每 15 分钟)
*/15 13-20 * * 1-5 cd /path/to/chanlunInvester && python3 scripts/chanlun_monitor.py UVIX >> logs/multi_level.log 2>&1

# 盘前分析 (9:00 EST)
0 13 * * 1-5 cd /path/to/chanlunInvester && python3 scripts/chanlun_monitor.py UVIX >> logs/premarket.log 2>&1

# 盘后总结 (16:30 EST)
30 20 * * 1-5 cd /path/to/chanlunInvester && python3 scripts/chanlun_monitor.py UVIX >> logs/postmarket.log 2>&1
```

---

## 🔧 故障排查

### 问题 1: 导入错误

```bash
# 错误：ModuleNotFoundError: No module named 'trading_system'

# 解决：设置 PYTHONPATH
export PYTHONPATH=/path/to/chanlunInvester/python-layer:$PYTHONPATH

# 或永久添加到 ~/.bashrc
echo 'export PYTHONPATH=/path/to/chanlunInvester/python-layer:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

### 问题 2: Yahoo Finance 数据获取失败

```bash
# 错误：YFRateLimitError: Too Many Requests

# 解决：添加延迟
import time
time.sleep(1)  # 在请求之间添加 1 秒延迟

# 或降低监控频率
# 编辑 crontab，从每 5 分钟改为每 15 分钟
```

### 问题 3: Telegram Bot 不响应

```bash
# 检查 Bot Token 是否正确
# 检查 Chat ID 是否正确
# 检查网络连接

# 测试 Bot
python3 -c "
from trading_system import ChanLunBot
bot = ChanLunBot(token='YOUR_TOKEN')
result = bot.send_message('YOUR_CHAT_ID', '测试')
print('成功' if result else '失败')
"
```

### 问题 4: Rust 编译失败

```bash
# 更新 Rust
rustup update

# 清理并重新编译
cd rust-core
cargo clean
cargo build --release

# 安装缺少的依赖
# Ubuntu/Debian:
sudo apt install build-essential
# macOS:
xcode-select --install
```

---

## 📊 性能优化

### 1. 使用缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_stock_data(symbol, period='5d'):
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)
```

### 2. 并行处理

```python
from concurrent.futures import ThreadPoolExecutor

def analyze_multiple_stocks(symbols):
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(analyze_stock, symbols))
    return results
```

### 3. 数据库存储

```python
# 使用 SQLite 存储历史数据
import sqlite3

conn = sqlite3.connect('chanlun_data.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_data (
        symbol TEXT,
        timestamp DATETIME,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER
    )
''')
```

---

## 📚 学习资源

### 文档

- `README.md` - 项目概述
- `docs/PRICE_DATA_FLOW.md` - 数据流说明
- `docs/YAHOO_FINANCE_RATE_LIMITS.md` - 速率限制
- `docs/CHANLUN_MONITOR_DEV_PLAN.md` - 开发计划
- `docs/PHASE6_7_COMPLETION.md` - Phase 6&7 报告

### 缠论学习

- 缠中说禅博客原文
- 缠论 108 课完整版
- 第 12 课：三类买卖点
- 第 14 课：区间套定理
- 第 24 课：MACD 背驰

### 社区支持

- GitHub Issues: 提交问题
- Discord: 加入社区讨论
- Telegram: 关注更新通知

---

## 🎯 快速开始示例

### 5 分钟快速测试

```bash
# 1. 克隆项目
git clone https://github.com/weisenchen/chanlunInvester.git
cd chanlunInvester

# 2. 安装依赖
pip install yfinance pandas numpy

# 3. 测试分析
PYTHONPATH=python-layer:$PYTHONPATH python3 scripts/chanlun_monitor.py AAPL

# 4. 测试回测
PYTHONPATH=python-layer:$PYTHONPATH python3 scripts/backtest.py AAPL --start 2026-01-01
```

### 15 分钟完整配置

```bash
# 1. 完整安装
python3 -m venv venv
source venv/bin/activate
pip install -r python-layer/requirements.txt

# 2. 配置 Telegram (可选)
# 按照上面的 Telegram Bot 配置步骤

# 3. 设置监控
cd scripts
./monitor_manager.sh start

# 4. 验证运行
./monitor_manager.sh status
```

---

## ✅ 安装完成检查清单

- [ ] 项目已克隆
- [ ] Python 依赖已安装
- [ ] 命令行工具可运行
- [ ] 股票分析测试通过
- [ ] 回测功能测试通过
- [ ] (可选) Telegram Bot 配置完成
- [ ] (可选) 监控任务已设置
- [ ] (可选) Rust 核心已编译

---

**🎉 安装完成！开始使用缠论监控系统吧！**

**有问题？** 查看 `docs/` 目录或提交 GitHub Issue。
