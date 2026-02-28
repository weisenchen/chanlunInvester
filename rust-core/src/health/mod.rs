//! Health Monitoring and Automatic Failover Module (Simplified)

use tracing::{info, warn};

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

/// Health monitor for dual-engine architecture
#[derive(Clone)]
pub struct HealthMonitor {
    active_engine: ActiveEngine,
    config: HealthConfig,
}

impl HealthMonitor {
    pub fn new(config: HealthConfig) -> Self {
        Self {
            active_engine: ActiveEngine::Rust,
            config,
        }
    }

    pub fn with_defaults() -> Self {
        Self::new(HealthConfig::default())
    }

    pub fn active_engine(&self) -> ActiveEngine {
        self.active_engine
    }

    pub fn status(&self) -> HealthStatus {
        HealthStatus {
            active_engine: self.active_engine,
            failover_enabled: self.config.failover_enabled,
        }
    }
}

/// Current health status
#[derive(Debug, Clone)]
pub struct HealthStatus {
    pub active_engine: ActiveEngine,
    pub failover_enabled: bool,
}
