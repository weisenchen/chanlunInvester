#!/usr/bin/env python3
"""
缠论数据下载模块 - ChanLun Data Downloader

支持多数据源、增量下载、本地缓存。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import sqlite3
from pathlib import Path
import hashlib


class DataSource:
    """数据源基类"""
    
    def fetch_klines(
        self,
        symbol: str,
        level: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        raise NotImplementedError


class YFinanceSource(DataSource):
    """Yahoo Finance 数据源"""
    
    def fetch_klines(
        self,
        symbol: str,
        level: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        try:
            import yfinance as yf
            
            # 映射级别到 yfinance 间隔
            interval_map = {
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '1d': '1d',
                '1w': '1wk',
                '1M': '1mo'
            }
            
            interval = interval_map.get(level, '1d')
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval)
            
            if df.empty:
                return pd.DataFrame()
            
            # 标准化列名
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"YFinance 错误：{e}")
            return pd.DataFrame()


class AKShareSource(DataSource):
    """AKShare A 股数据源"""
    
    def fetch_klines(
        self,
        symbol: str,
        level: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        try:
            import akshare as ak
            
            # A 股代码转换
            if symbol.endswith('.SZ') or symbol.endswith('.SH'):
                code = symbol.split('.')[0]
            else:
                code = symbol
            
            # 获取日线数据
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start.replace('-', ''),
                end_date=end.replace('-', ''),
                adjust="qfq"
            )
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"AKShare 错误：{e}")
            return pd.DataFrame()


class DataCache:
    """本地数据缓存 (SQLite + Parquet)"""
    
    def __init__(self, cache_dir: str = "./data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # SQLite 元数据
        self.db_path = self.cache_dir / "metadata.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                level TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_cache_key(self, symbol: str, level: str, start: str, end: str) -> str:
        """生成缓存键"""
        key_str = f"{symbol}:{level}:{start}:{end}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def get(self, symbol: str, level: str, start: str, end: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        cache_key = self._get_cache_key(symbol, level, start, end)
        parquet_file = self.cache_dir / f"{cache_key}.parquet"
        
        if parquet_file.exists():
            try:
                return pd.read_parquet(parquet_file)
            except Exception as e:
                print(f"缓存读取错误：{e}")
        
        return None
    
    def set(self, df: pd.DataFrame, symbol: str, level: str, start: str, end: str):
        """保存数据到缓存"""
        cache_key = self._get_cache_key(symbol, level, start, end)
        parquet_file = self.cache_dir / f"{cache_key}.parquet"
        
        df.to_parquet(parquet_file, index=True)
        
        # 更新元数据
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO cache_meta 
            (symbol, level, start_date, end_date, hash, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (symbol, level, start, end, cache_key))
        
        conn.commit()
        conn.close()
    
    def get_missing_ranges(
        self,
        symbol: str,
        level: str,
        start: str,
        end: str
    ) -> List[tuple]:
        """获取缺失的数据范围"""
        # 简化实现：检查是否有缓存
        cached = self.get(symbol, level, start, end)
        
        if cached is None or cached.empty:
            return [(start, end)]
        
        # 检查日期范围
        cached_start = cached.index.min().strftime('%Y-%m-%d')
        cached_end = cached.index.max().strftime('%Y-%m-%d')
        
        missing = []
        
        if start < cached_start:
            missing.append((start, cached_start))
        
        if end > cached_end:
            missing.append((cached_end, end))
        
        return missing


class DataDownloader:
    """数据下载器"""
    
    def __init__(
        self,
        source: str = "yfinance",
        cache_dir: str = "./data/cache"
    ):
        self.cache = DataCache(cache_dir)
        
        # 初始化数据源
        if source == "yfinance":
            self.data_source = YFinanceSource()
        elif source == "akshare":
            self.data_source = AKShareSource()
        else:
            self.data_source = YFinanceSource()
    
    def download(
        self,
        symbol: str,
        level: str = "1d",
        start: str = "2020-01-01",
        end: str = None
    ) -> pd.DataFrame:
        """下载 K 线数据"""
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
        
        # 检查缓存
        cached = self.cache.get(symbol, level, start, end)
        if cached is not None and not cached.empty:
            print(f"使用缓存数据：{symbol} {level}")
            return cached
        
        # 检查缺失范围
        missing_ranges = self.cache.get_missing_ranges(symbol, level, start, end)
        
        if not missing_ranges:
            print(f"数据完整：{symbol} {level}")
            return cached
        
        # 下载缺失数据
        all_dfs = []
        
        if cached is not None and not cached.empty:
            all_dfs.append(cached)
        
        for range_start, range_end in missing_ranges:
            print(f"下载 {symbol} {level}: {range_start} ~ {range_end}")
            
            df = self.data_source.fetch_klines(symbol, level, range_start, range_end)
            
            if not df.empty:
                all_dfs.append(df)
        
        if not all_dfs:
            return pd.DataFrame()
        
        # 合并数据
        result = pd.concat(all_dfs).sort_index().drop_duplicates()
        
        # 保存到缓存
        self.cache.set(result, symbol, level, start, end)
        
        return result
    
    def batch_download(
        self,
        symbols: List[str],
        level: str = "1d",
        start: str = "2020-01-01",
        end: str = None,
        workers: int = 4
    ) -> Dict[str, pd.DataFrame]:
        """批量下载"""
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
        
        results = {}
        
        # 简单串行下载（可改为多线程）
        for symbol in symbols:
            try:
                df = self.download(symbol, level, start, end)
                if not df.empty:
                    results[symbol] = df
                    print(f"✓ {symbol}: {len(df)} 条记录")
                else:
                    print(f"✗ {symbol}: 无数据")
            except Exception as e:
                print(f"✗ {symbol}: {e}")
        
        return results


class DataValidator:
    """数据校验器"""
    
    @staticmethod
    def validate(df: pd.DataFrame) -> Dict:
        """校验数据质量"""
        issues = {
            'missing_values': {},
            'outliers': [],
            'gaps': [],
            'duplicates': 0
        }
        
        # 检查缺失值
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    issues['missing_values'][col] = missing
        
        # 检查重复
        issues['duplicates'] = df.index.duplicated().sum()
        
        # 检查异常值
        if 'close' in df.columns:
            returns = df['close'].pct_change()
            outliers = returns[abs(returns) > 0.5]  # 单日涨跌超过 50%
            if len(outliers) > 0:
                issues['outliers'] = outliers.index.tolist()
        
        # 检查时间 gaps
        if len(df) > 1:
            time_diffs = df.index.to_series().diff()
            median_diff = time_diffs.median()
            gaps = time_diffs[time_diffs > median_diff * 2]
            if len(gaps) > 0:
                issues['gaps'] = gaps.index.tolist()
        
        return issues
    
    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """清理数据"""
        # 删除重复
        df = df[~df.index.duplicated(keep='first')]
        
        # 删除缺失值
        df = df.dropna()
        
        # 排序
        df = df.sort_index()
        
        return df


if __name__ == "__main__":
    # 示例：下载 CVE.TO 数据
    downloader = DataDownloader(source="yfinance", cache_dir="./data/cache")
    
    # 下载日线数据
    df = downloader.download(
        symbol="CVE.TO",
        level="1d",
        start="2025-01-01",
        end="2026-03-09"
    )
    
    print(f"下载完成：{len(df)} 条记录")
    print(df.tail())
    
    # 校验数据
    validator = DataValidator()
    issues = validator.validate(df)
    print(f"数据问题：{issues}")
    
    # 批量下载
    symbols = ["CVE.TO", "XEG.TO", "SU.TO", "CNQ.TO"]
    results = downloader.batch_download(symbols, level="1d")
    print(f"批量下载完成：{len(results)} 只股票")
