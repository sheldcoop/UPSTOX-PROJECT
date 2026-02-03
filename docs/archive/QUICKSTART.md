# 🚀 Quick Start Guide

## Single Command Startup

Instead of running multiple terminals, use the unified startup script:

```bash
./start.sh
```

This will:
- ✅ Activate Python virtual environment
- ✅ Start Flask API server on `http://localhost:5001`
- ✅ Start WebSocket server on `http://localhost:5002`
- ✅ Start Vite frontend on `http://localhost:5173`
- ✅ Log to `logs/api_server.log`, `logs/websocket.log`, `logs/vite.log`

**To stop:** Press `Ctrl+C` (stops all servers gracefully)

---

## Manual Startup (Old Way)

If you prefer running them separately:

### Terminal 1: Flask API
```bash
source .venv/bin/activate
python scripts/api_server.py
```

### Terminal 2: WebSocket Server
```bash
source .venv/bin/activate
python scripts/websocket_server.py
```

### Terminal 3: Vite Frontend
```bash
cd frontend
npm run dev
```

---

## Phase 3 Features (Production Ready) 🔴 NEW

### ✅ Live Upstox API Integration
**Endpoints:**
- `GET /api/upstox/profile` - User profile
- `GET /api/upstox/holdings` - Long-term holdings
- `GET /api/upstox/positions` - Day/net positions
- `GET /api/upstox/option-chain?symbol=NIFTY&expiry_date=2024-01-25` - Live option chain
- `GET /api/upstox/market-quote?symbol=NSE_INDEX|Nifty 50` - Real-time quote
- `GET /api/upstox/funds` - Account margin

**Test:**
```bash
curl http://localhost:5001/api/upstox/profile
```

### ✅ Order Placement System
**Endpoints:**
- `POST /api/order/place` - Place order
- `DELETE /api/order/cancel/<order_id>` - Cancel order
- `PUT /api/order/modify/<order_id>` - Modify order
- `GET /api/order/status/<order_id>` - Order status

**Example:**
```bash
curl -X POST http://localhost:5001/api/order/place \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY24125CE",
    "quantity": 50,
    "order_type": "LIMIT",
    "transaction_type": "BUY",
    "price": 150.50
  }'
```

### ✅ WebSocket Real-time Updates
**Server:** `ws://localhost:5002`

**Frontend Hook:**
```tsx
import { useWebSocket } from '@/hooks/useWebSocket';

const { isConnected, subscribeOptions } = useWebSocket();

useEffect(() => {
  if (isConnected) {
    subscribeOptions('NIFTY', '2024-01-25', (options) => {
      console.log('Options updated:', options);
    });
  }
}, [isConnected]);
```

**Events:**
- `subscribe_options` - Get option chain updates every 5 seconds
- `subscribe_quote` - Get market quote updates
- `subscribe_positions` - Get portfolio updates

### ✅ Strategy Backtesting
**Endpoints:**
- `POST /api/backtest/run` - Run backtest
- `GET /api/backtest/strategies` - Available strategies
- `GET /api/backtest/results` - Past backtest results

**Example:**
```bash
curl -X POST http://localhost:5001/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "iron_condor",
    "spot_price": 18000,
    "entry_date": "2024-01-01",
    "exit_date": "2024-01-10"
  }'
```

**Available Strategies:**
- Iron Condor - Sell OTM put/call spreads
- Bull Call Spread - Buy lower strike call, sell higher strike call

### ✅ Portfolio Analytics
**Endpoints:**
- `GET /api/analytics/performance` - Comprehensive performance metrics
- `GET /api/analytics/equity-curve?days=30` - Equity curve data

**Metrics:**
- Sharpe Ratio - Risk-adjusted returns
- Sortino Ratio - Downside deviation only
- Max Drawdown - Peak-to-trough decline
- Win Rate - Win %, avg win/loss, profit factor

**Test:**
```bash
curl http://localhost:5001/api/analytics/performance
```

### ✅ Modern Theme System
- **Light/Dark Mode Toggle:** Click sun/moon icon in top bar
- **Professional Colors:** Gradient design instead of pure black
- **Smooth Transitions:** CSS animations for theme switching
- **Persistent:** Remembers your preference in localStorage

---

## Troubleshooting

**Port already in use:**
```bash
# Kill processes on ports 5001, 5002, and 5173
lsof -ti:5001 | xargs kill -9
lsof -ti:5002 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**WebSocket not connecting:**
```bash
# Check if WebSocket server is running
curl http://localhost:5002/socket.io/
# Should return Socket.IO version info
```

**Frontend not loading:**
```bash
cd frontend
npm install
npm run dev
```

**Python packages missing:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install flask-socketio  # WebSocket dependency
```

**API authentication errors:**
```bash
# Check if token is valid
python -c "from scripts.auth_manager import AuthManager; auth = AuthManager(); print(auth.get_valid_token())"
```

---

## API Credentials

Your Upstox API credentials are already configured in `scripts/auth_manager.py`.

To verify:
```python
python -c "from scripts.auth_manager import AuthManager; print(AuthManager.has_credentials())"
```

If you need to re-authenticate, run the OAuth flow:
```bash
python scripts/auth_manager.py
```

---

## Development

**Hot Reload:**
- Frontend: Vite auto-reloads on file changes
- Backend: Flask restarts on Python file changes (if `debug=True`)

**Logs:**
- API: `logs/api_server.log`
- Frontend: `logs/vite.log`
- Downloads: `logs/data_downloader.log`
- Options: `logs/options_chain.log`

**Debug Panel:**
- Open platform → Click "Debug Panel" in sidebar
- View API logs with TraceID filtering
- Check download history
- See error dumps

---

🎉 **Happy Trading!**
