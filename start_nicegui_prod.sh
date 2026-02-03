#!/bin/bash
set -e

echo "=================================================="
echo "🚀 Starting UPSTOX Platform (NiceGUI Edition)"
echo "=================================================="

# Setup
mkdir -p logs cache
if [ -f .env ]; then
    echo "📋 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Cleanup
echo "🛑 Stopping existing instances..."
# Cleanup
echo "🛑 Stopping existing instances..."
lsof -ti :9000 | xargs kill -9 2>/dev/null || true
lsof -ti :5001 | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
pkill -f "gunicorn" || true
pkill -f "nicegui_dashboard.py" || true
pkill -f "oauth_server.py" || true
sleep 2

# Start API (Port 9000) - Using Gunicorn
echo "Starting API Server..."
APP_MODE=api PORT=9000 gunicorn \
    --config gunicorn_config.py \
    --bind "0.0.0.0:9000" \
    --daemon \
    --access-logfile "logs/api_access.log" \
    --error-logfile "logs/api_error.log" \
    wsgi:application
echo "✅ API Server started (Port 9000)"

# Start OAuth (Port 5050)
echo "Starting OAuth Server..."
nohup python3 scripts/oauth_server.py > logs/oauth.log 2>&1 &
echo "✅ OAuth Server started (Port 5050)"

# Start NiceGUI (Port 8080)
echo "Starting NiceGUI Dashboard..."
nohup python3 nicegui_dashboard.py > logs/nicegui.log 2>&1 &
echo "✅ NiceGUI Dashboard started (Port 8080)"

echo ""
echo "=================================================="
echo "🎉 SYSTEM IS LIVE!"
echo "=================================================="
echo "🌐 Dashboard:   http://localhost:8080"
echo "📡 API Server:  http://localhost:9000"
echo "🔐 OAuth:       http://localhost:5050"
echo "=================================================="
