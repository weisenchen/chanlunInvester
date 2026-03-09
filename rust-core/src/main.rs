//! Trading Server Entry Point
//! 
//! Main binary for the Rust trading engine with gRPC server
//! and health monitoring.

use anyhow::Result;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use std::sync::Arc;
use tokio::sync::Mutex;
use trading_core::{health, grpc};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    info!("Starting Trading Server v0.1.0");
    info!("Architecture: Rust primary + Python backup");

    // Load configuration
    let config = load_config()?;
    info!("Configuration loaded: {:?}", config);

    // Initialize health monitor with config from health module
    let health_cfg = health::HealthConfig {
        check_interval_ms: config.health.check_interval_ms,
        failover_enabled: config.health.failover_enabled,
        rust_port: config.server.port,
        python_port: 50056, // Placeholder for python engine
        ..Default::default()
    };
    
    let health_monitor = Arc::new(Mutex::new(health::HealthMonitor::new(health_cfg)));
    info!("Health monitor initialized");

    // Start gRPC server
    let addr = format!("{}:{}", config.server.host, config.server.port).parse()?;
    info!("Starting gRPC server on {}", addr);

    // Start health monitoring in a separate task
    let monitor_clone = Arc::clone(&health_monitor);
    tokio::spawn(async move {
        let mut monitor = monitor_clone.lock().await;
        monitor.run_monitoring_loop().await;
    });

    // Start gRPC server and block on it
    grpc::start_server(addr, Arc::clone(&health_monitor)).await
        .map_err(|e| anyhow::anyhow!("gRPC server failed: {}", e))?;

    info!("Shutting down...");
    Ok(())
}

fn load_config() -> Result<Config> {
    // TODO: Load from config/default.yaml
    Ok(Config::default())
}

#[derive(Debug, Clone)]
struct Config {
    server: ServerConfig,
    macd: MacdConfig,
    pen: PenConfig,
    segment: SegmentConfig,
    health: HealthConfig,
}

#[derive(Debug, Clone)]
struct ServerConfig {
    host: String,
    port: u16,
}

#[derive(Debug, Clone)]
struct MacdConfig {
    fast_period: u32,
    slow_period: u32,
    signal_period: u32,
}

#[derive(Debug, Clone)]
struct PenConfig {
    definition: String,
    strict_validation: bool,
}

#[derive(Debug, Clone)]
struct SegmentConfig {
    feature_sequence_strict: bool,
    handle_inclusion: bool,
}

#[derive(Debug, Clone)]
struct HealthConfig {
    check_interval_ms: u64,
    failover_enabled: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            server: ServerConfig {
                host: "0.0.0.0".to_string(),
                port: 50055,
            },
            macd: MacdConfig {
                fast_period: 12,
                slow_period: 26,
                signal_period: 9,
            },
            pen: PenConfig {
                definition: "new_3kline".to_string(),
                strict_validation: true,
            },
            segment: SegmentConfig {
                feature_sequence_strict: true,
                handle_inclusion: true,
            },
            health: HealthConfig {
                check_interval_ms: 1000,
                failover_enabled: true,
            },
        }
    }
}
