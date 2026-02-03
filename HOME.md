# 🏠 UPSTOX Trading Platform - Home

**Version:** 2.0  
**Last Updated:** 2026-02-03  
**Status:** ✅ Production Ready with 31 UI Pages

---

## 🚀 Quick Start

### Option 1: Docker (Recommended) - 3 minutes

```bash
# 1. Clone repository
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Configure environment
cp .env.example .env
# Edit .env with your Upstox API credentials

# 3. Start with Docker
docker-compose up -d

# 4. Access the platform
# Frontend: http://localhost:5001
# Backend API: http://localhost:8000
```

### Option 2: Ubuntu/Linux - 10 minutes

```bash
# 1. Clone repository
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Install Python 3.11+
sudo apt-get update
sudo apt-get install python3.11 python3-pip python3-venv

# 3. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env  # Add your credentials

# 6. Start services
# Terminal 1 - Backend API
python scripts/api_server.py

# Terminal 2 - Frontend Dashboard
python nicegui_dashboard.py

# Access: http://localhost:5001
```

### Option 3: Windows - 10 minutes

```powershell
# 1. Clone repository
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# 2. Install Python 3.11+ from python.org

# 3. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
copy .env.example .env
notepad .env  # Add your credentials

# 6. Start services
# Terminal 1
python scripts/api_server.py

# Terminal 2
python nicegui_dashboard.py

# Access: http://localhost:5001
```

---

## 📱 Platform Features

### 🎨 Frontend - 31 Interactive Pages

**Dashboard & Monitoring (4 pages)**
- 🏠 Home - Overview with key metrics
- 💚 Health - System health monitoring
- 📊 Portfolio Summary - Complete portfolio view
- 📈 Performance Analytics - Charts and metrics

**Trading (6 pages)**
- 📝 Positions - Current open positions
- 📋 Orders & Alerts - Paper trading orders
- ⚡ Live Trading - Real order placement
- 📖 Order Book - All orders history
- 📚 Trade Book - Executed trades
- 🎯 GTT Orders - Good Till Triggered orders

**Data & Market Info (5 pages)**
- 📡 Live Data - Real-time market quotes
- 🔗 Option Chain - Multi-expiry chains
- 📜 Historical Options - Historical data
- 📥 Downloads - Data export tools
- 📅 Market Calendar - Holidays & timings

**Strategies & Analysis (5 pages)**
- 🔬 Backtest - Strategy backtesting
- 📊 Signals - Trading signals (RSI, MACD, SMA)
- 🏗️ Strategy Builder - Multi-leg strategies
- 💰 Trade P&L - Profit & Loss tracking
- 🎲 Option Greeks - Greeks calculator

**Portfolio & Funds (4 pages)**
- 🔴 Upstox Live - Live account data
- 💵 Funds - Funds management
- 📊 Margins - Margin calculator
- 💼 Holdings - Long-term holdings

**Tools & Utilities (7 pages)**
- 👤 User Profile - Account information
- 🤖 AI Chat - Trading assistant
- 🔧 API Debugger - Testing console
- 📖 Guide - User documentation
- 🔍 Instruments Browser - Search instruments
- 💰 Charges Calculator - Brokerage calc
- 📊 F&O Instruments - Futures & Options

### ⚙️ Backend - 60+ API Endpoints

**Authentication & User**
- OAuth 2.0 with auto-refresh
- User profile & settings
- Token management

**Trading Operations**
- Order placement (market, limit, SL)
- Order modification & cancellation
- GTT order management
- Position tracking
- Holdings management

**Market Data**
- Real-time quotes
- Historical candles
- Option chains
- Market depth
- Expired instruments

**Analysis & Reports**
- Performance analytics
- P&L calculations
- Strategy backtesting
- Risk metrics
- Trade history

**WebSocket Streams**
- Real-time market data
- Portfolio updates
- Order status updates

---

## 📚 Documentation

### Essential Guides (in docs/)
- 📖 **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- 🛠️ **[LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md)** - Development setup
- 🧪 **[TESTING.md](docs/TESTING.md)** - Testing guide
- ⚠️ **[MISSING_API_ENDPOINTS.md](docs/MISSING_API_ENDPOINTS.md)** - API status

### Reference Documentation (in docs/)
- 📡 **[Upstox.md](docs/Upstox.md)** - Complete Upstox API reference
- 🔧 **[guides/](docs/guides/)** - Feature-specific guides
- 📦 **[archive/](docs/archive/)** - Historical documentation

### Quick References
- 📝 **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current project status
- 🎨 **[NICEGUI_SETUP.txt](NICEGUI_SETUP.txt)** - NiceGUI setup notes

---

## 🐳 Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Services
- **Frontend:** http://localhost:5001 (NiceGUI Dashboard)
- **Backend API:** http://localhost:8000 (Flask REST API)

### Configuration
Edit `docker-compose.yml` to customize:
- Port mappings
- Environment variables
- Volume mounts
- Resource limits

---

## 🖥️ Ubuntu Deployment

### System Requirements
- Ubuntu 20.04+ / Debian 11+
- Python 3.11+
- 2GB RAM minimum
- 10GB disk space

### Production Setup
```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip python3-venv nginx

# 2. Clone and setup
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
nano .env

# 4. Setup systemd services
sudo cp deploy/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable upstox-api upstox-frontend
sudo systemctl start upstox-api upstox-frontend

# 5. Configure Nginx (optional)
sudo cp deploy/nginx.conf /etc/nginx/sites-available/upstox
sudo ln -s /etc/nginx/sites-available/upstox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Users (Web Browser)                  │
└──────────────┬──────────────────────────────┘
               │
      ┌────────▼─────────┐
      │  NiceGUI Frontend │  Port 5001
      │  (31 Pages)       │  Python UI
      └────────┬──────────┘
               │ REST API
      ┌────────▼──────────┐
      │  Flask Backend    │  Port 8000
      │  (60+ Endpoints)  │  API Server
      └────────┬──────────┘
               │
      ┌────────▼──────────────────────┐
      │  Backend Services              │
      │  • Auth Manager (OAuth)        │
      │  • Risk Manager                │
      │  • Strategy Runner             │
      │  • Paper Trading               │
      │  • Performance Analytics       │
      └────────┬──────────────────────┘
               │
      ┌────────▼──────────────────────┐
      │  Data Layer                    │
      │  • SQLite (40+ tables)         │
      │  • Upstox API                  │
      │  • NewsAPI                     │
      │  • FinBERT AI                  │
      └────────────────────────────────┘
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Upstox API Credentials
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
REDIRECT_URI=http://localhost:8000/callback

# Optional - News & AI
NEWS_API_KEY=your_newsapi_key
GOOGLE_AI_API_KEY=your_google_ai_key

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=5001

# Database
DB_PATH=market_data.db

# Security
SECRET_KEY=your_random_secret_key
```

### Getting Upstox Credentials
1. Visit [Upstox Developer Portal](https://upstox.com/developer/)
2. Create a new app
3. Get your Client ID and Client Secret
4. Set redirect URI to `http://localhost:8000/callback`

---

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run specific tests
pytest tests/test_api_endpoints.py -v
pytest tests/test_frontend_pages.py -v
```

---

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Database Locked**
```bash
# Remove lock files
rm market_data.db-shm market_data.db-wal
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

**Docker Issues**
```bash
# Reset Docker
docker-compose down -v
docker-compose up -d --build
```

---

## 📞 Support & Resources

- 📖 **Documentation:** See docs/ folder
- 🐛 **Issues:** [GitHub Issues](https://github.com/sheldcoop/UPSTOX-PROJECT/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/sheldcoop/UPSTOX-PROJECT/discussions)
- 📧 **Email:** Contact repository owner

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Credits

- **Upstox** - Trading API provider
- **NiceGUI** - Python UI framework
- **NewsAPI** - Market news data
- **FinBERT** - Financial sentiment analysis

---

**Made with ❤️ for algorithmic traders**

**Status:** ✅ Production Ready  
**Version:** 2.0  
**Last Updated:** February 3, 2026
