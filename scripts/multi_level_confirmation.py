#!/usr/bin/env python3
"""
多级别背驰确认监控系统
Multi-Level Divergence Confirmation Monitor

缠论核心原理：
1. 大级别背驰只是预警，真正逆转需要次级别确认
2. 日线背驰 → 需要 30m 级别确认
3. 30m 背驰 → 需要 5m 级别确认
4. 级别递归：大级别 = 次级别的走势类型连接

提醒策略：
- 第一阶段：大级别背驰预警（观察名单）
- 第二阶段：次级别第一类买卖点（重点关注）
- 第三阶段：次级别第二类买卖点（确认入场）
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator


# ==================== 配置 ====================

TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
CONFIRMATION_STATE_FILE = "/home/wei/.openclaw/workspace/chanlunInvester/.confirmation_state.json"

# 级别递归配置
LEVEL_CONFIG = {
    '1w': {
        'child_level': '1d',
        'weight': 4.0,
        'divergence_threshold': 0.35,
        'confirmation_window_hours': 168,  # 1 周内需要次级别确认
    },
    '1d': {
        'child_level': '30m',
        'weight': 3.0,
        'divergence_threshold': 0.3,
        'confirmation_window_hours': 48,  # 48 小时内需要次级别确认
    },
    '30m': {
        'child_level': '5m',
        'weight': 2.0,
        'divergence_threshold': 0.25,
        'confirmation_window_hours': 12,  # 12 小时内需要次级别确认
    },
    '5m': {
        'child_level': None,  # 最小级别
        'weight': 1.0,
        'divergence_threshold': 0.2,
        'confirmation_window_hours': 0,
    }
}

# 监控标的
SYMBOLS = [
    # UVIX 已移除 (用户要求取消)
    # XEG.TO, CVE.TO 已移除 (用户要求取消)
    {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'levels': ['1d', '30m']},
    {'symbol': 'PAAS.TO', 'name': 'Pan American Silver', 'levels': ['1d', '30m']},
    {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['1d', '30m']},
    # 美股
    {'symbol': 'TEL', 'name': 'TE Connectivity (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'GOOG', 'name': 'Alphabet/Google (美股)', 'levels': ['1w', '1d']},
    {'symbol': 'INTC', 'name': 'Intel Corporation (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'EOSE', 'name': 'Eos Energy Enterprises (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'BABA', 'name': 'Alibaba Group (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'SMR', 'name': 'NuScale Power Corporation (美股)', 'levels': ['1d', '30m']},
    {'symbol': 'IONQ', 'name': 'IonQ Inc (美股/量子计算)', 'levels': ['1d', '30m']},
]


# ==================== 数据结构 ====================

class ConfirmationStage(Enum):
    """确认阶段"""
    WAITING = "waiting"  # 等待大级别背驰
    PARENT_DIVERGENCE = "parent_divergence"  # 大级别背驰已出现（预警）
    CHILD_BSP1 = "child_bsp1"  # 次级别第一类买卖点（关注）
    CHILD_BSP2 = "child_bsp2"  # 次级别第二类买卖点（确认）
    CONFIRMED = "confirmed"  # 逆转确认
    FAILED = "failed"  # 确认失败


@dataclass
class DivergenceSignal:
    """背驰信号"""
    symbol: str
    level: str
    signal_type: str  # 'buy' or 'sell'
    strength: float
    price: float
    timestamp: datetime
    macd_prev: float
    macd_current: float
    price_prev: float
    price_current: float


@dataclass
class ConfirmationState:
    """确认状态"""
    symbol: str
    parent_level: str
    child_level: str
    stage: ConfirmationStage
    parent_divergence: Optional[DivergenceSignal] = None
    child_bsp1: Optional[DivergenceSignal] = None
    child_bsp2: Optional[dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    confirmed_price: Optional[float] = None
    notes: str = ""


# ==================== 背驰检测器 ====================

class MultiLevelDivergenceDetector:
    """多级别背驰检测器"""
    
    def __init__(self):
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
    
    def fetch_data(self, symbol: str, timeframe: str) -> Optional[KlineSeries]:
        """获取数据"""
        try:
            import yfinance as yf
            
            period_map = {
                '5m': ('5d', '5m'),
                '30m': ('10d', '30m'),
                '1d': ('60d', '1d'),
                '1w': ('2y', '1wk'),
                'week': ('2y', '1wk'),
            }
            
            period, interval = period_map.get(timeframe, ('10d', '30m'))
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period, interval=interval)
            
            if len(history) == 0:
                return None
            
            klines = []
            for idx, row in history.iterrows():
                timestamp = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx
                kline = Kline(
                    timestamp=timestamp,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row.get('Volume', 0))
                )
                klines.append(kline)
            
            return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
            
        except Exception as e:
            print(f"❌ Error fetching {symbol} {timeframe}: {e}")
            return None
    
    def analyze_level(self, series: KlineSeries) -> dict:
        """分析单个级别"""
        fractals = self.fractal_detector.detect_all(series)
        pens = self.pen_calculator.identify_pens(series)
        segments = self.segment_calculator.detect_segments(pens)
        
        prices = [(k.high + k.low) / 2 for k in series.klines]
        macd_data = self.macd.calculate(prices)
        
        divergence = self._detect_divergence(segments, macd_data, series)
        bsp_list = self._detect_bsp(segments, fractals, divergence, series)
        
        return {
            'series': series,
            'fractals': fractals,
            'pens': pens,
            'segments': segments,
            'macd': macd_data,
            'divergence': divergence,
            'bsp': bsp_list,
        }
    
    def _detect_divergence(self, segments: List, macd_data: List, series: KlineSeries) -> Optional[DivergenceSignal]:
        """检测背驰"""
        if len(segments) < 2 or not macd_data:
            return None
        
        last_seg = segments[-1]
        prev_seg = None
        
        for seg in reversed(segments[:-1]):
            if seg.direction == last_seg.direction:
                prev_seg = seg
                break
        
        if not prev_seg:
            return None
        
        try:
            macd_prev = macd_data[prev_seg.end_idx].histogram
            macd_last = macd_data[last_seg.end_idx].histogram
            
            price_prev = prev_seg.end_price
            price_last = last_seg.end_price
            
            # 顶背驰
            if last_seg.direction == 'up':
                if price_last > price_prev and macd_last < macd_prev:
                    strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                    return DivergenceSignal(
                        symbol=series.symbol,
                        level=series.timeframe,
                        signal_type='sell',
                        strength=strength,
                        price=price_last,
                        timestamp=datetime.now(),
                        macd_prev=macd_prev,
                        macd_current=macd_last,
                        price_prev=price_prev,
                        price_current=price_last,
                    )
            
            # 底背驰
            elif last_seg.direction == 'down':
                if price_last < price_prev and macd_last > macd_prev:
                    strength = abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001)
                    return DivergenceSignal(
                        symbol=series.symbol,
                        level=series.timeframe,
                        signal_type='buy',
                        strength=strength,
                        price=price_last,
                        timestamp=datetime.now(),
                        macd_prev=macd_prev,
                        macd_current=macd_last,
                        price_prev=price_prev,
                        price_current=price_last,
                    )
        except Exception as e:
            print(f"⚠️ Divergence detection error: {e}")
        
        return None
    
    def _detect_bsp(self, segments: List, fractals: List, divergence: Optional[DivergenceSignal], series: KlineSeries) -> List[dict]:
        """检测买卖点"""
        bsp_list = []
        
        if divergence:
            bsp_list.append({
                'type': f"bsp1_{'buy' if divergence.signal_type == 'buy' else 'sell'}",
                'level': series.timeframe,
                'price': divergence.price,
                'confidence': min(divergence.strength, 0.9),
                'divergence': divergence,
            })
        
        # 第二类买卖点检测
        if len(fractals) >= 2:
            current_price = series.klines[-1].close
            
            if divergence and divergence.signal_type == 'buy':
                # 买 2：回调不破前低
                bottom_fractals = [f for f in fractals if not f.is_top][-2:]
                if len(bottom_fractals) == 2:
                    if bottom_fractals[-1].price > bottom_fractals[-2].price:
                        distance = (current_price - bottom_fractals[-1].price) / bottom_fractals[-1].price
                        if 0 < distance < 0.02:  # 2% 以内
                            bsp_list.append({
                                'type': 'bsp2_buy',
                                'level': series.timeframe,
                                'price': current_price,
                                'confidence': 0.7,
                                'description': '第二类买点：回调不破前低',
                            })
            
            elif divergence and divergence.signal_type == 'sell':
                # 卖 2：反弹不过前高
                top_fractals = [f for f in fractals if f.is_top][-2:]
                if len(top_fractals) == 2:
                    if top_fractals[-1].price < top_fractals[-2].price:
                        distance = (top_fractals[-1].price - current_price) / top_fractals[-1].price
                        if 0 < distance < 0.02:  # 2% 以内
                            bsp_list.append({
                                'type': 'bsp2_sell',
                                'level': series.timeframe,
                                'price': current_price,
                                'confidence': 0.7,
                                'description': '第二类卖点：反弹不过前高',
                            })
        
        return bsp_list


# ==================== 确认状态管理 ====================

class ConfirmationManager:
    """确认状态管理器"""
    
    def __init__(self):
        self.state_file = CONFIRMATION_STATE_FILE
        self.states: Dict[str, ConfirmationState] = {}
        self.load_state()
    
    def load_state(self):
        """加载状态"""
        if Path(self.state_file).exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.states[key] = self._dict_to_state(value)
            except Exception as e:
                print(f"⚠️ Failed to load state: {e}")
    
    def save_state(self):
        """保存状态"""
        try:
            data = {k: self._state_to_dict(v) for k, v in self.states.items()}
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Failed to save state: {e}")
    
    def _state_to_dict(self, state: ConfirmationState) -> dict:
        """状态转字典"""
        return {
            'symbol': state.symbol,
            'parent_level': state.parent_level,
            'child_level': state.child_level,
            'stage': state.stage.value,
            'parent_divergence': self._div_to_dict(state.parent_divergence) if state.parent_divergence else None,
            'child_bsp1': self._div_to_dict(state.child_bsp1) if state.child_bsp1 else None,
            'child_bsp2': state.child_bsp2,
            'created_at': str(state.created_at),
            'updated_at': str(state.updated_at),
            'confirmed_price': state.confirmed_price,
            'notes': state.notes,
        }
    
    def _div_to_dict(self, div: DivergenceSignal) -> dict:
        """背驰信号转字典"""
        return {
            'symbol': div.symbol,
            'level': div.level,
            'signal_type': div.signal_type,
            'strength': div.strength,
            'price': div.price,
            'timestamp': str(div.timestamp),
        }
    
    def _dict_to_state(self, data: dict) -> ConfirmationState:
        """字典转状态"""
        return ConfirmationState(
            symbol=data['symbol'],
            parent_level=data['parent_level'],
            child_level=data['child_level'],
            stage=ConfirmationStage(data['stage']),
            parent_divergence=self._dict_to_div(data['parent_divergence']) if data.get('parent_divergence') else None,
            child_bsp1=self._dict_to_div(data['child_bsp1']) if data.get('child_bsp1') else None,
            child_bsp2=data.get('child_bsp2'),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            confirmed_price=data.get('confirmed_price'),
            notes=data.get('notes', ''),
        )
    
    def _dict_to_div(self, data: dict) -> DivergenceSignal:
        """字典转背驰信号"""
        return DivergenceSignal(
            symbol=data['symbol'],
            level=data['level'],
            signal_type=data['signal_type'],
            strength=data['strength'],
            price=data['price'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            macd_prev=data.get('macd_prev', 0),
            macd_current=data.get('macd_current', 0),
            price_prev=data.get('price_prev', 0),
            price_current=data.get('price_current', 0),
        )
    
    def get_or_create_state(self, symbol: str, parent_level: str) -> ConfirmationState:
        """获取或创建状态"""
        key = f"{symbol}:{parent_level}"
        if key not in self.states:
            child_level = LEVEL_CONFIG.get(parent_level, {}).get('child_level')
            if child_level:
                self.states[key] = ConfirmationState(
                    symbol=symbol,
                    parent_level=parent_level,
                    child_level=child_level,
                    stage=ConfirmationStage.WAITING,
                )
        return self.states[key]
    
    def update_stage(self, symbol: str, parent_level: str, new_stage: ConfirmationStage, **kwargs):
        """更新阶段"""
        key = f"{symbol}:{parent_level}"
        state = self.get_or_create_state(symbol, parent_level)
        state.stage = new_stage
        state.updated_at = datetime.now()
        
        for k, v in kwargs.items():
            if hasattr(state, k):
                setattr(state, k, v)
        
        self.states[key] = state
        self.save_state()
    
    def check_timeout(self) -> List[str]:
        """检查超时"""
        timeout_keys = []
        now = datetime.now()
        
        for key, state in self.states.items():
            if state.stage == ConfirmationStage.PARENT_DIVERGENCE:
                config = LEVEL_CONFIG.get(state.parent_level, {})
                window_hours = config.get('confirmation_window_hours', 24)
                
                if (now - state.updated_at).total_seconds() / 3600 > window_hours:
                    state.stage = ConfirmationStage.FAILED
                    state.notes = f"超时：{window_hours}小时内未收到次级别确认"
                    state.updated_at = now
                    timeout_keys.append(key)
                    self.states[key] = state
        
        if timeout_keys:
            self.save_state()
        
        return timeout_keys


# ==================== 警报系统 ====================

class AlertSystem:
    """多级别确认警报系统
    
    核心原则：只有多级别联动共振才发送高优先级通知
    单级别背驰仅作为观察参考，不主动推送
    """
    
    def __init__(self):
        self.alert_log = ALERT_LOG
        self.openclaw_path = "/home/linuxbrew/.linuxbrew/bin/openclaw"
        # 单级别背驰只记录日志，不推送
        self.push_stages = [
            ConfirmationStage.CHILD_BSP1,   # 次级别第一类买卖点（多级别共振开始）
            ConfirmationStage.CHILD_BSP2,   # 次级别第二类买卖点（确认入场）
            ConfirmationStage.CONFIRMED,    # 完全确认
        ]
    
    def log_alert(self, message: str, push: bool = False):
        """记录警报
        
        Args:
            message: 警报内容
            push: 是否推送 Telegram（只有多级别共振时才为 True）
        """
        timestamp = datetime.now().isoformat()
        prefix = "📱 PUSH" if push else "📝 LOG"
        log_line = f"{timestamp} - {prefix} - {message}\n"
        
        with open(self.alert_log, 'a') as f:
            f.write(log_line)
        
        print(log_line.strip())
    
    def send_telegram(self, message: str):
        """发送 Telegram 警报"""
        try:
            import subprocess
            cmd = [
                self.openclaw_path,
                'message', 'send',
                '--target', TELEGRAM_CHAT_ID,
                '--message', message[:4000],  # Telegram 消息长度限制
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            print(f"📱 Telegram 已发送")
        except Exception as e:
            print(f"⚠️ Telegram send failed: {e}")
    
    def alert_parent_divergence(self, state: ConfirmationState, divergence: DivergenceSignal):
        """大级别背驰预警 - 仅记录日志，不推送
        
        核心原则：单级别背驰准确率较低，只作为观察名单
        """
        signal_emoji = "🟢" if divergence.signal_type == 'buy' else "🔴"
        signal_name = "买点" if divergence.signal_type == 'buy' else "卖点"
        
        # 仅记录日志，不推送 Telegram
        message = f"""
📝 **观察名单：大级别背驰预警** {signal_emoji}

📊 {state.symbol}
🔸 级别：{divergence.level}（大级别）
🔸 信号：第一类{signal_name}（背驰）
🔸 强度：{divergence.strength:.2f}
🔸 价格：${divergence.price:.2f}

📋 确认流程:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 等待 {state.child_level} 级别第一类{signal_name} ⏳
3️⃣ 等待 {state.child_level} 级别第二类{signal_name} ⏳

⏰ 确认窗口：{LEVEL_CONFIG.get(divergence.level, {}).get('confirmation_window_hours', 24)}小时
💡 状态：加入观察名单（等待多级别共振）
⚠️ 注意：单级别背驰准确率较低，需等待次级别确认
"""
        
        self.log_alert(f"⚠️ {state.symbol} {divergence.level}级别背驰预警 - {divergence.signal_type}", push=False)
        # 不发送 Telegram，仅记录日志
        print(f"   📝 已记录观察名单（不推送）")
    
    def alert_child_bsp1(self, state: ConfirmationState, bsp1: DivergenceSignal):
        """次级别第一类买卖点 - 多级别共振开始，推送提醒
        
        核心原则：大级别 + 次级别同时背驰 = 多级别共振（准确率显著提升）
        """
        signal_emoji = "🟢" if bsp1.signal_type == 'buy' else "🔴"
        signal_name = "买点" if bsp1.signal_type == 'buy' else "卖点"
        
        message = f"""
🔍 **多级别共振：次级别第一类{signal_name}** {signal_emoji}

📊 {state.symbol}
🔸 大级别：{state.parent_level} 背驰已确认 ✅
🔸 次级别：{bsp1.level} 第一类{signal_name} ✅
🔸 共振强度：{bsp1.strength:.2f}
🔸 价格：${bsp1.price:.2f}

📋 确认流程:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 次级别第一类{signal_name} 已出现 ✅
3️⃣ 等待次级别第二类{signal_name} ⏳

💡 状态：多级别共振，准确率显著提升
🎯 建议：重点关注，等待第二类买卖点确认
"""
        
        self.log_alert(f"🔍 {state.symbol} {bsp1.level}级别 BSP1（多级别共振） - {bsp1.signal_type}", push=True)
        self.send_telegram(message.strip())
    
    def alert_child_bsp2(self, state: ConfirmationState, bsp2: dict):
        """次级别第二类买卖点 - 多级别共振确认，最高优先级
        
        核心原则：大级别背驰 + 次级别 BSP1 + 次级别 BSP2 = 完整确认链（最高准确率）
        """
        signal_emoji = "🟢" if 'buy' in bsp2['type'] else "🔴"
        signal_name = "买点" if 'buy' in bsp2['type'] else "卖点"
        
        # 计算综合置信度
        parent_conf = state.parent_divergence.strength if state.parent_divergence else 0
        child_conf = state.child_bsp1.strength if state.child_bsp1 else 0
        combined_conf = min((parent_conf + child_conf) / 2 + 0.1, 0.95)  # 多级别共振提升置信度
        
        message = f"""
✅ **多级别共振确认！第二类{signal_name}** {signal_emoji}

📊 {state.symbol}
🔸 大级别：{state.parent_level} 背驰（强度:{parent_conf:.2f}）✅
🔸 次级别：{bsp2['level']} 第二类{signal_name} ✅
🔸 确认价格：${bsp2['price']:.2f}
🔸 综合置信度：{combined_conf:.0%}（多级别共振）

📋 完整确认链:
1️⃣ 大级别背驰已出现 ✅
2️⃣ 次级别第一类{signal_name} 已出现 ✅
3️⃣ 次级别第二类{signal_name} 已确认 ✅

🎯 逆转确认完成！
💡 状态：多级别共振确认，可入场
⚡ 准确率：显著高于单级别信号
"""
        
        self.log_alert(f"✅ {state.symbol} {bsp2['level']}级别 BSP2（多级别共振确认） - {signal_name}", push=True)
        self.send_telegram(message.strip())
    
    def alert_timeout(self, state: ConfirmationState):
        """确认超时 - 仅记录日志"""
        message = f"""
⏰ **确认超时** ⚠️

📊 {state.symbol}
🔸 大级别：{state.parent_level} 背驰
🔸 等待：{state.child_level} 级别确认
🔸 超时：{LEVEL_CONFIG.get(state.parent_level, {}).get('confirmation_window_hours', 24)}小时

💡 状态：确认失败，背驰可能失效
📋 建议：重新评估走势
📝 注意：单级别背驰在强趋势中容易失效
"""
        
        self.log_alert(f"⏰ {state.symbol} 确认超时 - 失败", push=False)
        # 超时不推送，仅记录
        print(f"   ⏰ 确认超时（已记录，不推送）")


# ==================== 主监控循环 ====================

class MultiLevelMonitor:
    """多级别背驰确认监控器"""
    
    def __init__(self):
        self.detector = MultiLevelDivergenceDetector()
        self.manager = ConfirmationManager()
        self.alerter = AlertSystem()
    
    def run(self, symbols: List[dict] = None):
        """运行监控"""
        if symbols is None:
            symbols = SYMBOLS
        
        print(f"\n{'='*70}")
        print("多级别背驰确认监控系统")
        print(f"{'='*70}\n")
        
        # 检查超时
        timeout_keys = self.manager.check_timeout()
        for key in timeout_keys:
            state = self.manager.states[key]
            self.alerter.alert_timeout(state)
        
        # 监控每个标的
        for symbol_config in symbols:
            symbol = symbol_config['symbol']
            levels = symbol_config['levels']
            
            print(f"\n📊 {symbol} ({symbol_config['name']})")
            print(f"   监控级别：{levels}")
            
            # 分析所有级别
            results = {}
            for level in levels:
                series = self.detector.fetch_data(symbol, level)
                if series:
                    results[level] = self.detector.analyze_level(series)
                    print(f"   {level}: {len(results[level]['segments'])} 线段, "
                          f"背驰={results[level]['divergence'] is not None}")
            
            # 检查多级别确认
            self._check_confirmation(symbol, results)
        
        print(f"\n{'='*70}")
        print("监控完成")
        print(f"{'='*70}\n")
    
    def _check_confirmation(self, symbol: str, results: Dict[str, dict]):
        """检查确认状态
        
        核心原则：只有多级别联动共振才推送高优先级通知
        """
        for parent_level, child_level_config in LEVEL_CONFIG.items():
            if parent_level not in results:
                continue
            
            child_level = child_level_config.get('child_level')
            if not child_level or child_level not in results:
                continue
            
            parent_result = results[parent_level]
            child_result = results[child_level]
            state = self.manager.get_or_create_state(symbol, parent_level)
            
            # 阶段 1: 大级别背驰检测 - 仅记录，不推送
            if parent_result['divergence'] and state.stage == ConfirmationStage.WAITING:
                div = parent_result['divergence']
                threshold = child_level_config.get('divergence_threshold', 0.3)
                
                if div.strength > threshold:
                    state.parent_divergence = div
                    state.stage = ConfirmationStage.PARENT_DIVERGENCE
                    self.manager.states[f"{symbol}:{parent_level}"] = state
                    self.manager.save_state()
                    self.alerter.alert_parent_divergence(state, div)  # 仅记录日志
                    print(f"   📝 {symbol} {parent_level}背驰预警 - 加入观察名单")
            
            # 阶段 2: 次级别第一类买卖点 - 多级别共振开始，推送
            if state.stage == ConfirmationStage.PARENT_DIVERGENCE:
                child_bsp1 = child_result['divergence']
                
                # 关键：必须同方向才构成共振
                if child_bsp1 and child_bsp1.signal_type == state.parent_divergence.signal_type:
                    state.child_bsp1 = child_bsp1
                    state.stage = ConfirmationStage.CHILD_BSP1
                    self.manager.states[f"{symbol}:{parent_level}"] = state
                    self.manager.save_state()
                    self.alerter.alert_child_bsp1(state, child_bsp1)  # 推送
                    print(f"   🔍 {symbol} 多级别共振！推送提醒")
            
            # 阶段 3: 次级别第二类买卖点 - 完整确认链，最高优先级
            if state.stage == ConfirmationStage.CHILD_BSP1:
                child_bsp2_list = [b for b in child_result['bsp'] if b['type'].startswith('bsp2')]
                
                if child_bsp2_list:
                    bsp2 = child_bsp2_list[0]
                    state.child_bsp2 = bsp2
                    state.stage = ConfirmationStage.CHILD_BSP2
                    state.confirmed_price = bsp2['price']
                    self.manager.states[f"{symbol}:{parent_level}"] = state
                    self.manager.save_state()
                    self.alerter.alert_child_bsp2(state, bsp2)  # 推送
                    print(f"   ✅ {symbol} 多级别共振确认！推送入场信号")


# ==================== 入口 ====================

if __name__ == "__main__":
    monitor = MultiLevelMonitor()
    monitor.run()
