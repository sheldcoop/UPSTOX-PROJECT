# Frontend-Backend Integration Guide

## Architecture Overview

Your Upstox trading platform now has a complete **two-tier Flask architecture**:

```
┌─────────────────────────┐
│   Frontend (app.py)     │  Port 5001
│  - HTML Templates       │
│  - Dashboard            │
│  - Positions            │
│  - Options Chain        │
│  - Data Downloads       │
└────────────┬────────────┘
             │ HTTP requests
             │ (via requests library)
             ↓
┌─────────────────────────┐
│ Backend API (api_server) │ Port 8000
│  - Portfolio            │
│  - Positions            │
│  - Orders               │
│  - Alerts               │
│  - Analytics            │
│  - Performance          │
└─────────────────────────┘
             │ Database
             ↓
      ┌──────────────┐
      │ market_data  │
      │   .db        │
      └──────────────┘
```

## File Structure

```
/Users/prince/Desktop/UPSTOX-project/
├── app.py                          # Frontend Flask app (Port 5001)
├── scripts/
│   ├── api_server.py              # Backend API server (Port 8000)
│   ├── auth_manager.py            # Authentication
│   ├── holdings_manager.py        # Holdings data
│   ├── performance_analytics.py   # Analytics
│   ├── risk_manager.py            # Risk calculations
│   └── ... (other modules)
├── templates/
│   ├── base.html                  # Master template
│   ├── dashboard.html             # Dashboard page
│   ├── positions.html             # Positions page
│   ├── options.html               # Options chain
│   └── downloads.html             # Data downloads
├── static/
│   ├── css/style.css              # Styling
│   └── js/main.js                 # Client-side interactivity
└── market_data.db                 # SQLite database
```

## Connection Details

### Frontend Server (app.py)
- **Port:** 5001
- **Purpose:** Serves HTML templates with integrated backend data
- **Start command:** 
  ```bash
  /Users/prince/Desktop/UPSTOX-project/.venv/bin/python app.py
  ```

### Backend API Server (api_server.py)
- **Port:** 8000
- **Purpose:** Provides REST API endpoints for portfolio, positions, orders, analytics
- **Start command:**
  ```bash
  /Users/prince/Desktop/UPSTOX-project/.venv/bin/python scripts/api_server.py
  ```

### Connection URL
Frontend calls backend at: `http://localhost:8000/api`

## How Frontend Gets Data

### 1. **Dashboard Data (Home Page)**
```python
# app.py - format_data_for_template()

def get_portfolio_data():
    response = requests.get(f'{BACKEND_API_URL}/portfolio', timeout=API_TIMEOUT)
    # Returns: { total_value, day_pnl, positions_count, mode, authenticated }

def get_market_indices():
    response = requests.get(f'{BACKEND_API_URL}/indices', timeout=API_TIMEOUT)
    # Returns: [ NIFTY, BANKNIFTY, VIX price data ]
```

### 2. **Positions Page**
```python
def get_positions_data():
    response = requests.get(f'{BACKEND_API_URL}/positions', timeout=API_TIMEOUT)
    # Returns: [ { symbol, qty, entry_price, current_price, pnl } ]
```

### 3. **Performance Metrics**
```python
def get_performance_data():
    response = requests.get(f'{BACKEND_API_URL}/performance', timeout=API_TIMEOUT)
    # Returns: { total_trades, win_rate, sharpe_ratio, max_drawdown }
```

## Backend API Endpoints

### Portfolio & Holdings
- `GET /api/portfolio` - Portfolio summary
- `GET /api/positions` - Open positions
- `GET /api/orders` - Order history
- `POST /api/orders` - Place new order

### Market Data
- `GET /api/indices` - Market indices (NIFTY, BANKNIFTY, VIX)
- `GET /api/watchlist` - Watchlist items
- `GET /api/options/chain?symbol=NIFTY` - Options chain

### Analytics & Performance
- `GET /api/performance` - Performance metrics
- `GET /api/alerts` - Active alerts
- `GET /api/signals` - Trading signals
- `GET /api/analytics/performance` - Comprehensive analytics
- `GET /api/analytics/equity-curve?days=30` - Equity curve

### Live Upstox API (Phase 3)
- `GET /api/upstox/profile` - User profile from Upstox
- `GET /api/upstox/holdings` - Live holdings
- `GET /api/upstox/positions` - Live positions
- `GET /api/upstox/option-chain?symbol=NIFTY` - Live options chain
- `GET /api/upstox/funds` - Account funds

### Data Download
- `POST /api/download/stocks` - Download OHLC data
- `GET /api/download/history` - List downloaded files
- `GET /api/download/logs` - Download logs

### Multi-Expiry Strategies
- `POST /api/strategies/calendar-spread` - Create calendar spread
- `POST /api/strategies/diagonal-spread` - Create diagonal spread
- `POST /api/strategies/double-calendar` - Create double calendar
- `POST /api/backtest/multi-expiry` - Backtest with auto-rolling

## Data Flow Example

### User navigates to Dashboard

```
1. Browser: GET http://localhost:5001/
2. Frontend (app.py):
   - @app.route('/') calls dashboard()
   - Calls format_data_for_template()
   - Calls get_portfolio_data()
   
3. Frontend makes HTTP request:
   - GET http://localhost:8000/api/portfolio
   
4. Backend (api_server.py):
   - @app.route('/api/portfolio') calls get_portfolio()
   - Queries database or Upstox API
   - Returns JSON: { total_value, day_pnl, positions_count, ... }
   
5. Frontend receives response
   - Formats data for display
   - Renders dashboard.html template with data
   - Browser displays portfolio stats, market indices, etc.
```

## Testing the Connection

### Test Frontend
```bash
curl http://localhost:5001/
# Should return HTML dashboard page
```

### Test Backend API
```bash
curl http://localhost:8000/api/health
# Should return: {"status": "healthy", "timestamp": "...", "database": "connected"}
```

### Test Frontend → Backend Communication
```bash
curl http://localhost:5001/api/data
# Should return portfolio data fetched from backend
```

## Fallback Mechanism

If backend API is unavailable, frontend uses **mock data**:
- Portfolio: ₹2,47,891.00 value, 12 positions
- Indices: NIFTY, BANKNIFTY, VIX mock prices
- This ensures UI remains functional during development

```python
# Example fallback in get_portfolio_data()
def get_portfolio_data():
    try:
        response = requests.get(f'{BACKEND_API_URL}/portfolio', timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch portfolio from backend: {e}")
    
    # Fallback mock data
    return {
        'authenticated': False,
        'total_value': 247891.00,
        'day_pnl': 4231.50,
        ...
    }
```

## Running Both Servers

### Option 1: Separate Terminals
```bash
# Terminal 1: Start Backend API
cd /Users/prince/Desktop/UPSTOX-project
/Users/prince/Desktop/UPSTOX-project/.venv/bin/python scripts/api_server.py

# Terminal 2: Start Frontend
cd /Users/prince/Desktop/UPSTOX-project
/Users/prince/Desktop/UPSTOX-project/.venv/bin/python app.py
```

### Option 2: Start Script
```bash
#!/bin/bash
# save as start_all.sh in project root

VENV="/Users/prince/Desktop/UPSTOX-project/.venv/bin/python"
PROJECT="/Users/prince/Desktop/UPSTOX-project"

echo "Starting Backend API on port 8000..."
$VENV $PROJECT/scripts/api_server.py &
BACKEND_PID=$!

sleep 2

echo "Starting Frontend on port 5001..."
$VENV $PROJECT/app.py &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Frontend: http://localhost:5001"
echo "Backend API: http://localhost:8000/api"
echo ""
echo "Press CTRL+C to stop both servers"

wait
```

## Next Steps

1. **Live Data Integration**
   - Replace mock data with real Upstox API calls
   - Implement WebSocket for real-time updates
   - See `scripts/upstox_live_api.py` for live integration

2. **Database Connectivity**
   - Configure proper SQLite indexes
   - Implement caching for frequently accessed data
   - Add data refresh schedules

3. **Authentication**
   - Implement user login/session management
   - Store user preferences
   - Manage multiple user portfolios

4. **Frontend Enhancements**
   - Add real-time price updates via WebSocket
   - Implement interactive charts
   - Add order placement UI
   - Build alert management dashboard

5. **Testing**
   - Add unit tests for API endpoints
   - Integration tests for frontend-backend
   - Load testing for performance
   - See `tests/` directory for test files

## Troubleshooting

### "Address already in use" error
```bash
# Find process using port
lsof -i :5001
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Frontend can't reach backend
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check CORS is enabled in `api_server.py`: `CORS(app)`
- Verify URL in `app.py`: `BACKEND_API_URL = 'http://localhost:8000/api'`

### Database errors
- Check database file exists: `ls -la market_data.db`
- Verify database is not locked: `lsof | grep market_data.db`
- Rebuild tables: `python scripts/database_validator.py`

## Performance Tips

1. **Enable query caching** in backend
2. **Implement pagination** for large datasets
3. **Use database indexes** for frequent queries
4. **Cache API responses** with Redis (optional)
5. **Compress API responses** using gzip

## Security Considerations

1. Use HTTPS in production (not HTTP)
2. Implement API authentication tokens
3. Validate all user input
4. Rate limit API endpoints
5. Use environment variables for sensitive config
6. Implement CSRF protection for forms

---

**Architecture by:** GitHub Copilot  
**Date:** February 1, 2026  
**Status:** ✅ Frontend-Backend Integration Complete
