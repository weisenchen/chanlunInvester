#!/usr/bin/env python3
"""
ChanLun Invester - Real-time Monitor with Telegram Alerts
缠论智能监控系统 - Telegram 预警

基于 chanlunInvester 核心引擎，实现多级别买卖点监控
支持：分型、笔、线段、中枢、背驰、买卖点检测
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json
import yaml
import tempfile
import fcntl

# === Configuration Loading ===
def load_config(config_path=None):
    """Load config.yaml, override with env vars where applicable."""
    if config_path is None:
        config_path = str(Path(__file__).parent.parent / "config" / "config.yaml")
    
    # Default config
    cfg = {
        "telegram": {"chat_id": "8365377574", "parse_mode": "HTML"},
        "symbols": [
            {'symbol': 'UVIX', 'name': '波动率指数', 'levels': ['5m', '30m']},
            {'symbol': 'XEG.TO', 'name': '加拿大能源 ETF', 'levels': ['30m', '1d']},
            {'symbol': 'CVE.TO', 'name': 'Cenovus Energy', 'levels': ['30m', '1d']},
            {'symbol': 'CNQ.TO', 'name': 'Canadian Natural Resources', 'levels': ['30m', '1d']},
            {'symbol': 'PAAS.TO', 'name': 'Pan American Silver', 'levels': ['30m', '1d']},
            {'symbol': 'TECK', 'name': 'Teck Resources Limited', 'levels': ['30m', '1d']},
        ],
        "data": {
            "count_per_level": {"5m": 200, "30m": 300, "1d": 500, "1wk": 250},
            "period_map": {"5m": "5d", "30m": "30d", "1d": "1y", "1wk": "5y"},
            "max_retries": 2,
            "retry_delay_seconds": 5,
        },
        "thresholds": {
            "5m": {"bsp2_pct": 0.01, "bsp1_min_strength": 2.0, "min_distance": 0.005, "bsp3_pct": 0.02, "bsp3_klines": 3},
            "30m": {"bsp2_pct": 0.015, "bsp1_min_strength": 3.0, "min_distance": 0.008, "bsp3_pct": 0.03, "bsp3_klines": 5},
            "1d": {"bsp2_pct": 0.03, "bsp1_min_strength": 5.0, "min_distance": 0.01, "bsp3_pct": 0.05, "bsp3_klines": 10},
        },
        "fusion_weights": {
            "5m": {"direction": 1.0, "signal": 2.0},
            "30m": {"direction": 2.0, "signal": 3.0},
            "1d": {"direction": 3.0, "signal": 5.0},
            "1wk": {"direction": 4.0, "signal": 8.0},
        },
        "fusion": {"strong_buy": 6.0, "buy": 3.0, "strong_sell": -6.0, "sell": -3.0},
        "antispam": {"min_price_change_pct": 0.003, "silence_period_minutes": 60, "state_ttl_hours": 24},
        "paths": {
            "alert_log": str(Path.home() / ".openclaw/workspace/chanlunInvester/alerts.log"),
            "alert_state_file": str(Path.home() / ".openclaw/workspace/chanlunInvester/.alert_state.json"),
        },
    }
    
    # Load from YAML if exists
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                yaml_cfg = yaml.safe_load(f) or {}
            # Deep merge yaml_cfg into cfg
            _deep_merge(cfg, yaml_cfg)
        except Exception as e:
            print(f"⚠️ Config load error (using defaults): {e}")
    
    # Env var overrides
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if env_token:
        cfg["telegram"]["bot_token"] = env_token
    env_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if env_chat:
        cfg["telegram"]["chat_id"] = env_chat
    
    return cfg


def _deep_merge(base, override):
    """Recursively merge override dict into base dict."""
    for key, val in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deep_merge(base[key], val)
        else:
            base[key] = val


# Load config
CONFIG = load_config()

# Extract commonly used values
TELEGRAM_CHAT_ID = CONFIG["telegram"]["chat_id"]
TELEGRAM_BOT_TOKEN = CONFIG["telegram"].get("bot_token", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
DATA_CONFIG = CONFIG["data"]
SYMBOLS = CONFIG["symbols"]
THRESHOLDS = CONFIG["thresholds"]
FUSION_WEIGHTS = CONFIG["fusion_weights"]
ANTISPAM = CONFIG["antispam"]
FUSION_THRESHOLDS = CONFIG["fusion"]
ALERT_LOG = CONFIG["paths"]["alert_log"]
ALERT_STATE_FILE = CONFIG["paths"]["alert_state_file"]

# Anti-spam settings
MIN_PRICE_CHANGE = ANTISPAM["min_price_change_pct"]
SILENCE_PERIOD_MINUTES = ANTISPAM["silence_period_minutes"]

# Add src/ to path for trading_system imports
sys.path.insert(0, str(Path(__file__).parent))

# Import trading system components
from trading_system.kline import Kline, KlineSeries, TimeFrame
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator
from trading_system.center import CenterDetector, Center
from trading_system.divergence import DivergenceDetector


def fetch_yahoo_data(symbol: str, timeframe: str = '30m', count: int = None):
    """Fetch real-time data from Yahoo Finance with retry logic and larger windows."""
    if count is None:
        count = DATA_CONFIG["count_per_level"].get(timeframe, 100)
    
    period_map = DATA_CONFIG["period_map"]
    max_retries = DATA_CONFIG["max_retries"]
    retry_delay = DATA_CONFIG["retry_delay_seconds"]
    
    # Get period and interval from config
    interval = timeframe
    period = period_map.get(timeframe, "1mo")

    for attempt in range(max_retries + 1):
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period, interval=interval)

            if len(history) == 0:
                if attempt < max_retries:
                    import time
                    time.sleep(retry_delay)
                    continue
                return None

            # Convert to Kline objects
            klines = []
            for idx, row in history.iterrows():
                if hasattr(idx, 'to_pydatetime'):
                    timestamp = idx.to_pydatetime()
                else:
                    timestamp = idx

                kline = Kline(
                    timestamp=timestamp,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row.get('Volume', 0))
                )
                klines.append(kline)

            # Take last 'count' klines
            if len(klines) > count:
                klines = klines[-count:]

            series = KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
            return series

        except Exception as e:
            if attempt < max_retries:
                import time
                print(f"    ⚠️ Retry {attempt+1}/{max_retries} for {symbol} {timeframe}: {e}")
                time.sleep(retry_delay)
            else:
                print(f"❌ Error fetching data for {symbol} {timeframe}: {e}")
                return None

def _check_reversal_structure(segments, direction='buy'):
    """
    Verify that recent segment structure supports Buy2/Sell2.
    
    Buy2 requires: prior downtrend (down segment) followed by reversal (up segment)
    Sell2 requires: prior uptrend (up segment) followed by reversal (down segment)
    
    缠论第21/32课：第二类买卖点需要第一类买卖点确认后的第一次回调/反弹
    """
    if len(segments) < 2:
        return False
    last_two = segments[-2:]
    if direction == 'buy':
        # Must show down → up reversal (recent downtrend followed by uptrend)
        return last_two[0].direction == 'down' and last_two[1].direction == 'up'
    else:
        # Must show up → down reversal
        return last_two[0].direction == 'up' and last_two[1].direction == 'down'


def _calc_pullback_ratio(segments, current_price, buy=True):
    """
    Calculate pullback depth as ratio of prior move height.
    Used for dynamic Buy2/Sell2 strength calculation.
    """
    if len(segments) < 2:
        return 1.0
    # The prior move is the segment before the last one
    prior_seg = segments[-2]
    prior_height = abs(prior_seg.end_price - prior_seg.start_price)
    if prior_height < 0.01:
        return 1.0
    # Pullback depth: how far has price retraced into the prior range
    if buy:
        pullback_from_high = abs(segments[-1].end_price - current_price) if segments[-1].direction == 'up' else 0
        ratio = pullback_from_high / prior_height
    else:
        pullback_from_low = abs(current_price - segments[-1].end_price) if segments[-1].direction == 'down' else 0
        ratio = pullback_from_low / prior_height
    return min(max(ratio, 0.1), 1.0)

def detect_buy_sell_points(series, fractals, pens, segments, macd_data, level="30m", centers=None):
    """
    Detect ChanLun buy/sell points (全6类买卖点检测)

    Detects all 6 types: Buy1, Buy2, Buy3, Sell1, Sell2, Sell3
    
    Phase 2 improvements:
    - Multi-method divergence: point + area + DIF (黄白线) comparison
    - 黄白线回拉0轴 check for center confirmation
    - Better trend verification (segment alignment + center overlap)
    - Segment-level area divergence (区间套 - Lesson 27)
    """
    signals = []
    div_tracking = {
        'bullish_score': 0.0,
        'bearish_score': 0.0,
        'bullish_details': {},
        'bearish_details': {},
    }

    if len(fractals) < 4 or len(pens) < 4:
        return {'signals': signals, 'divergence': div_tracking}

    # Get recent fractals
    top_fractals = [f for f in fractals if f.is_top][-3:]
    bottom_fractals = [f for f in fractals if not f.is_top][-3:]

    current_price = series.klines[-1].close

    # ========== 获取当前趋势方向 ==========
    last_pen = pens[-1]
    current_trend = 'up' if last_pen.is_up else 'down'

    # Also check segment-level trend for longer-term context
    latest_segments = segments[-2:] if len(segments) >= 2 else segments
    segment_trend = None
    if len(latest_segments) >= 1:
        segment_trend = latest_segments[-1].direction

    # Thresholds by level
    thresholds = {
        '5m':  {'bsp2': 0.01, 'bsp1': 2.0, 'min_distance': 0.005, 'bsp3_pct': 0.02, 'bsp3_klines': 3},
        '30m': {'bsp2': 0.015, 'bsp1': 3.0, 'min_distance': 0.008, 'bsp3_pct': 0.03, 'bsp3_klines': 5},
        '1d':  {'bsp2': 0.03, 'bsp1': 5.0, 'min_distance': 0.01, 'bsp3_pct': 0.05, 'bsp3_klines': 10}
    }
    thresh = thresholds.get(level, thresholds['30m'])

    # ========== Trend Verification for BSP1 (背驰需要趋势) ==========
    # 缠论核心：没有趋势，没有背驰（Lesson 15）
    # Buy1 requires a downtrend (≥2 descending non-overlapping centers)
    # Sell1 requires an uptrend (≥2 ascending non-overlapping centers)
    has_downtrend = False
    has_uptrend = False
    trend_strength = 0  # 0.0 to 3.0, how strong the trend is

    if centers and len(centers) >= 2:
        # 检查最后两个中枢是否构成趋势
        # 下跌趋势：后中枢GG < 前中枢DD（新的中枢完全在前一个的下方）
        # 上涨趋势：后中枢DD > 前中枢GG（新的中枢完全在前一个的上方）
        last_two = centers[-2:]
        c1, c2 = last_two[0], last_two[1]

        # 下跌趋势验证：c2 completely below c1
        if c2.gg < c1.dd:
            has_downtrend = True
            # Trend strength based on gap between centers
            gap = c1.dd - c2.gg
            trend_strength = min(gap / max(c1.range, 0.01), 3.0)
        # 上涨趋势验证：c2 completely above c1
        if c2.dd > c1.gg:
            has_uptrend = True
            gap = c2.dd - c1.gg
            trend_strength = min(gap / max(c1.range, 0.01), 3.0)

        if has_downtrend or has_uptrend:
            trend_type = '下跌趋势' if has_downtrend else '上涨趋势'
            print(f"    📐 趋势验证：{trend_type}已确认 ({len(centers)}个中枢, 强度:{trend_strength:.1f})")
        else:
            print(f"    ⚠️ 趋势未确认：{len(centers)}个中枢但无趋势（可能为盘整）")

    elif centers and len(centers) < 2:
        print(f"    ⚠️ 中枢不足：{len(centers)}个（需要≥2个才能形成趋势）")
        print(f"      (无趋势=无背驰：第一类买卖点被禁止)")

    # ========== 区间套趋势确认 (Segment Direction Alignment) ==========
    # Check if segment-level flow aligns with center trend direction
    segment_trend_confirmed = False
    if has_downtrend and segment_trend == 'down':
        segment_trend_confirmed = True
    elif has_uptrend and segment_trend == 'up':
        segment_trend_confirmed = True

    # Create divergence detector
    div_detector = DivergenceDetector()

    # ========== Buy Point 1 (第一类买点 - 底背驰) ==========
    # 条件：下跌趋势（≥2个中枢）+ MACD多方法底背驰
    # 理论来源：Lesson 14, 15, 24, 25
    # Phase 2: Uses combined point + area + DIF method
    if len(bottom_fractals) >= 2 and macd_data and has_downtrend:
        div_result = div_detector.detect_bullish_divergence(
            series, macd_data, segments, bottom_fractals, centers or []
        )

        if div_result.has_divergence:
            # Check zero-pullback for additional confirmation
            zp_result = div_detector.check_zero_pullback(macd_data, centers or [])

            # Final strength = divergence_score * (1 + trend_strength * 0.3) + pullback bonus
            final_strength = div_result.score * (1.0 + trend_strength * 0.3)
            if zp_result and zp_result.has_pullback:
                final_strength *= 1.2  # 20% boost for zero-pullback confirmation
            if segment_trend_confirmed:
                final_strength *= 1.15  # 15% boost for segment-level alignment

            signals.append({
                'type': 'buy1',
                'name': f'{level}级别第一类买点 (底背驰)',
                'price': current_price,
                'confidence': 'high' if final_strength >= 1.5 else 'medium',
                'strength': min(final_strength, 5.0),
                'description': (
                    f'底背驰(多方法融合): '
                    f'点={div_result.details.get("point_score", 0):.1f}, '
                    f'面积={div_result.details.get("area_score", 0):.1f}, '
                    f'DIF={div_result.details.get("dif_score", 0):.1f}'
                )
            })
            print(f"    ✅ Buy1: {div_result.score:.1f} (点:{div_result.details.get('point_score',0):.1f} "
                  f"面积:{div_result.details.get('area_score',0):.1f} "
                  f"DIF:{div_result.details.get('dif_score',0):.1f})"
                  f" {'+回拉0轴' if zp_result and zp_result.has_pullback else ''}")
        else:
            pt = div_result.details.get('point_score', 0)
            ar = div_result.details.get('area_score', 0)
            df = div_result.details.get('dif_score', 0)
            print(f"    ⚠️ Buy1 divergence insufficient: 点={pt:.1f} 面积={ar:.1f} DIF={df:.1f}")

    # ========== Sell Point 1 (第一类卖点 - 顶背驰) ==========
    # 条件：上涨趋势（≥2个中枢）+ MACD多方法顶背驰
    # 理论来源：Lesson 14, 15, 24, 25
    # Phase 2: Uses combined point + area + DIF method
    if len(top_fractals) >= 2 and macd_data and has_uptrend:
        div_result = div_detector.detect_bearish_divergence(
            series, macd_data, segments, top_fractals, centers or []
        )

        if div_result.has_divergence:
            zp_result = div_detector.check_zero_pullback(macd_data, centers or [])

            final_strength = div_result.score * (1.0 + trend_strength * 0.3)
            if zp_result and zp_result.has_pullback:
                final_strength *= 1.2
            if segment_trend_confirmed:
                final_strength *= 1.15

            signals.append({
                'type': 'sell1',
                'name': f'{level}级别第一类卖点 (顶背驰)',
                'price': current_price,
                'confidence': 'high' if final_strength >= 1.5 else 'medium',
                'strength': min(final_strength, 5.0),
                'description': (
                    f'顶背驰(多方法融合): '
                    f'点={div_result.details.get("point_score", 0):.1f}, '
                    f'面积={div_result.details.get("area_score", 0):.1f}, '
                    f'DIF={div_result.details.get("dif_score", 0):.1f}'
                )
            })
            print(f"    ✅ Sell1: {div_result.score:.1f} (点:{div_result.details.get('point_score',0):.1f} "
                  f"面积:{div_result.details.get('area_score',0):.1f} "
                  f"DIF:{div_result.details.get('dif_score',0):.1f})"
                  f" {'+回拉0轴' if zp_result and zp_result.has_pullback else ''}")
        else:
            pt = div_result.details.get('point_score', 0)
            ar = div_result.details.get('area_score', 0)
            df = div_result.details.get('dif_score', 0)
            print(f"    ⚠️ Sell1 divergence insufficient: 点={pt:.1f} 面积={ar:.1f} DIF={df:.1f}")

    # ========== Divergence-Aware Fusion Tracking (Phase 2) ==========
    # Always run divergence detection, even without centers/trend.
    if len(bottom_fractals) >= 2 and macd_data:
        bd = div_detector.detect_bullish_divergence(series, macd_data, segments, bottom_fractals, centers or [])
        if bd.has_divergence:
            div_tracking['bullish_score'] = bd.score
            div_tracking['bullish_details'] = bd.details
        # Also check segment-level divergence (区间套)
        sd = div_detector.check_segment_fractal_divergence(series, macd_data, segments)
        if sd and sd.has_divergence and sd.details.get('direction') == 'bullish':
            div_tracking['bullish_score'] = max(div_tracking['bullish_score'], sd.score * 0.7)
    if len(top_fractals) >= 2 and macd_data:
        bd = div_detector.detect_bearish_divergence(series, macd_data, segments, top_fractals, centers or [])
        if bd.has_divergence:
            div_tracking['bearish_score'] = bd.score
            div_tracking['bearish_details'] = bd.details
        sd = div_detector.check_segment_fractal_divergence(series, macd_data, segments)
        if sd and sd.has_divergence and sd.details.get('direction') == 'bearish':
            div_tracking['bearish_score'] = max(div_tracking['bearish_score'], sd.score * 0.7)

    # ========== Buy Point 2 (第二类买点) ==========
    # 缠论第21/32课：第二类买点 = 第一类买点确认后的第一次回调不破前低
    # 新增: 段结构验证 (down→up反转) + 动态强度
    has_reversal = _check_reversal_structure(segments, direction='buy')
    if len(bottom_fractals) >= 2 and current_trend == 'up' and has_reversal:
        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]

        # 回调不破前低（核心条件）
        if last_low.price > prev_low.price:
            distance = (current_price - last_low.price) / last_low.price
            if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                # Dynamic strength: scaled by pullback ratio (deeper pullback = weaker signal)
                pb_ratio = _calc_pullback_ratio(segments, current_price, buy=True)
                dyn_strength = 2.0 * (1.0 - pb_ratio * 0.5)  # 1.0-2.0 range
                signals.append({
                    'type': 'buy2',
                    'name': f'{level}级别第二类买点',
                    'price': current_price,
                    'confidence': 'medium',
                    'strength': round(dyn_strength, 2),
                    'description': f'反转确认(down→up) 回调不破前低 {prev_low.price:.2f}, 强度{dyn_strength:.1f}'
                })

    # ========== Sell Point 2 (第二类卖点) ==========
    # 缠论第21/32课：第二类卖点 = 第一类卖点确认后的第一次反弹不过前高
    # 新增: 段结构验证 (up→down反转) + 动态强度
    has_reversal = _check_reversal_structure(segments, direction='sell')
    if len(top_fractals) >= 2 and current_trend == 'down' and has_reversal:
        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]

        # 反弹不过前高（核心条件）
        if last_high.price < prev_high.price:
            distance = (last_high.price - current_price) / last_high.price
            if distance <= thresh['bsp2'] and distance >= thresh.get('min_distance', 0):
                pb_ratio = _calc_pullback_ratio(segments, current_price, buy=False)
                dyn_strength = 2.0 * (1.0 - pb_ratio * 0.5)
                signals.append({
                    'type': 'sell2',
                    'name': f'{level}级别第二类卖点',
                    'price': current_price,
                    'confidence': 'medium',
                    'strength': round(dyn_strength, 2),
                    'description': f'反转确认(up→down) 反弹不过前高 {prev_high.price:.2f}, 强度{dyn_strength:.1f}'
                })

    # ========== Buy Point 3 (第三类买点 - 中枢突破) ==========
    # 缠论定义（第18课）：中枢形成后，价格突破中枢上沿(ZG)，
    # 回调但不重新进入中枢（不跌破ZG），即为第三类买点
    if centers:
        for center in reversed(centers):
            # 只考虑已确认的中枢
            if not center.confirmed:
                continue

            # 检查当前价格是否在ZG之上（已经突破）
            if current_price <= center.zg:
                continue

            # 检查是否有离开段（突破段）
            exit_info = CenterDetector().detect_center_entry_exit(center, segments)
            exit_seg = exit_info.get('exit_segment')

            if exit_seg is None:
                continue

            # 检查突破的幅度（离开段是否明显）
            exit_direction = exit_seg.direction
            breakout_pct = (current_price - center.zg) / center.zg

            # 上涨走势中，突破中枢上沿
            if exit_direction == 'up' and breakout_pct > 0:
                # 检查是否已经回踩但没进中枢
                # 回踩幅度不能太大（超过bsp3_pct意味着可能趋势反转）
                pullback_pct = (current_price - center.zg) / center.zg
                if pullback_pct > 0 and pullback_pct < thresh['bsp3_pct']:
                    # Strength: deeper pullback = weaker signal, shallower = stronger
                    # Formula: 3.0 * (1 - pullback_pct/threshold), capped at [0.5, 5.0]
                    bsp3_strength = 3.0 * (1.0 - pullback_pct / thresh['bsp3_pct'])
                    bsp3_strength = max(0.5, min(bsp3_strength, 5.0))
                    signals.append({
                        'type': 'buy3',
                        'name': f'{level}级别第三类买点 (中枢突破)',
                        'price': current_price,
                        'confidence': 'high' if pullback_pct < thresh['bsp3_pct'] * 0.5 else 'medium',
                        'strength': round(bsp3_strength, 2),
                        'description': f'突破中枢ZG={center.zg:.2f}, 当前回踩 {current_price:.2f} (未进中枢)'
                    })
                break  # Only use the most recent center

    # ========== Sell Point 3 (第三类卖点 - 中枢跌破) ==========
    # 缠论定义：中枢形成后，价格跌破中枢下沿(ZD)，
    # 反弹但不重新进入中枢（不突破ZD），即为第三类卖点
    if centers:
        for center in reversed(centers):
            if not center.confirmed:
                continue

            # 检查当前价格是否在ZD之下（已经跌破）
            if current_price >= center.zd:
                continue

            # 检查是否有离开段
            exit_info = CenterDetector().detect_center_entry_exit(center, segments)
            exit_seg = exit_info.get('exit_segment')

            if exit_seg is None:
                continue

            exit_direction = exit_seg.direction
            breakdown_pct = (center.zd - current_price) / center.zd

            # 下跌走势中，跌破中枢下沿
            if exit_direction == 'down' and breakdown_pct > 0:
                pullback_pct = (center.zd - current_price) / center.zd
                if pullback_pct > 0 and pullback_pct < thresh['bsp3_pct']:
                    bsp3_strength = 3.0 * (1.0 - pullback_pct / thresh['bsp3_pct'])
                    bsp3_strength = max(0.5, min(bsp3_strength, 5.0))
                    signals.append({
                        'type': 'sell3',
                        'name': f'{level}级别第三类卖点 (中枢跌破)',
                        'price': current_price,
                        'confidence': 'high' if pullback_pct < thresh['bsp3_pct'] * 0.5 else 'medium',
                        'strength': round(bsp3_strength, 2),
                        'description': f'跌破中枢ZD={center.zd:.2f}, 当前反弹 {current_price:.2f} (未进中枢)'
                    })
                break

    # ========== 信号互斥检查 ==========
    # 缠论原理：同一级别同一时间只能有一个主导趋势
    buy_signals = [s for s in signals if s['type'].startswith('buy')]
    sell_signals = [s for s in signals if s['type'].startswith('sell')]

    if buy_signals and sell_signals:
        # 计算各自信号强度
        buy_strength = sum(s.get('strength', 1.0) for s in buy_signals)
        sell_strength = sum(s.get('strength', 1.0) for s in sell_signals)

        # 只保留更强的一方
        if buy_strength >= sell_strength:
            signals = buy_signals
        else:
            signals = sell_signals

        print(f"    ⚠️ 买卖点冲突检测：保留 {'买点' if buy_strength >= sell_strength else '卖点'} (买:{buy_strength:.1f} vs 卖:{sell_strength:.1f})")

    return {'signals': signals, 'divergence': div_tracking}


def load_alert_state():
    """Load alert state with atomic read."""
    if os.path.exists(ALERT_STATE_FILE):
        try:
            with open(ALERT_STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            # Corrupted state file — start fresh
            print(f"    ⚠️ Alert state file corrupted, resetting")
    return {"alerts": {}}


def save_alert_state(state):
    """Save alert state with atomic write (tempfile + rename, zero corruption risk)."""
    try:
        dir_path = os.path.dirname(ALERT_STATE_FILE)
        os.makedirs(dir_path, exist_ok=True)
        # Write to temp file, then atomically rename
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, prefix=".alert_state_tmp_")
        with os.fdopen(fd, 'w') as f:
            json.dump(state, f, indent=2, default=str)
            f.flush()
            os.fsync(fd)
        os.replace(tmp_path, ALERT_STATE_FILE)
    except Exception as e:
        print(f"⚠️ Failed to save alert state: {e}")


def should_send_alert(symbol: str, signal_type: str, level: str, current_price: float) -> bool:
    """
    Check if alert should be sent (防重复警报检查)
    
    Returns True if:
    - First alert for this signal
    - Price changed significantly (> MIN_PRICE_CHANGE)
    - Silence period has passed
    """
    state = load_alert_state()
    now = datetime.now()
    
    # Create unique key for this signal
    key = f"{symbol}:{signal_type}:{level}"
    
    if key in state["alerts"]:
        last_alert = state["alerts"][key]
        last_price = last_alert.get("price", 0)
        last_time = datetime.fromisoformat(last_alert["time"])
        
        # Check price change
        price_change = abs(current_price - last_price) / last_price if last_price > 0 else 0
        if price_change < MIN_PRICE_CHANGE:
            print(f"    ⏭️ Skip: 价格变化 {price_change*100:.2f}% < {MIN_PRICE_CHANGE*100:.1f}% 阈值")
            return False
        
        # Check silence period
        minutes_since = (now - last_time).total_seconds() / 60
        if minutes_since < SILENCE_PERIOD_MINUTES:
            print(f"    ⏭️ Skip: 静默期剩余 {SILENCE_PERIOD_MINUTES - minutes_since:.0f} 分钟")
            return False
        
        print(f"    ✅ 价格变化 {price_change*100:.2f}% > {MIN_PRICE_CHANGE*100:.1f}%，允许警报")
    
    return True


def update_alert_state(symbol: str, signal_type: str, level: str, price: float):
    """Update alert state after sending"""
    state = load_alert_state()
    key = f"{symbol}:{signal_type}:{level}"
    
    state["alerts"][key] = {
        "price": price,
        "time": datetime.now().isoformat(),
        "symbol": symbol,
        "signal_type": signal_type,
        "level": level
    }
    
    # Cleanup old alerts (older than 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    keys_to_remove = []
    for k, v in state["alerts"].items():
        try:
            alert_time = datetime.fromisoformat(v["time"])
            if alert_time < cutoff:
                keys_to_remove.append(k)
        except:
            pass
    
    for k in keys_to_remove:
        del state["alerts"][k]
    
    save_alert_state(state)


def send_telegram_alert(symbol: str, signals: list, level: str, fusion_info: dict = None):
    """Send Telegram alert with multi-level fusion info"""
    if not signals:
        return

    for signal in signals:
        signal_type = signal['type'].replace(' (背驰)', '').replace(' (顶背驰)', '').replace(' (中枢突破)', '').replace(' (中枢跌破)', '')
        if not should_send_alert(symbol, signal_type, level, signal['price']):
            continue

        emoji = {
            'buy1': '🟢',
            'buy2': '🟢',
            'buy3': '🟢',
            'sell1': '🔴',
            'sell2': '🔴',
            'sell3': '🔴'
        }.get(signal['type'].split()[0], '⚪')

        type_label = {
            'buy1': '第一类买点 (底背驰)',
            'buy2': '第二类买点',
            'buy3': '第三类买点 (中枢突破)',
            'sell1': '第一类卖点 (顶背驰)',
            'sell2': '第二类卖点',
            'sell3': '第三类卖点 (中枢跌破)'
        }.get(signal['type'], signal['type'])

        # Use USD prefix instead of $ to avoid shell variable expansion
        price_str = f"USD {signal['price']:.2f}"

        # Build multi-level fusion section
        fusion_text = ""
        if fusion_info:
            overall = fusion_info.get('overall', 'N/A')
            strength = fusion_info.get('total_strength', 0)
            levels_detail = fusion_info.get('levels_detail', [])
            fusion_text = f"\n📊 多级别联动：{overall} (强度:{strength:.1f})\n"
            if levels_detail:
                for ld in levels_detail:
                    fusion_text += f"  {ld.get('level','?')}: "
                    fusion_text += f"{'🟢' if ld.get('direction') == 'up' else '🔴'}{ld.get('direction','?')} "
                    fusion_text += f"({ld.get('signals', 0)}个信号)\n"

        message = f"""{emoji} {symbol} 缠论买卖点提醒

📊 信号：{type_label}
💰 价格：{price_str}
🎯 置信度：{signal['confidence']}
📝 说明：{signal['description']}
{fusion_text}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
级别：{level}"""

        # Log to file
        with open(ALERT_LOG, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {emoji} {symbol} {type_label} @ {price_str}\n")

        # Send Telegram message via Telegram Bot API (migrated from OpenClaw)
        try:
            if TELEGRAM_BOT_TOKEN:
                # Direct Telegram Bot API call (stdlib only, no dependencies)
                import urllib.request
                import urllib.parse
                payload = urllib.parse.urlencode({
                    'chat_id': TELEGRAM_CHAT_ID,
                    'text': message,
                    'parse_mode': 'HTML'
                }).encode()
                url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
                req = urllib.request.Request(url, data=payload)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"✅ Telegram alert sent: {symbol} {signal['type']}")
                        update_alert_state(symbol, signal_type, level, signal['price'])
                    else:
                        print(f"⚠️ Telegram send failed: HTTP {resp.status}")
            else:
                print(f"⚠️ TELEGRAM_BOT_TOKEN not set. Alert logged but not sent.")
                update_alert_state(symbol, signal_type, level, signal['price'])
        except Exception as e:
            print(f"❌ Error sending alert via Telegram API: {e}")
            # Fallback: still record the alert so we don't keep retrying
            print(f"    (Alert recorded to state but may not have been delivered)")
    else:
        # No signals sent - log fusion summary if available
        if fusion_info and fusion_info.get('overall') not in ('N/A', 'HOLD'):
            with open(ALERT_LOG, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {symbol} multi-level: {fusion_info['overall']} ({fusion_info['total_strength']:.1f})\n")


def analyze_symbol(symbol_config):
    """Analyze a single symbol across all levels with multi-level fusion"""
    symbol = symbol_config['symbol']
    name = symbol_config['name']
    levels = symbol_config['levels']

    print(f"\n{'='*60}")
    print(f"📊 {symbol} ({name})")
    print(f"{'='*60}")

    all_signals = []
    level_results = {}  # For multi-level fusion

    for level in levels:
        print(f"\n  [{level}] Analyzing...")

        # Fetch data
        series = fetch_yahoo_data(symbol, level, count=100)
        if series is None:
            print(f"    ❌ No data")
            continue

        # Detect fractals
        fractal_det = FractalDetector()
        fractals = fractal_det.detect_all(series)
        top_fractals = [f for f in fractals if f.is_top]
        bottom_fractals = [f for f in fractals if not f.is_top]

        # Detect pens
        pen_calc = PenCalculator(PenConfig(
            use_new_definition=True,
            strict_validation=True,
            min_klines_between_turns=3
        ))
        pens = pen_calc.identify_pens(series)

        # Detect segments
        seg_calc = SegmentCalculator(min_pens=3)
        segments = seg_calc.detect_segments(pens)

        # Detect centers (中枢) for Buy3/Sell3 detection
        center_det = CenterDetector(min_segments=3)
        centers = center_det.detect_centers(segments)
        # Also detect extension
        centers = center_det.detect_center_extension(centers)

        # Calculate MACD
        prices = [k.close for k in series.klines]
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        macd_data = macd.calculate(prices)

        # Detect buy/sell points (with center info for Buy3/Sell3)
        bsp_result = detect_buy_sell_points(series, fractals, pens, segments, macd_data, level, centers)
        signals = bsp_result['signals']
        div_track = bsp_result.get('divergence', {})

        # Include divergence tracking in level results for multi-level fusion
        div_bullish = div_track.get('bullish_score', 0.0)
        div_bearish = div_track.get('bearish_score', 0.0)
        if div_bullish > 0:
            print(f"    🟡 底背驰预警(无中枢): 得分={div_bullish:.1f}")
        if div_bearish > 0:
            print(f"    🔶 顶背驰预警(无中枢): 得分={div_bearish:.1f}")

        # Detect segment trend for multi-level fusion
        segment_trend = 'neutral'
        if len(segments) >= 1:
            segment_trend = segments[-1].direction

        # Store level results
        level_results[level] = {
            'signals': signals,
            'fractals': len(fractals),
            'pens': len(pens),
            'segments': len(segments),
            'centers': len(centers),
            'segment_trend': segment_trend
        }

        print(f"    分型：{len(fractals)} (顶：{len(top_fractals)}, 底：{len(bottom_fractals)})")
        print(f"    笔：{len(pens)}")
        print(f"    线段：{len(segments)}")
        print(f"    中枢：{len(centers)}")
        if centers:
            for ci, c in enumerate(centers):
                print(f"      中枢{ci+1}: ZG={c.zg:.2f}, ZD={c.zd:.2f}, 区间={c.range:.2f}")
        print(f"    买卖点：{len(signals)}")

        if signals:
            for sig in signals:
                print(f"      🎯 {sig['type']}: {sig['name']} @ USD {sig['price']:.2f}")
            all_signals.extend(signals)

    # ========== Multi-level fusion scoring ==========
    fusion_info = None
    if len(level_results) >= 1:
        # Weighted scoring across timeframes
        weights = {
            '5m':  {'direction': 1.0, 'signal': 2.0},
            '30m': {'direction': 2.0, 'signal': 3.0},
            '1d':  {'direction': 3.0, 'signal': 5.0}
        }
        total_strength = 0.0
        levels_detail = []

        for level, lr in level_results.items():
            w = weights.get(level, {'direction': 1.0, 'signal': 2.0})
            level_score = 0.0

            # Segment direction score
            if lr['segment_trend'] == 'up':
                level_score += w['direction']
            elif lr['segment_trend'] == 'down':
                level_score -= w['direction']

            # Signal score
            for sig in lr['signals']:
                sig_strength = sig.get('strength', 1.0)
                if sig['type'].startswith('buy'):
                    level_score += w['signal'] * sig_strength
                else:
                    level_score -= w['signal'] * sig_strength

            total_strength += level_score
            levels_detail.append({
                'level': level,
                'direction': lr['segment_trend'],
                'signals': len(lr['signals']),
                'score': level_score
            })

            print(f"\n    [{level}] 多级别评分: {level_score:+.1f} "
                  f"(方向:{w['direction']}x{lr['segment_trend']}, "
                  f"信号:{w['signal']}x{len(lr['signals'])})")

        # Determine overall signal
        if total_strength >= 6.0:
            overall = "STRONG_BUY"
        elif total_strength >= 3.0:
            overall = "BUY"
        elif total_strength <= -6.0:
            overall = "STRONG_SELL"
        elif total_strength <= -3.0:
            overall = "SELL"
        else:
            overall = "HOLD"

        fusion_info = {
            'overall': overall,
            'total_strength': total_strength,
            'levels_detail': levels_detail
        }
        print(f"\n  === 多级别联动信号: {overall} (总强度: {total_strength:+.1f}) ===")

    # Send alerts with fusion info
    if all_signals:
        send_telegram_alert(symbol, all_signals, levels[0], fusion_info)
    elif fusion_info and fusion_info['overall'] != 'HOLD':
        # Log fusion-only signal even without per-level signals
        print(f"\n  📊 融合信号: {fusion_info['overall']} (强度: {fusion_info['total_strength']:+.1f})")
        send_telegram_alert(symbol, [], levels[0], fusion_info)

    return all_signals


def main():
    """Main monitoring loop"""
    print(f"\n{'='*70}")
    print(f"缠论智能监控系统 - ChanLun Invester")
    print(f"{'='*70}")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控标的：{len(SYMBOLS)}")
    print(f"Telegram: {TELEGRAM_CHAT_ID}")
    print(f"{'='*70}")
    
    total_signals = 0
    
    for symbol_config in SYMBOLS:
        signals = analyze_symbol(symbol_config)
        total_signals += len(signals)
    
    print(f"\n{'='*70}")
    print(f"监控完成")
    print(f"{'='*70}")
    print(f"总信号数：{total_signals}")
    print(f"日志文件：{ALERT_LOG}")
    print(f"下次检查：15 分钟后")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
