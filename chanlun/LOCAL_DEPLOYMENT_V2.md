# 缠论 Invester 本地部署方案 v2.0

**版本:** v2.0 (LEAN-Inspired Local Edition)  
**设计原则:** 学习 LEAN 精华，避开设计陷阱  
**目标:** 简洁、易用、本地优先、零成本  
**更新日期:** 2026-02-23

---

## 1. 核心设计理念

### 1.1 学习 LEAN 的精华

| LEAN 优点 | ChanLun 采纳方式 |
|-----------|-----------------|
| ✅ 模块化插件 | Handler 可插拔，但保持简单 |
| ✅ 配置分层 | config.json + 环境 overlay |
| ✅ 策略示例库 | 10 个渐进式缠论示例 |
| ✅ CLI 工具 | chanlun 统一命令行 |
| ✅ Docker 部署 | 一键启动，<500MB 镜像 |
| ✅ 事件驱动 | 实时数据处理循环 |

### 1.2 避开 LEAN 的陷阱

| LEAN 缺点 | ChanLun 避免方案 |
|-----------|-----------------|
| ❌ 过于复杂 (6000+ 文件) | → 目标<1000 文件，保持简洁 |
| ❌ .NET 依赖重 (3GB+) | → Python+Rust <500MB |
| ❌ 数据需付费 | → AKShare/Baostock 免费 |
| ❌ 过度工程化 | → 最多 3 层嵌套 |
| ❌ 云端锁定 | → 本地优先，云端可选 |
| ❌ Python 次级 | → Python 一等公民 |

### 1.3 设计目标

```
理想状态:
- 安装时间：<5 分钟
- 启动时间：<5 秒
- 内存占用：<200MB
- Docker 镜像：<500MB
- 学习曲线：1-2 天上手
- 零成本启动：无需付费数据
```

---

## 2. 改进后的目录结构

### 2.1 整体架构

```
chanlun-local/
├── README.md                    # 项目说明
├── pyproject.toml              # Python 项目配置
├── Cargo.toml                  # Rust 项目配置
├── docker-compose.yml          # Docker 部署
├── launcher.py                 # 统一启动器 ⭐ NEW
│
├── configs/                    # 配置目录 ⭐ NEW
│   ├── config.json             # 基础配置
│   ├── config.backtest.json    # 回测环境叠加
│   ├── config.live.json        # 实盘环境叠加
│   └── config.dev.json         # 开发环境叠加
│
├── core/                       # Rust 核心引擎
│   ├── src/
│   │   ├── lib.rs
│   │   ├── fractal.rs          # 分型
│   │   ├── stroke.rs           # 笔
│   │   ├── segment.rs          # 线段
│   │   ├── center.rs           # 中枢
│   │   ├── divergence.rs       # 背驰
│   │   └── bsp.rs              # 买卖点
│   └── Cargo.toml
│
├── chanlun/                    # Python 包 (主模块)
│   ├── __init__.py
│   ├── engine.py               # Rust 引擎绑定
│   ├── analysis/               # 分析模块
│   │   ├── __init__.py
│   │   ├── fractal.py
│   │   ├── stroke.py
│   │   ├── segment.py
│   │   ├── center.py
│   │   ├── divergence.py
│   │   └── bsp.py
│   ├── data/                   # 数据模块
│   │   ├── __init__.py
│   │   ├── base.py             # 数据源基类
│   │   ├── akshare.py          # AKShare 实现
│   │   └── baostock.py         # Baostock 实现
│   ├── handlers/               # Handler 插件 ⭐ NEW
│   │   ├── __init__.py
│   │   ├── log_handler.py      # 日志
│   │   ├── alert_handler.py    # 预警
│   │   └── data_handler.py     # 数据
│   └── utils/
│       ├── config.py           # 配置加载 ⭐ NEW
│       └── helpers.py
│
├── examples/                   # 策略示例库 ⭐ NEW
│   ├── README.md
│   ├── 01_basic_fractal/
│   │   ├── README.md
│   │   └── main.py
│   ├── 02_bi_and_stroke/
│   │   └── main.py
│   ├── 03_segment_detection/
│   │   └── main.py
│   ├── 04_center_identification/
│   │   └── main.py
│   ├── 05_divergence_detection/
│   │   └── main.py
│   ├── 06_buy_sell_point_1/
│   │   └── main.py
│   ├── 07_buy_sell_point_2/
│   │   └── main.py
│   ├── 08_buy_sell_point_3/
│   │   └── main.py
│   ├── 09_interval_set/
│   │   └── main.py
│   └── 10_multi_level_analysis/
│       └── main.py
│
├── cli/                        # CLI 工具 ⭐ NEW
│   ├── __init__.py
│   ├── main.py                 # CLI 入口
│   ├── commands/
│   │   ├── analyze.py
│   │   ├── backtest.py
│   │   ├── monitor.py
│   │   └── server.py
│   └── utils/
│       └── formatters.py
│
├── backend/                    # 后端服务
│   ├── main.py                 # FastAPI 入口
│   ├── api/
│   │   ├── routes.py
│   │   └── websocket.py
│   ├── services/
│   │   ├── analysis.py
│   │   ├── bsp.py
│   │   └── alert.py
│   └── database/
│       ├── sqlite_db.py
│       └── models.py
│
├── frontend/                   # React 前端
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── api/
│   └── vite.config.ts
│
├── data/                       # 本地数据
│   ├── klines/                 # K 线缓存
│   ├── db.sqlite               # SQLite 数据库
│   └── config.json             # 运行时配置
│
├── scripts/                    # 工具脚本
│   ├── install.sh              # 一键安装
│   ├── download_klines.py      # 数据下载
│   └── backup_db.sh            # 数据库备份
│
└── tests/                      # 测试 ⭐ NEW
    ├── test_fractal.py
    ├── test_stroke.py
    ├── test_segment.py
    ├── test_center.py
    ├── test_divergence.py
    ├── test_bsp.py
    └── test_integration.py
```

---

## 3. 配置分层设计

### 3.1 基础配置

```json
// configs/config.json
{
  "_comment": "ChanLun Invester 基础配置",
  "version": "2.0",
  
  "environment": "dev",
  
  "data": {
    "folder": "./data",
    "provider": "akshare",
    "cache_enabled": true,
    "cache_ttl": 3600
  },
  
  "engine": {
    "rust_path": "./core/target/release/libchanlun_engine.so",
    "log_level": "INFO",
    "debug": false
  },
  
  "handlers": {
    "log": "chanlun.handlers.log_handler.ConsoleLogHandler",
    "alert": "chanlun.handlers.alert_handler.ConsoleAlertHandler",
    "data": "chanlun.handlers.data_handler.LocalDataHandler"
  },
  
  "limits": {
    "max_symbols": 100,
    "max_klines": 10000,
    "max_memory_mb": 500
  }
}
```

### 3.2 回测环境叠加

```json
// configs/config.backtest.json
{
  "_comment": "回测环境配置 (叠加到基础配置)",
  "environment": "backtest",
  
  "data": {
    "provider": "akshare",
    "cache_enabled": true
  },
  
  "backtest": {
    "start_date": "2020-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "commission_rate": 0.0003,
    "slippage": 0.001
  },
  
  "handlers": {
    "log": "chanlun.handlers.log_handler.FileLogHandler",
    "log_file": "./logs/backtest.log"
  }
}
```

### 3.3 实盘环境叠加

```json
// configs/config.live.json
{
  "_comment": "实盘环境配置 (叠加到基础配置)",
  "environment": "live",
  
  "data": {
    "provider": "realtime",
    "cache_enabled": false
  },
  
  "live": {
    "brokerage": "simulate",
    "auto_trade": false,
    "risk_check": true,
    "max_position_pct": 0.3
  },
  
  "handlers": {
    "alert": "chanlun.handlers.alert_handler.WebSocketAlertHandler",
    "alert_websocket": "ws://localhost:8765"
  }
}
```

### 3.4 配置加载器

```python
# chanlun/utils/config.py
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """配置加载器，支持分层叠加"""
    
    def __init__(self, base_path: str = "configs/config.json"):
        self.base_path = Path(base_path)
    
    def load(self, overlay_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置并叠加
        
        Args:
            overlay_path: 叠加配置文件路径 (可选)
        
        Returns:
            合并后的配置字典
        """
        # 加载基础配置
        config = self._load_json(self.base_path)
        
        # 叠加环境配置
        if overlay_path:
            overlay = self._load_json(Path(overlay_path))
            config = self._deep_merge(config, overlay)
        
        # 验证配置
        self._validate(config)
        
        return config
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """加载 JSON 文件"""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()
        
        for key, value in overlay.items():
            if key.startswith('_'):  # 跳过注释
                continue
            
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate(self, config: Dict):
        """验证配置有效性"""
        required = ['environment', 'data', 'engine', 'handlers']
        for key in required:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

# 使用示例
loader = ConfigLoader()

# 仅基础配置
config = loader.load()

# 叠加回测配置
config = loader.load("configs/config.backtest.json")

# 叠加实盘配置
config = loader.load("configs/config.live.json")
```

---

## 4. 统一启动器

### 4.1 启动器实现

```python
#!/usr/bin/env python3
# launcher.py
"""
ChanLun Invester 统一启动器

使用示例:
    python launcher.py analyze 000001.SZ --level 30m
    python launcher.py backtest strategy.py --start 2020-01-01
    python launcher.py monitor 000001.SZ
    python launcher.py server --port 8000
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(
        description='ChanLun Invester - 缠论智能分析系统 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析股票缠论结构
  python launcher.py analyze 000001.SZ --level 30m
  
  # 策略回测
  python launcher.py backtest examples/06_buy_sell_point_1/main.py --start 2020-01-01
  
  # 实时监控
  python launcher.py monitor 000001.SZ --alert telegram
  
  # 启动 API 服务
  python launcher.py server --port 8000
  
  # 使用 Docker
  docker-compose up -d
        """
    )
    
    parser.add_argument('--version', '-v', action='version', version='ChanLun Invester 2.0')
    parser.add_argument('--config', '-c', default='configs/config.json', help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # === analyze 命令 ===
    analyze_parser = subparsers.add_parser('analyze', help='分析股票缠论结构')
    analyze_parser.add_argument('symbol', help='股票代码 (如 000001.SZ)')
    analyze_parser.add_argument('--level', '-l', default='30m', 
                               choices=['1m', '5m', '30m', '1d', '1w'],
                               help='分析级别 (默认：30m)')
    analyze_parser.add_argument('--output', '-o', help='输出文件路径')
    analyze_parser.add_argument('--config', '-c', default='configs/config.backtest.json',
                               help='配置文件 (默认：config.backtest.json)')
    
    # === backtest 命令 ===
    backtest_parser = subparsers.add_parser('backtest', help='策略回测')
    backtest_parser.add_argument('strategy', help='策略文件路径')
    backtest_parser.add_argument('--start', '-s', required=True, help='开始日期 (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', '-e', required=True, help='结束日期 (YYYY-MM-DD)')
    backtest_parser.add_argument('--capital', '-c', type=float, default=100000,
                                help='初始资金 (默认：100000)')
    backtest_parser.add_argument('--output', '-o', default='backtest_result.json',
                                help='结果输出文件')
    
    # === monitor 命令 ===
    monitor_parser = subparsers.add_parser('monitor', help='实时监控股票')
    monitor_parser.add_argument('symbol', help='股票代码')
    monitor_parser.add_argument('--level', '-l', default='5m', help='监控级别')
    monitor_parser.add_argument('--alert', '-a', choices=['console', 'telegram', 'email', 'websocket'],
                               default='console', help='预警方式')
    monitor_parser.add_argument('--config', '-c', default='configs/config.live.json',
                               help='配置文件 (默认：config.live.json)')
    
    # === server 命令 ===
    server_parser = subparsers.add_parser('server', help='启动 API 服务')
    server_parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    server_parser.add_argument('--port', '-p', type=int, default=8000, help='监听端口')
    server_parser.add_argument('--reload', action='store_true', help='自动重载')
    
    # === research 命令 ===
    research_parser = subparsers.add_parser('research', help='启动 Jupyter 研究环境')
    research_parser.add_argument('--port', '-p', type=int, default=8888, help='Jupyter 端口')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应命令
    if args.command == 'analyze':
        from cli.commands.analyze import run_analyze
        run_analyze(args)
    
    elif args.command == 'backtest':
        from cli.commands.backtest import run_backtest
        run_backtest(args)
    
    elif args.command == 'monitor':
        from cli.commands.monitor import run_monitor
        run_monitor(args)
    
    elif args.command == 'server':
        from cli.commands.server import run_server
        run_server(args)
    
    elif args.command == 'research':
        from cli.commands.research import run_research
        run_research(args)

if __name__ == '__main__':
    main()
```

### 4.2 CLI 命令实现

```python
# cli/commands/analyze.py
"""分析命令实现"""

from chanlun import ChanLunEngine, AKShareDataSource
from chanlun.utils import ConfigLoader, format_table
import json

def run_analyze(args):
    """执行分析命令"""
    
    # 加载配置
    config_loader = ConfigLoader()
    config = config_loader.load(args.config)
    
    print(f"📊 ChanLun Invester v2.0")
    print(f"📈 分析标的：{args.symbol}")
    print(f"📉 分析级别：{args.level}")
    print(f"⚙️  数据源：{config['data']['provider']}")
    print()
    
    # 初始化
    print("正在初始化引擎...")
    engine = ChanLunEngine()
    data_source = AKShareDataSource()
    
    # 下载数据
    print(f"正在下载 K 线数据...")
    klines = data_source.get_klines(args.symbol, level=args.level, limit=1000)
    print(f"✓ 下载 {len(klines)} 条 K 线")
    
    # 分析走势
    print("正在分析缠论结构...")
    analysis = engine.analyze(klines)
    
    print(f"✓ 发现分型：{len(analysis.fractals)} 个")
    print(f"✓ 发现笔：{len(analysis.strokes)} 个")
    print(f"✓ 发现线段：{len(analysis.segments)} 个")
    print(f"✓ 发现中枢：{len(analysis.centers)} 个")
    
    # 识别买卖点
    print("正在识别买卖点...")
    from chanlun.analysis import detect_bsp
    bsp_list = detect_bsp(analysis)
    
    print(f"✓ 发现买卖点：{len(bsp_list)} 个")
    print()
    
    # 显示结果
    if bsp_list:
        print("最近买卖点:")
        rows = [[bsp.type, bsp.time, f"{bsp.price:.2f}", f"{bsp.confidence:.2f}"] 
                for bsp in bsp_list[-5:]]
        print(format_table(rows, headers=['类型', '时间', '价格', '置信度']))
    
    # 输出到文件
    if args.output:
        result = {
            'symbol': args.symbol,
            'level': args.level,
            'analysis': {
                'fractals': len(analysis.fractals),
                'strokes': len(analysis.strokes),
                'segments': len(analysis.segments),
                'centers': len(analysis.centers),
                'bsp': len(bsp_list)
            },
            'bsp_list': [
                {
                    'type': bsp.type,
                    'time': str(bsp.time),
                    'price': bsp.price,
                    'confidence': bsp.confidence
                }
                for bsp in bsp_list
            ]
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 结果已保存到：{args.output}")
```

---

## 5. 策略示例库

### 5.1 示例 1: 基础分型识别

```python
# examples/01_basic_fractal/main.py
"""
示例 1: 基础分型识别

学习目标:
- 理解顶分型和底分型的定义
- 掌握包含关系的处理方法
- 能够识别分型结构
"""

from chanlun import ChanLunEngine, AKShareDataSource
from chanlun.utils import plot_klines_with_fractals

def main():
    print("=" * 60)
    print("示例 1: 基础分型识别")
    print("=" * 60)
    
    # 1. 初始化
    engine = ChanLunEngine()
    data_source = AKShareDataSource()
    
    # 2. 下载数据
    print("\n下载 000001.SZ 日线数据...")
    klines = data_source.get_klines("000001.SZ", level="1d", limit=100)
    print(f"✓ 下载 {len(klines)} 条 K 线")
    
    # 3. 识别分型
    print("\n识别分型...")
    fractals = engine.detect_fractals(klines)
    
    top_fractals = [f for f in fractals if f.type == 'top']
    bottom_fractals = [f for f in fractals if f.type == 'bottom']
    
    print(f"✓ 发现顶分型：{len(top_fractals)} 个")
    print(f"✓ 发现底分型：{len(bottom_fractals)} 个")
    
    # 4. 显示结果
    print("\n最近 3 个顶分型:")
    for f in top_fractals[-3:]:
        print(f"  时间：{f.time}, 高点：{f.high:.2f}")
    
    print("\n最近 3 个底分型:")
    for f in bottom_fractals[-3:]:
        print(f"  时间：{f.time}, 低点：{f.low:.2f}")
    
    # 5. 可视化
    print("\n生成图表...")
    plot_klines_with_fractals(klines, fractals, output="01_fractals.png")
    print("✓ 图表已保存：01_fractals.png")

if __name__ == '__main__':
    main()
```

### 5.2 示例 6: 第一类买卖点

```python
# examples/06_buy_sell_point_1/main.py
"""
示例 6: 第一类买卖点识别

学习目标:
- 理解第一类买卖点的定义 (趋势背驰点)
- 掌握背驰的判断方法
- 能够识别买卖点

第一类买卖点定义:
- 买点：下跌趋势背驰后的反转点
- 卖点：上涨趋势背驰后的反转点
"""

from chanlun import ChanLunEngine, AKShareDataSource
from chanlun.analysis import detect_divergence, identify_bsp1
from chanlun.utils import plot_bsp

def main():
    print("=" * 60)
    print("示例 6: 第一类买卖点识别")
    print("=" * 60)
    
    # 1. 初始化
    engine = ChanLunEngine()
    data_source = AKShareDataSource()
    
    # 2. 下载数据 (需要更多数据以识别背驰)
    print("\n下载 000001.SZ 30 分钟数据...")
    klines = data_source.get_klines("000001.SZ", level="30m", limit=2000)
    print(f"✓ 下载 {len(klines)} 条 K 线")
    
    # 3. 分析走势结构
    print("\n分析分型、笔、线段...")
    analysis = engine.analyze(klines)
    print(f"✓ 分型：{len(analysis.fractals)} 个")
    print(f"✓ 笔：{len(analysis.strokes)} 个")
    print(f"✓ 线段：{len(analysis.segments)} 个")
    print(f"✓ 中枢：{len(analysis.centers)} 个")
    
    # 4. 检测背驰
    print("\n检测趋势背驰...")
    divergences = detect_divergence(analysis.segments, klines)
    print(f"✓ 发现背驰：{len(divergences)} 个")
    
    for div in divergences[-3:]:
        print(f"  {div.type} @ {div.time}")
        print(f"    价格：{div.price_a:.2f} → {div.price_b:.2f}")
        print(f"    MACD 面积：{div.macd_area_a:.2f} → {div.macd_area_b:.2f}")
        print(f"    置信度：{div.confidence:.2f}")
    
    # 5. 识别第一类买卖点
    print("\n识别第一类买卖点...")
    bsp1_list = identify_bsp1(divergences, analysis.centers)
    print(f"✓ 发现第一类买卖点：{len(bsp1_list)} 个")
    
    # 6. 显示结果
    print("\n买卖点详情:")
    for bsp in bsp1_list[-5:]:
        print(f"  {bsp.type} @ {bsp.time}")
        print(f"    价格：{bsp.price:.2f}")
        print(f"    背驰置信度：{bsp.confidence:.2f}")
        print(f"    相关中枢：{bsp.center_id}")
    
    # 7. 可视化
    print("\n生成图表...")
    plot_bsp(klines, analysis, bsp1_list, output="06_bsp1.png")
    print("✓ 图表已保存：06_bsp1.png")
    
    print("\n💡 学习要点:")
    print("  1. 第一类买卖点必须是趋势背驰点")
    print("  2. 背驰的判断依据是 MACD 面积比较")
    print("  3. 置信度>0.8 的买卖点更可靠")
    print("  4. 结合中枢位置判断买卖点的有效性")

if __name__ == '__main__':
    main()
```

---

## 6. 事件驱动架构

### 6.1 事件循环实现

```python
# chanlun/engine/event_loop.py
"""事件驱动引擎"""

import asyncio
from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    KLINE_UPDATE = "kline_update"
    FRACTAL_UPDATE = "fractal_update"
    BSP_DETECT = "bsp_detect"
    ALERT_TRIGGER = "alert_trigger"

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: float

class EventHandler:
    """事件处理器基类"""
    
    async def handle(self, event: Event):
        raise NotImplementedError

class EventEngine:
    """事件引擎"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._running = False
    
    def register(self, event_type: EventType, handler: EventHandler):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def emit(self, event: Event):
        """触发事件"""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                await handler.handle(event)
    
    async def run(self, data_feed: Callable):
        """运行事件循环"""
        self._running = True
        
        while self._running:
            try:
                # 1. 获取新数据
                kline = await data_feed()
                
                # 2. 触发 K 线更新事件
                await self.emit(Event(
                    type=EventType.KLINE_UPDATE,
                    data={"kline": kline},
                    timestamp=kline.timestamp
                ))
                
                # 等待下一个 K 线
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Event loop error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """停止事件循环"""
        self._running = False

# 使用示例
class AnalysisHandler(EventHandler):
    """分析事件处理器"""
    
    def __init__(self, engine):
        self.engine = engine
        self.klines = []
    
    async def handle(self, event: Event):
        if event.type == EventType.KLINE_UPDATE:
            # 更新 K 线
            self.klines.append(event.data["kline"])
            
            # 更新缠论结构
            analysis = self.engine.analyze(self.klines)
            
            # 触发分析更新事件
            await event_engine.emit(Event(
                type=EventType.FRACTAL_UPDATE,
                data={"analysis": analysis},
                timestamp=event.timestamp
            ))

class AlertHandler(EventHandler):
    """预警事件处理器"""
    
    async def handle(self, event: Event):
        if event.type == EventType.BSP_DETECT:
            bsp = event.data["bsp"]
            print(f"🚨 买卖点预警：{bsp.type} @ {bsp.price}")
            # 发送 Telegram/邮件等
```

---

## 7. Docker 部署优化

### 7.1 精简 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /chanlun

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Rust (最小化)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

# 复制并编译 Rust 引擎
COPY core/ /chanlun/core/
RUN cd /chanlun/core && cargo build --release && mkdir -p /chanlun/chanlun/lib && cp target/release/libchanlun_engine.so /chanlun/chanlun/lib/

# 安装 Python 依赖
COPY pyproject.toml requirements.txt /chanlun/
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用
COPY chanlun/ /chanlun/chanlun/
COPY cli/ /chanlun/cli/
COPY backend/ /chanlun/backend/
COPY launcher.py /chanlun/

# 创建数据目录
RUN mkdir -p /chanlun/data /chanlun/logs

# 设置卷
VOLUME /chanlun/data

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import chanlun; print('OK')" || exit 1

# 启动命令
ENTRYPOINT ["python", "launcher.py"]
CMD ["server", "--port", "8000"]

# 暴露端口
EXPOSE 8000
```

### 7.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  chanlun:
    build: .
    container_name: chanlun-invester
    ports:
      - "8000:8000"
    volumes:
      - ./data:/chanlun/data
      - ./configs:/chanlun/configs
      - ./logs:/chanlun/logs
    environment:
      - CHANLUN_ENV=dev
      - CHANLUN_CONFIG=configs/config.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import chanlun; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # 可选：前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - chanlun
    restart: unless-stopped
  
  # 可选：本地 AI (需要 8GB+ 内存)
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama-data:/root/.ollama
    restart: unless-stopped
    profiles:
      - ai
```

### 7.3 一键启动脚本

```bash
#!/bin/bash
# scripts/install.sh

set -e

echo "🚀 ChanLun Invester v2.0 安装脚本"
echo "=================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.11+"
    exit 1
fi

echo "✓ Python 版本：$(python3 --version)"

# 检查 Rust
if ! command -v rustc &> /dev/null; then
    echo "⚠️  检测到 Rust 未安装，正在安装..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile minimal
    source $HOME/.cargo/env
fi

echo "✓ Rust 版本：$(rustc --version)"

# 创建目录
echo "\n📁 创建目录结构..."
mkdir -p data logs configs

# 安装 Python 依赖
echo "\n📦 安装 Python 依赖..."
pip install -r requirements.txt

# 编译 Rust 引擎
echo "\n🔨 编译 Rust 引擎..."
cd core && cargo build --release && cd ..

# 初始化配置
echo "\n⚙️  初始化配置..."
if [ ! -f configs/config.json ]; then
    cp configs/config.example.json configs/config.json
    echo "✓ 创建基础配置：configs/config.json"
fi

# 初始化数据库
echo "\n🗄️  初始化数据库..."
python -c "from backend.database import init_db; init_db()"

# 下载示例数据
echo "\n📥 下载示例数据..."
python scripts/download_klines.py --symbol 000001.SZ --limit 1000

echo "\n✅ 安装完成!"
echo ""
echo "启动命令:"
echo "  # 方式 1: 直接启动"
echo "  python launcher.py server --port 8000"
echo ""
echo "  # 方式 2: Docker 启动"
echo "  docker-compose up -d"
echo ""
echo "  # 方式 3: 分析股票"
echo "  python launcher.py analyze 000001.SZ --level 30m"
echo ""
echo "访问地址："
echo "  API:    http://localhost:8000"
echo "  Web UI: http://localhost:3000 (需启动 frontend)"
echo ""
```

---

## 8. 测试框架

### 8.1 单元测试

```python
# tests/test_fractal.py
"""分型识别测试"""

import pytest
from chanlun.engine import ChanLunEngine
from chanlun.data import KLine

def test_top_fractal():
    """测试顶分型识别"""
    engine = ChanLunEngine()
    
    # 构造顶分型数据
    klines = [
        KLine(high=10, low=9, open=9.5, close=9.8),
        KLine(high=12, low=10, open=10, close=11),   # 顶分型中间 K 线
        KLine(high=11, low=9, open=10.5, close=9.5),
    ]
    
    fractals = engine.detect_fractals(klines)
    top_fractals = [f for f in fractals if f.type == 'top']
    
    assert len(top_fractals) == 1
    assert top_fractals[0].high == 12

def test_bottom_fractal():
    """测试底分型识别"""
    engine = ChanLunEngine()
    
    # 构造底分型数据
    klines = [
        KLine(high=12, low=10, open=11, close=10.5),
        KLine(high=10, low=8, open=10, close=9),     # 底分型中间 K 线
        KLine(high=11, low=9, open=9.5, close=10.5),
    ]
    
    fractals = engine.detect_fractals(klines)
    bottom_fractals = [f for f in fractals if f.type == 'bottom']
    
    assert len(bottom_fractals) == 1
    assert bottom_fractals[0].low == 8

def test_containment():
    """测试包含关系处理"""
    engine = ChanLunEngine()
    
    # 构造包含关系 K 线
    klines = [
        KLine(high=10, low=9, open=9.5, close=9.8),
        KLine(high=10.5, low=8.5, open=9, close=10),  # 包含前一根
    ]
    
    processed = engine.process_containment(klines)
    
    # 处理后应该合并为一根 K 线
    assert len(processed) == 1
    assert processed[0].high == 10.5
    assert processed[0].low == 8.5
```

---

## 9. 实施路线图

### Phase 1: 基础架构 (2 周) ✅

- [x] LEAN 架构分析
- [x] 设计原则确定
- [ ] 目录结构实现
- [ ] 配置分层设计
- [ ] 统一启动器

### Phase 2: 核心功能 (4 周)

- [ ] Rust 引擎完善
- [ ] CLI 工具实现
- [ ] 10 个策略示例
- [ ] 事件驱动架构

### Phase 3: 部署优化 (2 周)

- [ ] Docker 镜像优化
- [ ] 一键安装脚本
- [ ] 测试框架完善

### Phase 4: 文档与发布 (2 周)

- [ ] 完整文档
- [ ] 视频教程
- [ ] v2.0 Release

**总计:** 10 周完成 v2.0

---

## 10. 性能目标

| 指标 | LEAN | ChanLun v1 | ChanLun v2 目标 |
|------|------|------------|-----------------|
| **安装时间** | 30 分钟+ | 10 分钟 | **<5 分钟** |
| **启动时间** | 30 秒 | 10 秒 | **<5 秒** |
| **内存占用** | 500MB+ | 300MB | **<200MB** |
| **Docker 镜像** | 2GB+ | 800MB | **<500MB** |
| **文件数量** | 6000+ | 200 | **<1000** |
| **学习曲线** | 1-2 周 | 3-5 天 | **1-2 天** |

---

## 总结

### 核心改进

1. ✅ **配置分层** - 学习 LEAN 的 overlay 设计
2. ✅ **统一启动器** - chanlun CLI 工具
3. ✅ **策略示例库** - 10 个渐进式示例
4. ✅ **事件驱动** - 实时数据处理
5. ✅ **简洁设计** - 避免过度工程化
6. ✅ **本地优先** - 零成本启动

### 最终目标

**成为缠论领域的事实标准 - 简洁、专业、易用。**

---

**文档结束**

---

**版本:** v2.0  
**状态:** 设计中  
**最后更新:** 2026-02-23
