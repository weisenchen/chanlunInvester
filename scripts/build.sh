#!/bin/bash
# Build script for trading system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Building Trading System..."
echo ""

# Build Rust core
echo "🦀 Building Rust core..."
cd rust-core
cargo build --release
cd ..
echo "✅ Rust build complete"
echo ""

# Build Python layer
echo "🐍 Building Python layer..."
cd python-layer
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
deactivate
cd ..
echo "✅ Python build complete"
echo ""

# Generate gRPC code
echo "📡 Generating gRPC code..."
if ! command -v protoc &> /dev/null; then
    echo "⚠️  protoc not found, skipping gRPC generation"
    echo "   Install with: apt install protobuf-compiler or brew install protobuf"
else
    # Generate Rust gRPC code
    cd rust-core
    cargo install protoc-gen-prost 2>/dev/null || true
    cd ..
    
    # Generate Python gRPC code
    cd python-layer
    python3 -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=../proto/*.proto
    cd ..
    echo "✅ gRPC code generated"
fi
echo ""

echo "🎉 Build complete!"
echo ""
echo "Next steps:"
echo "  - Run tests: ./scripts/test.sh"
echo "  - Start development: docker-compose up"
echo "  - Start production: docker-compose -f docker-compose.prod.yml up -d"
