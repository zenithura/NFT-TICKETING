#!/bin/bash
# Start monitoring stack script

echo "📊 Starting Monitoring Stack"
echo "============================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start monitoring services
echo "Starting Prometheus, Grafana, and Alertmanager..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check services
echo ""
echo "Checking service status..."

check_service() {
    local url=$1
    local name=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $name is running at $url"
    else
        echo "❌ $name is not responding at $url"
    fi
}

check_service "http://localhost:9090/-/healthy" "Prometheus"
check_service "http://localhost:3001/api/health" "Grafana"
check_service "http://localhost:9093/-/healthy" "Alertmanager"

echo ""
echo "============================"
echo "📊 Monitoring Stack Started!"
echo ""
echo "Access services:"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3001 (admin/admin)"
echo "  - Alertmanager:  http://localhost:9093"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.monitoring.yml down"

