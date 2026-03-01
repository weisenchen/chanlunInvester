//! Health Monitoring and Automatic Failover Module

use std::sync::atomic::{AtomicU32, AtomicBool, Ordering};
use tracing::{info, warn, error};

/// Which engine is currently active
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ActiveEngine {
    Rust,
    Python,
}

impl Default for ActiveEngine {
    fn default() -> Self {
        ActiveEngine::Rust
    }
}

impl ActiveEngine {
    pub fn as_str(&self) -> &'static str {
        match self {
            ActiveEngine::Rust => "rust",
            ActiveEngine::Python => "python",
        }
    }
}

/// Configuration for health monitoring
#[derive(Debug, Clone)]
pub struct HealthConfig {
    pub check_interval_ms: u64,
    pub max_failures_before_switch: u32,
    pub response_timeout_ms: u64,
    pub failover_enabled: bool,
}

impl Default for HealthConfig {
    fn default() -> Self {
        Self {
            check_interval_ms: 1000,
            max_failures_before_switch: 3,
            response_timeout_ms: 500,
            failover_enabled: true,
        }
    }
}

/// Health monitor for dual-engine architecture with atomic state
pub struct HealthMonitor {
    active_engine: AtomicU32, // 0 = Rust, 1 = Python
    rust_failures: AtomicU32,
    python_failures: AtomicU32,
    failover_enabled: AtomicBool,
    max_failures: AtomicU32,
}

impl Default for HealthMonitor {
    fn default() -> Self {
        Self::new(HealthConfig::default())
    }
}

impl HealthMonitor {
    pub fn new(config: HealthConfig) -> Self {
        Self {
            active_engine: AtomicU32::new(0), // Rust
            rust_failures: AtomicU32::new(0),
            python_failures: AtomicU32::new(0),
            failover_enabled: AtomicBool::new(config.failover_enabled),
            max_failures: AtomicU32::new(config.max_failures_before_switch),
        }
    }

    pub fn with_defaults() -> Self {
        Self::new(HealthConfig::default())
    }

    /// Get currently active engine
    pub fn active_engine(&self) -> ActiveEngine {
        match self.active_engine.load(Ordering::SeqCst) {
            0 => ActiveEngine::Rust,
            _ => ActiveEngine::Python,
        }
    }

    /// Record failure for specified engine
    pub fn record_failure(&self, engine: ActiveEngine) {
        let failures = match engine {
            ActiveEngine::Rust => &self.rust_failures,
            ActiveEngine::Python => &self.python_failures,
        };
        
        let count = failures.fetch_add(1, Ordering::SeqCst) + 1;
        let max = self.max_failures.load(Ordering::SeqCst);
        
        warn!("{} engine failure #{} (max: {})", engine.as_str(), count, max);
        
        // Check if failover needed
        if count >= max && self.failover_enabled.load(Ordering::SeqCst) {
            self.perform_failover(engine);
        }
    }

    /// Record success for specified engine (resets failure counter)
    pub fn record_success(&self, engine: ActiveEngine) {
        let failures = match engine {
            ActiveEngine::Rust => &self.rust_failures,
            ActiveEngine::Python => &self.python_failures,
        };
        
        let prev = failures.swap(0, Ordering::SeqCst);
        if prev > 0 {
            info!("{} engine recovered (failures: {} -> 0)", engine.as_str(), prev);
        }
    }

    /// Perform failover to backup engine
    fn perform_failover(&self, failed_engine: ActiveEngine) {
        let new_engine = match failed_engine {
            ActiveEngine::Rust => {
                info!("⚠️  FAILOVER: Rust → Python (Rust exceeded max failures)");
                ActiveEngine::Python
            }
            ActiveEngine::Python => {
                info!("⚠️  FAILBACK: Python → Rust (Python exceeded max failures)");
                ActiveEngine::Rust
            }
        };

        self.active_engine.store(new_engine as u32, Ordering::SeqCst);
        
        // Reset failure counters
        self.rust_failures.store(0, Ordering::SeqCst);
        self.python_failures.store(0, Ordering::SeqCst);
        
        info!("✓ Failover complete: {} is now active", new_engine.as_str());
    }

    /// Get current status
    pub fn status(&self) -> HealthStatus {
        HealthStatus {
            active_engine: self.active_engine(),
            rust_failures: self.rust_failures.load(Ordering::SeqCst),
            python_failures: self.python_failures.load(Ordering::SeqCst),
            failover_enabled: self.failover_enabled.load(Ordering::SeqCst),
        }
    }

    /// Manually trigger failover (for testing/admin)
    pub fn force_failover(&self) -> ActiveEngine {
        let current = self.active_engine();
        let new_engine = match current {
            ActiveEngine::Rust => ActiveEngine::Python,
            ActiveEngine::Python => ActiveEngine::Rust,
        };
        
        info!("Manual failover: {} → {}", current.as_str(), new_engine.as_str());
        self.active_engine.store(new_engine as u32, Ordering::SeqCst);
        new_engine
    }
}

/// Current health status
#[derive(Debug, Clone)]
pub struct HealthStatus {
    pub active_engine: ActiveEngine,
    pub rust_failures: u32,
    pub python_failures: u32,
    pub failover_enabled: bool,
}
