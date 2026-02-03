# 📘 UPSTOX Trading Platform - Complete Documentation

**Version:** 2.0  
**Last Updated:** February 3, 2026  
**Status:** Production Ready ✅

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Backend Services](#backend-services)
4. [Frontend Pages](#frontend-pages)
5. [API Endpoints](#api-endpoints)
6. [Testing Guide](#testing-guide)
7. [Deployment Guide](#deployment-guide)
8. [Development Workflow](#development-workflow)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## 🚀 Quick Start

### Option 1: Local Development (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Upstox credentials:
# CLIENT_ID=your_client_id
# CLIENT_SECRET=your_client_secret
# REDIRECT_URI=http://localhost:8000/callback

# 5. Generate encryption key
python scripts/generate_encryption_key.py

# 6. Start API server (Terminal 1)
python scripts/api_server.py
# Server will start on http://localhost:8000

# 7. Start frontend dashboard (Terminal 2)
python nicegui_dashboard.py
# Dashboard will open at http://localhost:5001
```

### Option 2: Docker (3 minutes)

```bash
# 1. Clone and configure
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
docker-compose up -d

# 3. Access services
# Frontend: http://localhost:5001
# API: http://localhost:8000
```

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────┐
│         Users (Browser)              │
└─────────────┬───────────────────────┘
              │
    ┌─────────▼─────────┐
    │   NiceGUI         │  Port 5001
    │   Frontend        │  (Python UI)
    └─────────┬─────────┘
              │ HTTP/REST
    ┌─────────▼─────────┐
    │   Flask API       │  Port 8000
    │   Server          │  (REST Endpoints)
    └─────────┬─────────┘
              │
    ┌─────────▼─────────────────────┐
    │  Backend Services              │
    │  • AuthManager (OAuth)         │
    │  • RiskManager (Limits)        │
    │  • StrategyRunner (Algo)       │
    │  • PaperTrading (Virtual)      │
    │  • PerformanceAnalytics        │
    └─────────┬─────────────────────┘
              │
    ┌─────────▼─────────────────────┐
    │  Data Layer                    │
    │  • SQLite Database (40 tables) │
    │  • Upstox API Integration      │
    │  • NewsAPI (Market News)       │
    │  • FinBERT (AI Sentiment)      │
    └────────────────────────────────┘
```

### Tech Stack

- **Backend:** Python 3.11+, Flask 3.0
- **Frontend:** NiceGUI 1.4.0+ (Python-based)
- **Database:** SQLite 3 (PostgreSQL-ready)
- **Server:** Gunicorn (production), Flask dev server (local)
- **APIs:** Upstox v2/v3, NewsAPI, Google AI

---

## 📦 Backend Services

### Core Services (Located in `/scripts/`)

| Service | File | Purpose |
|---------|------|---------|
| **Authentication** | `auth_manager.py` | OAuth 2.0, token encryption/refresh |
| **Risk Management** | `risk_manager.py` | Position limits, circuit breakers, VAR |
| **Order Management** | `order_manager_v3.py` | Order placement, modification, tracking |
| **Paper Trading** | `paper_trading.py` | Virtual portfolio simulation |
| **Strategy Runner** | `strategy_runner.py` | RSI, MACD, SMA strategy execution |
| **Backtesting** | `backtest_engine.py` | Historical strategy testing |
| **Analytics** | `performance_analytics.py` | Sharpe/Sortino, win rate, equity curve |
| **Data Sync** | `data_sync_manager.py` | Market data synchronization |
| **Alert System** | `alert_system.py` | Price/volume/technical alerts |
| **Market Info** | `market_info_service.py` | Status, holidays, timings |
| **AI Assistant** | `ai_service.py` | AI-powered trading insights |

### Service Initialization

```python
# Example: Using AuthManager
from scripts.auth_manager import AuthManager

auth = AuthManager()
token = auth.get_valid_token()  # Auto-refreshes if expired

# Example: Using RiskManager
from scripts.risk_manager import RiskManager

risk = RiskManager()
allowed_qty = risk.calculate_position_size('RELIANCE', 2500)
```

---

## 🎨 Frontend Pages

### Available Pages (22 Total)

| Category | Page | File | Purpose |
|----------|------|------|---------|
| **Dashboard** | Home | `home.py` | Overview, quick stats |
| **Dashboard** | Health | `health.py` | System health monitoring |
| **Trading** | Positions | `positions.py` | Current positions & P&L |
| **Trading** | Orders & Alerts | `orders_alerts.py` | Order management, alerts |
| **Trading** | Live Trading | `live_trading.py` | Real order placement |
| **Data** | Live Data | `live_data.py` | Real-time market data |
| **Data** | Option Chain | `option_chain.py` | Options data viewer |
| **Data** | Historical Options | `historical_options.py` | Historical option data |
| **Data** | Downloads | `downloads.py` | Data export tools |
| **Strategies** | Backtest | `backtest.py` | Strategy backtesting |
| **Strategies** | Signals | `signals.py` | Trading signals dashboard |
| **Strategies** | Strategy Builder | `strategies.py` | Multi-leg option strategies |
| **Analytics** | Analytics | `analytics.py` | Performance metrics |
| **Analytics** | Option Greeks | `option_greeks.py` | Greeks calculation |
| **Upstox** | Upstox Live | `upstox_live.py` | Live account data |
| **Upstox** | User Profile | `user_profile.py` | Account information |
| **Tools** | AI Chat | `ai_chat.py` | AI trading assistant |
| **Tools** | API Debugger | `api_debugger.py` | API testing console |
| **Tools** | Guide | `guide.py` | User documentation |
| **FNO** | F&O Instruments | `fno.py` | Futures & Options list |

### Page Navigation Structure

```
📊 Dashboard
├─ 🏠 Home
└─ 💚 Health

📈 Trading
├─ 📊 Positions
├─ 📝 Orders & Alerts
└─ ⚡ Live Trading

📉 Data
├─ 📡 Live Data
├─ 🔗 Option Chain
├─ 📜 Historical Options
└─ 📥 Downloads

🎯 Strategies
├─ 🔬 Backtest
├─ 📊 Signals
└─ 🏗️ Strategy Builder

📊 Analytics
├─ 📈 Performance
└─ 🎲 Option Greeks

🔌 Upstox
├─ 🔴 Live Data
└─ 👤 User Profile

🛠️ Tools
├─ 🤖 AI Chat
├─ 🔧 API Debugger
└─ 📖 Guide
```

---

## 🔌 API Endpoints

### Complete Endpoint List (60+ endpoints)

#### Portfolio & User (5 endpoints)
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/user/profile` - User profile
- `GET /api/positions` - Current positions
- `GET /api/upstox/holdings` - Holdings list
- `GET /api/upstox/funds` - Available funds

#### Orders (6 endpoints)
- `GET /api/orders` - Order history
- `POST /api/orders` - Place order
- `DELETE /api/orders/<id>` - Cancel order
- `PATCH /api/orders/<id>` - Modify order
- `GET /api/alerts` - Get alerts
- `POST /api/alerts` - Create alert

#### Market Data (8 endpoints)
- `GET /api/upstox/market-quote` - Live quotes
- `GET /api/upstox/option-chain` - Option chain data
- `GET /api/market/status` - Market status
- `GET /api/market/holidays` - Holiday calendar
- `GET /api/market/timings` - Trading hours
- `GET /api/quote/ltp` - Last traded price
- `GET /api/quote/ohlc` - OHLC data
- `GET /api/quote/option-greek` - Option Greeks

#### Historical Data (6 endpoints)
- `GET /api/historical-candle/intraday` - Intraday data
- `GET /api/historical-candle/daily` - Daily candles
- `GET /api/historical-candle/weekly` - Weekly candles
- `GET /api/download/option-chain` - Download option chain
- `GET /api/download/expired-options` - Download expired options
- `GET /api/download/historical` - Download historical data

#### Strategies & Signals (10 endpoints)
- `GET /api/signals` - All signals
- `GET /api/signals/<strategy>` - Strategy-specific signals
- `POST /api/strategies/calendar-spread` - Calendar spread
- `POST /api/strategies/diagonal-spread` - Diagonal spread
- `POST /api/strategies/double-calendar` - Double calendar
- `GET /api/strategies/available` - Available strategies
- `POST /api/backtest/run` - Run backtest
- `GET /api/backtest/strategies` - Backtest strategies
- `GET /api/backtest/results` - Backtest results
- `POST /api/backtest/multi-expiry` - Multi-expiry backtest

#### Analytics (3 endpoints)
- `GET /api/analytics/performance` - Performance metrics
- `GET /api/analytics/equity-curve` - Equity curve data
- `GET /api/performance` - 30-day performance

#### WebSocket (2 endpoints)
- `GET /api/feed/portfolio-stream-feed/authorize` - Portfolio stream auth
- `GET /api/feed/market-data-feed/authorize` - Market data stream auth

#### System (3 endpoints)
- `GET /api/health` - Health check
- `GET /api/instruments/nse-eq` - NSE instruments
- `POST /api/auth/logout` - Logout

### API Usage Examples

```python
import requests

BASE_URL = "http://localhost:8000"

# Get portfolio
response = requests.get(f"{BASE_URL}/api/portfolio")
portfolio = response.json()

# Place paper order
order_data = {
    "symbol": "RELIANCE",
    "qty": 10,
    "side": "BUY",
    "order_type": "LIMIT",
    "price": 2500
}
response = requests.post(f"{BASE_URL}/api/orders", json=order_data)
order = response.json()

# Get market status
response = requests.get(f"{BASE_URL}/api/market/status")
status = response.json()
```

---

## 🧪 Testing Guide

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run specific test file
pytest tests/test_api_endpoints.py

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run only fast tests (exclude slow/live tests)
pytest -m "not slow and not live"
```

### Test Categories

- **Unit Tests** (`-m unit`) - Fast, no dependencies
- **Integration Tests** (`-m integration`) - Mocked external services
- **API Tests** (`-m api`) - API endpoint tests
- **Live Tests** (`-m live`) - Require Upstox credentials (skip in CI)
- **Slow Tests** (`-m slow`) - Long-running (>5s)

### Writing Tests

```python
import pytest
from scripts.auth_manager import AuthManager

def test_auth_manager_initialization():
    """Test AuthManager can be initialized"""
    auth = AuthManager()
    assert auth is not None

@pytest.mark.live
def test_get_profile():
    """Test getting user profile (requires auth)"""
    auth = AuthManager()
    profile = auth.get_profile()
    assert "name" in profile
```

---

## 🚀 Deployment Guide

### Production Deployment (Oracle Cloud / VPS)

```bash
# 1. Clone repository on server
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Run deployment script
sudo bash deploy/oracle_cloud_deploy.sh

# 3. Configure environment
sudo nano /home/runner/UPSTOX-PROJECT/.env
# Add your credentials

# 4. Start services
sudo systemctl start upstox-api
sudo systemctl start upstox-frontend

# 5. Enable auto-start on boot
sudo systemctl enable upstox-api
sudo systemctl enable upstox-frontend

# 6. Check status
sudo systemctl status upstox-api
sudo systemctl status upstox-frontend
```

### Service Management

```bash
# Start services
sudo systemctl start upstox-api
sudo systemctl start upstox-frontend

# Stop services
sudo systemctl stop upstox-api
sudo systemctl stop upstox-frontend

# Restart services
sudo systemctl restart upstox-api
sudo systemctl restart upstox-frontend

# View logs
sudo journalctl -u upstox-api -f
sudo journalctl -u upstox-frontend -f
```

---

## 💻 Development Workflow

### Setting Up Development Environment

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Create branch for feature
git checkout -b feature/my-new-feature

# 3. Install development dependencies
pip install -r requirements.txt
pip install black flake8 pytest pytest-cov

# 4. Make changes and test
black .  # Format code
flake8 .  # Lint code
pytest  # Run tests

# 5. Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/my-new-feature

# 6. Create pull request on GitHub
```

### Code Quality Standards

- **Formatting:** Black (100% compliance required)
- **Linting:** Flake8 (0 errors required)
- **Testing:** pytest (>80% coverage target)
- **Security:** CodeQL scan (0 vulnerabilities)

---

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

#### Database Locked
```bash
# Remove SQLite journal files
rm market_data.db-shm market_data.db-wal
```

#### Authentication Fails
```bash
# Generate new encryption key
python scripts/generate_encryption_key.py
# Update .env with Upstox credentials
```

#### Tests Fail
```bash
# Install all dependencies
pip install -r requirements.txt
# Skip live tests
pytest -m "not live"
```

---

## ❓ FAQ

### Q: How do I get Upstox API credentials?
A: Register at [Upstox Developer Portal](https://upstox.com/developer/), create an app, and copy Client ID and Secret.

### Q: Can I use this for live trading?
A: Yes, but use the Live Trading page with caution. Test thoroughly with paper trading first.

### Q: What's the difference between paper and live trading?
A: Paper trading uses simulated orders in SQLite database. Live trading places real orders via Upstox API.

### Q: How do I add a new strategy?
A: Add strategy class to `scripts/strategy_runner.py` and register it in the strategies list.

### Q: Can I deploy on AWS/Azure?
A: Yes, the Docker setup works on any cloud provider. Update nginx config for your domain.

### Q: How do I backup data?
A: Run `cp market_data.db backups/market_data_$(date +%Y%m%d).db`

### Q: What's the database schema?
A: See `scripts/check_schema.py` output for complete schema with 40+ tables.

---

## 📞 Support

- **Documentation:** This file + README.md
- **Issues:** [GitHub Issues](https://github.com/sheldcoop/UPSTOX-PROJECT/issues)
- **Discussions:** [GitHub Discussions](https://github.com/sheldcoop/UPSTOX-PROJECT/discussions)

---

## 📄 License

MIT License - See LICENSE file

---

**Last Updated:** February 3, 2026  
**Maintained by:** UPSTOX Project Contributors  
**Version:** 2.0 Production Ready ✅
