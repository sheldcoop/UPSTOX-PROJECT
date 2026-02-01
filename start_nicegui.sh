#!/bin/bash
# Start both servers for NiceGUI Trading Dashboard

echo "🚀 Starting Upstox Trading Platform (NiceGUI)"
echo "================================================"

# Kill any existing processes
pkill -f "api_server.py" 2>/dev/null || true
pkill -f "nicegui_dashboard.py" 2>/dev/null || true

sleep 1

# Activate virtual environment
cd /Users/prince/Desktop/UPSTOX-project
source .venv/bin/activate

# Start Flask backend
echo "📡 Starting Flask API Server (port 9000)..."
python3 scripts/api_server.py --port 9000 > /tmp/flask_server.log 2>&1 &
FLASK_PID=$!
echo "✅ Flask backend started (PID: $FLASK_PID)"

# Start OAuth Server (for login flow)
echo "🔐 Starting OAuth Server (port 5050)..."
python3 scripts/oauth_server.py > /tmp/oauth_server.log 2>&1 &
OAUTH_PID=$!
echo "✅ OAuth server started (PID: $OAUTH_PID)"

# Wait for Flask to be ready
sleep 2

# Start NiceGUI frontend
echo "🎨 Starting NiceGUI Dashboard (port 8080)..."
LOG_FILE="nicegui_server.log"
python3 nicegui_dashboard.py > "$LOG_FILE" 2>&1 &
NICEGUI_PID=$!
echo "✅ NiceGUI dashboard started (PID: $NICEGUI_PID)"
echo "📄 Logs writing to: $PWD/$LOG_FILE"

sleep 2

# Open browser
echo ""
echo "🌐 Dashboard ready at: http://127.0.0.1:8080"
echo "🔐 OAuth Service at:   http://127.0.0.1:5050"
echo ""
echo "📊 Pages available:"
echo "  • 🏠 Dashboard - Portfolio overview"
echo "  • 📥 Downloads - Download market data"
echo "  • 📊 Positions - Open positions"
echo "  • 💱 Options - Options chain"
echo "  • 🧪 Backtest - Backtesting engine"
echo "  • 🎯 Strategies - Trading strategies"
echo "  • 🔔 Alerts - Alert rules"
echo ""
echo "🛑 To stop servers:"
echo "  pkill -f 'api_server.py'"
echo "  pkill -f 'oauth_server.py'"
echo "  pkill -f 'nicegui_dashboard.py'"
echo ""

# Keep script running
wait
