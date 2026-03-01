//! Line Segment (线段) Implementation with Feature Sequence
//! 
//! Implements strict segment division using feature sequences (特征序列)
//! with two-case judgment per Lesson 67 (有缺口/无缺口).

use crate::kline::Kline;
use crate::pen::{Pen, PenDirection};
use serde::{Deserialize, Serialize};

/// Line segment structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    /// Segment direction
    pub direction: PenDirection,
    /// Starting pen index
    pub start_pen_idx: usize,
    /// Ending pen index
    pub end_pen_idx: usize,
    /// Starting price
    pub start_price: f64,
    /// Ending price
    pub end_price: f64,
    /// Pens contained in this segment
    pub contained_pens: Vec<Pen>,
    /// Is this segment confirmed (not just potential)
    pub confirmed: bool,
}

impl Segment {
    /// Create a new segment
    pub fn new(
        direction: PenDirection,
        start_pen_idx: usize,
        end_pen_idx: usize,
        start_price: f64,
        end_price: f64,
    ) -> Self {
        Self {
            direction,
            start_pen_idx,
            end_pen_idx,
            start_price,
            end_price,
            contained_pens: Vec::new(),
            confirmed: false,
        }
    }

    /// Calculate segment magnitude
    pub fn magnitude(&self) -> f64 {
        (self.end_price - self.start_price).abs()
    }

    /// Number of pens in segment
    pub fn pen_count(&self) -> usize {
        self.contained_pens.len()
    }
}

/// Feature element for segment division
#[derive(Debug, Clone)]
pub struct FeatureElement {
    /// High price of feature
    pub high: f64,
    /// Low price of feature
    pub low: f64,
    /// Direction of the pen that forms this feature
    pub direction: PenDirection,
    /// Index in original pen sequence
    pub pen_idx: usize,
    /// Whether this feature has a gap with previous
    pub has_gap: bool,
}

/// Configuration for segment division
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SegmentConfig {
    /// Use strict feature sequence method
    pub use_feature_sequence: bool,
    /// Handle inclusion relationships in feature sequence
    pub handle_inclusion: bool,
    /// Require minimum 3 features per segment
    pub min_features_per_segment: usize,
    /// Price threshold for gap detection
    pub gap_threshold: f64,
}

impl Default for SegmentConfig {
    fn default() -> Self {
        Self {
            use_feature_sequence: true,
            handle_inclusion: true,
            min_features_per_segment: 3,
            gap_threshold: 0.0, // Any gap counts
        }
    }
}

/// Segment calculator implementing feature sequence method
pub struct SegmentCalculator {
    config: SegmentConfig,
}

impl SegmentCalculator {
    /// Create new segment calculator
    pub fn new(config: SegmentConfig) -> Self {
        Self { config }
    }

    /// Create with defaults
    pub fn with_defaults() -> Self {
        Self::new(SegmentConfig::default())
    }

    /// Divide pens into segments using feature sequence method
    /// 
    /// Feature Sequence Method (特征序列方法):
    /// 1. Up segment: Use downward pens as feature sequence
    /// 2. Down segment: Use upward pens as feature sequence
    /// 3. Two cases:
    ///    - Case 1 (无缺口): No gap between features → standard division
    ///    - Case 2 (有缺口): Gap exists → need confirmation from next feature
    pub fn divide_segments(&self, pens: &[Pen]) -> Vec<Segment> {
        if pens.len() < 3 {
            return Vec::new();
        }

        let mut segments = Vec::new();
        let mut current_segment_start = 0;

        // Build feature sequences
        let features = self.build_feature_sequence(pens);
        
        if features.len() < 3 {
            return Vec::new();
        }

        // Process feature sequence for segment breaks
        let mut i = 0;
        while i < features.len() - 2 {
            // Check for potential segment break
            if let Some(break_point) = self.find_segment_break(&features, i) {
                // Create segment from start to break point
                if break_point.pen_idx > current_segment_start {
                    let segment = self.create_segment(
                        pens,
                        current_segment_start,
                        break_point.pen_idx,
                    );
                    if segment.pen_count() >= self.config.min_features_per_segment - 1 {
                        segments.push(segment);
                        current_segment_start = break_point.pen_idx;
                    }
                }
                i = break_point.pen_idx;
            } else {
                i += 1;
            }
        }

        // Add final segment if it has enough pens
        if current_segment_start < pens.len() - 1 {
            let final_segment = self.create_segment(
                pens,
                current_segment_start,
                pens.len() - 1,
            );
            if final_segment.pen_count() >= 2 {
                segments.push(final_segment);
            }
        }

        segments
    }

    /// Build feature sequence from pens
    /// 
    /// For upward segments: use downward pens (笔) as features
    /// For downward segments: use upward pens (笔) as features
    fn build_feature_sequence(&self, pens: &[Pen]) -> Vec<FeatureElement> {
        let mut features = Vec::new();

        for (i, pen) in pens.iter().enumerate() {
            let feature = FeatureElement {
                high: pen.start_price.max(pen.end_price),
                low: pen.start_price.min(pen.end_price),
                direction: pen.direction,
                pen_idx: i,
                has_gap: false,
            };

            // Check for gap with previous feature
            if let Some(prev) = features.last() {
                feature.has_gap = self.has_gap(prev, &feature);
            }

            features.push(feature);
        }

        // Handle inclusion relationships if configured
        if self.config.handle_inclusion {
            features = self.process_feature_inclusion(features);
        }

        features
    }

    /// Check if there's a gap between two features
    fn has_gap(&self, prev: &FeatureElement, curr: &FeatureElement) -> bool {
        match (prev.direction, curr.direction) {
            // Both upward features
            (PenDirection::Up, PenDirection::Up) => {
                // Gap if curr.low > prev.high
                curr.low > prev.high + self.config.gap_threshold
            }
            // Both downward features
            (PenDirection::Down, PenDirection::Down) => {
                // Gap if curr.high < prev.low
                curr.high < prev.low - self.config.gap_threshold
            }
            _ => false,
        }
    }

    /// Process inclusion relationships in feature sequence
    /// 
    /// Inclusion handling (包含关系处理):
    /// - Upward trend: Use higher high + higher low (高高 + 低高)
    /// - Downward trend: Use lower high + lower low (低低 + 高低)
    fn process_feature_inclusion(&self, features: Vec<FeatureElement>) -> Vec<FeatureElement> {
        if features.is_empty() {
            return features;
        }

        let mut processed = vec![features[0].clone()];

        for i in 1..features.len() {
            let prev = processed.last().unwrap();
            let curr = &features[i];

            // Check for inclusion
            let is_included = (curr.high <= prev.high && curr.low >= prev.low) ||
                             (curr.high >= prev.high && curr.low <= prev.low);

            if is_included {
                // Merge features based on trend direction
                let direction = if processed.len() > 1 {
                    // Determine trend from previous direction
                    if processed[processed.len() - 1].high > processed[processed.len() - 2].high {
                        PenDirection::Up
                    } else {
                        PenDirection::Down
                    }
                } else {
                    PenDirection::Up // Default
                };

                let merged = match direction {
                    PenDirection::Up => FeatureElement {
                        high: prev.high.max(curr.high),
                        low: prev.low.max(curr.low),
                        direction: prev.direction,
                        pen_idx: curr.pen_idx,
                        has_gap: prev.has_gap,
                    },
                    PenDirection::Down => FeatureElement {
                        high: prev.high.min(curr.high),
                        low: prev.low.min(curr.low),
                        direction: prev.direction,
                        pen_idx: curr.pen_idx,
                        has_gap: prev.has_gap,
                    },
                };

                processed.pop();
                processed.push(merged);
            } else {
                processed.push(curr.clone());
            }
        }

        processed
    }

    /// Find segment break point in feature sequence
    /// 
    /// Two-Case Judgment (两情况判断):
    /// - Case 1 (无缺口): No gap → break when feature sequence makes new high/low
    /// - Case 2 (有缺口): Gap exists → need confirmation from next feature
    fn find_segment_break(&self, features: &[FeatureElement], start: usize) -> Option<&FeatureElement> {
        if start + 2 >= features.len() {
            return None;
        }

        let first = &features[start];
        let second = &features[start + 1];
        let third = &features[start + 2];

        // Check for gap between first and second
        let has_gap = second.has_gap;

        if !has_gap {
            // Case 1: No gap (无缺口)
            // Standard division: break when third feature breaks first's high/low
            match first.direction {
                PenDirection::Up => {
                    // Upward segment: break when third makes lower low
                    if third.low < first.low {
                        return Some(second);
                    }
                }
                PenDirection::Down => {
                    // Downward segment: break when third makes higher high
                    if third.high > first.high {
                        return Some(second);
                    }
                }
            }
        } else {
            // Case 2: With gap (有缺口)
            // Need confirmation: wait for next feature to confirm the break
            if start + 3 < features.len() {
                let fourth = &features[start + 3];
                match first.direction {
                    PenDirection::Up => {
                        // Confirm if fourth also makes lower low
                        if fourth.low < first.low && third.low < first.low {
                            return Some(third);
                        }
                    }
                    PenDirection::Down => {
                        // Confirm if fourth also makes higher high
                        if fourth.high > first.high && third.high > first.high {
                            return Some(third);
                        }
                    }
                }
            }
        }

        None
    }

    /// Create segment from pen range
    fn create_segment(&self, pens: &[Pen], start_idx: usize, end_idx: usize) -> Segment {
        let start_pen = &pens[start_idx];
        let end_pen = &pens[end_idx];

        let mut segment = Segment::new(
            start_pen.direction,
            start_idx,
            end_idx,
            start_pen.start_price,
            end_pen.end_price,
        );

        // Add contained pens
        for i in start_idx..=end_idx {
            if i < pens.len() {
                segment.contained_pens.push(pens[i].clone());
            }
        }

        // Mark as confirmed if it has successor
        segment.confirmed = end_idx < pens.len() - 1;

        segment
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pen::Pen;

    #[test]
    fn test_segment_creation() {
        let calc = SegmentCalculator::with_defaults();
        
        // Create test pens (up, down, up, down pattern)
        let pens = vec![
            Pen::up(0, 2, 100.0, 105.0),
            Pen::down(2, 4, 105.0, 102.0),
            Pen::up(4, 6, 102.0, 108.0),
            Pen::down(6, 8, 108.0, 104.0),
            Pen::up(8, 10, 104.0, 110.0),
        ];

        let segments = calc.divide_segments(&pens);
        
        // Should identify at least one segment
        assert!(!segments.is_empty() || pens.len() < 3);
    }

    #[test]
    fn test_gap_detection() {
        let calc = SegmentCalculator::with_defaults();
        
        let feat1 = FeatureElement {
            high: 105.0,
            low: 100.0,
            direction: PenDirection::Up,
            pen_idx: 0,
            has_gap: false,
        };

        let feat2 = FeatureElement {
            high: 110.0,
            low: 106.0, // Gap: low (106) > prev high (105)
            direction: PenDirection::Up,
            pen_idx: 1,
            has_gap: false,
        };

        assert!(calc.has_gap(&feat1, &feat2));
    }
}
