//! gRPC Service Implementation

use tonic::{transport::Server, Request, Response, Status};
use tracing::{info, warn};

// Include generated code
pub mod pb {
    include!(concat!(env!("OUT_DIR"), "/trading.rs"));
}

use pb::{
    trading_service_server::{TradingService, TradingServiceServer},
    *,
};

use crate::kline::Kline;
use crate::pen::PenCalculator;
use crate::health::HealthMonitor;

/// Trading service implementation
pub struct TradingServiceImpl {
    health_monitor: HealthMonitor,
    pen_calculator: PenCalculator,
}

impl TradingServiceImpl {
    pub fn new(health_monitor: HealthMonitor) -> Self {
        Self {
            health_monitor,
            pen_calculator: PenCalculator::new(),
        }
    }
}

#[tonic::async_trait]
impl TradingService for TradingServiceImpl {
    async fn submit_klines(
        &self,
        request: Request<SubmitKlinesRequest>,
    ) -> Result<Response<SubmitKlinesResponse>, Status> {
        let req = request.into_inner();
        
        info!(
            "SubmitKlines: symbol={}, timeframe={:?}, count={}",
            req.symbol,
            req.timeframe,
            req.klines.len()
        );

        // Convert protobuf Klines to internal Klines
        let klines: Vec<Kline> = req.klines
            .iter()
            .map(|k| Kline::from_proto(k))
            .collect();

        // TODO: Store klines in data store
        
        Ok(Response::new(SubmitKlinesResponse {
            success: true,
            processed_count: klines.len() as i32,
            error_message: String::new(),
        }))
    }

    async fn calculate_pens(
        &self,
        request: Request<CalculatePensRequest>,
    ) -> Result<Response<CalculatePensResponse>, Status> {
        let req = request.into_inner();
        
        info!(
            "CalculatePens: symbol={}, timeframe={:?}, last_n={}",
            req.symbol,
            req.timeframe,
            req.last_n
        );

        // TODO: Get klines from storage
        // let klines = self.storage.get_klines(&req.symbol, req.timeframe, req.last_n)?;
        
        // Calculate pens
        // let pens = self.pen_calculator.calculate(&klines)?;
        
        Ok(Response::new(CalculatePensResponse {
            success: true,
            pens: vec![], // TODO: Return actual pens
            error_message: String::new(),
        }))
    }

    async fn calculate_segments(
        &self,
        request: Request<CalculateSegmentsRequest>,
    ) -> Result<Response<CalculateSegmentsResponse>, Status> {
        let req = request.into_inner();
        
        info!(
            "CalculateSegments: symbol={}, timeframe={:?}",
            req.symbol,
            req.timeframe
        );

        // TODO: Implement segment calculation
        
        Ok(Response::new(CalculateSegmentsResponse {
            success: true,
            segments: vec![],
            error_message: String::new(),
        }))
    }

    async fn get_macd(
        &self,
        request: Request<GetMacdRequest>,
    ) -> Result<Response<GetMacdResponse>, Status> {
        let req = request.into_inner();
        
        info!(
            "GetMACD: symbol={}, timeframe={:?}, periods={:?}/{:?}/{:?}",
            req.symbol,
            req.timeframe,
            req.fast_period,
            req.slow_period,
            req.signal_period
        );

        // TODO: Implement MACD calculation
        
        Ok(Response::new(GetMacdResponse {
            success: true,
            current: Some(MACD {
                macd_line: 0.0,
                signal_line: 0.0,
                histogram: 0.0,
            }),
            history: vec![],
            error_message: String::new(),
        }))
    }

    async fn health_check(
        &self,
        request: Request<HealthCheckRequest>,
    ) -> Result<Response<HealthCheckResponse>, Status> {
        let req = request.into_inner();
        
        let status = match req.service.as_str() {
            "rust" => HealthStatus::Healthy,
            "python" => HealthStatus::Degraded, // Python is backup
            _ => HealthStatus::Unhealthy,
        };

        Ok(Response::new(HealthCheckResponse {
            status: status as i32,
            latency_ms: 0.5,
            message: format!("{} service healthy", req.service),
        }))
    }

    async fn get_status(
        &self,
        _request: Request<GetStatusRequest>,
    ) -> Result<Response<GetStatusResponse>, Status> {
        let health = self.health_monitor.status();

        Ok(Response::new(GetStatusResponse {
            success: true,
            active_engine: "rust".to_string(),
            failover_enabled: health.failover_enabled,
            health: match health.active_engine {
                crate::health::ActiveEngine::Rust => HealthStatus::Healthy as i32,
                crate::health::ActiveEngine::Python => HealthStatus::Degraded as i32,
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
    health_monitor: HealthMonitor,
) -> Result<(), Box<dyn std::error::Error>> {
    let service = TradingServiceImpl::new(health_monitor);

    info!("Starting gRPC server on {}", addr);

    Server::builder()
        .add_service(TradingServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
