#!/bin/bash
#
# Stop Production Services
#

echo "🛑 Stopping UPSTOX Trading Platform..."

# Stop API Server
if [ -f logs/api.pid ]; then
    PID=$(cat logs/api.pid)
    echo "Stopping API Server (PID: $PID)..."
    kill -TERM $PID 2>/dev/null || echo "API Server already stopped"
    rm logs/api.pid
else
    echo "No API Server PID file found"
fi

# Stop Frontend Server
if [ -f logs/frontend.pid ]; then
    PID=$(cat logs/frontend.pid)
    echo "Stopping Frontend Server (PID: $PID)..."
    kill -TERM $PID 2>/dev/null || echo "Frontend Server already stopped"
    rm logs/frontend.pid
else
    echo "No Frontend Server PID file found"
fi

# Kill any remaining gunicorn processes for this app
pkill -f "gunicorn.*upstox_trading_platform" 2>/dev/null || true

echo "✅ All services stopped"
