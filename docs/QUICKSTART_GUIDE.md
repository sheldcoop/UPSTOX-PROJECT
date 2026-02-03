# 🚀 Upstox Trading Platform - Quickstart Guide

**Version:** 3.0  
**Last Updated:** February 2026

## Overview

Production-grade algorithmic trading platform with:
- **Backend:** 11 production features (Flask API, risk management, strategies, analytics)
- **Frontend:** Modern NiceGUI dashboard with 38/52 endpoints (73% coverage)
- **Database:** SQLite with 40+ tables
- **Real-time:** WebSocket support for live data

---

## ⚡ Quick Start (5 Minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with Upstox API credentials
```

### 3. Start Platform
```bash
./start_nicegui.sh
```

### 4. Access
Open: **http://localhost:8080**

---

## 📱 Dashboard Features

### Trading
- **Orders & Alerts** - Paper trading management
- **Live Trading** - Real order placement ⚠️
- **Positions** - P&L tracking
- **Option Chain** - Live options data

### Strategies
- **Signals** - Trading signals
- **Strategy Builder** - Calendar/diagonal spreads
- **Backtest** - Historical testing

### Analytics
- **Analytics Dashboard** - Performance metrics
- **Upstox Live** - Real-time account data

---

## 📊 Coverage Status

- **Total Endpoints:** 52
- **Frontend Coverage:** 38 (73.1%)
- **CI/CD:** ✅ Passing
- **Linting:** ✅ Black + Flake8

---

For detailed documentation, see:
- **README.md** - Main docs
- **API_ENDPOINTS.md** - API reference
- **LOCAL_DEVELOPMENT.md** - Development guide

**Happy Trading! ��**
