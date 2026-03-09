//! Line Segment (线段) Detection Module
//! 
//! Implements line segment division based on Lesson 67, 68, 71, 78
//! using feature sequence analysis.

use crate::pen::{Pen, PenDirection};
use serde::{Deserialize, Serialize};

/// Line segment structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Segment {
    /// Segment direction
    pub direction: PenDirection,
    /// Starting K-line index
    pub start_idx: usize,
    /// Ending K-line index
    pub end_idx: usize,
    /// Starting price
    pub start_price: f64,
    /// Ending price
    pub end_price: f64,
    /// Number of pens in this segment
    pub pen_count: usize,
    /// Whether the feature sequence has a gap
    pub has_gap: bool,
    /// Whether this segment is confirmed
    pub confirmed: bool,
}

impl Segment {
    /// Check if this is an upward segment
    pub fn is_up(&self) -> bool {
        self.direction == PenDirection::Up
    }

    /// Check if this is a downward segment
    pub fn is_down(&self) -> bool {
        self.direction == PenDirection::Down
    }

    /// Calculate segment magnitude
    pub fn magnitude(&self) -> f64 {
        (self.end_price - self.start_price).abs()
    }
}

/// Segment calculator implementing feature sequence analysis
pub struct SegmentCalculator {
    min_pens: usize,
}

impl SegmentCalculator {
    /// Create a new segment calculator
    pub fn new(min_pens: usize) -> Self {
        Self { min_pens }
    }

    /// Create with default settings (minimum 3 pens)
    pub fn with_defaults() -> Self {
        Self::new(3)
    }

    /// Detect all segments in a pen sequence
    pub fn detect_segments(&self, pens: &[Pen]) -> Vec<Segment> {
        if pens.len() < self.min_pens {
            return Vec::new();
        }

        let mut segments = Vec::new();
        let mut i = 0;

        while i <= pens.len() - self.min_pens {
            if let Some(segment) = self.try_build_segment(pens, i) {
                i += segment.pen_count;
                segments.push(segment);
            } else {
                i += 1;
            }
        }

        segments
    }

    /// Try to build a segment starting from a specific pen index
    fn try_build_segment(&self, pens: &[Pen], start: usize) -> Option<Segment> {
        if start >= pens.len() {
            return None;
        }

        let first_pen = &pens[start];
        let direction = first_pen.direction;
        
        // Feature sequence consists of pens in the same direction as the segment
        let mut feature_sequence = vec![first_pen];
        
        for i in (start + 1)..pens.len() {
            let pen = &pens[i];
            
            if pen.direction == direction {
                feature_sequence.push(pen);
                
                // For a segment to end, we need at least 3 elements in feature sequence
                // or a clear reversal/fractal in the feature sequence
                if feature_sequence.len() >= 2 {
                    let has_gap = self.check_gap(&feature_sequence);
                    let is_fractal = self.check_feature_fractal(&feature_sequence);
                    
                    if is_fractal {
                        let last_pen = feature_sequence.last().unwrap();
                        let pen_count = i - start + 1;
                        
                        return Some(Segment {
                            direction,
                            start_idx: first_pen.start_idx,
                            end_idx: last_pen.end_idx,
                            start_price: first_pen.start_price,
                            end_price: last_pen.end_price,
                            pen_count,
                            has_gap,
                            confirmed: true,
                        });
                    }
                }
            }
        }

        None
    }

    /// Check if feature sequence has a gap
    fn check_gap(&self, feature_seq: &[&Pen]) -> bool {
        if feature_seq.len() < 2 {
            return false;
        }

        let elem1 = feature_seq[0];
        let elem2 = feature_seq[1];

        match elem1.direction {
            PenDirection::Up => elem1.end_price < elem2.start_price,
            PenDirection::Down => elem1.end_price > elem2.start_price,
        }
    }

    /// Check for fractal in feature sequence
    fn check_feature_fractal(&self, feature_seq: &[&Pen]) -> bool {
        if feature_seq.len() < 3 {
            // Simplified: 2 elements might be enough for a basic break
            return feature_seq.len() >= 2;
        }

        let last_three = &feature_seq[feature_seq.len() - 3..];
        
        match last_three[0].direction {
            PenDirection::Up => {
                let m_high = last_three[1].end_price;
                m_high > last_three[0].end_price && m_high > last_three[2].end_price
            }
            PenDirection::Down => {
                let m_low = last_three[1].end_price;
                m_low < last_three[0].end_price && m_low < last_three[2].end_price
            }
        }
    }
}
