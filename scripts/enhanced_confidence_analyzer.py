#!/usr/bin/env python3
"""
高波动股票行业趋势与基本面量化指标系统
Industry Trend & Fundamental Quantitative Indicators for High-Volatility Stocks

适用于：量子计算、AI、生物科技、新能源等高波动、行业敏感型股票

核心指标：
1. 行业趋势指标 (Industry Trend)
2. 基本面强度指标 (Fundamental Strength)
3. 消息面情绪指标 (Sentiment)
4. 资金流指标 (Capital Flow)
5. 波动率调整指标 (Volatility-Adjusted)

综合置信度 = 缠论信号 × 行业趋势 × 基本面 × 消息面
"""

import json
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import yfinance as yf
import requests


# ==================== 数据结构 ====================

class IndustrySector(Enum):
    """行业分类"""
    QUANTUM_COMPUTING = "quantum_computing"  # 量子计算
    AI_ML = "ai_ml"  # AI/机器学习
    BIOTECH = "biotech"  # 生物科技
    CLEAN_ENERGY = "clean_energy"  # 清洁能源
    SEMICONDUCTOR = "semiconductor"  # 半导体
    AEROSPACE = "aerospace"  # 航天
    TRADITIONAL = "traditional"  # 传统行业


@dataclass
class IndustryTrendData:
    """行业趋势数据"""
    sector: IndustrySector
    sector_etf_change_1d: float = 0.0  # 行业 ETF 日涨跌
    sector_etf_change_5d: float = 0.0  # 行业 ETF 5 日涨跌
    sector_etf_change_20d: float = 0.0  # 行业 ETF 20 日涨跌
    relative_strength: float = 1.0  # 相对强度 (个股/行业)
    trend_score: float = 0.5  # 趋势得分 (0-1)


@dataclass
class FundamentalData:
    """基本面数据"""
    market_cap: float = 0.0  # 市值
    pe_ratio: Optional[float] = None  # 市盈率
    ps_ratio: Optional[float] = None  # 市销率
    revenue_growth: Optional[float] = None  # 营收增长率
    gross_margin: Optional[float] = None  # 毛利率
    cash_ratio: Optional[float] = None  # 现金比率
    debt_to_equity: Optional[float] = None  # 负债权益比
    fundamental_score: float = 0.5  # 基本面得分 (0-1)


@dataclass
class SentimentData:
    """消息面情绪数据"""
    news_count_24h: int = 0  # 24 小时新闻数量
    news_sentiment: float = 0.0  # 新闻情绪 (-1 到 1)
    social_mentions: int = 0  # 社交媒体提及
    analyst_upgrades_7d: int = 0  # 7 天内分析师上调
    analyst_downgrades_7d: int = 0  # 7 天内分析师下调
    sentiment_score: float = 0.5  # 情绪得分 (0-1)


@dataclass
class CapitalFlowData:
    """资金流数据"""
    volume_ratio: float = 1.0  # 成交量比率 (当日/平均)
    institutional_ownership: float = 0.0  # 机构持股比例
    insider_trading_30d: float = 0.0  # 内部交易净额 (30 天)
    short_interest: float = 0.0  # 空头比例
    flow_score: float = 0.5  # 资金流得分 (0-1)


@dataclass
class VolatilityData:
    """波动率数据"""
    atr_14d: float = 0.0  # 14 日平均真实波幅
    historical_volatility_30d: float = 0.0  # 30 日历史波动率
    implied_volatility: Optional[float] = None  # 隐含波动率 (如有期权)
    beta: float = 1.0  # Beta 系数
    volatility_adjustment: float = 1.0  # 波动率调整系数


@dataclass
class EnhancedConfidence:
    """增强置信度"""
    chanlun_signal: str  # 缠论信号类型
    chanlun_confidence: float  # 缠论原始置信度
    industry_weight: float = 0.25  # 行业趋势权重
    fundamental_weight: float = 0.25  # 基本面权重
    sentiment_weight: float = 0.20  # 情绪权重
    capital_flow_weight: float = 0.15  # 资金流权重
    volatility_weight: float = 0.15  # 波动率权重
    
    industry_score: float = 0.5  # 行业得分
    fundamental_score: float = 0.5  # 基本面得分
    sentiment_score: float = 0.5  # 情绪得分
    capital_flow_score: float = 0.5  # 资金流得分
    volatility_adjustment: float = 1.0  # 波动率调整
    
    # 计算结果
    weighted_score: float = 0.0  # 加权得分
    final_confidence: float = 0.0  # 最终置信度
    reliability_level: str = "medium"  # 可靠性等级


# ==================== 行业分类配置 ====================

# 股票 - 行业映射
STOCK_SECTOR_MAP = {
    'IONQ': IndustrySector.QUANTUM_COMPUTING,
    'RGTI': IndustrySector.QUANTUM_COMPUTING,
    'QBTS': IndustrySector.QUANTUM_COMPUTING,
    'NVDA': IndustrySector.AI_ML,
    'AMD': IndustrySector.AI_ML,
    'GOOG': IndustrySector.AI_ML,
    'MSFT': IndustrySector.AI_ML,
    'MRNA': IndustrySector.BIOTECH,
    'BNTX': IndustrySector.BIOTECH,
    'CRSP': IndustrySector.BIOTECH,
    'ENPH': IndustrySector.CLEAN_ENERGY,
    'SEDG': IndustrySector.CLEAN_ENERGY,
    'FSLR': IndustrySector.CLEAN_ENERGY,
    'TSLA': IndustrySector.CLEAN_ENERGY,
    'INTC': IndustrySector.SEMICONDUCTOR,
    'TSM': IndustrySector.SEMICONDUCTOR,
    'ASML': IndustrySector.SEMICONDUCTOR,
    'LRCX': IndustrySector.SEMICONDUCTOR,
    'RKLB': IndustrySector.AEROSPACE,
    'BA': IndustrySector.AEROSPACE,
    'LMT': IndustrySector.AEROSPACE,
}

# 行业 ETF 映射
SECTOR_ETF_MAP = {
    IndustrySector.QUANTUM_COMPUTING: 'QTUM',  # Defiance Quantum ETF
    IndustrySector.AI_ML: 'AIQ',  # Global X AI & Tech ETF
    IndustrySector.BIOTECH: 'IBB',  # iShares Biotechnology ETF
    IndustrySector.CLEAN_ENERGY: 'ICLN',  # iShares Clean Energy ETF
    IndustrySector.SEMICONDUCTOR: 'SMH',  # VanEck Semiconductor ETF
    IndustrySector.AEROSPACE: 'ITA',  # iShares U.S. Aerospace & Defense ETF
    IndustrySector.TRADITIONAL: 'SPY',  # S&P 500 ETF
}


# ==================== 指标计算 ====================

class IndustryTrendAnalyzer:
    """行业趋势分析器"""
    
    def __init__(self):
        self._etf_cache = {}
        self._cache_timeout = timedelta(minutes=30)
    
    def get_sector_etf(self, sector: IndustrySector) -> str:
        """获取行业 ETF 代码"""
        return SECTOR_ETF_MAP.get(sector, 'SPY')
    
    def analyze(self, symbol: str, sector: IndustrySector) -> IndustryTrendData:
        """分析行业趋势"""
        etf_symbol = self.get_sector_etf(sector)
        
        try:
            # 获取行业 ETF 数据
            etf = yf.Ticker(etf_symbol)
            etf_hist = etf.history(period='1mo')
            
            # 获取个股数据
            stock = yf.Ticker(symbol)
            stock_hist = stock.history(period='1mo')
            
            if len(etf_hist) < 5 or len(stock_hist) < 5:
                return IndustryTrendData(sector=sector)
            
            # 计算 ETF 涨跌
            etf_close = etf_hist['Close'].values
            etf_change_1d = (etf_close[-1] - etf_close[-2]) / etf_close[-2] if len(etf_close) >= 2 else 0
            etf_change_5d = (etf_close[-1] - etf_close[-5]) / etf_close[-5] if len(etf_close) >= 5 else 0
            etf_change_20d = (etf_close[-1] - etf_close[0]) / etf_close[0] if len(etf_close) >= 20 else 0
            
            # 计算相对强度
            stock_close = stock_hist['Close'].values
            stock_change_20d = (stock_close[-1] - stock_close[0]) / stock_close[0] if len(stock_close) >= 20 else 0
            relative_strength = stock_change_20d / abs(etf_change_20d) if etf_change_20d != 0 else 1.0
            
            # 计算趋势得分
            trend_score = self._calculate_trend_score(etf_change_1d, etf_change_5d, etf_change_20d, relative_strength)
            
            return IndustryTrendData(
                sector=sector,
                sector_etf_change_1d=etf_change_1d,
                sector_etf_change_5d=etf_change_5d,
                sector_etf_change_20d=etf_change_20d,
                relative_strength=relative_strength,
                trend_score=trend_score
            )
            
        except Exception as e:
            print(f"⚠️ Industry trend analysis error for {symbol}: {e}")
            return IndustryTrendData(sector=sector)
    
    def _calculate_trend_score(self, change_1d: float, change_5d: float, 
                               change_20d: float, relative_strength: float) -> float:
        """计算趋势得分 (0-1)"""
        # 短期趋势 (1 日) - 权重 20%
        short_score = min(max(0.5 + change_1d * 10, 0), 1) * 0.2
        
        # 中期趋势 (5 日) - 权重 30%
        mid_score = min(max(0.5 + change_5d * 5, 0), 1) * 0.3
        
        # 长期趋势 (20 日) - 权重 30%
        long_score = min(max(0.5 + change_20d * 2, 0), 1) * 0.3
        
        # 相对强度 - 权重 20%
        rs_score = min(max(0.5 + (relative_strength - 1) * 0.2, 0), 1) * 0.2
        
        return short_score + mid_score + long_score + rs_score


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def analyze(self, symbol: str) -> FundamentalData:
        """分析基本面"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # 提取基本面数据
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE')
            ps_ratio = info.get('priceToBook')  # 用市净率替代市销率
            revenue_growth = info.get('revenueGrowth')
            gross_margin = info.get('grossMargins')
            
            # 计算现金比率
            total_cash = info.get('totalCash', 0)
            total_debt = info.get('totalDebt', 0)
            cash_ratio = total_cash / total_debt if total_debt > 0 else None
            
            # 负债权益比
            debt_to_equity = info.get('debtToEquity')
            
            # 计算基本面得分
            fundamental_score = self._calculate_fundamental_score(
                market_cap, pe_ratio, ps_ratio, revenue_growth, 
                gross_margin, cash_ratio, debt_to_equity
            )
            
            return FundamentalData(
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                ps_ratio=ps_ratio,
                revenue_growth=revenue_growth,
                gross_margin=gross_margin,
                cash_ratio=cash_ratio,
                debt_to_equity=debt_to_equity,
                fundamental_score=fundamental_score
            )
            
        except Exception as e:
            print(f"⚠️ Fundamental analysis error for {symbol}: {e}")
            return FundamentalData()
    
    def _calculate_fundamental_score(self, market_cap: float, pe_ratio: Optional[float],
                                     ps_ratio: Optional[float], revenue_growth: Optional[float],
                                     gross_margin: Optional[float], cash_ratio: Optional[float],
                                     debt_to_equity: Optional[float]) -> float:
        """计算基本面得分 (0-1)"""
        score = 0.5  # 基础分
        weights = 0.0
        
        # 市值评分 (大市值更稳定) - 权重 15%
        if market_cap > 0:
            if market_cap > 100e9:  # >1000 亿
                score += 0.15
            elif market_cap > 10e9:  # >100 亿
                score += 0.10
            elif market_cap > 1e9:  # >10 亿
                score += 0.05
            weights += 0.15
        
        # 营收增长评分 - 权重 25%
        if revenue_growth is not None:
            if revenue_growth > 0.5:  # >50% 增长
                score += 0.25
            elif revenue_growth > 0.2:  # >20% 增长
                score += 0.15
            elif revenue_growth > 0:  # 正增长
                score += 0.05
            elif revenue_growth < -0.2:  # <-20% 下滑
                score -= 0.15
            weights += 0.25
        
        # 毛利率评分 - 权重 20%
        if gross_margin is not None:
            if gross_margin > 0.7:  # >70%
                score += 0.20
            elif gross_margin > 0.5:  # >50%
                score += 0.12
            elif gross_margin > 0.3:  # >30%
                score += 0.05
            elif gross_margin < 0.1:  # <10%
                score -= 0.10
            weights += 0.20
        
        # 现金比率评分 - 权重 20%
        if cash_ratio is not None:
            if cash_ratio > 2:  # 现金充裕
                score += 0.20
            elif cash_ratio > 1:
                score += 0.10
            elif cash_ratio < 0.5:  # 现金紧张
                score -= 0.10
            weights += 0.20
        
        # 负债权益比评分 - 权重 20%
        if debt_to_equity is not None:
            if debt_to_equity < 0.3:  # 低负债
                score += 0.20
            elif debt_to_equity < 0.7:
                score += 0.10
            elif debt_to_equity > 2:  # 高负债
                score -= 0.15
            weights += 0.20
        
        # 归一化到 0-1
        return min(max(score, 0), 1)


class SentimentAnalyzer:
    """消息面情绪分析器"""
    
    def analyze(self, symbol: str) -> SentimentData:
        """分析消息面情绪"""
        try:
            # 获取新闻数据 (使用 yfinance 的新闻功能)
            stock = yf.Ticker(symbol)
            news = stock.news or []
            
            # 计算 24 小时新闻数量和情绪
            now = datetime.now()
            news_24h = []
            sentiment_sum = 0.0
            
            for item in news:
                provider_publish_time = item.get('providerPublishTime', 0)
                news_time = datetime.fromtimestamp(provider_publish_time) if provider_publish_time else None
                
                if news_time and (now - news_time).total_seconds() < 86400:  # 24 小时内
                    news_24h.append(item)
                    # 简单情绪分析 (基于标题关键词)
                    title = item.get('title', '').lower()
                    sentiment = self._analyze_title_sentiment(title)
                    sentiment_sum += sentiment
            
            news_count_24h = len(news_24h)
            news_sentiment = sentiment_sum / news_count_24h if news_count_24h > 0 else 0
            
            # 计算情绪得分
            sentiment_score = self._calculate_sentiment_score(
                news_count_24h, news_sentiment, 0, 0
            )
            
            return SentimentData(
                news_count_24h=news_count_24h,
                news_sentiment=news_sentiment,
                sentiment_score=sentiment_score
            )
            
        except Exception as e:
            print(f"⚠️ Sentiment analysis error for {symbol}: {e}")
            return SentimentData()
    
    def _analyze_title_sentiment(self, title: str) -> float:
        """分析标题情绪 (-1 到 1)"""
        positive_words = ['beat', 'upgrade', 'growth', 'gain', 'surge', 'rally', 'bullish', 
                         'positive', 'strong', 'record', 'breakthrough', 'partnership', 'deal']
        negative_words = ['miss', 'downgrade', 'loss', 'drop', 'plunge', 'crash', 'bearish',
                         'negative', 'weak', 'warning', 'lawsuit', 'investigation', 'delay']
        
        score = 0.0
        words = title.split()
        
        for word in words:
            if word in positive_words:
                score += 0.1
            elif word in negative_words:
                score -= 0.1
        
        return min(max(score, -1), 1)
    
    def _calculate_sentiment_score(self, news_count: int, news_sentiment: float,
                                   upgrades: int, downgrades: int) -> float:
        """计算情绪得分 (0-1)"""
        score = 0.5  # 基础分
        
        # 新闻数量评分 (适度关注是好事，过多可能是负面)
        if 5 <= news_count <= 20:
            score += 0.15
        elif news_count > 50:
            score -= 0.10  # 新闻过多可能是危机
        
        # 新闻情绪评分
        score += news_sentiment * 0.3
        
        # 分析师评级变化
        if upgrades > downgrades:
            score += 0.15
        elif downgrades > upgrades:
            score -= 0.15
        
        return min(max(score, 0), 1)


class CapitalFlowAnalyzer:
    """资金流分析器"""
    
    def analyze(self, symbol: str) -> CapitalFlowData:
        """分析资金流"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period='3mo')
            
            # 计算成交量比率
            volume = hist['Volume'].values
            avg_volume_30d = sum(volume[-30:]) / min(len(volume), 30) if len(volume) >= 30 else sum(volume) / len(volume)
            current_volume = volume[-1] if len(volume) > 0 else 0
            volume_ratio = current_volume / avg_volume_30d if avg_volume_30d > 0 else 1.0
            
            # 机构持股比例
            institutional_ownership = info.get('institutionalOwnership', 0.0)
            
            # 空头比例
            short_interest = info.get('shortPercentOfFloat', 0.0)
            
            # 计算资金流得分
            flow_score = self._calculate_flow_score(volume_ratio, institutional_ownership, short_interest)
            
            return CapitalFlowData(
                volume_ratio=volume_ratio,
                institutional_ownership=institutional_ownership,
                short_interest=short_interest,
                flow_score=flow_score
            )
            
        except Exception as e:
            print(f"⚠️ Capital flow analysis error for {symbol}: {e}")
            return CapitalFlowData()
    
    def _calculate_flow_score(self, volume_ratio: float, institutional_ownership: float,
                             short_interest: float) -> float:
        """计算资金流得分 (0-1)"""
        score = 0.5  # 基础分
        
        # 成交量比率评分 (放量上涨是好事)
        if 1.5 <= volume_ratio <= 3.0:
            score += 0.20  # 适度放量
        elif volume_ratio > 5.0:
            score -= 0.10  # 异常放量可能是出货
        elif volume_ratio < 0.5:
            score -= 0.10  # 缩量
        
        # 机构持股评分
        if institutional_ownership > 0.7:
            score += 0.20  # 机构高度认可
        elif institutional_ownership > 0.4:
            score += 0.10
        elif institutional_ownership < 0.1:
            score -= 0.10  # 机构不看好
        
        # 空头比例评分 (过高可能是风险)
        if short_interest > 0.2:
            score -= 0.20  # 空头比例过高
        elif short_interest > 0.1:
            score -= 0.10
        elif short_interest < 0.03:
            score += 0.10  # 空头很少
        
        return min(max(score, 0), 1)


class VolatilityAnalyzer:
    """波动率分析器"""
    
    def analyze(self, symbol: str) -> VolatilityData:
        """分析波动率"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='3mo')
            info = stock.info
            
            # 计算 ATR (14 日)
            high = hist['High'].values
            low = hist['Low'].values
            close = hist['Close'].values
            
            tr_list = []
            for i in range(1, min(15, len(close))):
                tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
                tr_list.append(tr)
            atr_14d = sum(tr_list) / len(tr_list) if tr_list else 0
            
            # 计算历史波动率 (30 日)
            if len(close) >= 30:
                returns = [(close[i] - close[i-1]) / close[i-1] for i in range(1, len(close))]
                import statistics
                historical_volatility_30d = statistics.stdev(returns[-30:]) * math.sqrt(252)  # 年化
            else:
                historical_volatility_30d = 0
            
            # Beta 系数
            beta = info.get('beta', 1.0)
            
            # 计算波动率调整系数
            volatility_adjustment = self._calculate_volatility_adjustment(
                atr_14d, historical_volatility_30d, beta
            )
            
            return VolatilityData(
                atr_14d=atr_14d,
                historical_volatility_30d=historical_volatility_30d,
                beta=beta,
                volatility_adjustment=volatility_adjustment
            )
            
        except Exception as e:
            print(f"⚠️ Volatility analysis error for {symbol}: {e}")
            return VolatilityData()
    
    def _calculate_volatility_adjustment(self, atr: float, hist_vol: float, beta: float) -> float:
        """计算波动率调整系数 (0.5-1.5)"""
        # 基础调整 (基于历史波动率)
        if hist_vol < 0.3:  # 低波动
            adjustment = 1.2  # 提高置信度
        elif hist_vol < 0.5:  # 中等波动
            adjustment = 1.0  # 不调整
        elif hist_vol < 0.8:  # 高波动
            adjustment = 0.8  # 降低置信度
        else:  # 极高波动
            adjustment = 0.6  # 大幅降低
        
        # Beta 调整
        if beta > 2.0:
            adjustment *= 0.9
        elif beta < 0.8:
            adjustment *= 1.1
        
        return min(max(adjustment, 0.5), 1.5)


# ==================== 主分析器 ====================

class EnhancedConfidenceAnalyzer:
    """增强置信度分析器"""
    
    def __init__(self):
        self.industry_analyzer = IndustryTrendAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.capital_flow_analyzer = CapitalFlowAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
    
    def analyze(self, symbol: str, chanlun_signal: str, chanlun_confidence: float) -> EnhancedConfidence:
        """分析增强置信度"""
        print(f"\n🔍 增强置信度分析：{symbol}")
        
        # 获取行业分类
        sector = STOCK_SECTOR_MAP.get(symbol, IndustrySector.TRADITIONAL)
        print(f"   行业：{sector.value}")
        
        # 分析各维度
        industry_data = self.industry_analyzer.analyze(symbol, sector)
        print(f"   行业趋势得分：{industry_data.trend_score:.2f}")
        
        fundamental_data = self.fundamental_analyzer.analyze(symbol)
        print(f"   基本面得分：{fundamental_data.fundamental_score:.2f}")
        
        sentiment_data = self.sentiment_analyzer.analyze(symbol)
        print(f"   情绪得分：{sentiment_data.sentiment_score:.2f}")
        
        capital_flow_data = self.capital_flow_analyzer.analyze(symbol)
        print(f"   资金流得分：{capital_flow_data.flow_score:.2f}")
        
        volatility_data = self.volatility_analyzer.analyze(symbol)
        print(f"   波动率调整：{volatility_data.volatility_adjustment:.2f}")
        
        # 创建结果对象
        result = EnhancedConfidence(
            chanlun_signal=chanlun_signal,
            chanlun_confidence=chanlun_confidence,
            industry_score=industry_data.trend_score,
            fundamental_score=fundamental_data.fundamental_score,
            sentiment_score=sentiment_data.sentiment_score,
            capital_flow_score=capital_flow_data.flow_score,
            volatility_adjustment=volatility_data.volatility_adjustment
        )
        
        # 计算加权得分
        result = self._calculate_weighted_score(result)
        
        # 确定可靠性等级
        result.reliability_level = self._determine_reliability_level(result.final_confidence)
        
        print(f"\n   最终置信度：{result.final_confidence:.2f} ({result.reliability_level})")
        
        return result
    
    def _calculate_weighted_score(self, result: EnhancedConfidence) -> EnhancedConfidence:
        """计算加权得分"""
        # 加权平均
        weighted_score = (
            result.industry_score * result.industry_weight +
            result.fundamental_score * result.fundamental_weight +
            result.sentiment_score * result.sentiment_weight +
            result.capital_flow_score * result.capital_flow_weight
        )
        
        # 应用波动率调整
        adjusted_score = weighted_score * result.volatility_adjustment
        
        # 与缠论原始置信度结合
        # 最终置信度 = 缠论置信度 × 增强系数
        enhancement_factor = 0.5 + adjusted_score  # 0.5-1.5
        final_confidence = result.chanlun_confidence * enhancement_factor
        
        result.weighted_score = weighted_score
        result.final_confidence = min(max(final_confidence, 0), 1)  # 限制在 0-1
        
        return result
    
    def _determine_reliability_level(self, confidence: float) -> str:
        """确定可靠性等级"""
        if confidence >= 0.85:
            return "very_high"  # 非常高
        elif confidence >= 0.70:
            return "high"  # 高
        elif confidence >= 0.55:
            return "medium"  # 中等
        elif confidence >= 0.40:
            return "low"  # 低
        else:
            return "very_low"  # 非常低
    
    def generate_report(self, result: EnhancedConfidence) -> str:
        """生成分析报告"""
        report = f"""
📊 增强置信度分析报告

🎯 缠论信号
   类型：{result.chanlun_signal}
   原始置信度：{result.chanlun_confidence:.0f}%

📈 行业趋势 (权重 {result.industry_weight:.0%})
   得分：{result.industry_score:.2f}
   贡献：{result.industry_score * result.industry_weight:.3f}

💰 基本面 (权重 {result.fundamental_weight:.0%})
   得分：{result.fundamental_score:.2f}
   贡献：{result.fundamental_score * result.fundamental_weight:.3f}

📰 消息面 (权重 {result.sentiment_weight:.0%})
   得分：{result.sentiment_score:.2f}
   贡献：{result.sentiment_score * result.sentiment_weight:.3f}

💵 资金流 (权重 {result.capital_flow_weight:.0%})
   得分：{result.capital_flow_score:.2f}
   贡献：{result.capital_flow_score * result.capital_flow_weight:.3f}

📊 波动率调整
   调整系数：{result.volatility_adjustment:.2f}

═══════════════════════════════════════
加权得分：{result.weighted_score:.3f}
最终置信度：{result.final_confidence:.0f}%
可靠性等级：{result.reliability_level.upper()}
═══════════════════════════════════════
"""
        return report


# ==================== 测试入口 ====================

if __name__ == "__main__":
    # 测试示例
    analyzer = EnhancedConfidenceAnalyzer()
    
    # 测试 IONQ
    result = analyzer.analyze("IONQ", "buy1_divergence", 0.75)
    print(analyzer.generate_report(result))
