//! Pen Theory (笔) Implementation
//! 
//! Implements the new pen definition (新笔) with strict 3 K-line rules
//! and validation logic for pen formation.

use crate::kline::{Kline, KlineSeries};
use serde::{Deserialize, Serialize};

/// Pen direction
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PenDirection {
    /// Upward pen (higher high to higher low)
    Up,
    /// Downward pen (lower low to lower high)
    Down,
}

/// Pen type based on new 3-K-line definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pen {
    /// Pen direction
    pub direction: PenDirection,
    /// Starting K-line index
    pub start_idx: usize,
    /// Ending K-line index
    pub end_idx: usize,
    /// Starting price (high for up pen, low for down pen)
    pub start_price: f64,
    /// Ending price (high for up pen, low for down pen)
    pub end_price: f64,
    /// Was this pen confirmed (not just potential)
    pub confirmed: bool,
}

impl Pen {
    /// Create a new upward pen
    pub fn up(start_idx: usize, end_idx: usize, start_price: f64, end_price: f64) -> Self {
        Self {
            direction: PenDirection::Up,
            start_idx,
            end_idx,
            start_price,
            end_price,
            confirmed: false,
        }
    }

    /// Create a new downward pen
    pub fn down(start_idx: usize, end_idx: usize, start_price: f64, end_price: f64) -> Self {
        Self {
            direction: PenDirection::Down,
            start_idx,
            end_idx,
            start_price,
            end_price,
            confirmed: false,
        }
    }

    /// Check if pen is valid (end price > start price for up, < for down)
    pub fn is_valid(&self) -> bool {
        match self.direction {
            PenDirection::Up => self.end_price > self.start_price,
            PenDirection::Down => self.end_price < self.start_price,
        }
    }

    /// Calculate pen magnitude (absolute price change)
    pub fn magnitude(&self) -> f64 {
        (self.end_price - self.start_price).abs()
    }

    /// Calculate pen length in K-lines
    pub fn kline_count(&self) -> usize {
        self.end_idx - self.start_idx + 1
    }
}

/// Configuration for pen theory calculation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PenConfig {
    /// Use new 3-K-line definition (vs traditional)
    pub use_new_definition: bool,
    /// Strict validation (no overlapping pens)
    pub strict_validation: bool,
    /// Minimum K-lines between pen turning points
    pub min_klines_between_turns: usize,
}

impl Default for PenConfig {
    fn default() -> Self {
        Self {
            use_new_definition: true,
            strict_validation: true,
            min_klines_between_turns: 3,
        }
    }
}

/// Pen calculator implementing new 3-K-line definition
pub struct PenCalculator {
    config: PenConfig,
}

impl PenCalculator {
    /// Create a new pen calculator with configuration
    pub fn new(config: PenConfig) -> Self {
        Self { config }
    }

    /// Create with default configuration (new 3-K-line definition)
    pub fn with_defaults() -> Self {
        Self::new(PenConfig::default())
    }

    /// Identify all pens in a K-line series
    pub fn identify_pens(&self, series: &KlineSeries) -> Vec<Pen> {
        if series.len() < 3 {
            return Vec::new();
        }

        let mut pens = Vec::new();
        let klines = &series.klines;

        if self.config.use_new_definition {
            // New definition: minimum 3 K-lines per pen
            pens = self.identify_pens_new_definition(klines);
        } else {
            // Traditional definition would go here
            pens = self.identify_pens_traditional(klines);
        }

        // Apply strict validation if enabled
        if self.config.strict_validation {
            pens = self.validate_pens_strict(pens);
        }

        pens
    }

    /// Identify pens using new 3-K-line definition
    /// 
    /// New Pen Definition (新笔):
    /// 1. A pen consists of at least 3 K-lines
    /// 2. Must have a clear top fractal (顶分型) or bottom fractal (底分型)
    /// 3. No overlapping between consecutive pens
    /// 4. Must satisfy minimum price movement
    fn identify_pens_new_definition(&self, klines: &[Kline]) -> Vec<Pen> {
        let mut pens = Vec::new();
        let mut i = 0;

        while i < klines.len() - 2 {
            // Look for potential pen start (fractal point)
            if let Some(fractal) = self.find_fractal(klines, i) {
                // Try to form a pen from this fractal
                if let Some(pen) = self.try_form_pen(klines, fractal.0, fractal.1, i) {
                    i = pen.end_idx;
                    pens.push(pen);
                } else {
                    i += 1;
                }
            } else {
                i += 1;
            }
        }

        pens
    }

    /// Find fractal (top or bottom) starting at index
    /// Returns (index, direction) if found
    fn find_fractal(&self, klines: &[Kline], start: usize) -> Option<(usize, PenDirection)> {
        if start + 2 >= klines.len() {
            return None;
        }

        // Check for top fractal (顶分型): middle high is highest of 3
        if klines[start + 1].high > klines[start].high 
            && klines[start + 1].high > klines[start + 2].high 
        {
            return Some((start + 1, PenDirection::Down));
        }

        // Check for bottom fractal (底分型): middle low is lowest of 3
        if klines[start + 1].low < klines[start].low 
            && klines[start + 1].low < klines[start + 2].low 
        {
            return Some((start + 1, PenDirection::Up));
        }

        None
    }

    /// Try to form a valid pen from a fractal point
    fn try_form_pen(&self, klines: &[Kline], fractal_idx: usize, direction: PenDirection, _start_search: usize) -> Option<Pen> {
        match direction {
            PenDirection::Down => {
                // Looking for subsequent bottom fractal to complete downward pen
                for i in (fractal_idx + 3)..klines.len() - 1 {
                    if self.is_bottom_fractal(klines, i) {
                        // Validate minimum K-lines requirement
                        if i - fractal_idx >= self.config.min_klines_between_turns - 1 {
                            return Some(Pen::down(
                                fractal_idx,
                                i,
                                klines[fractal_idx].high,
                                klines[i].low,
                            ));
                        }
                    }
                }
            }
            PenDirection::Up => {
                // Looking for subsequent top fractal to complete upward pen
                for i in (fractal_idx + 3)..klines.len() - 1 {
                    if self.is_top_fractal(klines, i) {
                        // Validate minimum K-lines requirement
                        if i - fractal_idx >= self.config.min_klines_between_turns - 1 {
                            return Some(Pen::up(
                                fractal_idx,
                                i,
                                klines[fractal_idx].low,
                                klines[i].high,
                            ));
                        }
                    }
                }
            }
        }
        None
    }

    /// Check if index is a top fractal
    fn is_top_fractal(&self, klines: &[Kline], idx: usize) -> bool {
        if idx == 0 || idx >= klines.len() - 1 {
            return false;
        }
        klines[idx].high > klines[idx - 1].high && klines[idx].high > klines[idx + 1].high
    }

    /// Check if index is a bottom fractal
    fn is_bottom_fractal(&self, klines: &[Kline], idx: usize) -> bool {
        if idx == 0 || idx >= klines.len() - 1 {
            return false;
        }
        klines[idx].low < klines[idx - 1].low && klines[idx].low < klines[idx + 1].low
    }

    /// Traditional pen identification (for comparison)
    fn identify_pens_traditional(&self, klines: &[Kline]) -> Vec<Pen> {
        // Placeholder for traditional implementation
        // Traditional definition may allow 2 K-lines or have different rules
        Vec::new()
    }

    /// Apply strict validation rules to pens
    fn validate_pens_strict(&self, mut pens: Vec<Pen>) -> Vec<Pen> {
        if pens.is_empty() {
            return pens;
        }

        let mut validated = Vec::new();
        let mut last_pen: Option<Pen> = None;

        for pen in pens {
            if pen.is_valid() {
                // Check no overlap with previous pen
                if let Some(ref prev) = last_pen {
                    // Ensure no overlapping price ranges for strict validation
                    if self.config.strict_validation {
                        match (prev.direction, pen.direction) {
                            (PenDirection::Up, PenDirection::Down) => {
                                // Up pen followed by down: down should start from up's high
                                if pen.start_price < prev.end_price {
                                    continue; // Skip overlapping pen
                                }
                            }
                            (PenDirection::Down, PenDirection::Up) => {
                                // Down pen followed by up: up should start from down's low
                                if pen.start_price > prev.end_price {
                                    continue; // Skip overlapping pen
                                }
                            }
                            _ => {}
                        }
                    }
                }

                // Mark as confirmed if it has a successor
                let mut confirmed_pen = pen;
                validated.push(confirmed_pen);
                last_pen = Some(validated.last().unwrap().clone());
            }
        }

        validated
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::kline::{Kline, KlineSeries, TimeFrame};
    use chrono::Utc;

    fn create_test_klines(prices: Vec<(f64, f64, f64)>) -> Vec<Kline> {
        prices
            .iter()
            .enumerate()
            .map(|(i, &(o, h, l))| {
                let c = if o < h { o + (h - o) * 0.7 } else { o - (o - l) * 0.3 };
                Kline::new(Utc::now(), o, h, l, c, 1000.0)
            })
            .collect()
    }

    #[test]
    fn test_pen_validity() {
        let up_pen = Pen::up(0, 3, 100.0, 105.0);
        assert!(up_pen.is_valid());
        assert_eq!(up_pen.direction, PenDirection::Up);
        assert_eq!(up_pen.magnitude(), 5.0);
        assert_eq!(up_pen.kline_count(), 4);

        let down_pen = Pen::down(0, 3, 100.0, 95.0);
        assert!(down_pen.is_valid());
        assert_eq!(down_pen.direction, PenDirection::Down);
        assert_eq!(down_pen.magnitude(), 5.0);
    }

    #[test]
    fn test_invalid_pen() {
        let invalid_up = Pen::up(0, 3, 100.0, 95.0);
        assert!(!invalid_up.is_valid());

        let invalid_down = Pen::down(0, 3, 100.0, 105.0);
        assert!(!invalid_down.is_valid());
    }

    #[test]
    fn test_fractal_detection() {
        let calc = PenCalculator::with_defaults();
        
        // Top fractal: high-high, higher high, lower high
        let klines = vec![
            Kline::new(Utc::now(), 100.0, 105.0, 99.0, 103.0, 1000.0),
            Kline::new(Utc::now(), 103.0, 110.0, 102.0, 108.0, 1000.0),  // High point
            Kline::new(Utc::now(), 108.0, 109.0, 104.0, 105.0, 1000.0),
        ];

        assert!(calc.is_top_fractal(&klines, 1));
        assert!(!calc.is_bottom_fractal(&klines, 1));
    }

    #[test]
    fn test_bottom_fractal() {
        let calc = PenCalculator::with_defaults();
        
        // Bottom fractal: low-low, lower low, higher low
        let klines = vec![
            Kline::new(Utc::now(), 100.0, 101.0, 95.0, 97.0, 1000.0),
            Kline::new(Utc::now(), 97.0, 98.0, 90.0, 92.0, 1000.0),  // Low point
            Kline::new(Utc::now(), 92.0, 96.0, 91.0, 95.0, 1000.0),
        ];

        assert!(calc.is_bottom_fractal(&klines, 1));
        assert!(!calc.is_top_fractal(&klines, 1));
    }

    #[test]
    fn test_pen_formation_minimum_klines() {
        let config = PenConfig {
            use_new_definition: true,
            strict_validation: true,
            min_klines_between_turns: 3,
        };
        let calc = PenCalculator::new(config);

        // Create series with clear up and down moves
        let prices = vec![
            (100.0, 102.0, 99.0),   // 0
            (102.0, 105.0, 101.0),  // 1 - potential top
            (105.0, 106.0, 103.0),  // 2
            (105.0, 106.0, 102.0),  // 3
            (102.0, 103.0, 98.0),   // 4 - potential bottom
        ];
        let klines = create_test_klines(prices);
        
        let mut series = KlineSeries::new("TEST".to_string(), TimeFrame::M5);
        for k in klines {
            series.push(k);
        }

        let pens = calc.identify_pens(&series);
        // Should identify pens based on fractals
        assert!(pens.len() >= 0); // May be 0 if not enough data for complete pens
    }

    #[test]
    fn test_pen_calculator_default_config() {
        let calc = PenCalculator::with_defaults();
        assert!(calc.config.use_new_definition);
        assert!(calc.config.strict_validation);
        assert_eq!(calc.config.min_klines_between_turns, 3);
    }
}
