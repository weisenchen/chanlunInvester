#!/bin/bash
# Test script for trading system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🧪 Running Tests..."
echo ""

# Run Rust tests
echo "🦀 Running Rust tests..."
cd rust-core
cargo test
cd ..
echo "✅ Rust tests passed"
echo ""

# Run Python tests
echo "🐍 Running Python tests..."
cd python-layer
source venv/bin/activate
python -m pytest tests/ -v
deactivate
cd ..
echo "✅ Python tests passed"
echo ""

echo "🎉 All tests passed!"
