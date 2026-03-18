//! Trading Core Library
//! 
//! High-performance trading system implementing pen theory (笔理论)
//! with strict line segment division and configurable indicators.
//! 
//! # Features
//! 
//! - 🦀 Rust core for high-performance computing
//! - 🐍 Python backup for flexibility
//! - 🔄 Automatic failover
//! - 📊 Universal stock monitoring (AAPL, TSLA, BTC-USD, etc.)
//! - 🎯 Multi-level ChanLun analysis

pub mod kline;
pub mod fractal;
pub mod pen;
pub mod segment;
pub mod indicators;
pub mod health;
pub mod grpc;
pub mod monitor;

pub use kline::*;
pub use fractal::*;
pub use pen::*;
pub use segment::*;
pub use indicators::*;
pub use monitor::*;
