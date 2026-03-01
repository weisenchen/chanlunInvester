//! Trading Core Library
//! 
//! High-performance trading system implementing pen theory (笔理论)
//! with strict line segment division and configurable indicators.

pub mod kline;
pub mod pen;
pub mod segment;
pub mod indicators;
pub mod health;
pub mod grpc;
pub mod metrics;
pub mod divergence;
pub mod bsp;

pub use kline::*;
pub use pen::*;
pub use segment::*;
pub use indicators::*;
