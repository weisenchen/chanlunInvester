#!/bin/bash
# Generate Python gRPC code from proto files

set -e

PROTO_DIR="../proto"
PYTHON_DIR="trading_system"

echo "🔨 Generating Python gRPC code from proto files..."

# Generate Python gRPC code
python3 -m grpc_tools.protoc \
    -I${PROTO_DIR} \
    --python_out=${PYTHON_DIR} \
    --grpc_python_out=${PYTHON_DIR} \
    ${PROTO_DIR}/trading.proto

echo "✅ Python gRPC code generated in ${PYTHON_DIR}/"
ls -la ${PYTHON_DIR}/*_pb2*.py 2>/dev/null || echo "  (files will be created after first run)"
