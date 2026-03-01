//! Buy/Sell Points (买卖点) Detection Module
//! 
//! Implements buy/sell point detection per Lessons 12, 20, 21, 53
//! - First buy/sell point (1 买/1 卖)
//! - Second buy/sell point (2 买/2 卖)
//! - Third buy/sell point (3 买/3 卖)

use crate::pen::{Pen, PenDirection};
use crate::segment::Segment;
use crate::divergence::{DivergenceSignal, DivergenceType, DivergenceLevel};
use serde::{Deserialize, Serialize};

/// Buy/Sell point type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BSPType {
    /// First buy point (1 买) - trend divergence bottom
    Buy1,
    /// Second buy point (2 买) - pullback without new low
    Buy2,
    /// Third buy point (3 买) - break of center then pullback
    Buy3,
    /// First sell point (1 卖) - trend divergence top
    Sell1,
    /// Second sell point (2 卖) - rally without new high
    Sell2,
    /// Third sell point (3 卖) - break of center then rally
    Sell3,
}

impl BSPType {
    pub fn is_buy(&self) -> bool {
        matches!(self, BSPType::Buy1 | BSPType::Buy2 | BSPType::Buy3)
    }

    pub fn is_sell(&self) -> bool {
        matches!(self, BSPType::Sell1 | BSPType::Sell2 | BSPType::Sell3)
    }
}

/// Buy/Sell Point signal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuySellPoint {
    /// Type of buy/sell point
    pub bsp_type: BSPType,
    /// Price level
    pub price: f64,
    /// K-line index
    pub index: usize,
    /// Confidence (0.0 - 1.0)
    pub confidence: f64,
    /// Associated divergence signal (for 1st BSP)
    pub divergence: Option<DivergenceSignal>,
    /// Notes/reasoning
    pub notes: String,
}

/// Configuration for BSP detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BSPConfig {
    /// Minimum confidence threshold
    pub min_confidence: f64,
    /// Enable 1st BSP detection (requires divergence)
    pub enable_bsp1: bool,
    /// Enable 2nd BSP detection
    pub enable_bsp2: bool,
    /// Enable 3rd BSP detection (requires center)
    pub enable_bsp3: bool,
    /// Pullback threshold for 2nd BSP (percentage)
    pub pullback_threshold_pct: f64,
}

impl Default for BSPConfig {
    fn default() -> Self {
        Self {
            min_confidence: 0.6,
            enable_bsp1: true,
            enable_bsp2: true,
            enable_bsp3: true,
            pullback_threshold_pct: 0.382, // Fibonacci 38.2%
        }
    }
}

/// Buy/Sell Point detector
pub struct BSPDetector {
    config: BSPConfig,
}

impl BSPDetector {
    /// Create new BSP detector
    pub fn new(config: BSPConfig) -> Self {
        Self { config }
    }

    /// Create with defaults
    pub fn with_defaults() -> Self {
        Self::new(BSPConfig::default())
    }

    /// Detect all buy/sell points
    pub fn detect_all(
        &self,
        pens: &[Pen],
        segments: &[Segment],
        divergences: &[DivergenceSignal],
    ) -> Vec<BuySellPoint> {
        let mut bsps = Vec::new();

        if self.config.enable_bsp1 {
            bsps.extend(self.detect_bsp1(pens, divergences));
        }

        if self.config.enable_bsp2 {
            bsps.extend(self.detect_bsp2(pens));
        }

        if self.config.enable_bsp3 {
            // Requires center (中枢) detection - placeholder for now
            // bsps.extend(self.detect_bsp3(pens, centers));
        }

        // Filter by confidence
        bsps.retain(|bsp| bsp.confidence >= self.config.min_confidence);

        bsps
    }

    /// Detect First Buy/Sell Points (1 买/1 卖)
    /// 
    /// First Buy Point (1 买):
    /// - Occurs at end of downtrend
    /// - Requires bullish divergence (price lower low, MACD higher low)
    /// - Best when multi-level divergence aligns
    /// 
    /// First Sell Point (1 卖):
    /// - Occurs at end of uptrend
    /// - Requires bearish divergence (price higher high, MACD lower high)
    pub fn detect_bsp1(
        &self,
        pens: &[Pen],
        divergences: &[DivergenceSignal],
    ) -> Vec<BuySellPoint> {
        let mut bsps = Vec::new();

        for div in divergences {
            match div.div_type {
                DivergenceType::Bullish => {
                    // Potential 1st buy point
                    let confidence = self.calculate_bsp1_confidence(div, pens);
                    
                    if confidence >= self.config.min_confidence {
                        bsps.push(BuySellPoint {
                            bsp_type: BSPType::Buy1,
                            price: div.price_b,
                            index: div.index,
                            confidence,
                            divergence: Some(div.clone()),
                            notes: format!(
                                "1st buy point - {} divergence (strength: {:.2})",
                                match div.level {
                                    DivergenceLevel::Pen => "pen-level",
                                    DivergenceLevel::Segment => "segment-level",
                                    DivergenceLevel::MultiLevel => "multi-level",
                                },
                                div.strength
                            ),
                        });
                    }
                }
                DivergenceType::Bearish => {
                    // Potential 1st sell point
                    let confidence = self.calculate_bsp1_confidence(div, pens);
                    
                    if confidence >= self.config.min_confidence {
                        bsps.push(BuySellPoint {
                            bsp_type: BSPType::Sell1,
                            price: div.price_b,
                            index: div.index,
                            confidence,
                            divergence: Some(div.clone()),
                            notes: format!(
                                "1st sell point - {} divergence (strength: {:.2})",
                                match div.level {
                                    DivergenceLevel::Pen => "pen-level",
                                    DivergenceLevel::Segment => "segment-level",
                                    DivergenceLevel::MultiLevel => "multi-level",
                                },
                                div.strength
                            ),
                        });
                    }
                }
            }
        }

        bsps
    }

    /// Calculate confidence for 1st BSP
    fn calculate_bsp1_confidence(&self, div: &DivergenceSignal, pens: &[Pen]) -> f64 {
        let mut confidence = div.strength;

        // Boost confidence for multi-level divergence
        if div.level == DivergenceLevel::MultiLevel {
            confidence = (confidence + 1.0) / 2.0;
        }

        // Boost if divergence occurs after extended trend
        let trend_pens = self.count_consecutive_pens_same_direction(pens, div.index);
        if trend_pens >= 5 {
            confidence = (confidence + 0.8) / 2.0;
        }

        confidence.min(1.0)
    }

    /// Detect Second Buy/Sell Points (2 买/2 卖)
    /// 
    /// Second Buy Point (2 买):
    /// - After 1st buy point confirmed
    /// - Pullback but doesn't make new low
    /// - Entry with better risk/reward than chasing
    /// 
    /// Second Sell Point (2 卖):
    /// - After 1st sell point confirmed
    /// - Rally but doesn't make new high
    pub fn detect_bsp2(&self, pens: &[Pen]) -> Vec<BuySellPoint> {
        let mut bsps = Vec::new();

        if pens.len() < 4 {
            return bsps;
        }

        // Look for pullback patterns
        for i in 2..pens.len() {
            // Check for potential 2nd buy (after bottom)
            if pens[i].direction == PenDirection::Down {
                // Find previous down pen
                for j in (0..i).rev() {
                    if pens[j].direction == PenDirection::Down {
                        // Check if current low is higher than previous low (no new low)
                        if pens[i].end_price > pens[j].end_price {
                            // Pullback without new low - potential 2nd buy
                            let pullback_ratio = self.calculate_pullback_ratio(&pens[j], &pens[i]);
                            
                            if pullback_ratio <= self.config.pullback_threshold_pct {
                                bsps.push(BuySellPoint {
                                    bsp_type: BSPType::Buy2,
                                    price: pens[i].end_price,
                                    index: pens[i].end_idx,
                                    confidence: 0.7,
                                    divergence: None,
                                    notes: format!(
                                        "2nd buy point - pullback without new low (retracement: {:.1}%)",
                                        pullback_ratio * 100.0
                                    ),
                                });
                            }
                            break;
                        }
                    }
                }
            }

            // Check for potential 2nd sell (after top)
            if pens[i].direction == PenDirection::Up {
                for j in (0..i).rev() {
                    if pens[j].direction == PenDirection::Up {
                        // Check if current high is lower than previous high (no new high)
                        if pens[i].end_price < pens[j].end_price {
                            let pullback_ratio = self.calculate_pullback_ratio(&pens[j], &pens[i]);
                            
                            if pullback_ratio <= self.config.pullback_threshold_pct {
                                bsps.push(BuySellPoint {
                                    bsp_type: BSPType::Sell2,
                                    price: pens[i].end_price,
                                    index: pens[i].end_idx,
                                    confidence: 0.7,
                                    divergence: None,
                                    notes: format!(
                                        "2nd sell point - rally without new high (retracement: {:.1}%)",
                                        pullback_ratio * 100.0
                                    ),
                                });
                            }
                            break;
                        }
                    }
                }
            }
        }

        bsps
    }

    /// Detect Third Buy/Sell Points (3 买/3 卖)
    /// 
    /// Third Buy Point (3 买):
    /// - Price breaks above center (中枢)
    /// - Pulls back to test center top
    /// - Doesn't fall back into center
    /// 
    /// Third Sell Point (3 卖):
    /// - Price breaks below center
    /// - Rallies back to test center bottom
    /// - Doesn't rise back into center
    pub fn detect_bsp3(&self, _pens: &[Pen], _segments: &[Segment]) -> Vec<BuySellPoint> {
        // Requires center (中枢) detection
        // Placeholder - would need center module implementation
        Vec::new()
    }

    /// Count consecutive pens in same direction before index
    fn count_consecutive_pens_same_direction(&self, pens: &[Pen], index: usize) -> usize {
        if pens.is_empty() {
            return 0;
        }

        let target_dir = pens[index].direction;
        let mut count = 0;

        for i in (0..=index).rev() {
            if pens[i].direction == target_dir {
                count += 1;
            } else {
                break;
            }
        }

        count
    }

    /// Calculate pullback ratio between two pens
    fn calculate_pullback_ratio(&self, prev: &Pen, curr: &Pen) -> f64 {
        let price_range = (prev.end_price - prev.start_price).abs();
        if price_range == 0.0 {
            return 1.0;
        }

        let pullback = (curr.end_price - prev.end_price).abs();
        pullback / price_range
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bsp_type_classification() {
        assert!(BSPType::Buy1.is_buy());
        assert!(BSPType::Buy2.is_buy());
        assert!(BSPType::Buy3.is_buy());
        assert!(!BSPType::Sell1.is_buy());

        assert!(BSPType::Sell1.is_sell());
        assert!(BSPType::Sell2.is_sell());
        assert!(BSPType::Sell3.is_sell());
        assert!(!BSPType::Buy1.is_sell());
    }

    #[test]
    fn test_bsp_config_defaults() {
        let config = BSPConfig::default();
        assert_eq!(config.min_confidence, 0.6);
        assert!(config.enable_bsp1);
        assert!(config.enable_bsp2);
        assert!(config.enable_bsp3);
        assert_eq!(config.pullback_threshold_pct, 0.382);
    }

    #[test]
    fn test_bsp1_detection_with_divergence() {
        let detector = BSPDetector::with_defaults();
        
        let divergences = vec![
            DivergenceSignal {
                div_type: DivergenceType::Bullish,
                level: DivergenceLevel::Pen,
                price_a: 100.0,
                price_b: 95.0,
                macd_a: -0.5,
                macd_b: -0.3,
                index: 10,
                strength: 0.8,
            }
        ];

        let pens = vec![
            Pen::down(0, 2, 105.0, 100.0),
            Pen::up(2, 4, 100.0, 103.0),
            Pen::down(4, 6, 103.0, 95.0),
        ];

        let bsps = detector.detect_bsp1(&pens, &divergences);
        
        assert_eq!(bsps.len(), 1);
        assert_eq!(bsps[0].bsp_type, BSPType::Buy1);
        assert!(bsps[0].confidence >= 0.6);
    }
}
