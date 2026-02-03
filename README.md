# 🚀 UPSTOX Trading Platform

**Production-grade algorithmic trading platform with 31 UI pages built on Upstox API**

[![CI/CD Pipeline](https://github.com/sheldcoop/UPSTOX-PROJECT/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/sheldcoop/UPSTOX-PROJECT/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UI Pages](https://img.shields.io/badge/UI_Pages-31-success.svg)]()
[![API Endpoints](https://img.shields.io/badge/API_Endpoints-60+-blue.svg)]()

---

## ⚡ Quick Start (3 Steps)

### 🖥️ Local Development (Recommended - 5 minutes)

```bash
# Step 1: Clone & Setup
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Step 2: Configure
cp .env.example .env
# Edit .env with your Upstox credentials

# Step 3: Run
python run_platform.py

# Access: http://localhost:5001
```

**That's it!** The platform will:
- ✅ Check your Python version
- ✅ Verify dependencies
- ✅ Initialize the database
- ✅ Start all services (API + Frontend + OAuth)
- ✅ Open your browser automatically

For manual control, see [Local Development Guide](docs/LOCAL_DEVELOPMENT.md).

---

### 🐳 Docker (Alternative - 3 minutes)

```bash
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
cp .env.example .env
# Edit .env with your Upstox credentials

docker-compose up -d

# Access: http://localhost:5001
```

---

---

## 📊 What's Included

### ✅ 31 Interactive UI Pages
- **Dashboard**: Home, Health, Portfolio Summary, Analytics
- **Trading**: Positions, Orders, Live Trading, Order Book, Trade Book, GTT Orders
- **Data**: Live Data, Option Chain, Historical Data, Downloads, Market Calendar
- **Strategies**: Backtest, Signals, Strategy Builder, Trade P&L
- **Portfolio**: Upstox Live, Funds, Margins, Holdings  
- **Tools**: AI Chat, API Debugger, Instruments Browser, Charges Calculator, Guide

### ✅ 60+ Backend API Endpoints
- Authentication & User Management
- Trading Operations (Orders, Positions, Holdings)
- Market Data (Quotes, Candles, Option Chains)
- Analytics & Reports (P&L, Performance, Risk)
- WebSocket Streams (Real-time updates)

### ✅ Production Features
- OAuth 2.0 Authentication with auto-refresh
- Risk Management & Position Sizing
- Trading Strategies (RSI, MACD, SMA)
- Paper Trading System
- Performance Analytics
- AI-Powered Sentiment Analysis
- Docker Deployment Ready

---

## 📚 Documentation

**Essential Reading:**
- 🚀 **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
- 🛠️ **[docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md)** - Development setup
- 📊 **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current status

**Reference:**
- 🧪 **[docs/TESTING.md](docs/TESTING.md)** - Testing guide
- ⚠️ **[docs/MISSING_API_ENDPOINTS.md](docs/MISSING_API_ENDPOINTS.md)** - API status
- 📡 **[docs/Upstox.md](docs/Upstox.md)** - Upstox API reference
- 📖 **[docs/guides/](docs/guides/)** - Feature-specific guides

---

## 🏗️ Architecture
sudo bash deploy/oracle_cloud_deploy.sh

# Configure credentials
cp .env.example .env
nano .env

# Restart services
sudo systemctl restart upstox-api upstox-frontend
```

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete deployment guide.

---

## 📚 Documentation

### Getting Started
- 📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide (single source of truth)
- 🛠️ **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Local development setup and workflow
- 🧪 **[TESTING.md](TESTING.md)** - Testing guide and best practices

### Technical Documentation
- 🏗️ **[COMPREHENSIVE_ANALYSIS.md](COMPREHENSIVE_ANALYSIS.md)** - Complete system architecture
- 📡 **[docs/ENDPOINTS.md](docs/ENDPOINTS.md)** - API endpoint documentation
- 🔧 **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details

### Migration Guides
- 🔄 **[V3_API_IMPLEMENTATION_GUIDE.md](V3_API_IMPLEMENTATION_GUIDE.md)** - Upstox API v3 migration
- 🌐 **[WEBSOCKET_IMPLEMENTATION_PLAN.md](WEBSOCKET_IMPLEMENTATION_PLAN.md)** - WebSocket v3 upgrade
- 📋 **[MISSING_API_ENDPOINTS.md](MISSING_API_ENDPOINTS.md)** - Pending API integrations

### Operations
- 🐛 **[.github/debugging-protocol.md](.github/debugging-protocol.md)** - Complete debugging protocol (1000 lines)
- 📖 **[.github/debugging-examples.md](.github/debugging-examples.md)** - 6 real-world debugging scenarios
- ⚡ **[.github/debugging-quick-reference.md](.github/debugging-quick-reference.md)** - Quick debugging cheat sheets
- 📊 **[docs/PRODUCTION_FEATURES.md](docs/PRODUCTION_FEATURES.md)** - Production feature list
- 🔒 **[docs/SECURITY_PATCH.md](docs/SECURITY_PATCH.md)** - Security guidelines

---

## 🏛️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│                 USERS (Browser/API)                  │
└────────────────────┬────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │   Nginx (Port 80)   │  SSL Termination
          └──────────┬──────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐           ┌─────▼──────┐
    │  API    │           │  Frontend  │
    │ :8000   │◄─────────►│  :5001     │
    │(Gunicorn)           │ (NiceGUI)  │
    └────┬────┘           └────────────┘
         │
    ┌────▼────────────────────────────────┐
    │  Backend Services                    │
    │  • AuthManager (OAuth 2.0)          │
    │  • RiskManager (Position sizing)    │
    │  • StrategyRunner (Backtesting)     │
    │  • AlertSystem (Notifications)      │
    │  • PaperTrading (Simulation)        │
    └────┬────────────────────────────────┘
         │
    ┌────▼────────────────────────────────┐
    │  Data Layer                          │
    │  • SQLite (40+ tables)              │
    │  • Redis (Caching - optional)       │
    │  • NewsAPI (Market news)            │
    │  • FinBERT (Sentiment AI)           │
    └─────────────────────────────────────┘
```

### Database Schema (40+ Tables)

- **Market Data:** `ohlc_data`, `option_chain`, `market_quotes`
- **Trading:** `trading_signals`, `paper_orders`, `backtest_results`
- **Risk:** `risk_metrics`, `position_limits`, `circuit_breaker_state`
- **Alerts:** `alert_rules`, `alert_history`, `price_alerts`
- **Analytics:** `performance_metrics`, `strategy_results`
- **Auth:** `oauth_tokens`, `user_settings`

---

## 🛠️ Tech Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** Flask 3.0.0 (modular blueprints)
- **WSGI Server:** Gunicorn (production)
- **Database:** SQLite 3 (PostgreSQL-ready)
- **Cache:** Redis (optional)
- **Data Processing:** Pandas 2.1.4, NumPy 1.26.2

### Frontend
- **Framework:** NiceGUI 1.4.0+ (Python-based reactive UI)
- **Real-time:** Flask-SocketIO 5.3.6
- **Charts:** Plotly, Matplotlib
- **Styling:** Tailwind CSS (via NiceGUI)

### AI/ML
- **Sentiment Analysis:** FinBERT (transformers)
- **Market Insights:** Google Generative AI
- **News:** NewsAPI.org

### DevOps
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (reverse proxy)
- **Process Management:** systemd
- **Monitoring:** Prometheus + Grafana
- **CI/CD:** GitHub Actions
- **Security:** Trivy vulnerability scanner

### External APIs
- **Trading:** Upstox API v2/v3
- **News:** NewsAPI.org
- **Corporate Actions:** NSE India (web scraping)

---

## 📋 Prerequisites

### Required
- Python 3.11 or higher
- Upstox API credentials (Client ID + Secret)
- 4GB RAM minimum
- 50GB storage recommended

### Optional
- Redis (for caching)
- Docker (for containerized deployment)
- PostgreSQL (for production database)

---

## 🎯 Use Cases

### 1. Algorithmic Trading
- Develop and backtest trading strategies
- Execute automated trades via Upstox API
- Monitor performance with real-time analytics

### 2. Paper Trading
- Practice trading without risking real money
- Test strategies with realistic market conditions
- Track virtual portfolio performance

### 3. Market Research
- Access historical market data
- Analyze option chains and Greeks
- Monitor corporate actions and news

### 4. Risk Management
- Set position limits and stop-losses
- Calculate portfolio risk metrics (VAR, Sharpe)
- Circuit breaker protection

---

## 🔒 Security

- ✅ OAuth 2.0 with token encryption (Fernet)
- ✅ No secrets in source code (environment variables)
- ✅ Systemd security hardening
- ✅ Regular security scans (Trivy)
- ✅ Rate limiting on API endpoints
- ✅ Input validation and sanitization

**See:** [docs/SECURITY_PATCH.md](docs/SECURITY_PATCH.md)

---

## 📊 Current Status

| Component | Status | Coverage |
|-----------|--------|----------|
| Backend Services | ✅ Complete | 11/11 features |
| API Endpoints | ✅ Complete | 50+ endpoints |
| Frontend Pages | ✅ Complete | 12 pages |
| Database Schema | ✅ Complete | 40+ tables |
| Documentation | ✅ Complete | Consolidated |
| CI/CD Pipeline | ✅ Passing | Automated |
| Production Ready | ✅ Yes | Deployed |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

**See:** [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) for development workflow

---

## 🐛 Troubleshooting

### Quick Debugging
See **[.github/debugging-quick-reference.md](.github/debugging-quick-reference.md)** for instant help.

### Common Issues

**Import errors:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**Port already in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database locked:**
```bash
rm market_data.db-shm market_data.db-wal
```

**UI not updating (NiceGUI):**
- Check if you're using `@ui.refreshable` decorator
- Call `.refresh()` after async updates
- See debugging-examples.md for solutions

**UI freezes on button click:**
- Never use `time.sleep()` in event handlers
- Use `await run.io_bound()` for blocking operations
- See async awareness section in debugging protocol

**Docker networking issues:**
- Use service names instead of `localhost`
- Set `API_BASE=http://backend:9000` in environment

**For complete debugging guide:** [.github/debugging-protocol.md](.github/debugging-protocol.md)

**See:** [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for deployment-specific issues

---

## 📞 Support

- 📖 **Documentation:** See links above
- 🐛 **Issues:** [GitHub Issues](https://github.com/sheldcoop/UPSTOX-PROJECT/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/sheldcoop/UPSTOX-PROJECT/discussions)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Upstox** - Trading API provider
- **NiceGUI** - Python UI framework
- **NewsAPI** - Market news data
- **FinBERT** - Financial sentiment analysis

---

## 🎯 Roadmap

- [ ] Migrate to Upstox API v3 (WebSocket, orders)
- [ ] Add real-time WebSocket streaming
- [ ] PostgreSQL migration for scalability
- [ ] Advanced chart analysis tools
- [ ] Mobile app (React Native)
- [ ] Multi-broker support

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** February 3, 2026

**Made with ❤️ for algorithmic traders**

