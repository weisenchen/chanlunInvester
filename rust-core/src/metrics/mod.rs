//! Metrics Collection Module
//! 
//! Performance and trading metrics for monitoring and analysis.

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, AtomicU32, Ordering};
use std::time::{Instant, Duration};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Trading metrics snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingMetrics {
    /// Total K-lines processed
    pub klines_processed: u64,
    /// Total pens identified
    pub pens_identified: u64,
    /// Total segments identified
    pub segments_identified: u64,
    /// Average processing latency (ms)
    pub avg_latency_ms: f64,
    /// Last update timestamp
    pub last_update: DateTime<Utc>,
    /// Uptime in seconds
    pub uptime_secs: u64,
}

/// Performance metrics collector
pub struct MetricsCollector {
    start_time: Instant,
    klines_processed: AtomicU64,
    pens_identified: AtomicU64,
    segments_identified: AtomicU64,
    total_latency_ms: AtomicU64,
    latency_count: AtomicU64,
    errors_count: AtomicU32,
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

impl MetricsCollector {
    /// Create new metrics collector
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            klines_processed: AtomicU64::new(0),
            pens_identified: AtomicU64::new(0),
            segments_identified: AtomicU64::new(0),
            total_latency_ms: AtomicU64::new(0),
            latency_count: AtomicU64::new(0),
            errors_count: AtomicU32::new(0),
        }
    }

    /// Record K-lines processed
    pub fn record_klines(&self, count: usize) {
        self.klines_processed.fetch_add(count as u64, Ordering::SeqCst);
    }

    /// Record pens identified
    pub fn record_pens(&self, count: usize) {
        self.pens_identified.fetch_add(count as u64, Ordering::SeqCst);
    }

    /// Record segments identified
    pub fn record_segments(&self, count: usize) {
        self.segments_identified.fetch_add(count as u64, Ordering::SeqCst);
    }

    /// Record processing latency
    pub fn record_latency(&self, latency_ms: u64) {
        self.total_latency_ms.fetch_add(latency_ms, Ordering::SeqCst);
        self.latency_count.fetch_add(1, Ordering::SeqCst);
    }

    /// Record an error
    pub fn record_error(&self) {
        self.errors_count.fetch_add(1, Ordering::SeqCst);
    }

    /// Get current metrics snapshot
    pub fn get_metrics(&self) -> TradingMetrics {
        let klines = self.klines_processed.load(Ordering::SeqCst);
        let pens = self.pens_identified.load(Ordering::SeqCst);
        let segments = self.segments_identified.load(Ordering::SeqCst);
        let total_latency = self.total_latency_ms.load(Ordering::SeqCst);
        let latency_count = self.latency_count.load(Ordering::SeqCst);
        let errors = self.errors_count.load(Ordering::SeqCst);

        let avg_latency = if latency_count > 0 {
            total_latency as f64 / latency_count as f64
        } else {
            0.0
        };

        let uptime = self.start_time.elapsed().as_secs();

        TradingMetrics {
            klines_processed: klines,
            pens_identified: pens,
            segments_identified: segments,
            avg_latency_ms: avg_latency,
            last_update: Utc::now(),
            uptime_secs: uptime,
        }
    }

    /// Get error count
    pub fn error_count(&self) -> u32 {
        self.errors_count.load(Ordering::SeqCst)
    }

    /// Reset all counters
    pub fn reset(&self) {
        self.klines_processed.store(0, Ordering::SeqCst);
        self.pens_identified.store(0, Ordering::SeqCst);
        self.segments_identified.store(0, Ordering::SeqCst);
        self.total_latency_ms.store(0, Ordering::SeqCst);
        self.latency_count.store(0, Ordering::SeqCst);
        self.errors_count.store(0, Ordering::SeqCst);
    }
}

/// Latency tracker for detailed timing
pub struct LatencyTracker {
    start: Instant,
}

impl LatencyTracker {
    pub fn start() -> Self {
        Self {
            start: Instant::now(),
        }
    }

    pub fn elapsed_ms(&self) -> u64 {
        self.start.elapsed().as_millis() as u64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrics_collection() {
        let collector = MetricsCollector::new();
        
        collector.record_klines(100);
        collector.record_pens(5);
        collector.record_segments(2);
        collector.record_latency(50);
        collector.record_latency(30);

        let metrics = collector.get_metrics();
        
        assert_eq!(metrics.klines_processed, 100);
        assert_eq!(metrics.pens_identified, 5);
        assert_eq!(metrics.segments_identified, 2);
        assert_eq!(metrics.avg_latency_ms, 40.0);
        assert!(metrics.uptime_secs >= 0);
    }

    #[test]
    fn test_latency_tracker() {
        let tracker = LatencyTracker::start();
        std::thread::sleep(Duration::from_millis(10));
        let elapsed = tracker.elapsed_ms();
        assert!(elapsed >= 10);
    }
}
