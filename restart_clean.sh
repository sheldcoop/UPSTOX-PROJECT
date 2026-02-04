#!/bin/bash
# Clean restart script - kills all old processes and starts fresh

echo "🧹 Cleaning up old processes..."

# Kill any running nicegui processes
pkill -f nicegui_dashboard.py 2>/dev/null
pkill -f api_server.py 2>/dev/null  
pkill -f oauth_server.py 2>/dev/null

# Wait for processes to die
sleep 2

# Remove PID files
rm -f logs/*.pid 2>/dev/null

# Check if ports are free
echo "🔍 Checking ports..."
lsof -ti:5001 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5050 | xargs kill -9 2>/dev/null

sleep 1

echo "✅ Cleanup complete!"
echo "🚀 Starting platform..."

# Start platform with Python 3.11
python3.11 run_platform.py
