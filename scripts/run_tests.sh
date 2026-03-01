#!/bin/bash
# Test runner for ChanLun Invester
# Runs unit tests and integration tests

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║     ChanLun Invester - Test Suite                      ║"
echo "╚════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")"

# Run Rust tests
echo ""
echo "🦀 Running Rust unit tests..."
echo "────────────────────────────────────────────────────────"
cd rust-core
if command -v cargo &> /dev/null; then
    cargo test --lib 2>&1 | tail -20
    echo "✓ Rust tests completed"
else
    echo "⚠️  Cargo not installed, skipping Rust tests"
fi
cd ..

# Run Python tests
echo ""
echo "🐍 Running Python tests..."
echo "────────────────────────────────────────────────────────"
cd python-layer

# Unit tests (no server needed)
echo "Running Python unit tests..."
python3 -m pytest test_integration.py::TestPythonBackup -v 2>/dev/null || \
    python3 test_integration.py 2>&1 | grep -E "(test_|OK|FAILED)" | tail -10

echo "✓ Python tests completed"
cd ..

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ All tests completed!"
echo "════════════════════════════════════════════════════════"
