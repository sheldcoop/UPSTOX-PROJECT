#!/bin/bash
# Start both servers for NiceGUI Trading Dashboard
# For local development only - see start_nicegui_prod.sh for production

set -e  # Exit on error

echo "🚀 Starting Upstox Trading Platform (NiceGUI)"
echo "================================================"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default ports from environment or use defaults
API_PORT=${API_PORT:-9000}
OAUTH_PORT=${OAUTH_PORT:-5050}
NICEGUI_PORT=${NICEGUI_PORT:-8080}

# Kill any existing processes on our ports (safer than pkill)
echo "🛑 Stopping existing instances..."
lsof -ti :$API_PORT | xargs kill -9 2>/dev/null || true
lsof -ti :$OAUTH_PORT | xargs kill -9 2>/dev/null || true
lsof -ti :$NICEGUI_PORT | xargs kill -9 2>/dev/null || true

sleep 1

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Create logs directory
mkdir -p logs

# Start Flask backend
echo "📡 Starting Flask API Server (port $API_PORT)..."
python3 scripts/api_server.py --port $API_PORT > logs/flask_server.log 2>&1 &
FLASK_PID=$!
echo "✅ Flask backend started (PID: $FLASK_PID)"

# Start OAuth Server (for login flow)
echo "🔐 Starting OAuth Server (port $OAUTH_PORT)..."
python3 scripts/oauth_server.py > logs/oauth_server.log 2>&1 &
OAUTH_PID=$!
echo "✅ OAuth server started (PID: $OAUTH_PID)"

# Start Telegram Bot (if configured)
if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "🤖 Starting Telegram Bot..."
    python3 scripts/ai_assistant_bot.py > logs/telegram_bot.log 2>&1 &
    BOT_PID=$!
    echo "✅ Telegram Bot started (PID: $BOT_PID)"
fi

# Wait for Flask to be ready
echo "⏳ Waiting for services to initialize..."
sleep 3

# Start NiceGUI frontend
echo "🎨 Starting NiceGUI Dashboard (port $NICEGUI_PORT)..."
python3 nicegui_dashboard.py > logs/nicegui_server.log 2>&1 &
NICEGUI_PID=$!
echo "✅ NiceGUI dashboard started (PID: $NICEGUI_PID)"

# Save PIDs for easy cleanup
echo "$FLASK_PID" > logs/flask.pid
echo "$OAUTH_PID" > logs/oauth.pid
echo "$NICEGUI_PID" > logs/nicegui.pid
[ ! -z "$BOT_PID" ] && echo "$BOT_PID" > logs/telegram.pid

sleep 2

# Health checks
echo ""
echo "🏥 Running health checks..."
if curl -f http://localhost:$API_PORT/api/health > /dev/null 2>&1; then
    echo "✅ API Server is healthy"
else
    echo "⚠️  API Server health check failed (may still be starting)"
fi

echo ""
echo "=================================================="
echo "🎉 All services started successfully!"
echo "=================================================="
echo ""
echo "🌐 Dashboard:       http://127.0.0.1:$NICEGUI_PORT"
echo "📡 API Server:      http://127.0.0.1:$API_PORT"
echo "🔐 OAuth Service:   http://127.0.0.1:$OAUTH_PORT"
echo ""
echo "📊 Available Pages:"
echo "  • 🏠 Dashboard - Portfolio overview"
echo "  • 📥 Downloads - Download market data"
echo "  • 📊 Positions - Open positions"
echo "  • 💱 Options - Options chain"
echo "  • 🧪 Backtest - Backtesting engine"
echo "  • 🎯 Strategies - Trading strategies"
echo "  • 🔔 Alerts - Alert rules"
echo ""
echo "📝 Logs:"
echo "  • API:      tail -f logs/flask_server.log"
echo "  • OAuth:    tail -f logs/oauth_server.log"
echo "  • NiceGUI:  tail -f logs/nicegui_server.log"
echo ""
echo "🛑 To stop all servers:"
echo "  kill \$(cat logs/*.pid)"
echo "  Or press Ctrl+C"
echo ""
echo "=================================================="

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    [ -f logs/flask.pid ] && kill $(cat logs/flask.pid) 2>/dev/null
    [ -f logs/oauth.pid ] && kill $(cat logs/oauth.pid) 2>/dev/null
    [ -f logs/nicegui.pid ] && kill $(cat logs/nicegui.pid) 2>/dev/null
    [ -f logs/telegram.pid ] && kill $(cat logs/telegram.pid) 2>/dev/null
    rm -f logs/*.pid
    echo "✅ Services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Keep script running
wait
