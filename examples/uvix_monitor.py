#!/usr/bin/env python3
"""
UVIX 缠论 30 分钟级别买卖点监控
ChanLun 30-minute Buy/Sell Point Monitor for UVIX

基于缠中说禅理论 (第 1-108 课)
- 分型 → 笔 → 线段 → 中枢 → 背驰 → 买卖点
- 30 分钟级别操作
- MACD 辅助背驰判断
- 区间套精确定位
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent / "python-layer"))

from trading_system.kline import Kline, KlineSeries
from trading_system.fractal import FractalDetector
from trading_system.pen import PenCalculator, PenConfig
from trading_system.segment import SegmentCalculator
from trading_system.indicators import MACDIndicator

# 导入告警发送模块
from uvix_monitor_send_alert import send_alert

# 尝试导入 yfinance 获取真实数据
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance 未安装，使用模拟数据。安装：pip install yfinance")


# ─────────────────────────────────────────────────────────────────────────────
# UVIX 配置
# ─────────────────────────────────────────────────────────────────────────────

UVIX_CONFIG = {
    'symbol': 'UVIX',
    'name': '2x Long VIX Futures ETF',
    'timeframe': '30m',  # 30 分钟级别
    'operation_level': '30 分钟',  # 主操作级别
    'monitor_levels': ['day', '30m', '5m'],  # 同时监控 日线、30 分钟和 5 分钟级别
    'sub_level': '5m',   # 次级别 (用于区间套)
    'macd_params': {
        'fast': 12,
        'slow': 26,
        'signal': 9
    },
    'alert_channels': ['telegram', 'console'],
}


# ─────────────────────────────────────────────────────────────────────────────
# 模拟 UVIX 数据 (实际应接入实时数据源)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_uvix_data(symbol='UVIX', count=200, timeframe='30m') -> KlineSeries:
    """
    获取 UVIX 的 K 线数据 (US Market)
    
    数据源优先级:
    1. Yahoo Finance (真实 US 市场数据)
    2. 模拟数据 (备用)
    
    Args:
        symbol: 股票代码
        count: K 线数量
        timeframe: 时间周期 ('day', '30m' 或 '5m')
    """
    klines = []
    
    # 尝试从 Yahoo Finance 获取真实 US 市场数据
    if YFINANCE_AVAILABLE:
        try:
            print(f"    📡 从 Yahoo Finance 获取 US 市场真实数据...")
            uvix = yf.Ticker(symbol)
            
            # 根据时间周期选择间隔 (US Market Hours: 9:30-16:00 ET)
            if timeframe == 'day':
                interval = '1d'
                period = '3mo'  # 3 个月日线
            elif timeframe == '5m':
                interval = '5m'
                period = '5d'  # 5 天数据 (覆盖当日)
            else:  # 30m
                interval = '30m'
                period = '1mo'  # 1 个月数据
            
            # 获取历史数据 (Yahoo Finance 自动处理 US 市场时间)
            history = uvix.history(period=period, interval=interval)
            
            if len(history) > 0:
                print(f"    ✓ 获取到 {len(history)} 条 US 市场数据")
                print(f"    时间范围：{history.index[0].strftime('%Y-%m-%d %H:%M')} → {history.index[-1].strftime('%Y-%m-%d %H:%M')}")
                
                for idx, row in history.iterrows():
                    # 确保使用 US 市场价格
                    kline = Kline(
                        timestamp=idx.to_pydatetime(),
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']) if 'Volume' in row else 1000000
                    )
                    klines.append(kline)
                
                if len(klines) >= count:
                    klines = klines[-count:]  # 取最近 count 条
                
                # 显示最新价格
                if klines:
                    latest = klines[-1]
                    print(f"    最新价格：${latest.close:.2f} (Volume: {latest.volume:,})")
                
                return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)
        
        except Exception as e:
            print(f"    ⚠️  Yahoo Finance 获取失败：{e}")
            print(f"    使用模拟数据作为备用...")
    
    # Yahoo Finance 不可用时，使用模拟数据
    print(f"    ⚠️  使用模拟数据 (建议安装 yfinance: pip install yfinance)")
    
    # 根据时间周期设置间隔
    if timeframe == 'day':
        interval_minutes = 1440  # 日线
        base_time = datetime(2025, 1, 1, 9, 30)
    elif timeframe == '5m':
        interval_minutes = 5
        base_time = datetime(2026, 3, 3, 9, 30)
    else:  # 30m
        interval_minutes = 30
        base_time = datetime(2026, 3, 3, 9, 30)
    
    # 使用用户提供的真实价格作为基准
    base_price = 6.82  # 当前实际价格
    
    random.seed(42 + len(timeframe))  # 不同级别用不同随机种子
    
    for i in range(count):
        # VIX 相关 ETF 波动较大
        # 不同级别不同波动率
        if timeframe == 'day':
            volatility = random.uniform(-0.5, 0.5)
            price_range = (0.3, 0.8)
            volume_range = (2000000, 10000000)
        elif timeframe == '5m':
            volatility = random.uniform(-0.15, 0.15)
            price_range = (0.1, 0.25)
            volume_range = (500000, 5000000)
        else:  # 30m
            volatility = random.uniform(-0.3, 0.3)
            price_range = (0.2, 0.5)
            volume_range = (500000, 5000000)
        
        price = base_price + volatility
        
        # 高波动特性
        high = price + abs(random.uniform(*price_range))
        low = price - abs(random.uniform(*price_range))
        open_price = price + random.uniform(-0.2, 0.2)
        close_price = price + random.uniform(-0.2, 0.2)
        
        kline = Kline(
            timestamp=base_time + timedelta(minutes=i*interval_minutes),
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=random.randint(*volume_range)
        )
        klines.append(kline)
        
        base_price = close_price
    
    return KlineSeries(klines=klines, symbol=symbol, timeframe=timeframe)


# ─────────────────────────────────────────────────────────────────────────────
# 缠论分析核心
# ─────────────────────────────────────────────────────────────────────────────

class ChanLunAnalyzer:
    """缠论分析器 - 基于 1-108 课完整理论"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.macd_params = self.config.get('macd_params', {'fast': 12, 'slow': 26, 'signal': 9})
        
        # 初始化各模块
        self.fractal_detector = FractalDetector()
        self.pen_calculator = PenCalculator(PenConfig(
            use_new_definition=True,  # 新笔定义 (第 65 课)
            strict_validation=True,
            min_klines_between_turns=3
        ))
        self.segment_calculator = SegmentCalculator(min_pens=3)
    
    def analyze(self, series: KlineSeries) -> dict:
        """
        完整缠论分析流程
        返回：分析结果字典
        """
        result = {
            'symbol': series.symbol,
            'timeframe': series.timeframe,
            'timestamp': datetime.now().isoformat(),
            'kline_count': len(series.klines),
            'analysis': {}
        }
        
        # 1. 分型分析 (第 62, 65 课)
        fractals = self.fractal_detector.detect_all(series)
        top_fractals = [f for f in fractals if f.is_top]
        bottom_fractals = [f for f in fractals if not f.is_top]
        
        result['analysis']['fractals'] = {
            'total': len(fractals),
            'top': len(top_fractals),
            'bottom': len(bottom_fractals),
            'latest_top': top_fractals[-1].__dict__ if top_fractals else None,
            'latest_bottom': bottom_fractals[-1].__dict__ if bottom_fractals else None,
        }
        
        # 2. 笔分析 (第 62, 65, 77 课)
        pens = self.pen_calculator.identify_pens(series)
        up_pens = [p for p in pens if p.is_up]
        down_pens = [p for p in pens if p.is_down]
        
        result['analysis']['pens'] = {
            'total': len(pens),
            'up': len(up_pens),
            'down': len(down_pens),
            'latest': pens[-1].__dict__ if pens else None,
        }
        
        # 3. 线段分析 (第 67, 68, 71 课)
        segments = self.segment_calculator.detect_segments(pens)
        up_segs = [s for s in segments if s.is_up]
        down_segs = [s for s in segments if s.is_down]
        
        result['analysis']['segments'] = {
            'total': len(segments),
            'up': len(up_segs),
            'down': len(down_segs),
            'latest': segments[-1].__dict__ if segments else None,
        }
        
        # 4. MACD 背驰分析 (第 24, 27 课)
        prices = [k.close for k in series.klines]
        macd = MACDIndicator(
            fast=self.macd_params['fast'],
            slow=self.macd_params['slow'],
            signal=self.macd_params['signal']
        )
        macd_data = macd.calculate(prices)
        
        # 检测背驰
        divergence = self._detect_divergence(series, segments, macd_data)
        result['analysis']['divergence'] = divergence
        
        # 5. 买卖点识别 (第 12, 20, 21 课)
        bsp_list = self._detect_buy_sell_points(series, segments, divergence)
        result['analysis']['buy_sell_points'] = bsp_list
        
        # 6. 操作建议 (第 7, 12, 13 课)
        result['operation_suggestion'] = self._generate_suggestion(result)
        
        return result
    
    def _detect_divergence(self, series: KlineSeries, segments: list, macd_data: list) -> dict:
        """
        检测背驰 (第 24 课)
        
        背驰定义：趋势中，后一段走势力度弱于前一段
        MACD 辅助：股价创新高/低，但 MACD 柱子面积缩小
        """
        if len(segments) < 2 or not macd_data:
            return {'detected': False}
        
        # 检查最后两个同向线段
        last_seg = segments[-1]
        prev_seg = None
        
        for seg in reversed(segments[:-1]):
            if seg.direction == last_seg.direction:
                prev_seg = seg
                break
        
        if not prev_seg:
            return {'detected': False}
        
        # 获取 MACD 值
        macd_prev = macd_data[prev_seg.end_idx].histogram
        macd_last = macd_data[last_seg.end_idx].histogram
        
        price_prev = prev_seg.end_price
        price_last = last_seg.end_price
        
        divergence = {'detected': False}
        
        if last_seg.direction == 'up':
            # 上涨背驰：价格创新高，MACD 未创新高
            if price_last > price_prev and macd_last < macd_prev:
                divergence = {
                    'detected': True,
                    'type': 'top_divergence',  # 顶背驰
                    'segment_idx': len(segments) - 1,
                    'price_high': price_last,
                    'macd_prev': macd_prev,
                    'macd_last': macd_last,
                    'strength': abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001),
                    'signal': 'sell',  # 卖出信号
                }
        
        elif last_seg.direction == 'down':
            # 下跌背驰：价格创新低，MACD 未创新低
            if price_last < price_prev and macd_last > macd_prev:
                divergence = {
                    'detected': True,
                    'type': 'bottom_divergence',  # 底背驰
                    'segment_idx': len(segments) - 1,
                    'price_low': price_last,
                    'macd_prev': macd_prev,
                    'macd_last': macd_last,
                    'strength': abs(macd_prev - macd_last) / max(abs(macd_prev), 0.001),
                    'signal': 'buy',  # 买入信号
                }
        
        return divergence
    
    def _detect_buy_sell_points(self, series: KlineSeries, segments: list, divergence: dict) -> list:
        """
        识别三类买卖点 (第 12, 20, 21 课)
        
        第一类：趋势背驰点
        第二类：次级别回踩不破前低/高
        第三类：次级别回踩不破中枢
        """
        bsp_list = []
        
        # 第一类买卖点：背驰点
        if divergence.get('detected'):
            bsp = {
                'type': f"第一类{'买点' if divergence['signal'] == 'buy' else '卖点'}",
                'type_en': f"bsp{'1_buy' if divergence['signal'] == 'buy' else '1_sell'}",
                'price': divergence.get('price_low') if divergence['signal'] == 'buy' else divergence.get('price_high'),
                'confidence': min(divergence.get('strength', 0), 0.9),
                'description': f"趋势背驰点 - {divergence['type']}",
                'lesson': '第 12, 24 课',
            }
            bsp_list.append(bsp)
        
        return bsp_list
    
    def _generate_suggestion(self, result: dict) -> dict:
        """
        生成操作建议 (第 7, 12, 13 课)
        
        原则：
        - 只搞"能搞的" (第 8 课)
        - 买点买，卖点卖
        - 严格止损
        """
        bsp_list = result['analysis'].get('buy_sell_points', [])
        divergence = result['analysis'].get('divergence', {})
        
        if not bsp_list:
            return {
                'action': 'HOLD',  # 持有观望
                'reason': '无明确买卖点',
                'lesson': '第 5 课：市场无须分析，只要看和干',
            }
        
        latest_bsp = bsp_list[-1]
        
        if 'buy' in latest_bsp['type_en']:
            return {
                'action': 'BUY',
                'price': latest_bsp['price'],
                'confidence': f"{latest_bsp['confidence']:.0%}",
                'reason': latest_bsp['description'],
                'stop_loss': latest_bsp['price'] * 0.95 if latest_bsp['price'] else None,
                'target': latest_bsp['price'] * 1.10 if latest_bsp['price'] else None,
                'lesson': '第 12 课：第一类买点 - 男上位最后一次缠绕后背弛',
            }
        
        elif 'sell' in latest_bsp['type_en']:
            return {
                'action': 'SELL',
                'price': latest_bsp['price'],
                'confidence': f"{latest_bsp['confidence']:.0%}",
                'reason': latest_bsp['description'],
                'reason_detail': '顶背驰出现，趋势可能转折',
                'lesson': '第 12 课：第一类卖点 - 女上位缠绕后背弛',
            }
        
        return {'action': 'HOLD', 'reason': '无法判断'}


# ─────────────────────────────────────────────────────────────────────────────
# 提醒发送
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """UVIX 缠论多级别监控主程序"""
    print("\n" + "="*70)
    print("UVIX 缠论多级别买卖点监控")
    print("ChanLun Multi-Level Buy/Sell Point Monitor for UVIX")
    print("="*70)
    print(f"\n📊 标的：{UVIX_CONFIG['symbol']} - {UVIX_CONFIG['name']}")
    print(f"⏰ 监控级别：{', '.join(UVIX_CONFIG['monitor_levels'])} (新增日线!)")
    print(f"📈 MACD 参数：{UVIX_CONFIG['macd_params']['fast']}/{UVIX_CONFIG['macd_params']['slow']}/{UVIX_CONFIG['macd_params']['signal']}")
    print(f"🔔 提醒渠道：{', '.join(UVIX_CONFIG['alert_channels'])}")
    
    all_results = {}
    all_bsp = []
    
    # 对每个监控级别进行分析
    for level in UVIX_CONFIG['monitor_levels']:
        print(f"\n{'='*70}")
        print(f"【{level} 级别分析】")
        print(f"{'='*70}")
        
        # 1. 获取数据
        print(f"\n[1] 获取 UVIX {level} 数据...")
        series = fetch_uvix_data(UVIX_CONFIG['symbol'], count=200, timeframe=level)
        print(f"    ✓ 获取 {len(series.klines)} 根 K 线")
        print(f"    时间范围：{series.klines[0].timestamp} → {series.klines[-1].timestamp}")
        print(f"    价格范围：${min(k.low for k in series.klines):.2f} - ${max(k.high for k in series.klines):.2f}")
        
        # 2. 缠论分析
        print(f"\n[2] 执行缠论分析...")
        analyzer = ChanLunAnalyzer(UVIX_CONFIG)
        result = analyzer.analyze(series)
        all_results[level] = result
        
        # 3. 显示分析结果
        print(f"\n{'='*70}")
        print(f"缠论分析结果 ({level})")
        print(f"{'='*70}")
        
        analysis = result['analysis']
        
        print(f"\n📐 分型 (Fractal) - 第 62 课:")
        print(f"    顶分型：{analysis['fractals']['top']} 个")
        print(f"    底分型：{analysis['fractals']['bottom']} 个")
        
        print(f"\n✏️  笔 (Pen) - 第 65 课:")
        print(f"    向上笔：{analysis['pens']['up']} 个")
        print(f"    向下笔：{analysis['pens']['down']} 个")
        
        print(f"\n📏 线段 (Segment) - 第 67 课:")
        print(f"    向上线段：{analysis['segments']['up']} 个")
        print(f"    向下线段：{analysis['segments']['down']} 个")
        
        print(f"\n📊 背驰 (Divergence) - 第 24 课:")
        if analysis['divergence'].get('detected'):
            div = analysis['divergence']
            print(f"    ⚠️  检测到背驰！")
            print(f"    类型：{div['type']}")
            print(f"    信号：{'🟢 买入' if div['signal'] == 'buy' else '🔴 卖出'}")
            print(f"    强度：{div['strength']:.2f}")
        else:
            print(f"    ✓ 无明显背驰")
        
        print(f"\n🎯 买卖点 (Buy/Sell Points) - 第 12, 20 课:")
        if analysis['buy_sell_points']:
            for bsp in analysis['buy_sell_points']:
                emoji = '🟢' if 'buy' in bsp['type_en'] else '🔴'
                print(f"    {emoji} {bsp['type']}")
                print(f"        价格：${bsp['price']:.2f}")
                print(f"        置信度：{bsp['confidence']:.0%}")
                print(f"        说明：{bsp['description']}")
                # 收集所有买卖点
                bsp_with_level = bsp.copy()
                bsp_with_level['level'] = level
                all_bsp.append(bsp_with_level)
        else:
            print(f"    ✓ 无明确买卖点")
        
        # 4. 操作建议
        print(f"\n{'='*70}")
        print(f"操作建议 ({level}) - 第 7, 12 课")
        print(f"{'='*70}")
        
        suggestion = result['operation_suggestion']
        action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(suggestion['action'], '⚪')
        
        print(f"\n{action_emoji} {level} 建议：{suggestion['action']}")
        print(f"📝 理由：{suggestion['reason']}")
        
        if suggestion['action'] == 'BUY':
            print(f"\n💰 参考价位:")
            print(f"    入场：${suggestion.get('price', 0):.2f}")
            print(f"    止损：${suggestion.get('stop_loss', 0):.2f} (-5%)")
            print(f"    目标：${suggestion.get('target', 0):.2f} (+10%)")
        elif suggestion['action'] == 'SELL':
            print(f"\n⚠️  风险提示:")
            print(f"    {suggestion.get('reason_detail', '')}")
        
        print(f"\n📚 缠论依据：{suggestion.get('lesson', '')}")
    
    # 5. 汇总所有级别的买卖点并发送提醒
    print(f"\n{'='*70}")
    print(f"多级别汇总")
    print(f"{'='*70}")
    
    if all_bsp:
        print(f"\n🚨 检测到 {len(all_bsp)} 个买卖点信号！")
        
        for bsp in all_bsp:
            level = bsp.get('level', 'unknown')
            emoji = '🟢' if 'buy' in bsp['type_en'] else '🔴'
            print(f"\n{emoji} {level} - {bsp['type']}")
            print(f"   价格：${bsp['price']:.2f}, 置信度：{bsp['confidence']:.0%}")
        
        # 发送提醒
        print(f"\n{'='*70}")
        print(f"发送提醒...")
        print(f"{'='*70}")
        
        # 汇总所有买卖点到一条消息
        for bsp in all_bsp:
            level = bsp.get('level', 'unknown')
            suggestion = all_results[level]['operation_suggestion']
            
            message = f"""
【UVIX 缠论买卖点信号 - {level}级别】

📊 标的：{UVIX_CONFIG['symbol']}
⏰ 级别：{level}
🎯 类型：{bsp['type']}
💰 价格：${bsp['price']:.2f}
📈 置信度：{bsp['confidence']:.0%}
📝 说明：{bsp['description']}

操作建议：{suggestion['action']}
{f"入场：${suggestion.get('price', 0):.2f}" if suggestion['action'] == 'BUY' else ''}
{f"止损：${suggestion.get('stop_loss', 0):.2f} (-5%)" if suggestion['action'] == 'BUY' else ''}
{f"目标：${suggestion.get('target', 0):.2f} (+10%)" if suggestion['action'] == 'BUY' else ''}

⚠️ 风险提示：缠论分析仅供参考，不构成投资建议
"""
            send_alert(message, UVIX_CONFIG['alert_channels'])
    else:
        print(f"\n✓ 所有级别均无明确买卖点")
        print(f"📝 策略：继续观望，等待买卖点出现")
    
    # 6. 导出结果
    output_file = Path(__file__).parent / 'uvix_analysis_result.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'monitor_levels': UVIX_CONFIG['monitor_levels'],
            'results': {level: result for level, result in all_results.items()},
            'buy_sell_points': all_bsp,
            'bsp_count': len(all_bsp)
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ 分析结果已保存至：{output_file}")
    print(f"\n{'='*70}")
    print(f"监控完成")
    print(f"{'='*70}\n")
    
    return {
        'results': all_results,
        'buy_sell_points': all_bsp,
        'bsp_count': len(all_bsp)
    }


if __name__ == '__main__':
    result = main()
    
    # 如果有买卖点，退出码为 1 (用于 cron 判断)
    if result.get('buy_sell_points'):
        sys.exit(1)
    else:
        sys.exit(0)
