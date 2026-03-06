//! Health Monitoring and Automatic Failover Module

use std::time::Duration;
use tokio::time::interval;
use tracing::{info, warn, error, debug};

/// Health status of an engine
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EngineHealth {
    Healthy,
    Degraded,
    Unhealthy,
    Unknown,
}

/// Configuration for health monitoring
#[derive(Debug, Clone)]
pub struct HealthConfig {
    /// Check interval in milliseconds
    pub check_interval_ms: u64,
    /// Maximum consecutive failures before failover
    pub max_failures_before_switch: u32,
    /// Response timeout in milliseconds
    pub response_timeout_ms: u64,
    /// Enable automatic failover
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
pub struct HealthMonitor {
    config: HealthConfig,
    rust_failures: u32,
    python_failures: u32,
    active_engine: ActiveEngine,
}

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

impl HealthMonitor {
    /// Create a new health monitor
    pub fn new(config: HealthConfig) -> Self {
        Self {
            config,
            rust_failures: 0,
            python_failures: 0,
            active_engine: ActiveEngine::Rust,
        }
    }

    /// Create with default configuration
    pub fn with_defaults() -> Self {
        Self::new(HealthConfig::default())
    }

    /// Get the currently active engine
    pub fn active_engine(&self) -> ActiveEngine {
        self.active_engine
    }

    /// Check health of the specified engine
    pub async fn check_engine_health(
        &self,
        engine: ActiveEngine,
    ) -> Result<EngineHealth, Box<dyn std::error::Error>> {
        let (host, port) = match engine {
            ActiveEngine::Rust => ("localhost", 50051),
            ActiveEngine::Python => ("localhost", 50052),
        };

        // TODO: Implement actual gRPC health check
        // For now, simulate with timeout
        let timeout = Duration::from_millis(self.config.response_timeout_ms);
        
        tokio::time::timeout(timeout, async {
            // Simulate health check - replace with actual gRPC call
            // let channel = Channel::from_static(format!("http://{}:{}", host, port))
            //     .connect()
            //     .await?;
            // let mut client = HealthClient::new(channel);
            // let response = client.check(HealthCheckRequest {}).await?;
            Ok(EngineHealth::Healthy)
        })
        .await
        .unwrap_or(Ok(EngineHealth::Unhealthy))
    }

    /// Record a failure for the specified engine
    pub fn record_failure(&mut self, engine: ActiveEngine) {
        match engine {
            ActiveEngine::Rust => {
                self.rust_failures += 1;
                warn!("Rust engine failure #{}", self.rust_failures);
            }
            ActiveEngine::Python => {
                self.python_failures += 1;
                warn!("Python engine failure #{}", self.python_failures);
            }
        }
    }

    /// Record a success for the specified engine (resets failure counter)
    pub fn record_success(&mut self, engine: ActiveEngine) {
        match engine {
            ActiveEngine::Rust => {
                if self.rust_failures > 0 {
                    debug!("Rust engine recovered (failures: {} -> 0)", self.rust_failures);
                    self.rust_failures = 0;
                }
            }
            ActiveEngine::Python => {
                if self.python_failures > 0 {
                    debug!("Python engine recovered (failures: {} -> 0)", self.python_failures);
                    self.python_failures = 0;
                }
            }
        }
    }

    /// Check if failover should occur
    pub fn should_failover(&self) -> bool {
        if !self.config.failover_enabled {
            return false;
        }

        match self.active_engine {
            ActiveEngine::Rust => self.rust_failures >= self.config.max_failures_before_switch,
            ActiveEngine::Python => self.python_failures >= self.config.max_failures_before_switch,
        }
    }

    /// Perform failover to the backup engine
    pub fn perform_failover(&mut self) -> ActiveEngine {
        let previous = self.active_engine;
        
        self.active_engine = match self.active_engine {
            ActiveEngine::Rust => {
                info!("Failing over from Rust to Python engine");
                ActiveEngine::Python
            }
            ActiveEngine::Python => {
                info!("Failing over from Python to Rust engine");
                ActiveEngine::Rust
            }
        };

        // Reset failure counters after failover
        self.rust_failures = 0;
        self.python_failures = 0;

        info!("Failover complete: {:?} is now active", self.active_engine);
        self.active_engine
    }

    /// Run continuous health monitoring loop
    pub async fn run_monitoring_loop(&mut self) {
        let mut interval_tracker = interval(Duration::from_millis(self.config.check_interval_ms));
        
        info!("Starting health monitoring loop (interval: {}ms)", self.config.check_interval_ms);

        loop {
            interval_tracker.tick().await;

            // Check current active engine
            match self.check_engine_health(self.active_engine).await {
                Ok(EngineHealth::Healthy) => {
                    self.record_success(self.active_engine);
                }
                Ok(_) | Err(_) => {
                    self.record_failure(self.active_engine);
                    
                    // Check if failover is needed
                    if self.should_failover() {
                        self.perform_failover();
                    }
                }
            }

            // Also check backup engine health (non-blocking)
            let backup_engine = match self.active_engine {
                ActiveEngine::Rust => ActiveEngine::Python,
                ActiveEngine::Python => ActiveEngine::Rust,
            };

            if let Ok(health) = self.check_engine_health(backup_engine).await {
                match health {
                    EngineHealth::Healthy => {
                        debug!("Backup engine ({:?}) is healthy", backup_engine);
                    }
                    _ => {
                        warn!("Backup engine ({:?}) is not healthy", backup_engine);
                    }
                }
            }
        }
    }

    /// Get current status
    pub fn status(&self) -> HealthStatus {
        HealthStatus {
            active_engine: self.active_engine,
            rust_failures: self.rust_failures,
            python_failures: self.python_failures,
            failover_enabled: self.config.failover_enabled,
        }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_failure_tracking() {
        let mut monitor = HealthMonitor::with_defaults();
        
        // Initial state
        assert_eq!(monitor.active_engine(), ActiveEngine::Rust);
        assert!(!monitor.should_failover());

        // Record failures
        for _ in 0..2 {
            monitor.record_failure(ActiveEngine::Rust);
            assert!(!monitor.should_failover());
        }

        // Third failure should trigger failover
        monitor.record_failure(ActiveEngine::Rust);
        assert!(monitor.should_failover());
    }

    #[test]
    fn test_failover() {
        let mut monitor = HealthMonitor::with_defaults();
        
        // Force failover
        monitor.rust_failures = 3;
        let new_engine = monitor.perform_failover();
        
        assert_eq!(new_engine, ActiveEngine::Python);
        assert_eq!(monitor.active_engine(), ActiveEngine::Python);
        assert_eq!(monitor.rust_failures, 0);
    }

    #[test]
    fn test_recovery() {
        let mut monitor = HealthMonitor::with_defaults();
        
        monitor.record_failure(ActiveEngine::Rust);
        monitor.record_failure(ActiveEngine::Rust);
        assert_eq!(monitor.rust_failures, 2);

        monitor.record_success(ActiveEngine::Rust);
        assert_eq!(monitor.rust_failures, 0);
    }
}
