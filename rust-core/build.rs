//! Build script for gRPC code generation

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Tell Cargo to rerun if proto files change
    println!("cargo:rerun-if-changed=../proto/trading.proto");
    
    // Generate Rust code from proto
    tonic_build::compile_protos("../proto/trading.proto")?;
    
    Ok(())
}
