#!/bin/bash

# Upstox Trading Platform - Quick Start Script
# Sets up all new features and enhancements

set -e

echo "=============================================="
echo "  UPSTOX Trading Platform - Setup Script"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo ""
echo "Step 2: Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

echo ""
echo "Step 3: Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""
echo "Step 4: Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "Step 5: Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ .env file created from .env.example${NC}"
    echo -e "${YELLOW}  Please edit .env and add your credentials${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo "Step 6: Creating required directories..."
mkdir -p logs debug_dumps cache downloads
echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo "Step 7: Adding database indexes..."
if [ -f "market_data.db" ]; then
    python scripts/add_database_indexes.py --db-type sqlite 2>/dev/null || echo -e "${YELLOW}⚠ Some indexes already exist${NC}"
    echo -e "${GREEN}✓ Database indexes added${NC}"
else
    echo -e "${YELLOW}⚠ market_data.db not found, skipping indexes${NC}"
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your credentials in .env:"
echo "   - UPSTOX_CLIENT_ID"
echo "   - UPSTOX_CLIENT_SECRET"
echo "   - EMAIL_FROM, EMAIL_PASSWORD (optional)"
echo "   - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (optional)"
echo ""
echo "2. Choose your deployment method:"
echo ""
echo "   Option A - Local Development:"
echo "   $ python app.py                    # Start frontend (port 5001)"
echo "   $ python scripts/api_server.py     # Start API (port 8000)"
echo ""
echo "   Option B - Docker Deployment:"
echo "   $ docker-compose up -d             # Start all services"
echo "   $ docker-compose logs -f           # View logs"
echo ""
echo "   Option C - Production Deployment:"
echo "   $ ./start_production.sh            # Start with Gunicorn"
echo ""
echo "3. Access the application:"
echo "   Frontend:   http://localhost:5001"
echo "   API:        http://localhost:8000"
echo "   Prometheus: http://localhost:9090  (if using Docker)"
echo "   Grafana:    http://localhost:3000  (if using Docker)"
echo ""
echo "4. Run tests:"
echo "   $ pytest tests/ -v"
echo ""
echo "5. Read documentation:"
echo "   - NEW_FEATURES_README.md - New features guide"
echo "   - IMPROVEMENTS_SUGGESTIONS.md - Implementation details"
echo "   - README.md - General documentation"
echo ""
echo -e "${GREEN}Happy trading! 🚀${NC}"
echo ""
