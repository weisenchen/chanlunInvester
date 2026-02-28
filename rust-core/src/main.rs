//! Trading Server Entry Point
//! 
//! Main binary for the Rust trading engine with gRPC server
//! and health monitoring.

use anyhow::Result;
use tracing::{info, error};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod kline;
mod pen;
mod segment;
mod indicators;
mod health;
mod grpc;

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

    // Initialize health monitor
    let health_monitor = health::HealthMonitor::new(&config).await?;
    info!("Health monitor initialized");

    // Start gRPC server
    let addr = format!("{}:{}", config.server.host, config.server.port).parse()?;
    info!("Starting gRPC server on {}", addr);

    // TODO: Implement gRPC server startup
    // grpc::start_server(addr, health_monitor).await?;

    info!("Trading server started successfully");
    
    // Keep running
    tokio::signal::ctrl_c().await?;
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
                port: 50051,
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
