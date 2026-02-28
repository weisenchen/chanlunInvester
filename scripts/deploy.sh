#!/bin/bash
# Deployment script for trading system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

ENV="${1:-dev}"

echo "🚀 Deploying Trading System (environment: $ENV)..."
echo ""

if [ "$ENV" = "prod" ]; then
    echo "Building production images..."
    docker-compose -f docker-compose.prod.yml build
    
    echo "Starting production services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "Waiting for services to be healthy..."
    sleep 10
    
    echo "Checking service status..."
    docker-compose -f docker-compose.prod.yml ps
else
    echo "Building development images..."
    docker-compose build
    
    echo "Starting development services..."
    docker-compose up -d
    
    echo "Waiting for services to be healthy..."
    sleep 10
    
    echo "Checking service status..."
    docker-compose ps
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Services:"
echo "  - Rust Engine:  localhost:50051"
echo "  - Python Engine: localhost:50052"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
