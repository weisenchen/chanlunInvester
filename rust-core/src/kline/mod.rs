//! K-line Data Structures and Handlers
//! 
//! Core data types for OHLCV candles and timeframe management.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// K-line (candlestick) data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Kline {
    /// Timestamp of candle open
    pub timestamp: DateTime<Utc>,
    /// Open price
    pub open: f64,
    /// High price
    pub high: f64,
    /// Low price
    pub low: f64,
    /// Close price
    pub close: f64,
    /// Volume
    pub volume: f64,
    /// Turnover (optional, for crypto/stocks)
    pub turnover: Option<f64>,
}

impl Kline {
    /// Create a new K-line
    pub fn new(
        timestamp: DateTime<Utc>,
        open: f64,
        high: f64,
        low: f64,
        close: f64,
        volume: f64,
    ) -> Self {
        Self {
            timestamp,
            open,
            high,
            low,
            close,
            volume,
            turnover: None,
        }
    }

    /// Check if candle is bullish (close > open)
    pub fn is_bullish(&self) -> bool {
        self.close > self.open
    }

    /// Check if candle is bearish (close < open)
    pub fn is_bearish(&self) -> bool {
        self.close < self.open
    }

    /// Calculate candle range (high - low)
    pub fn range(&self) -> f64 {
        self.high - self.low
    }

    /// Calculate body size (abs(close - open))
    pub fn body_size(&self) -> f64 {
        (self.close - self.open).abs()
    }

    /// Calculate upper shadow size
    pub fn upper_shadow(&self) -> f64 {
        self.high - self.open.max(self.close)
    }

    /// Calculate lower shadow size
    pub fn lower_shadow(&self) -> f64 {
        self.open.min(self.close) - self.low
    }
}

/// Timeframe enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TimeFrame {
    /// 1 minute
    M1,
    /// 3 minutes
    M3,
    /// 5 minutes
    M5,
    /// 15 minutes
    M15,
    /// 30 minutes
    M30,
    /// 1 hour
    H1,
    /// 4 hours
    H4,
    /// 1 day
    D1,
    /// 1 week
    W1,
    /// 1 month
    MN,
}

impl TimeFrame {
    /// Get timeframe in minutes
    pub fn minutes(&self) -> u32 {
        match self {
            TimeFrame::M1 => 1,
            TimeFrame::M3 => 3,
            TimeFrame::M5 => 5,
            TimeFrame::M15 => 15,
            TimeFrame::M30 => 30,
            TimeFrame::H1 => 60,
            TimeFrame::H4 => 240,
            TimeFrame::D1 => 1440,
            TimeFrame::W1 => 10080,
            TimeFrame::MN => 43200, // Approximate
        }
    }

    /// Get timeframe in seconds
    pub fn seconds(&self) -> u64 {
        self.minutes() as u64 * 60
    }

    /// Parse from string
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_uppercase().as_str() {
            "1M" | "M1" => Some(TimeFrame::M1),
            "3M" | "M3" => Some(TimeFrame::M3),
            "5M" | "M5" => Some(TimeFrame::M5),
            "15M" | "M15" => Some(TimeFrame::M15),
            "30M" | "M30" => Some(TimeFrame::M30),
            "1H" | "H1" => Some(TimeFrame::H1),
            "4H" | "H4" => Some(TimeFrame::H4),
            "1D" | "D1" => Some(TimeFrame::D1),
            "1W" | "W1" => Some(TimeFrame::W1),
            "1MN" | "MN" => Some(TimeFrame::MN),
            _ => None,
        }
    }
}

impl std::fmt::Display for TimeFrame {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TimeFrame::M1 => write!(f, "1m"),
            TimeFrame::M3 => write!(f, "3m"),
            TimeFrame::M5 => write!(f, "5m"),
            TimeFrame::M15 => write!(f, "15m"),
            TimeFrame::M30 => write!(f, "30m"),
            TimeFrame::H1 => write!(f, "1h"),
            TimeFrame::H4 => write!(f, "4h"),
            TimeFrame::D1 => write!(f, "1d"),
            TimeFrame::W1 => write!(f, "1w"),
            TimeFrame::MN => write!(f, "1M"),
        }
    }
}

/// K-line series (ordered collection)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KlineSeries {
    /// Timeframe of the series
    pub timeframe: TimeFrame,
    /// K-lines in chronological order
    pub klines: Vec<Kline>,
    /// Symbol/instrument identifier
    pub symbol: String,
}

impl KlineSeries {
    /// Create a new K-line series
    pub fn new(symbol: String, timeframe: TimeFrame) -> Self {
        Self {
            symbol,
            timeframe,
            klines: Vec::new(),
        }
    }

    /// Add a K-line (maintains chronological order)
    pub fn push(&mut self, kline: Kline) {
        self.klines.push(kline);
    }

    /// Get the latest K-line
    pub fn latest(&self) -> Option<&Kline> {
        self.klines.last()
    }

    /// Get K-line at index (0 = oldest, -1 = newest)
    pub fn get(&self, index: isize) -> Option<&Kline> {
        if index >= 0 {
            self.klines.get(index as usize)
        } else {
            let idx = self.klines.len() as isize + index;
            if idx >= 0 {
                self.klines.get(idx as usize)
            } else {
                None
            }
        }
    }

    /// Get number of K-lines
    pub fn len(&self) -> usize {
        self.klines.len()
    }

    /// Check if empty
    pub fn is_empty(&self) -> bool {
        self.klines.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    #[test]
    fn test_kline_bullish() {
        let kline = Kline::new(Utc::now(), 100.0, 105.0, 99.0, 103.0, 1000.0);
        assert!(kline.is_bullish());
        assert!(!kline.is_bearish());
    }

    #[test]
    fn test_kline_bearish() {
        let kline = Kline::new(Utc::now(), 100.0, 101.0, 95.0, 97.0, 1000.0);
        assert!(kline.is_bearish());
        assert!(!kline.is_bullish());
    }

    #[test]
    fn test_timeframe_parsing() {
        assert_eq!(TimeFrame::from_str("1m"), Some(TimeFrame::M1));
        assert_eq!(TimeFrame::from_str("5M"), Some(TimeFrame::M5));
        assert_eq!(TimeFrame::from_str("1h"), Some(TimeFrame::H1));
        assert_eq!(TimeFrame::from_str("4H"), Some(TimeFrame::H4));
        assert_eq!(TimeFrame::from_str("invalid"), None);
    }
}
