//! ChanLun Stock Monitor - Rust Core
//! 通用股票监控系统核心模块
//! 支持任意美股/ETF/加密货币
//!
//! # Usage
//!
//! ```rust
//! use monitor::{ChanLunMonitor, MonitorConfig};
//!
//! let config = MonitorConfig::default();
//! let monitor = ChanLunMonitor::new(config);
//!
//! // Analyze single stock
//! let result = monitor.analyze("AAPL", vec!["1d", "30m", "5m"]);
//!
//! // Generate trading plan
//! if let Ok(analysis) = result {
//!     let plan = monitor.generate_trading_plan(&analysis);
//! }
//! ```

use crate::kline::{Kline, KlineSeries};
use crate::fractal::{FractalDetector, Fractal};
use crate::pen::{PenCalculator, PenConfig, Pen};
use crate::segment::{SegmentCalculator, Segment};
use crate::indicators::{MACD, MACDResult};

use std::collections::HashMap;
use std::error::Error;
use std::fmt;

/// 监控配置
#[derive(Debug, Clone)]
pub struct MonitorConfig {
    pub timeframes: Vec<String>,
    pub min_confidence: f64,
    pub weights: HashMap<String, LevelWeight>,
}

/// 级别权重
#[derive(Debug, Clone)]
pub struct LevelWeight {
    pub direction: f64,
    pub divergence: f64,
}

impl Default for MonitorConfig {
    fn default() -> Self {
        let mut weights = HashMap::new();
        weights.insert("1d".to_string(), LevelWeight { direction: 3.0, divergence: 6.0 });
        weights.insert("4h".to_string(), LevelWeight { direction: 2.5, divergence: 5.0 });
        weights.insert("1h".to_string(), LevelWeight { direction: 2.0, divergence: 4.0 });
        weights.insert("30m".to_string(), LevelWeight { direction: 2.0, divergence: 4.0 });
        weights.insert("15m".to_string(), LevelWeight { direction: 1.5, divergence: 3.0 });
        weights.insert("5m".to_string(), LevelWeight { direction: 1.0, divergence: 4.0 });
        
        Self {
            timeframes: vec!["1d".to_string(), "30m".to_string(), "5m".to_string()],
            min_confidence: 0.7,
            weights,
        }
    }
}

/// 分析结果
#[derive(Debug, Clone)]
pub struct AnalysisResult {
    pub symbol: String,
    pub timestamp: String,
    pub current_price: f64,
    pub signal: Signal,
    pub strength: f64,
    pub reasoning: Vec<String>,
    pub levels: HashMap<String, LevelAnalysis>,
}

/// 交易信号
#[derive(Debug, Clone, PartialEq)]
pub enum Signal {
    StrongBuy,
    Buy,
    Hold,
    Sell,
    StrongSell,
}

impl fmt::Display for Signal {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Signal::StrongBuy => write!(f, "STRONG_BUY"),
            Signal::Buy => write!(f, "BUY"),
            Signal::Hold => write!(f, "HOLD"),
            Signal::Sell => write!(f, "SELL"),
            Signal::StrongSell => write!(f, "STRONG_SELL"),
        }
    }
}

/// 级别分析结果
#[derive(Debug, Clone)]
pub struct LevelAnalysis {
    pub fractals: FractalAnalysis,
    pub pens: PenAnalysis,
    pub segments: SegmentAnalysis,
    pub divergence: Option<Divergence>,
    pub buy_sell_points: Vec<BuySellPoint>,
}

#[derive(Debug, Clone)]
pub struct FractalAnalysis {
    pub total: usize,
    pub top: usize,
    pub bottom: usize,
}

#[derive(Debug, Clone)]
pub struct PenAnalysis {
    pub total: usize,
    pub up: usize,
    pub down: usize,
}

#[derive(Debug, Clone)]
pub struct SegmentAnalysis {
    pub total: usize,
    pub up: usize,
    pub down: usize,
}

#[derive(Debug, Clone)]
pub struct Divergence {
    pub detected: bool,
    pub div_type: String,
    pub price: f64,
    pub strength: f64,
    pub signal: String,
}

#[derive(Debug, Clone)]
pub struct BuySellPoint {
    pub bsp_type: String,
    pub price: f64,
    pub confidence: f64,
    pub description: String,
}

/// 交易计划
#[derive(Debug, Clone)]
pub struct TradingPlan {
    pub action: String,
    pub entry: f64,
    pub stop_loss: f64,
    pub target1: f64,
    pub target2: f64,
    pub position_size: String,
    pub risk_reward: f64,
}

/// 错误类型
#[derive(Debug)]
pub enum MonitorError {
    DataFetchError(String),
    AnalysisError(String),
    NoDataAvailable,
}

impl fmt::Display for MonitorError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            MonitorError::DataFetchError(msg) => write!(f, "Data fetch error: {}", msg),
            MonitorError::AnalysisError(msg) => write!(f, "Analysis error: {}", msg),
            MonitorError::NoDataAvailable => write!(f, "No data available"),
        }
    }
}

impl Error for MonitorError {}

/// 缠论股票监控器
pub struct ChanLunMonitor {
    config: MonitorConfig,
    fractal_detector: FractalDetector,
    pen_calculator: PenCalculator,
    segment_calculator: SegmentCalculator,
    macd: MACD,
}

impl ChanLunMonitor {
    /// 创建新的监控器
    pub fn new(config: MonitorConfig) -> Self {
        Self {
            fractal_detector: FractalDetector::default(),
            pen_calculator: PenCalculator::with_config(PenConfig {
                use_new_definition: true,
                strict_validation: true,
                min_klines_between_turns: 3,
            }),
            segment_calculator: SegmentCalculator::with_min_pens(3),
            macd: MACD::default(),
            config,
        }
    }
    
    /// 分析股票
    pub fn analyze(&self, symbol: &str, timeframes: Vec<&str>) -> Result<AnalysisResult, MonitorError> {
        // 获取多个级别数据 (实际应用中需要从数据源获取)
        let mut data: HashMap<String, KlineSeries> = HashMap::new();
        let mut current_price: Option<f64> = None;
        
        for timeframe in timeframes {
            // 这里应该调用数据源获取实际数据
            // 现在使用示例数据
            let series = self._create_sample_data(symbol, timeframe);
            if let Some(last_kline) = series.klines.last() {
                if current_price.is_none() {
                    current_price = Some(last_kline.close);
                }
            }
            data.insert(timeframe.to_string(), series);
        }
        
        if data.is_empty() {
            return Err(MonitorError::NoDataAvailable);
        }
        
        // 执行分析
        let mut analysis_results: HashMap<String, LevelAnalysis> = HashMap::new();
        for (timeframe, series) in &data {
            analysis_results.insert(
                timeframe.clone(),
                self._analyze_level(series),
            );
        }
        
        // 多级别联动分析
        let (signal_strength, reasoning) = self._multi_level_analysis(&analysis_results);
        
        // 生成信号
        let signal = self._generate_signal(signal_strength);
        
        Ok(AnalysisResult {
            symbol: symbol.to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
            current_price: current_price.unwrap_or(0.0),
            signal,
            strength: signal_strength,
            reasoning,
            levels: analysis_results,
        })
    }
    
    /// 分析单个级别
    fn _analyze_level(&self, series: &KlineSeries) -> LevelAnalysis {
        // 1. 分型
        let fractals = self.fractal_detector.detect_all(series);
        let fractal_analysis = FractalAnalysis {
            total: fractals.len(),
            top: fractals.iter().filter(|f| f.is_top()).count(),
            bottom: fractals.iter().filter(|f| !f.is_top()).count(),
        };
        
        // 2. 笔
        let pens = self.pen_calculator.identify_pens(series);
        let pen_analysis = PenAnalysis {
            total: pens.len(),
            up: pens.iter().filter(|p| p.is_up()).count(),
            down: pens.iter().filter(|p| p.is_down()).count(),
        };
        
        // 3. 线段
        let segments = self.segment_calculator.detect_segments(&pens);
        let segment_analysis = SegmentAnalysis {
            total: segments.len(),
            up: segments.iter().filter(|s| s.is_up()).count(),
            down: segments.iter().filter(|s| s.is_down()).count(),
        };
        
        // 4. 背驰
        let prices: Vec<f64> = series.klines.iter().map(|k| k.close).collect();
        let macd_data = self.macd.calculate(&prices);
        let divergence = self._detect_divergence(&segments, &macd_data);
        
        // 5. 买卖点
        let buy_sell_points = self._detect_buy_sell_points(&segments, &divergence);
        
        LevelAnalysis {
            fractals: fractal_analysis,
            pens: pen_analysis,
            segments: segment_analysis,
            divergence,
            buy_sell_points,
        }
    }
    
    /// 检测背驰
    fn _detect_divergence(&self, segments: &[Segment], macd_data: &[MACDResult]) -> Option<Divergence> {
        if segments.len() < 2 || macd_data.is_empty() {
            return None;
        }
        
        let last_seg = segments.last().unwrap();
        let mut prev_seg: Option<&Segment> = None;
        
        for seg in segments.iter().rev().skip(1) {
            if seg.direction == last_seg.direction {
                prev_seg = Some(seg);
                break;
            }
        }
        
        if let Some(prev) = prev_seg {
            if let (Some(prev_macd), Some(last_macd)) = (
                macd_data.get(prev.end_idx),
                macd_data.get(last_seg.end_idx),
            ) {
                let macd_prev = prev_macd.histogram;
                let macd_last = last_macd.histogram;
                
                let price_prev = prev.end_price;
                let price_last = last_seg.end_price;
                
                if last_seg.is_up() {
                    if price_last > price_prev && macd_last < macd_prev {
                        let strength = (macd_prev - macd_last).abs() / macd_prev.abs().max(0.001);
                        return Some(Divergence {
                            detected: true,
                            div_type: "top_divergence".to_string(),
                            price: price_last,
                            strength,
                            signal: "sell".to_string(),
                        });
                    }
                } else {
                    if price_last < price_prev && macd_last > macd_prev {
                        let strength = (macd_prev - macd_last).abs() / macd_prev.abs().max(0.001);
                        return Some(Divergence {
                            detected: true,
                            div_type: "bottom_divergence".to_string(),
                            price: price_last,
                            strength,
                            signal: "buy".to_string(),
                        });
                    }
                }
            }
        }
        
        None
    }
    
    /// 识别买卖点
    fn _detect_buy_sell_points(&self, segments: &[Segment], divergence: &Option<Divergence>) -> Vec<BuySellPoint> {
        let mut bsp_list = Vec::new();
        
        if let Some(div) = divergence {
            let bsp_type = if div.signal == "buy" {
                "第一类买点".to_string()
            } else {
                "第一类卖点".to_string()
            };
            
            bsp_list.push(BuySellPoint {
                bsp_type,
                price: div.price,
                confidence: div.strength.min(0.9),
                description: format!("趋势背驰点 - {}", div.div_type),
            });
        }
        
        bsp_list
    }
    
    /// 多级别联动分析
    fn _multi_level_analysis(&self, results: &HashMap<String, LevelAnalysis>) -> (f64, Vec<String>) {
        let mut signal_strength = 0.0;
        let mut reasoning = Vec::new();
        
        for (timeframe, analysis) in results {
            let weight = self.config.weights.get(timeframe)
                .unwrap_or(&LevelWeight { direction: 1.0, divergence: 2.0 });
            
            // 线段方向
            if analysis.segments.up > 0 {
                signal_strength += weight.direction;
                reasoning.push(format!("✓ {}上涨线段 (+{})", timeframe, weight.direction));
            }
            if analysis.segments.down > 0 {
                signal_strength -= weight.direction;
                reasoning.push(format!("✗ {}下跌线段 (-{})", timeframe, weight.direction));
            }
            
            // 背驰
            if let Some(div) = &analysis.divergence {
                if div.signal == "buy" {
                    signal_strength += weight.divergence;
                    reasoning.push(format!(
                        "🟢 {}底背驰 (强度:{:.2f}) (+{})",
                        timeframe, div.strength, weight.divergence
                    ));
                } else {
                    signal_strength -= weight.divergence;
                    reasoning.push(format!(
                        "🔴 {}顶背驰 (强度:{:.2f}) (-{})",
                        timeframe, div.strength, weight.divergence
                    ));
                }
            }
            
            // 买卖点
            for bsp in &analysis.buy_sell_points {
                if bsp.bsp_type.contains("买点") {
                    signal_strength += weight.divergence;
                    reasoning.push(format!(
                        "🟢 {}{} (+{})",
                        timeframe, bsp.bsp_type, weight.divergence
                    ));
                } else {
                    signal_strength -= weight.divergence;
                    reasoning.push(format!(
                        "🔴 {}{} (-{})",
                        timeframe, bsp.bsp_type, weight.divergence
                    ));
                }
            }
        }
        
        (signal_strength, reasoning)
    }
    
    /// 生成交易信号
    fn _generate_signal(&self, strength: f64) -> Signal {
        if strength >= 8.0 {
            Signal::StrongBuy
        } else if strength >= 4.0 {
            Signal::Buy
        } else if strength <= -8.0 {
            Signal::StrongSell
        } else if strength <= -4.0 {
            Signal::Sell
        } else {
            Signal::Hold
        }
    }
    
    /// 生成交易计划
    pub fn generate_trading_plan(&self, result: &AnalysisResult) -> TradingPlan {
        let price = result.current_price;
        
        match result.signal {
            Signal::StrongBuy | Signal::Buy => {
                let position_size = if result.signal == Signal::StrongBuy {
                    "heavy".to_string()
                } else {
                    "normal".to_string()
                };
                
                TradingPlan {
                    action: "BUY".to_string(),
                    entry: price,
                    stop_loss: price * 0.97,
                    target1: price * 1.03,
                    target2: price * 1.05,
                    position_size,
                    risk_reward: 1.7,
                }
            }
            Signal::StrongSell | Signal::Sell => {
                let position_size = if result.signal == Signal::StrongSell {
                    "heavy".to_string()
                } else {
                    "normal".to_string()
                };
                
                TradingPlan {
                    action: "SELL".to_string(),
                    entry: price,
                    stop_loss: price * 1.03,
                    target1: price * 0.97,
                    target2: price * 0.95,
                    position_size,
                    risk_reward: 1.7,
                }
            }
            Signal::Hold => TradingPlan {
                action: "HOLD".to_string(),
                entry: 0.0,
                stop_loss: 0.0,
                target1: 0.0,
                target2: 0.0,
                position_size: "none".to_string(),
                risk_reward: 0.0,
            },
        }
    }
    
    /// 创建示例数据 (实际应用中应该从数据源获取)
    fn _create_sample_data(&self, symbol: &str, timeframe: &str) -> KlineSeries {
        use chrono::{Duration, Utc};
        use rand::Rng;
        
        let mut klines = Vec::new();
        let mut rng = rand::thread_rng();
        let mut base_price = 100.0;
        let mut current_time = Utc::now();
        
        let count = match timeframe {
            "1d" => 200,
            "30m" => 100,
            "5m" => 100,
            _ => 100,
        };
        
        for _ in 0..count {
            let volatility = rng.gen_range(-0.02..0.02);
            base_price *= 1.0 + volatility;
            
            let high = base_price * (1.0 + rng.gen_range(0.0..0.01));
            let low = base_price * (1.0 - rng.gen_range(0.0..0.01));
            let open = base_price * (1.0 + rng.gen_range(-0.005..0.005));
            let close = base_price * (1.0 + rng.gen_range(-0.005..0.005));
            
            klines.push(Kline {
                timestamp: current_time,
                open,
                high,
                low,
                close,
                volume: rng.gen_range(100000..1000000),
            });
            
            current_time -= Duration::minutes(30);
        }
        
        klines.reverse();
        
        KlineSeries {
            klines,
            symbol: symbol.to_string(),
            timeframe: timeframe.to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_monitor_creation() {
        let config = MonitorConfig::default();
        let monitor = ChanLunMonitor::new(config);
        assert!(true);
    }
    
    #[test]
    fn test_analyze_stock() {
        let config = MonitorConfig::default();
        let monitor = ChanLunMonitor::new(config);
        
        let result = monitor.analyze("AAPL", vec!["1d", "30m", "5m"]);
        assert!(result.is_ok());
        
        let analysis = result.unwrap();
        assert_eq!(analysis.symbol, "AAPL");
    }
    
    #[test]
    fn test_signal_generation() {
        let config = MonitorConfig::default();
        let monitor = ChanLunMonitor::new(config);
        
        assert_eq!(monitor._generate_signal(10.0), Signal::StrongBuy);
        assert_eq!(monitor._generate_signal(5.0), Signal::Buy);
        assert_eq!(monitor._generate_signal(0.0), Signal::Hold);
        assert_eq!(monitor._generate_signal(-5.0), Signal::Sell);
        assert_eq!(monitor._generate_signal(-10.0), Signal::StrongSell);
    }
}
