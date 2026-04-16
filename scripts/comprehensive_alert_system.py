#!/usr/bin/env python3
"""
全方位股票预警系统
Comprehensive Stock Alert System

整合三大维度：
1. 基本面分析 (Fundamental Analysis)
2. 行业新闻监控 (Industry News Monitoring)
3. 缠论技术分析 (ChanLun Technical Analysis)

适用于：高波动、行业敏感型股票的全方位监控
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import yfinance as yf
import requests
from enhanced_confidence_analyzer import (
    EnhancedConfidenceAnalyzer,
    EnhancedConfidence,
    STOCK_SECTOR_MAP,
    IndustrySector,
    SECTOR_ETF_MAP
)

sys.path.insert(0, str(Path(__file__).parent / "python-layer"))


# ==================== 配置 ====================

TELEGRAM_CHAT_ID = "8365377574"
ALERT_LOG = "/home/wei/.openclaw/workspace/chanlunInvester/alerts.log"
NEWS_CACHE_DIR = "/home/wei/.openclaw/workspace/chanlunInvester/cache/news"
FUNDAMENTAL_CACHE_DIR = "/home/wei/.openclaw/workspace/chanlunInvester/cache/fundamental"

# 预警阈值配置
ALERT_THRESHOLDS = {
    'fundamental_score': 0.6,      # 基本面得分阈值
    'news_sentiment': 0.3,         # 新闻情绪阈值
    'chanlun_confidence': 0.65,    # 缠论置信度阈值
    'combined_score': 0.7,         # 综合得分阈值
}

# 监控股票池
MONITOR_STOCKS = [
    # 量子计算
    {'symbol': 'IONQ', 'name': 'IonQ Inc', 'sector': 'quantum_computing', 'priority': 'high'},
    {'symbol': 'RGTI', 'name': 'Rigetti Computing', 'sector': 'quantum_computing', 'priority': 'medium'},
    {'symbol': 'QBTS', 'name': 'D-Wave Quantum', 'sector': 'quantum_computing', 'priority': 'medium'},
    
    # 航天国防
    {'symbol': 'RKLB', 'name': 'Rocket Lab USA', 'sector': 'aerospace', 'priority': 'high'},
    {'symbol': 'SMR', 'name': 'NuScale Power', 'sector': 'clean_energy', 'priority': 'high'},
    
    # 清洁能源
    {'symbol': 'ENPH', 'name': 'Enphase Energy', 'sector': 'clean_energy', 'priority': 'medium'},
    {'symbol': 'FSLR', 'name': 'First Solar', 'sector': 'clean_energy', 'priority': 'medium'},
    
    # 半导体
    {'symbol': 'INTC', 'name': 'Intel Corporation', 'sector': 'semiconductor', 'priority': 'high'},
    {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': 'ai_ml', 'priority': 'high'},
    
    # 生物科技
    {'symbol': 'MRNA', 'name': 'Moderna Inc', 'sector': 'biotech', 'priority': 'medium'},
]


# ==================== 数据结构 ====================

class AlertLevel(Enum):
    """警报级别"""
    CRITICAL = "critical"  # _critical_ 级别：重大机会/风险
    HIGH = "high"          # 高级别：强烈关注
    MEDIUM = "medium"      # 中级别：值得关注
    LOW = "low"            # 低级别：观察为主
    INFO = "info"          # 信息级别：仅作通知


class AlertType(Enum):
    """警报类型"""
    FUNDAMENTAL_BREAKTHROUGH = "fundamental_breakthrough"  # 基本面突破
    FUNDAMENTAL_DETERIORATION = "fundamental_deterioration"  # 基本面恶化
    NEWS_BREAKTHROUGH = "news_breakthrough"  # 重大利好新闻
    NEWS_WARNING = "news_warning"  # 重大利空新闻
    CHANLUN_BUY = "chanlun_buy"  # 缠论买入信号
    CHANLUN_SELL = "chanlun_sell"  # 缠论卖出信号
    COMPREHENSIVE_BUY = "comprehensive_buy"  # 综合买入信号
    COMPREHENSIVE_SELL = "comprehensive_sell"  # 综合卖出信号
    SECTOR_ROTATION = "sector_rotation"  # 行业轮动信号


@dataclass
class FundamentalAlert:
    """基本面警报"""
    symbol: str
    alert_type: str
    title: str
    description: str
    score: float
    key_metrics: Dict
    timestamp: datetime
    level: AlertLevel = AlertLevel.MEDIUM


@dataclass
class NewsAlert:
    """新闻警报"""
    symbol: str
    alert_type: str
    title: str
    description: str
    sentiment: float
    news_count: int
    key_news: List[Dict]
    timestamp: datetime
    level: AlertLevel = AlertLevel.MEDIUM


@dataclass
class ChanLunAlert:
    """缠论警报"""
    symbol: str
    alert_type: str
    signal_type: str  # buy1, buy2, sell1, sell2
    level: str  # 5m, 30m, 1d
    price: float
    confidence: float
    enhanced_confidence: Optional[float]
    timestamp: datetime
    level: AlertLevel = AlertLevel.MEDIUM


@dataclass
class ComprehensiveAlert:
    """综合警报"""
    symbol: str
    alert_type: AlertType
    title: str
    description: str
    
    # 三大维度得分
    fundamental_score: float
    news_sentiment_score: float
    chanlun_score: float
    
    # 综合得分
    combined_score: float
    
    # 详细数据
    fundamental_data: Optional[Dict] = None
    news_data: Optional[Dict] = None
    chanlun_data: Optional[Dict] = None
    
    # 操作建议
    action: str = "observe"  # buy, sell, observe, avoid
    position_size: str = "none"  # full, normal, light, none
    stop_loss: Optional[str] = None
    
    timestamp: datetime = field(default_factory=datetime.now)
    level: AlertLevel = AlertLevel.MEDIUM


# ==================== 基本面监控 ====================

class FundamentalMonitor:
    """基本面监控器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = timedelta(hours=1)
    
    def check_breakthrough(self, symbol: str, name: str) -> Optional[FundamentalAlert]:
        """检查基本面突破"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            alerts = []
            
            # 检查营收增长突破
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth and revenue_growth > 0.5:  # >50% 增长
                alerts.append(FundamentalAlert(
                    symbol=symbol,
                    alert_type='revenue_breakthrough',
                    title=f"📈 {name} 营收增长突破",
                    description=f"营收增长率达 {revenue_growth:.1%}，远超行业平均",
                    score=0.8 + min(revenue_growth, 1.0) * 0.2,
                    key_metrics={'revenue_growth': revenue_growth},
                    timestamp=datetime.now(),
                    level=AlertLevel.HIGH if revenue_growth > 0.8 else AlertLevel.MEDIUM
                ))
            
            # 检查毛利率突破
            gross_margin = info.get('grossMargins', 0)
            if gross_margin and gross_margin > 0.7:  # >70% 毛利率
                alerts.append(FundamentalAlert(
                    symbol=symbol,
                    alert_type='margin_breakthrough',
                    title=f"💰 {name} 毛利率突破",
                    description=f"毛利率达 {gross_margin:.1%}，显示强大定价权",
                    score=0.75 + gross_margin * 0.25,
                    key_metrics={'gross_margin': gross_margin},
                    timestamp=datetime.now(),
                    level=AlertLevel.MEDIUM
                ))
            
            # 检查机构持股突破
            institutional = info.get('institutionalOwnership', 0)
            if institutional and institutional > 0.8:  # >80% 机构持股
                alerts.append(FundamentalAlert(
                    symbol=symbol,
                    alert_type='institutional_breakthrough',
                    title=f"🏦 {name} 机构持股突破",
                    description=f"机构持股达 {institutional:.1%}，获专业投资者高度认可",
                    score=0.7 + institutional * 0.3,
                    key_metrics={'institutional_ownership': institutional},
                    timestamp=datetime.now(),
                    level=AlertLevel.MEDIUM
                ))
            
            # 检查现金流恶化
            total_cash = info.get('totalCash', 0)
            total_debt = info.get('totalDebt', 0)
            if total_debt > 0 and total_cash / total_debt < 0.3:  # 现金比率<0.3
                alerts.append(FundamentalAlert(
                    symbol=symbol,
                    alert_type='cash_warning',
                    title=f"⚠️ {name} 现金流预警",
                    description=f"现金比率仅 {total_cash/total_debt:.2f}，需关注流动性风险",
                    score=0.3,
                    key_metrics={'cash_ratio': total_cash/total_debt},
                    timestamp=datetime.now(),
                    level=AlertLevel.HIGH
                ))
            
            return alerts if alerts else None
            
        except Exception as e:
            print(f"⚠️ Fundamental monitor error for {symbol}: {e}")
            return None
    
    def get_fundamental_score(self, symbol: str) -> float:
        """获取基本面综合得分"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            score = 0.5  # 基础分
            
            # 营收增长 (30%)
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth:
                score += min(max(revenue_growth, -0.5), 1.0) * 0.3
            
            # 毛利率 (25%)
            gross_margin = info.get('grossMargins', 0)
            if gross_margin:
                score += gross_margin * 0.25
            
            # 机构持股 (20%)
            institutional = info.get('institutionalOwnership', 0)
            score += institutional * 0.2
            
            # 现金比率 (15%)
            total_cash = info.get('totalCash', 0)
            total_debt = info.get('totalDebt', 0)
            if total_debt > 0:
                cash_ratio = total_cash / total_debt
                score += min(cash_ratio, 2.0) / 2.0 * 0.15
            else:
                score += 0.15  # 无负债
            
            # 市值规模 (10%)
            market_cap = info.get('marketCap', 0)
            if market_cap > 100e9:
                score += 0.1
            elif market_cap > 10e9:
                score += 0.05
            
            return min(max(score, 0), 1)
            
        except Exception as e:
            print(f"⚠️ Get fundamental score error for {symbol}: {e}")
            return 0.5


# ==================== 新闻监控 ====================

class NewsMonitor:
    """新闻监控器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = timedelta(minutes=15)
    
    def analyze_news(self, symbol: str, name: str) -> Optional[NewsAlert]:
        """分析新闻并生成警报"""
        try:
            stock = yf.Ticker(symbol)
            news = stock.news or []
            
            if not news:
                return None
            
            # 分析 24 小时新闻
            now = datetime.now()
            news_24h = []
            sentiment_sum = 0.0
            key_news = []
            
            positive_keywords = [
                'beat', 'upgrade', 'growth', 'gain', 'surge', 'rally', 'bullish',
                'positive', 'strong', 'record', 'breakthrough', 'partnership', 'deal',
                'announce', 'launch', 'approve', 'success', 'win', 'contract', 'award'
            ]
            negative_keywords = [
                'miss', 'downgrade', 'loss', 'drop', 'plunge', 'crash', 'bearish',
                'negative', 'weak', 'warning', 'lawsuit', 'investigation', 'delay',
                'recall', 'fail', 'reject', 'cut', 'probe', 'fine', 'penalty'
            ]
            
            for item in news:
                provider_publish_time = item.get('providerPublishTime', 0)
                news_time = datetime.fromtimestamp(provider_publish_time) if provider_publish_time else None
                
                if news_time and (now - news_time).total_seconds() < 86400:  # 24 小时内
                    news_24h.append(item)
                    title = item.get('title', '').lower()
                    
                    # 情绪分析
                    sentiment = 0.0
                    for word in positive_keywords:
                        if word in title:
                            sentiment += 0.15
                    for word in negative_keywords:
                        if word in title:
                            sentiment -= 0.15
                    
                    sentiment = min(max(sentiment, -1), 1)
                    sentiment_sum += sentiment
                    
                    # 重大新闻标记
                    if abs(sentiment) >= 0.3:
                        key_news.append({
                            'title': item.get('title', ''),
                            'publisher': item.get('publisher', ''),
                            'sentiment': sentiment,
                            'link': item.get('link', '')
                        })
            
            if not news_24h:
                return None
            
            avg_sentiment = sentiment_sum / len(news_24h)
            
            # 生成警报
            alerts = []
            
            # 重大利好
            if avg_sentiment > 0.3 or len([n for n in key_news if n['sentiment'] > 0.3]) >= 2:
                alerts.append(NewsAlert(
                    symbol=symbol,
                    alert_type='news_breakthrough',
                    title=f"📰 {name} 重大利好新闻",
                    description=f"24 小时内 {len(news_24h)} 条新闻，平均情绪 {avg_sentiment:.2f}",
                    sentiment=avg_sentiment,
                    news_count=len(news_24h),
                    key_news=key_news,
                    timestamp=datetime.now(),
                    level=AlertLevel.HIGH if avg_sentiment > 0.5 else AlertLevel.MEDIUM
                ))
            
            # 重大利空
            if avg_sentiment < -0.3 or len([n for n in key_news if n['sentiment'] < -0.3]) >= 2:
                alerts.append(NewsAlert(
                    symbol=symbol,
                    alert_type='news_warning',
                    title=f"⚠️ {name} 重大利空新闻",
                    description=f"24 小时内 {len(news_24h)} 条新闻，平均情绪 {avg_sentiment:.2f}",
                    sentiment=avg_sentiment,
                    news_count=len(news_24h),
                    key_news=key_news,
                    timestamp=datetime.now(),
                    level=AlertLevel.HIGH if avg_sentiment < -0.5 else AlertLevel.MEDIUM
                ))
            
            # 新闻爆发 (数量异常)
            if len(news_24h) > 20:
                alerts.append(NewsAlert(
                    symbol=symbol,
                    alert_type='news_surge',
                    title=f"🔥 {name} 新闻爆发",
                    description=f"24 小时内 {len(news_24h)} 条新闻，远超正常水平",
                    sentiment=avg_sentiment,
                    news_count=len(news_24h),
                    key_news=key_news,
                    timestamp=datetime.now(),
                    level=AlertLevel.MEDIUM
                ))
            
            return alerts if alerts else None
            
        except Exception as e:
            print(f"⚠️ News monitor error for {symbol}: {e}")
            return None
    
    def get_news_sentiment_score(self, symbol: str) -> float:
        """获取新闻情绪得分"""
        try:
            stock = yf.Ticker(symbol)
            news = stock.news or []
            
            if not news:
                return 0.5
            
            now = datetime.now()
            sentiment_sum = 0.0
            count = 0
            
            positive_keywords = ['beat', 'upgrade', 'growth', 'gain', 'surge', 'rally', 'bullish', 'positive', 'strong']
            negative_keywords = ['miss', 'downgrade', 'loss', 'drop', 'plunge', 'crash', 'bearish', 'negative', 'weak']
            
            for item in news:
                provider_publish_time = item.get('providerPublishTime', 0)
                news_time = datetime.fromtimestamp(provider_publish_time) if provider_publish_time else None
                
                if news_time and (now - news_time).total_seconds() < 86400:
                    title = item.get('title', '').lower()
                    sentiment = 0.0
                    
                    for word in positive_keywords:
                        if word in title:
                            sentiment += 0.1
                    for word in negative_keywords:
                        if word in title:
                            sentiment -= 0.1
                    
                    sentiment_sum += min(max(sentiment, -1), 1)
                    count += 1
            
            if count == 0:
                return 0.5
            
            # 归一化到 0-1
            avg_sentiment = sentiment_sum / count
            return 0.5 + avg_sentiment * 0.5
            
        except Exception as e:
            print(f"⚠️ Get news sentiment error for {symbol}: {e}")
            return 0.5


# ==================== 缠论信号监控 ====================

class ChanLunMonitor:
    """缠论信号监控器"""
    
    def __init__(self):
        self.enhanced_analyzer = EnhancedConfidenceAnalyzer()
    
    def analyze_signal(self, symbol: str, signal_type: str, 
                      chanlun_confidence: float, price: float,
                      level: str) -> ChanLunAlert:
        """分析缠论信号并生成警报"""
        
        # 使用增强置信度分析
        enhanced = self.enhanced_analyzer.analyze(symbol, signal_type, chanlun_confidence)
        
        # 确定警报级别
        if enhanced.final_confidence >= 0.85:
            alert_level = AlertLevel.CRITICAL
        elif enhanced.final_confidence >= 0.70:
            alert_level = AlertLevel.HIGH
        elif enhanced.final_confidence >= 0.55:
            alert_level = AlertLevel.MEDIUM
        else:
            alert_level = AlertLevel.LOW
        
        # 确定信号方向
        is_buy = 'buy' in signal_type.lower()
        alert_type = AlertType.CHANLUN_BUY if is_buy else AlertType.CHANLUN_SELL
        
        return ChanLunAlert(
            symbol=symbol,
            alert_type=alert_type.value,
            signal_type=signal_type,
            level=level,
            price=price,
            confidence=chanlun_confidence,
            enhanced_confidence=enhanced.final_confidence,
            timestamp=datetime.now(),
            level=alert_level
        )


# ==================== 综合预警引擎 ====================

class ComprehensiveAlertEngine:
    """综合预警引擎"""
    
    def __init__(self):
        self.fundamental_monitor = FundamentalMonitor()
        self.news_monitor = NewsMonitor()
        self.chanlun_monitor = ChanLunMonitor()
    
    def evaluate_comprehensive(self, symbol: str, name: str, sector: str,
                              chanlun_signal: Optional[Dict] = None) -> List[ComprehensiveAlert]:
        """综合评估并生成警报"""
        alerts = []
        
        # 获取三大维度数据
        fundamental_score = self.fundamental_monitor.get_fundamental_score(symbol)
        news_score = self.news_monitor.get_news_sentiment_score(symbol)
        chanlun_score = chanlun_signal.get('confidence', 0.5) if chanlun_signal else 0.5
        
        # 检查是否有缠论信号
        if chanlun_signal:
            enhanced_confidence = self._calculate_enhanced_confidence(
                symbol, chanlun_signal['type'], chanlun_score
            )
            
            # 综合得分计算
            combined_score = (
                fundamental_score * 0.35 +
                news_score * 0.25 +
                enhanced_confidence * 0.40
            )
            
            # 生成综合警报
            is_buy = 'buy' in chanlun_signal['type'].lower()
            alert_type = AlertType.COMPREHENSIVE_BUY if is_buy else AlertType.COMPREHENSIVE_SELL
            
            # 确定操作建议
            if combined_score >= 0.8:
                action = "strong_buy" if is_buy else "strong_sell"
                position = "full"
                alert_level = AlertLevel.CRITICAL
            elif combined_score >= 0.7:
                action = "buy" if is_buy else "sell"
                position = "normal"
                alert_level = AlertLevel.HIGH
            elif combined_score >= 0.55:
                action = "light_buy" if is_buy else "light_sell"
                position = "light"
                alert_level = AlertLevel.MEDIUM
            else:
                action = "observe"
                position = "none"
                alert_level = AlertLevel.LOW
            
            alerts.append(ComprehensiveAlert(
                symbol=symbol,
                alert_type=alert_type,
                title=f"{'🟢' if is_buy else '🔴'} {name} 综合{'买入' if is_buy else '卖出'}信号",
                description=f"综合得分 {combined_score:.0f}% (基本面{fundamental_score:.0f}% + 新闻{news_score:.0f}% + 技术{enhanced_confidence:.0f}%)",
                fundamental_score=fundamental_score,
                news_sentiment_score=news_score,
                chanlun_score=enhanced_confidence,
                combined_score=combined_score,
                fundamental_data={'score': fundamental_score},
                news_data={'score': news_score},
                chanlun_data=chanlun_signal,
                action=action,
                position_size=position,
                timestamp=datetime.now(),
                level=alert_level
            ))
        
        return alerts
    
    def _calculate_enhanced_confidence(self, symbol: str, signal_type: str, 
                                       base_confidence: float) -> float:
        """计算增强置信度"""
        try:
            enhanced = self.enhanced_analyzer.analyze(symbol, signal_type, base_confidence)
            return enhanced.final_confidence
        except:
            return base_confidence


# ==================== 警报推送 ====================

def format_comprehensive_alert(alert: ComprehensiveAlert) -> str:
    """格式化综合警报消息"""
    icons = {
        AlertLevel.CRITICAL: '🚨',
        AlertLevel.HIGH: '🔴',
        AlertLevel.MEDIUM: '🟡',
        AlertLevel.LOW: '🔵',
        AlertLevel.INFO: '⚪'
    }
    
    icon = icons.get(alert.level, '⚪')
    
    action_emoji = {
        'strong_buy': '💰',
        'buy': '🟢',
        'light_buy': '📈',
        'observe': '👀',
        'light_sell': '📉',
        'sell': '🔴',
        'strong_sell': '💸'
    }
    
    message = f"""{icon} {alert.symbol} {alert.title}

📊 综合得分：{alert.combined_score:.0f}%
   基本面：{alert.fundamental_score:.0f}% (权重 35%)
   新闻面：{alert.news_sentiment_score:.0f}% (权重 25%)
   技术面：{alert.chanlun_score:.0f}% (权重 40%)

💡 操作建议:
{action_emoji.get(alert.action, '⚪')} 策略：{alert.action.upper()}
📈 仓位：{alert.position_size}
⏰ 时间：{alert.timestamp.strftime('%Y-%m-%d %H:%M')}

─────────────────────────────
⚠️ 投资有风险，决策需谨慎
"""
    
    return message


def send_alert(alert: ComprehensiveAlert):
    """发送警报"""
    message = format_comprehensive_alert(alert)
    
    # 记录日志
    with open(ALERT_LOG, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {alert.level.value.upper()} - {alert.symbol} - {alert.title}\n")
    
    # 发送 Telegram
    try:
        env = os.environ.copy()
        env['PATH'] = '/home/linuxbrew/.linuxbrew/bin:' + env.get('PATH', '')
        safe_message = message.replace("'", "'\"'\"'")
        cmd = f"/home/wei/openclaw/openclaw message send --target 'telegram:{TELEGRAM_CHAT_ID}' -m '{safe_message}'"
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, env=env)
        
        if result.returncode == 0:
            print(f"✅ Alert sent: {alert.symbol} {alert.alert_type.value}")
        else:
            print(f"⚠️ Telegram send failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error sending alert: {e}")


# ==================== 主监控循环 ====================

def run_comprehensive_monitor():
    """运行综合监控系统"""
    print("=" * 60)
    print("全方位股票预警系统 - Comprehensive Stock Alert System")
    print("=" * 60)
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控标的：{len(MONITOR_STOCKS)} 只")
    print("=" * 60)
    
    engine = ComprehensiveAlertEngine()
    
    for stock in MONITOR_STOCKS:
        symbol = stock['symbol']
        name = stock['name']
        sector = stock['sector']
        priority = stock['priority']
        
        print(f"\n📊 分析：{symbol} ({name})")
        print(f"   行业：{sector} | 优先级：{priority}")
        
        # 获取基本面得分
        fundamental_score = engine.fundamental_monitor.get_fundamental_score(symbol)
        print(f"   基本面得分：{fundamental_score:.2f}")
        
        # 获取新闻情绪
        news_score = engine.news_monitor.get_news_sentiment_score(symbol)
        print(f"   新闻情绪：{news_score:.2f}")
        
        # 检查基本面警报
        fundamental_alerts = engine.fundamental_monitor.check_breakthrough(symbol, name)
        if fundamental_alerts:
            for alert in fundamental_alerts:
                print(f"   ⚠️ 基本面警报：{alert.title}")
        
        # 检查新闻警报
        news_alerts = engine.news_monitor.analyze_news(symbol, name)
        if news_alerts:
            for alert in news_alerts:
                print(f"   ⚠️ 新闻警报：{alert.title}")
        
        # 模拟缠论信号 (实际应从 monitor_all.py 获取)
        # 这里仅做演示
        if fundamental_score > 0.7 and news_score > 0.6:
            # 基本面和新闻面都好，假设有缠论买入信号
            chanlun_signal = {
                'type': 'buy1_divergence',
                'confidence': 0.75,
                'price': 0,  # 实际应从监控系统获取
                'level': '30m'
            }
            
            comprehensive_alerts = engine.evaluate_comprehensive(
                symbol, name, sector, chanlun_signal
            )
            
            for alert in comprehensive_alerts:
                if alert.level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
                    print(f"   🚨 综合警报：{alert.title}")
                    send_alert(alert)
    
    print("\n" + "=" * 60)
    print("监控完成")
    print("=" * 60)


if __name__ == "__main__":
    run_comprehensive_monitor()
