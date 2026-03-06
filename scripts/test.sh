#!/bin/bash
# Trading System Test Runner
# 交易系统测试运行器

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$PROJECT_DIR/tests"

echo "========================================================================"
echo "ChanLun Trading System - Test Suite"
echo "缠论智能分析系统 - 测试套件"
echo "========================================================================"
echo ""

cd "$PROJECT_DIR"

# Add python-layer to PYTHONPATH
export PYTHONPATH="$PROJECT_DIR/python-layer:$PYTHONPATH"

PASSED=0
FAILED=0

# Run Python tests
echo "[1/3] Running Python module tests..."
echo ""

for test_file in "$TESTS_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        test_name=$(basename "$test_file")
        echo "Running $test_name..."
        
        if python3 "$test_file"; then
            PASSED=$((PASSED + 1))
            echo "✓ $test_name passed"
        else
            FAILED=$((FAILED + 1))
            echo "✗ $test_name failed"
        fi
        echo ""
    fi
done

# Run example smoke tests
echo "[2/3] Running example smoke tests..."
echo ""

EXAMPLES_PASSED=0
EXAMPLES_FAILED=0

for example_dir in "$PROJECT_DIR/examples"/[0-9][0-9]_*/; do
    if [ -d "$example_dir" ]; then
        example_name=$(basename "$example_dir")
        main_py="$example_dir/main.py"
        
        if [ -f "$main_py" ]; then
            echo "Testing example: $example_name..."
            
            # Run example with timeout
            if timeout 30 python3 "$main_py" > /dev/null 2>&1; then
                EXAMPLES_PASSED=$((EXAMPLES_PASSED + 1))
                echo "✓ $example_name passed"
            else
                EXAMPLES_FAILED=$((EXAMPLES_FAILED + 1))
                echo "✗ $example_name failed"
            fi
        fi
    fi
done

echo ""
PASSED=$((PASSED + EXAMPLES_PASSED))
FAILED=$((FAILED + EXAMPLES_FAILED))

# Check Rust tests (if Rust is installed)
echo "[3/3] Checking Rust tests..."
echo ""

if command -v cargo &> /dev/null; then
    RUST_DIR="$PROJECT_DIR/rust-core"
    if [ -d "$RUST_DIR" ]; then
        echo "Running Rust tests..."
        cd "$RUST_DIR"
        
        if cargo test --quiet 2>&1; then
            echo "✓ Rust tests passed"
            PASSED=$((PASSED + 1))
        else
            echo "✗ Rust tests failed"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "⚠ Rust directory not found, skipping Rust tests"
    fi
else
    echo "⚠ Cargo not installed, skipping Rust tests"
fi

cd "$PROJECT_DIR"

# Summary
echo ""
echo "========================================================================"
echo "Test Summary"
echo "========================================================================"
echo ""
echo "  Total Tests:  $((PASSED + FAILED))"
echo "  Passed:       $PASSED"
echo "  Failed:       $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "  Status:       ✓ ALL TESTS PASSED"
    echo "========================================================================"
    exit 0
else
    echo "  Status:       ✗ SOME TESTS FAILED"
    echo "========================================================================"
    exit 1
fi
