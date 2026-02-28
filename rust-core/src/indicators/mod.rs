//! Indicators Module
//! 
//! Technical indicators including configurable MACD.

use crate::kline::Kline;
use serde::{Deserialize, Serialize};

/// MACD Indicator with configurable parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MACDConfig {
    /// Fast EMA period (default: 12)
    pub fast_period: usize,
    /// Slow EMA period (default: 26)
    pub slow_period: usize,
    /// Signal EMA period (default: 9)
    pub signal_period: usize,
}

impl Default for MACDConfig {
    fn default() -> Self {
        Self {
            fast_period: 12,
            slow_period: 26,
            signal_period: 9,
        }
    }
}

/// MACD values for a single period
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MACDValue {
    /// MACD line (DIF): Fast EMA - Slow EMA
    pub macd_line: f64,
    /// Signal line (DEA): EMA of MACD line
    pub signal_line: f64,
    /// Histogram: MACD line - Signal line
    pub histogram: f64,
}

impl MACDValue {
    pub fn new(macd_line: f64, signal_line: f64) -> Self {
        Self {
            macd_line,
            signal_line,
            histogram: macd_line - signal_line,
        }
    }
}

/// MACD Calculator
pub struct MACDCalculator {
    config: MACDConfig,
}

impl MACDCalculator {
    pub fn new(config: MACDConfig) -> Self {
        Self { config }
    }

    pub fn with_defaults() -> Self {
        Self::new(MACDConfig::default())
    }

    /// Calculate MACD for a series of K-lines
    /// 
    /// Uses close prices for calculation
    pub fn calculate(&self, klines: &[Kline]) -> Vec<MACDValue> {
        if klines.len() < self.config.slow_period {
            return Vec::new();
        }

        let closes: Vec<f64> = klines.iter().map(|k| k.close).collect();
        
        // Calculate EMAs
        let fast_ema = self.calculate_ema(&closes, self.config.fast_period);
        let slow_ema = self.calculate_ema(&closes, self.config.slow_period);
        
        // Calculate MACD line (DIF)
        let macd_line: Vec<f64> = fast_ema
            .iter()
            .zip(slow_ema.iter())
            .map(|(f, s)| f - s)
            .collect();
        
        // Calculate Signal line (DEA) - EMA of MACD line
        let signal_line = self.calculate_ema(&macd_line, self.config.signal_period);
        
        // Combine into MACD values
        macd_line
            .iter()
            .zip(signal_line.iter())
            .map(|(ml, sl)| MACDValue::new(*ml, *sl))
            .collect()
    }

    /// Calculate Exponential Moving Average
    fn calculate_ema(&self, data: &[f64], period: usize) -> Vec<f64> {
        if data.is_empty() || period == 0 {
            return Vec::new();
        }

        let mut ema = Vec::with_capacity(data.len());
        let multiplier = 2.0 / (period + 1) as f64;

        // First EMA is SMA
        let initial_sma: f64 = data[..period].iter().sum::<f64>() / period as f64;
        ema.push(initial_sma);

        // Calculate remaining EMAs
        for i in period..data.len() {
            let prev_ema = ema.last().unwrap();
            let current_ema = (data[i] - prev_ema) * multiplier + prev_ema;
            ema.push(current_ema);
        }

        // Pad with initial values for indices < period
        let mut padded = vec![initial_sma; period - 1];
        padded.append(&mut ema);
        padded
    }

    /// Calculate MACD histogram area for a range (used for divergence detection)
    pub fn calculate_area(&self, macd_values: &[MACDValue], start: usize, end: usize) -> f64 {
        if start >= end || end > macd_values.len() {
            return 0.0;
        }

        macd_values[start..end]
            .iter()
            .map(|v| v.histogram.abs())
            .sum()
    }

    /// Check for bullish divergence (price makes lower low, MACD makes higher low)
    pub fn is_bullish_divergence(
        &self,
        macd_values: &[MACDValue],
        price_low_a: f64,
        price_low_b: f64,
        macd_idx_a: usize,
        macd_idx_b: usize,
    ) -> bool {
        // Price makes lower low
        if price_low_b >= price_low_a {
            return false;
        }

        // MACD makes higher low (bullish divergence)
        if macd_idx_b >= macd_values.len() || macd_idx_a >= macd_values.len() {
            return false;
        }

        macd_values[macd_idx_b].histogram > macd_values[macd_idx_a].histogram
    }

    /// Check for bearish divergence (price makes higher high, MACD makes lower high)
    pub fn is_bearish_divergence(
        &self,
        macd_values: &[MACDValue],
        price_high_a: f64,
        price_high_b: f64,
        macd_idx_a: usize,
        macd_idx_b: usize,
    ) -> bool {
        // Price makes higher high
        if price_high_b <= price_high_a {
            return false;
        }

        // MACD makes lower high (bearish divergence)
        if macd_idx_b >= macd_values.len() || macd_idx_a >= macd_values.len() {
            return false;
        }

        macd_values[macd_idx_b].histogram < macd_values[macd_idx_a].histogram
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::kline::Kline;
    use chrono::Utc;

    #[test]
    fn test_macd_calculation() {
        let calc = MACDCalculator::with_defaults();
        
        // Create test data (enough for MACD 12/26/9)
        let klines: Vec<Kline> = (0..50)
            .map(|i| Kline::new(
                Utc::now(),
                100.0 + i as f64,
                105.0 + i as f64,
                95.0 + i as f64,
                100.0 + i as f64,
                1000.0,
            ))
            .collect();

        let macd_values = calc.calculate(&klines);
        
        // Should have values (with padding for EMA warmup)
        assert!(!macd_values.is_empty());
        assert_eq!(macd_values.len(), klines.len());
    }

    #[test]
    fn test_macd_custom_config() {
        let config = MACDConfig {
            fast_period: 8,
            slow_period: 17,
            signal_period: 9,
        };
        let calc = MACDCalculator::new(config);
        
        // Test with shorter data period
        let klines: Vec<Kline> = (0..30)
            .map(|i| Kline::new(Utc::now(), 100.0, 100.0, 100.0, 100.0 + i as f64, 1000.0))
            .collect();

        let macd_values = calc.calculate(&klines);
        assert_eq!(macd_values.len(), klines.len());
    }
}
