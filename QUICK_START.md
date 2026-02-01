# QUICK START - Frontend-Backend Connected ✅

## Current Status
✅ **Frontend and Backend are now fully connected!**

### Running Servers
- **Frontend:** http://localhost:5001 (Flask app.py)
- **Backend API:** http://localhost:8000/api (Flask api_server.py)
- **Database:** market_data.db

## View the Platform
Open in browser: **http://localhost:5001/**

### Available Pages
- `/` - Dashboard with portfolio stats and market indices
- `/positions` - Stock holdings and positions
- `/options` - Options chain data
- `/downloads` - Data download center

## How It Works

### Frontend (app.py - Port 5001)
Serves HTML pages with real data from the backend API:
```python
# When user opens http://localhost:5001/
1. Calls get_portfolio_data()
2. Fetches from: http://localhost:8000/api/portfolio
3. Receives JSON data
4. Renders dashboard.html with real data
```

### Backend API (api_server.py - Port 8000)
Provides REST endpoints for trading data:
```
GET /api/portfolio       - Portfolio summary
GET /api/positions       - Open positions  
GET /api/indices         - Market indices (NIFTY, BANKNIFTY, VIX)
GET /api/orders          - Order history
GET /api/performance     - Performance analytics
POST /api/orders         - Place new order
... and 100+ more endpoints
```

## Data Flow Diagram

```
User Browser
    ↓
http://localhost:5001/  (Frontend)
    ↓
app.py renders HTML
    ↓
get_portfolio_data() calls
    ↓
http://localhost:8000/api/portfolio  (Backend)
    ↓
api_server.py queries database
    ↓
market_data.db
    ↓
Returns JSON
    ↓
Frontend renders page with data
    ↓
User sees portfolio stats, positions, etc.
```

## Testing the Connection

### Test 1: Frontend is working
```bash
curl http://localhost:5001/ | head -20
# Should return HTML starting with <!DOCTYPE html>
```

### Test 2: Backend API is working
```bash
curl http://localhost:8000/api/portfolio
# Should return JSON with portfolio data
```

### Test 3: Frontend → Backend connection
```bash
curl http://localhost:5001/api/data | python3 -m json.tool
# Should return formatted portfolio data
```

## Key Features Integrated

### Portfolio Management
✅ Display total portfolio value  
✅ Show day's P&L (profit/loss)  
✅ Track open positions  
✅ View position-wise P&L  

### Market Data
✅ Real-time market indices (NIFTY, BANKNIFTY, VIX)  
✅ Options chain data  
✅ Watchlist management  

### Trading Features
✅ Paper trading system (simulated orders)  
✅ Risk management rules  
✅ Alert system  
✅ Performance analytics  

### Data Management
✅ Download OHLC data (Parquet/CSV)  
✅ Download history tracking  
✅ Database validation and repair  

## Next Steps

### 1. Authenticate with Upstox
```bash
python scripts/store_token.py
# Follow OAuth flow to get real Upstox access token
```

### 2. View Live Data
Once authenticated, frontend will automatically fetch:
- Live portfolio from Upstox
- Real positions and holdings
- Actual market prices
- Real-time analytics

### 3. Place Live Orders
Use the Order API to place real trades:
```bash
curl -X POST http://localhost:8000/api/order/place \
  -H "Content-Type: application/json" \
  -d '{"symbol": "INFY", "quantity": 1, "order_type": "MARKET", "transaction_type": "BUY"}'
```

### 4. Enable Real-Time Updates
Run WebSocket server for live prices:
```bash
python scripts/websocket_server.py
# Runs on port 5002
```

## Architecture Benefits

| Aspect | Benefit |
|--------|---------|
| **Separation of Concerns** | Frontend and backend can be deployed independently |
| **Scalability** | Backend can handle multiple frontend clients |
| **Reusability** | API endpoints can be used by mobile apps, external tools |
| **Testing** | Test frontend and backend separately |
| **Maintenance** | Easy to update one layer without affecting other |

## File Locations

```
Frontend Code:
  /app.py                  # Main Flask application
  /templates/*             # HTML templates
  /static/css/style.css   # Styling
  /static/js/main.js      # Client-side logic

Backend Code:
  /scripts/api_server.py          # Main API server
  /scripts/auth_manager.py        # Authentication
  /scripts/holdings_manager.py    # Holdings management
  /scripts/performance_analytics.py # Analytics
  /scripts/paper_trading.py       # Paper trading simulator
  /scripts/risk_manager.py        # Risk calculations
  ... and 40+ more backend modules

Database:
  /market_data.db         # SQLite database

Documentation:
  /FRONTEND_BACKEND_CONNECTION.md  # Detailed integration guide
  /QUICK_START.md                 # This file
  /ENDPOINTS.md                   # API endpoint documentation
```

## Troubleshooting

### Issue: "Port already in use"
**Solution:** Kill the process using the port
```bash
lsof -i :5001   # Find Frontend process
lsof -i :8000   # Find Backend process
kill -9 <PID>   # Kill the process
```

### Issue: Frontend shows mock data instead of real data
**Check:**
1. Backend is running: `curl http://localhost:8000/api/portfolio`
2. Frontend can reach backend: Check browser console for errors
3. API endpoint is correct in app.py: Should be `http://localhost:8000/api`

### Issue: Database errors
**Solution:** Rebuild database schema
```bash
python scripts/database_validator.py
```

### Issue: 500 errors from API
**Check logs:**
```bash
tail -50 logs/api_server.log
# Or check debug_dumps/ directory for error details
```

## Database Schema

The backend uses 40+ SQLite tables for:
- Market data (OHLC candles)
- Trading signals (RSI, MACD strategies)
- Paper orders and positions
- Risk metrics and alerts
- Performance tracking
- User authentication tokens
- Portfolio analytics

## Performance Tips

1. **Cold Start**: First request may be slow (database initialization)
2. **Caching**: Backend caches API responses for 60 seconds
3. **Database Indexes**: Already optimized for common queries
4. **Concurrency**: Both Flask servers support multiple concurrent requests

## Production Deployment

When deploying to production:

1. **Use proper WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   gunicorn -w 4 -b 0.0.0.0:8000 scripts.api_server:app
   ```

2. **Use HTTPS**
   ```bash
   # Use nginx as reverse proxy with SSL certificates
   ```

3. **Environment Variables**
   ```bash
   export UPSTOX_CLIENT_ID="your_client_id"
   export UPSTOX_CLIENT_SECRET="your_secret"
   export FLASK_ENV="production"
   ```

4. **Use Redis for caching**
   ```bash
   pip install redis
   # Configure cache in api_server.py
   ```

5. **Database backups**
   ```bash
   sqlite3 market_data.db ".backup '/path/to/backup.db'"
   ```

## Support & Documentation

- **API Docs:** See ENDPOINTS.md for all available API endpoints
- **Integration Guide:** See FRONTEND_BACKEND_CONNECTION.md for detailed architecture
- **Backend Modules:** Each script has docstrings explaining functionality
- **Test Cases:** See tests/ directory for example usage

---

**Status:** ✅ Frontend-Backend Integration Complete  
**Last Updated:** February 1, 2026  
**Frontend:** Running on http://localhost:5001  
**Backend:** Running on http://localhost:8000  
