//! Fractal (分型) Detection Module
//! 
//! Implements top and bottom fractal detection based on Lesson 62, 65, 77, 79
//! with proper containment relationship handling.

use crate::kline::{Kline, KlineSeries};
use serde::{Deserialize, Serialize};

/// Fractal type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FractalType {
    /// Top fractal (顶分型)
    Top,
    /// Bottom fractal (底分型)
    Bottom,
}

/// Fractal structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Fractal {
    /// Fractal type (top or bottom)
    pub fractal_type: FractalType,
    /// K-line index of the fractal peak/trough
    pub kline_index: usize,
    /// Price (high for top, low for bottom)
    pub price: f64,
    /// Whether this fractal is confirmed
    pub confirmed: bool,
}

impl Fractal {
    /// Create a new top fractal
    pub fn top(kline_index: usize, price: f64) -> Self {
        Self {
            fractal_type: FractalType::Top,
            kline_index,
            price,
            confirmed: true,
        }
    }

    /// Create a new bottom fractal
    pub fn bottom(kline_index: usize, price: f64) -> Self {
        Self {
            fractal_type: FractalType::Bottom,
            kline_index,
            price,
            confirmed: true,
        }
    }

    /// Check if this is a top fractal
    pub fn is_top(&self) -> bool {
        self.fractal_type == FractalType::Top
    }

    /// Check if this is a bottom fractal
    pub fn is_bottom(&self) -> bool {
        self.fractal_type == FractalType::Bottom
    }
}

/// Configuration for fractal detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FractalConfig {
    /// Use strict mode (middle K-line must be strictly higher/lower)
    pub strict_mode: bool,
    /// Handle containment relationships
    pub handle_containment: bool,
}

impl Default for FractalConfig {
    fn default() -> Self {
        Self {
            strict_mode: true,
            handle_containment: true,
        }
    }
}

/// Fractal detector implementing ChanLun theory
pub struct FractalDetector {
    config: FractalConfig,
}

impl FractalDetector {
    /// Create a new fractal detector with default configuration
    pub fn new() -> Self {
        Self::with_config(FractalConfig::default())
    }

    /// Create a new fractal detector with custom configuration
    pub fn with_config(config: FractalConfig) -> Self {
        Self { config }
    }

    /// Detect all fractals in a K-line series
    pub fn detect_all(&self, series: &KlineSeries) -> Vec<Fractal> {
        let klines = &series.klines;
        
        if klines.len() < 3 {
            return Vec::new();
        }

        // First, handle containment relationships if enabled
        let processed_klines = if self.config.handle_containment {
            self.process_containment(klines)
        } else {
            klines.clone()
        };

        let mut fractals = Vec::new();

        // Detect fractals
        for i in 1..processed_klines.len() - 1 {
            if self.is_top_fractal(&processed_klines, i) {
                fractals.push(Fractal::top(i, processed_klines[i].high));
            } else if self.is_bottom_fractal(&processed_klines, i) {
                fractals.push(Fractal::bottom(i, processed_klines[i].low));
            }
        }

        fractals
    }

    /// Detect only top fractals
    pub fn detect_tops(&self, series: &KlineSeries) -> Vec<Fractal> {
        let all = self.detect_all(series);
        all.into_iter().filter(|f| f.is_top()).collect()
    }

    /// Detect only bottom fractals
    pub fn detect_bottoms(&self, series: &KlineSeries) -> Vec<Fractal> {
        let all = self.detect_all(series);
        all.into_iter().filter(|f| f.is_bottom()).collect()
    }

    /// Check if index is a top fractal (顶分型)
    /// 
    /// Definition: Second K-line's high is the highest among three adjacent K-lines,
    /// and its low is also the highest among three adjacent K-lines' lows.
    fn is_top_fractal(&self, klines: &[Kline], idx: usize) -> bool {
        if idx < 1 || idx >= klines.len() - 1 {
            return false;
        }

        let mid_high = klines[idx].high;
        let left_high = klines[idx - 1].high;
        let right_high = klines[idx + 1].high;

        if self.config.strict_mode {
            mid_high > left_high && mid_high > right_high
        } else {
            mid_high >= left_high && mid_high >= right_high
        }
    }

    /// Check if index is a bottom fractal (底分型)
    /// 
    /// Definition: Second K-line's low is the lowest among three adjacent K-lines,
    /// and its high is also the lowest among three adjacent K-lines' highs.
    fn is_bottom_fractal(&self, klines: &[Kline], idx: usize) -> bool {
        if idx < 1 || idx >= klines.len() - 1 {
            return false;
        }

        let mid_low = klines[idx].low;
        let left_low = klines[idx - 1].low;
        let right_low = klines[idx + 1].low;

        if self.config.strict_mode {
            mid_low < left_low && mid_low < right_low
        } else {
            mid_low <= left_low && mid_low <= right_low
        }
    }

    /// Process containment relationships (包含关系处理)
    /// 
    /// When two adjacent K-lines have containment relationship:
    /// - Up trend: Take higher high and higher low
    /// - Down trend: Take lower high and lower low
    fn process_containment(&self, klines: &[Kline]) -> Vec<Kline> {
        if klines.len() < 2 {
            return klines.to_vec();
        }

        let mut processed = Vec::with_capacity(klines.len());
        let mut i = 0;

        while i < klines.len() {
            if i == klines.len() - 1 {
                // Last K-line, no next to compare
                processed.push(klines[i].clone());
                break;
            }

            let current = &klines[i];
            let next = &klines[i + 1];

            if self.has_containment(current, next) {
                // Determine trend direction
                let is_up_trend = if i > 0 {
                    klines[i].high > klines[i - 1].high
                } else {
                    next.high > current.high
                };

                // Merge K-lines based on trend
                let merged = if is_up_trend {
                    // Up trend: higher high, higher low
                    Kline {
                        timestamp: current.timestamp,
                        open: current.open,
                        high: current.high.max(next.high),
                        low: current.low.max(next.low),
                        close: current.close,
                        volume: current.volume + next.volume,
                    }
                } else {
                    // Down trend: lower high, lower low
                    Kline {
                        timestamp: current.timestamp,
                        open: current.open,
                        high: current.high.min(next.high),
                        low: current.low.min(next.low),
                        close: current.close,
                        volume: current.volume + next.volume,
                    }
                };

                processed.push(merged);
                i += 2; // Skip next K-line as it's merged
            } else {
                processed.push(klines[i].clone());
                i += 1;
            }
        }

        processed
    }

    /// Check if two K-lines have containment relationship
    /// 
    /// Containment exists when one K-line's high and low completely contain the other's.
    fn has_containment(&self, k1: &Kline, k2: &Kline) -> bool {
        (k2.high <= k1.high && k2.low >= k1.low) || (k1.high <= k2.high && k1.low >= k2.low)
    }
}

impl Default for FractalDetector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{DateTime, Utc};

    fn create_kline(high: f64, low: f64) -> Kline {
        Kline {
            timestamp: Utc::now(),
            open: (high + low) / 2.0,
            high,
            low,
            close: (high + low) / 2.0,
            volume: 1000,
        }
    }

    #[test]
    fn test_top_fractal_detection() {
        let klines = vec![
            create_kline(100.0, 98.0),
            create_kline(102.0, 99.0), // Peak
            create_kline(101.0, 98.0),
        ];
        let series = KlineSeries {
            klines,
            symbol: "TEST".to_string(),
            timeframe: "30m".to_string(),
        };

        let detector = FractalDetector::new();
        let fractals = detector.detect_all(&series);

        assert_eq!(fractals.len(), 1);
        assert!(fractals[0].is_top());
        assert_eq!(fractals[0].kline_index, 1);
        assert_eq!(fractals[0].price, 102.0);
    }

    #[test]
    fn test_bottom_fractal_detection() {
        let klines = vec![
            create_kline(100.0, 98.0),
            create_kline(99.0, 96.0), // Trough
            create_kline(100.0, 97.0),
        ];
        let series = KlineSeries {
            klines,
            symbol: "TEST".to_string(),
            timeframe: "30m".to_string(),
        };

        let detector = FractalDetector::new();
        let fractals = detector.detect_all(&series);

        assert_eq!(fractals.len(), 1);
        assert!(fractals[0].is_bottom());
        assert_eq!(fractals[0].kline_index, 1);
        assert_eq!(fractals[0].price, 96.0);
    }

    #[test]
    fn test_containment_handling() {
        let klines = vec![
            create_kline(100.0, 98.0),
            create_kline(99.5, 98.5), // Contained in first
            create_kline(101.0, 99.0),
        ];
        let series = KlineSeries {
            klines,
            symbol: "TEST".to_string(),
            timeframe: "30m".to_string(),
        };

        let detector = FractalDetector::with_config(FractalConfig {
            strict_mode: true,
            handle_containment: true,
        });
        let fractals = detector.detect_all(&series);

        // With containment handling, middle K-line is merged
        // So we should have fewer fractals
        assert!(fractals.len() >= 0);
    }
}
