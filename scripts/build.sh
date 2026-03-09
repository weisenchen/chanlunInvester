#!/bin/bash
# Build script for trading system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

echo "🔧 Building Trading System..."
echo ""

# Check dependencies
echo "🔍 Checking dependencies..."

MISSING_DEPS=0

# Check Cargo
if ! command -v cargo &> /dev/null; then
    # Try common cargo path just in case
    if [ -f "$HOME/.cargo/bin/cargo" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo "❌ cargo not found. Please install Rust: https://rustup.rs/"
        MISSING_DEPS=1
    fi
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3."
    MISSING_DEPS=1
fi

# Check protoc (required for Rust gRPC build)
if ! command -v protoc &> /dev/null; then
    echo "⚠️  protoc not found. This is required for building the Rust core."
    echo "   Install with: sudo apt install protobuf-compiler or brew install protobuf"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -ne 0 ]; then
    echo ""
    echo "🛑 Build cannot continue due to missing dependencies."
    exit 1
fi

echo "✅ All dependencies found."
echo ""

# Build Rust core
echo "🦀 Building Rust core..."
cd rust-core
# Note: build.rs will handle gRPC code generation for Rust
cargo build --release
cd ..
echo "✅ Rust build complete"
echo ""

# Build Python layer
echo "🐍 Building Python layer..."
cd python-layer
if [ ! -d "venv" ]; then
    python3 -m venv venv || { echo "❌ Failed to create virtualenv. Ensure python3-venv is installed."; exit 1; }
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
echo "✅ Python build complete"
echo ""

# Generate Python gRPC code (Rust ones are handled by cargo)
echo "📡 Generating Python gRPC code..."
./venv/bin/python3 -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/trading.proto
deactivate
cd ..
echo "✅ gRPC code generated"

echo ""

echo "🎉 Build complete!"
echo ""
echo "Next steps:"
echo "  - Run tests: ./scripts/test.sh"
echo "  - Start development: docker-compose up"
echo "  - Start production: docker-compose -f docker-compose.prod.yml up -d"
