#!/bin/bash
#
# Production Startup Script for Oracle Cloud
# Starts both API server and Frontend server using Gunicorn
#

set -e

echo "=================================================="
echo "🚀 Starting UPSTOX Trading Platform (Production)"
echo "=================================================="

# Create necessary directories
mkdir -p logs
mkdir -p cache
mkdir -p debug_dumps
mkdir -p downloads

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for required environment variables
if [ -z "$UPSTOX_CLIENT_ID" ]; then
    echo "⚠️  WARNING: UPSTOX_CLIENT_ID not set. Please configure .env file"
fi

# Set default ports if not specified
export API_PORT=${API_PORT:-8000}
export FRONTEND_PORT=${FRONTEND_PORT:-5001}

# Function to start a service
start_service() {
    local mode=$1
    local port=$2
    local log_prefix=$3
    
    echo "Starting $mode on port $port..."
    APP_MODE=$mode PORT=$port gunicorn \
        --config gunicorn_config.py \
        --bind "0.0.0.0:$port" \
        --access-logfile "logs/${log_prefix}_access.log" \
        --error-logfile "logs/${log_prefix}_error.log" \
        wsgi:application &
    
    echo "$!" > "logs/${log_prefix}.pid"
    echo "✅ $mode started (PID: $(cat logs/${log_prefix}.pid))"
}

# Stop any existing instances
echo "🛑 Stopping any existing instances..."
if [ -f logs/api.pid ]; then
    kill $(cat logs/api.pid) 2>/dev/null || true
    rm logs/api.pid
fi
if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null || true
    rm logs/frontend.pid
fi

# Wait a moment for ports to be released
sleep 2

# Start API Server
start_service "api" "$API_PORT" "api"

# Start Frontend Server
start_service "frontend" "$FRONTEND_PORT" "frontend"

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Health check
echo "🏥 Running health checks..."
if curl -f http://localhost:$API_PORT/api/health > /dev/null 2>&1; then
    echo "✅ API Server is healthy"
else
    echo "❌ API Server health check failed"
fi

if curl -f http://localhost:$FRONTEND_PORT/api/health > /dev/null 2>&1; then
    echo "✅ Frontend Server is healthy"
else
    echo "⚠️  Frontend Server health check failed (may not have /api/health endpoint)"
fi

echo ""
echo "=================================================="
echo "✅ Platform Started Successfully"
echo "=================================================="
echo "📡 API Server:      http://localhost:$API_PORT"
echo "🌐 Frontend:        http://localhost:$FRONTEND_PORT"
echo "📊 Health Check:    http://localhost:$API_PORT/api/health"
echo ""
echo "📝 Logs:"
echo "   API:       tail -f logs/api_error.log"
echo "   Frontend:  tail -f logs/frontend_error.log"
echo ""
echo "🛑 To stop:"
echo "   ./stop_production.sh"
echo "=================================================="
