//! gRPC Service Implementation
//! 
//! Implements the proto-defined `TradingService` for 
//! Rust-Python hybrid communication.

pub mod trading {
    tonic::include_proto!("trading");
}

use tonic::{Request, Response, Status};
use trading::trading_service_server::TradingService;
use crate::health::{HealthMonitor, EngineHealth};
use tokio::sync::Mutex;
use std::sync::Arc;

/// Implementation of the gRPC Trading Service
pub struct TradingServiceHandler {
    health_monitor: Arc<Mutex<HealthMonitor>>,
}

impl TradingServiceHandler {
    /// Create a new service handler
    pub fn new(health_monitor: Arc<Mutex<HealthMonitor>>) -> Self {
        Self { health_monitor }
    }
}

#[tonic::async_trait]
impl TradingService for TradingServiceHandler {
    async fn submit_klines(
        &self,
        _request: Request<trading::SubmitKlinesRequest>,
    ) -> Result<Response<trading::SubmitKlinesResponse>, Status> {
        Ok(Response::new(trading::SubmitKlinesResponse {
            success: true,
            processed_count: 0,
            error_message: String::new(),
        }))
    }

    async fn calculate_pens(
        &self,
        _request: Request<trading::CalculatePensRequest>,
    ) -> Result<Response<trading::CalculatePensResponse>, Status> {
        Ok(Response::new(trading::CalculatePensResponse {
            success: true,
            pens: Vec::new(),
            error_message: String::new(),
        }))
    }

    async fn calculate_segments(
        &self,
        _request: Request<trading::CalculateSegmentsRequest>,
    ) -> Result<Response<trading::CalculateSegmentsResponse>, Status> {
        Ok(Response::new(trading::CalculateSegmentsResponse {
            success: true,
            segments: Vec::new(),
            error_message: String::new(),
        }))
    }

    async fn get_macd(
        &self,
        _request: Request<trading::GetMacdRequest>,
    ) -> Result<Response<trading::GetMacdResponse>, Status> {
        Ok(Response::new(trading::GetMacdResponse {
            success: true,
            current: None,
            history: Vec::new(),
            error_message: String::new(),
        }))
    }

    async fn health_check(
        &self,
        _request: Request<trading::HealthCheckRequest>,
    ) -> Result<Response<trading::HealthCheckResponse>, Status> {
        let monitor = self.health_monitor.lock().await;
        let status = monitor.status(EngineHealth::Healthy);
        
        Ok(Response::new(trading::HealthCheckResponse {
            status: match status.health {
                EngineHealth::Healthy => trading::HealthStatus::Healthy as i32,
                EngineHealth::Degraded => trading::HealthStatus::Degraded as i32,
                EngineHealth::Unhealthy => trading::HealthStatus::Unhealthy as i32,
                EngineHealth::Unknown => trading::HealthStatus::Unspecified as i32,
            },
            latency_ms: 0.0,
            message: String::new(),
        }))
    }

    async fn get_status(
        &self,
        _request: Request<trading::GetStatusRequest>,
    ) -> Result<Response<trading::GetStatusResponse>, Status> {
        let monitor = self.health_monitor.lock().await;
        let status = monitor.status(EngineHealth::Healthy);
        
        Ok(Response::new(trading::GetStatusResponse {
            success: true,
            active_engine: format!("{:?}", status.active_engine),
            failover_enabled: status.failover_enabled,
            health: match status.health {
                EngineHealth::Healthy => trading::HealthStatus::Healthy as i32,
                EngineHealth::Degraded => trading::HealthStatus::Degraded as i32,
                EngineHealth::Unhealthy => trading::HealthStatus::Unhealthy as i32,
                EngineHealth::Unknown => trading::HealthStatus::Unspecified as i32,
            },
            symbols_tracked: 0,
            pens_calculated: 0,
            segments_calculated: 0,
        }))
    }
}

/// Start the gRPC server
pub async fn start_server(
    addr: std::net::SocketAddr,
    health_monitor: Arc<Mutex<HealthMonitor>>,
) -> Result<(), Box<dyn std::error::Error>> {
    use trading::trading_service_server::TradingServiceServer;
    
    let handler = TradingServiceHandler::new(health_monitor);
    
    tonic::transport::Server::builder()
        .add_service(TradingServiceServer::new(handler))
        .serve(addr)
        .await?;
        
    Ok(())
}
