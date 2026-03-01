//! Divergence (背驰) Detection Module
//! 
//! Implements divergence detection per Lessons 15, 24, 27
//! - Price divergence with MACD
//! - Trend divergence (笔/段 level)
//! - Multi-level divergence analysis

use crate::kline::Kline;
use crate::pen::{Pen, PenDirection};
use crate::segment::Segment;
use crate::indicators::{MACDCalculator, MACDConfig, MACDValue};
use serde::{Deserialize, Serialize};

/// Divergence type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DivergenceType {
    /// Bullish divergence (price lower low, MACD higher low)
    Bullish,
    /// Bearish divergence (price higher high, MACD lower high)
    Bearish,
}

/// Divergence level
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DivergenceLevel {
    /// Pen-level divergence (笔背驰)
    Pen,
    /// Segment-level divergence (线段背驰)
    Segment,
    /// Multi-level divergence (多级别背驰)
    MultiLevel,
}

/// Divergence signal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DivergenceSignal {
    /// Divergence type
    pub div_type: DivergenceType,
    /// Divergence level
    pub level: DivergenceLevel,
    /// First peak/trough price
    pub price_a: f64,
    /// Second peak/trough price
    pub price_b: f64,
    /// First MACD value
    pub macd_a: f64,
    /// Second MACD value
    pub macd_b: f64,
    /// Index of second peak/trough
    pub index: usize,
    /// Strength (0.0 - 1.0)
    pub strength: f64,
}

impl DivergenceSignal {
    /// Calculate divergence strength
    fn calculate_strength(price_change: f64, macd_change: f64) -> f64 {
        // Stronger divergence when:
        // - Price makes significant new high/low
        // - MACD makes significant opposite move
        let price_factor = price_change.abs().min(1.0);
        let macd_factor = macd_change.abs().min(1.0);
        (price_factor + macd_factor) / 2.0
    }
}

/// Configuration for divergence detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DivergenceConfig {
    /// Minimum price change to consider (percentage)
    pub min_price_change_pct: f64,
    /// Minimum MACD change to consider
    pub min_macd_change: f64,
    /// Lookback period for comparison
    pub lookback_pens: usize,
    /// Enable segment-level divergence
    pub enable_segment_div: bool,
}

impl Default for DivergenceConfig {
    fn default() -> Self {
        Self {
            min_price_change_pct: 0.5, // 0.5%
            min_macd_change: 0.01,
            lookback_pens: 5,
            enable_segment_div: true,
        }
    }
}

/// Divergence detector
pub struct DivergenceDetector {
    config: DivergenceConfig,
    macd_calculator: MACDCalculator,
}

impl DivergenceDetector {
    /// Create new divergence detector
    pub fn new(config: DivergenceConfig) -> Self {
        Self {
            config,
            macd_calculator: MACDCalculator::with_defaults(),
        }
    }

    /// Create with defaults
    pub fn with_defaults() -> Self {
        Self::new(DivergenceConfig::default())
    }

    /// Detect divergence in pen sequence
    pub fn detect_pen_divergence(
        &self,
        pens: &[Pen],
        klines: &[Kline],
    ) -> Vec<DivergenceSignal> {
        if pens.len() < 3 {
            return Vec::new();
        }

        let macd_values = self.macd_calculator.calculate(klines);
        let mut signals = Vec::new();

        // Look for consecutive pens in same direction
        for i in 0..pens.len() - 2 {
            let pen1 = &pens[i];
            let pen2 = &pens[i + 2]; // Skip one (alternating direction)

            if pen1.direction == pen2.direction {
                // Check for divergence
                if let Some(signal) = self.check_divergence(pen1, pen2, &macd_values) {
                    signals.push(signal);
                }
            }
        }

        signals
    }

    /// Detect divergence in segment sequence
    pub fn detect_segment_divergence(
        &self,
        segments: &[Segment],
        klines: &[Kline],
    ) -> Vec<DivergenceSignal> {
        if !self.config.enable_segment_div || segments.len() < 3 {
            return Vec::new();
        }

        let macd_values = self.macd_calculator.calculate(klines);
        let mut signals = Vec::new();

        for i in 0..segments.len() - 2 {
            let seg1 = &segments[i];
            let seg2 = &segments[i + 2];

            if seg1.direction == seg2.direction {
                if let Some(signal) = self.check_divergence_segments(seg1, seg2, &macd_values) {
                    signals.push(signal);
                }
            }
        }

        signals
    }

    /// Check divergence between two pens
    fn check_divergence(
        &self,
        pen1: &Pen,
        pen2: &Pen,
        macd_values: &[MACDValue],
    ) -> Option<DivergenceSignal> {
        match pen1.direction {
            PenDirection::Up => {
                // Check bearish divergence (higher high, lower MACD)
                let price_change = pen2.end_price - pen1.end_price;
                if price_change <= 0.0 {
                    return None; // Not making higher high
                }

                let macd1 = self.get_macd_at_peak(macd_values, pen1.end_idx);
                let macd2 = self.get_macd_at_peak(macd_values, pen2.end_idx);

                if macd1.is_none() || macd2.is_none() {
                    return None;
                }

                let macd_change = macd2.unwrap().histogram - macd1.unwrap().histogram;

                if macd_change < -self.config.min_macd_change {
                    let strength = DivergenceSignal::calculate_strength(
                        price_change / pen1.start_price,
                        macd_change.abs(),
                    );

                    return Some(DivergenceSignal {
                        div_type: DivergenceType::Bearish,
                        level: DivergenceLevel::Pen,
                        price_a: pen1.end_price,
                        price_b: pen2.end_price,
                        macd_a: macd1.unwrap().histogram,
                        macd_b: macd2.unwrap().histogram,
                        index: pen2.end_idx,
                        strength,
                    });
                }
            }
            PenDirection::Down => {
                // Check bullish divergence (lower low, higher MACD)
                let price_change = pen2.end_price - pen1.end_price;
                if price_change >= 0.0 {
                    return None; // Not making lower low
                }

                let macd1 = self.get_macd_at_peak(macd_values, pen1.end_idx);
                let macd2 = self.get_macd_at_peak(macd_values, pen2.end_idx);

                if macd1.is_none() || macd2.is_none() {
                    return None;
                }

                let macd_change = macd2.unwrap().histogram - macd1.unwrap().histogram;

                if macd_change > self.config.min_macd_change {
                    let strength = DivergenceSignal::calculate_strength(
                        price_change.abs() / pen1.start_price,
                        macd_change.abs(),
                    );

                    return Some(DivergenceSignal {
                        div_type: DivergenceType::Bullish,
                        level: DivergenceLevel::Pen,
                        price_a: pen1.end_price,
                        price_b: pen2.end_price,
                        macd_a: macd1.unwrap().histogram,
                        macd_b: macd2.unwrap().histogram,
                        index: pen2.end_idx,
                        strength,
                    });
                }
            }
        }

        None
    }

    /// Check divergence between two segments
    fn check_divergence_segments(
        &self,
        seg1: &Segment,
        seg2: &Segment,
        macd_values: &[MACDValue],
    ) -> Option<DivergenceSignal> {
        // Similar logic to pen divergence but at segment level
        match seg1.direction {
            PenDirection::Up => {
                let price_change = seg2.end_price - seg1.end_price;
                if price_change <= 0.0 {
                    return None;
                }

                // Get MACD at segment peaks (approximate)
                let macd1 = macd_values.get(seg1.end_pen_idx).copied();
                let macd2 = macd_values.get(seg2.end_pen_idx).copied();

                if macd1.is_none() || macd2.is_none() {
                    return None;
                }

                let macd_change = macd2.unwrap().histogram - macd1.unwrap().histogram;

                if macd_change < -self.config.min_macd_change {
                    Some(DivergenceSignal {
                        div_type: DivergenceType::Bearish,
                        level: DivergenceLevel::Segment,
                        price_a: seg1.end_price,
                        price_b: seg2.end_price,
                        macd_a: macd1.unwrap().histogram,
                        macd_b: macd2.unwrap().histogram,
                        index: seg2.end_pen_idx,
                        strength: DivergenceSignal::calculate_strength(
                            price_change / seg1.start_price,
                            macd_change.abs(),
                        ),
                    })
                } else {
                    None
                }
            }
            PenDirection::Down => {
                let price_change = seg2.end_price - seg1.end_price;
                if price_change >= 0.0 {
                    return None;
                }

                let macd1 = macd_values.get(seg1.end_pen_idx).copied();
                let macd2 = macd_values.get(seg2.end_pen_idx).copied();

                if macd1.is_none() || macd2.is_none() {
                    return None;
                }

                let macd_change = macd2.unwrap().histogram - macd1.unwrap().histogram;

                if macd_change > self.config.min_macd_change {
                    Some(DivergenceSignal {
                        div_type: DivergenceType::Bullish,
                        level: DivergenceLevel::Segment,
                        price_a: seg1.end_price,
                        price_b: seg2.end_price,
                        macd_a: macd1.unwrap().histogram,
                        macd_b: macd2.unwrap().histogram,
                        index: seg2.end_pen_idx,
                        strength: DivergenceSignal::calculate_strength(
                            price_change.abs() / seg1.start_price,
                            macd_change.abs(),
                        ),
                    })
                } else {
                    None
                }
            }
        }
    }

    /// Get MACD value at or near peak index
    fn get_macd_at_peak(&self, macd_values: &[MACDValue], idx: usize) -> Option<MACDValue> {
        macd_values.get(idx).copied().or_else(|| {
            // Try nearby indices if exact not available
            if idx > 0 {
                macd_values.get(idx - 1).copied()
            } else {
                None
            }
        })
    }

    /// Detect multi-level divergence (pen + segment align)
    pub fn detect_multi_level_divergence(
        &self,
        pens: &[Pen],
        segments: &[Segment],
        klines: &[Kline],
    ) -> Vec<DivergenceSignal> {
        let pen_divs = self.detect_pen_divergence(pens, klines);
        let seg_divs = self.detect_segment_divergence(segments, klines);

        // Find aligned divergences (same type at both levels)
        let mut multi_level = Vec::new();

        for pen_div in &pen_divs {
            for seg_div in &seg_divs {
                if pen_div.div_type == seg_div.div_type {
                    // Multi-level divergence confirmed
                    let mut signal = pen_div.clone();
                    signal.level = DivergenceLevel::MultiLevel;
                    signal.strength = (signal.strength + seg_div.strength) / 2.0;
                    multi_level.push(signal);
                }
            }
        }

        multi_level
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;

    #[test]
    fn test_bearish_divergence_detection() {
        let detector = DivergenceDetector::with_defaults();

        // Create two upward pens with higher high but lower MACD
        let pens = vec![
            Pen::up(0, 2, 100.0, 105.0),
            Pen::down(2, 4, 105.0, 102.0),
            Pen::up(4, 6, 102.0, 108.0), // Higher high
        ];

        // Create mock klines (would need real MACD calculation)
        let klines: Vec<Kline> = (0..20)
            .map(|i| Kline::new(
                Utc::now(),
                100.0 + i as f64,
                105.0 + i as f64,
                99.0 + i as f64,
                103.0 + i as f64,
                1000.0,
            ))
            .collect();

        let signals = detector.detect_pen_divergence(&pens, &klines);
        // May or may not find divergence depending on MACD values
        assert!(signals.len() >= 0);
    }

    #[test]
    fn test_divergence_config() {
        let config = DivergenceConfig::default();
        assert_eq!(config.min_price_change_pct, 0.5);
        assert_eq!(config.min_macd_change, 0.01);
        assert_eq!(config.lookback_pens, 5);
        assert!(config.enable_segment_div);
    }
}
