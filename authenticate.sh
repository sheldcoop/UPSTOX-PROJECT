#!/bin/bash

# Upstox Authentication Setup
# Run this to connect your Upstox account

echo "╔══════════════════════════════════════════════════╗"
echo "║   Upstox Authentication Setup                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please run: ./setup_auth.sh first"
    exit 1
fi

echo "✅ Credentials loaded from .env"
echo ""
echo "🔐 Starting OAuth server..."
echo "   1. A browser window will open"
echo "   2. Login to Upstox"
echo "   3. Authorize the app"
echo "   4. Return here when done"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Start OAuth server with Python path fix
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)/scripts:$PYTHONPATH"
python3 scripts/oauth_server.py --open-browser
