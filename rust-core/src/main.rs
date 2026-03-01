//! Trading Server Entry Point
//! 
//! Main binary for the Rust trading engine with gRPC server
//! and health monitoring.

use anyhow::Result;
use tracing::{info, error, warn};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod kline;
mod pen;
mod segment;
mod indicators;
mod health;
mod grpc;
mod metrics;

use metrics::{MetricsCollector, LatencyTracker};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    info!("╔════════════════════════════════════════════════════════╗");
    info!("║     ChanLun Trading Server v0.1.0                      ║");
    info!("╠════════════════════════════════════════════════════════╣");
    info!("║  Architecture: Rust primary + Python backup            ║");
    info!("║  Pen Theory: New 3-K-line definition (新笔)            ║");
    info!("║  Segments: Feature sequence method (特征序列)          ║");
    info!("╚════════════════════════════════════════════════════════╝");

    // Load configuration
    let config = load_config()?;
    info!("Configuration loaded");

    // Initialize metrics collector
    let metrics = MetricsCollector::new();
    info!("Metrics collector initialized");

    // Initialize health monitor
    let health_monitor = health::HealthMonitor::with_defaults();
    info!("Health monitor initialized (active: {:?})", health_monitor.active_engine());

    // Start gRPC server
    let addr = format!("{}:{}", config.server.host, config.server.port).parse()?;
    info!("gRPC server listening on {}", addr);

    // Clone health monitor for gRPC server
    let health_monitor_clone = health_monitor.clone();
    
    // Spawn gRPC server task
    let server_handle = tokio::spawn(async move {
        if let Err(e) = grpc::start_server(addr, health_monitor_clone).await {
            error!("gRPC server error: {}", e);
        }
    });

    info!("✅ Trading server started successfully");
    info!("Press Ctrl+C to shutdown");
    
    // Keep running
    tokio::signal::ctrl_c().await?;
    warn!("Shutdown signal received");
    
    // Get final metrics
    let final_metrics = metrics.get_metrics();
    info!("📊 Final Metrics:");
    info!("   - K-lines processed: {}", final_metrics.klines_processed);
    info!("   - Pens identified: {}", final_metrics.pens_identified);
    info!("   - Segments identified: {}", final_metrics.segments_identified);
    info!("   - Avg latency: {:.2}ms", final_metrics.avg_latency_ms);
    info!("   - Uptime: {}s", final_metrics.uptime_secs);
    
    info!("Shutting down...");
    server_handle.abort();

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
