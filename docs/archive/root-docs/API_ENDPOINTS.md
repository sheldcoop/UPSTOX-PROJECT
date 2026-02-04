# 🗺️ API Endpoints & Frontend Integration Map

**Last Updated:** February 3, 2026  
**Total Endpoints:** 52 across 11 blueprints

This document maps all backend API endpoints to frontend pages, showing implementation status, test coverage, and integration gaps.

---

## 📊 Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Blueprints** | 11 | 100% |
| **Total Endpoints** | 52 | 100% |
| **Endpoints with Frontend UI** | 7 | 13.5% |
| **Endpoints with Tests** | 7 | 13.5% |
| **Orphaned Endpoints (No UI)** | 45 | 86.5% |
| **Untested Endpoints** | 45 | 86.5% |

---

## 🎯 Complete Endpoint Inventory

### 1. Health Blueprint (`scripts/blueprints/health.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/health` | GET | Health check for monitoring | ❌ None | ✅ Yes | ✅ Complete |

**Gap:** None - health checks working

---

### 2. Portfolio Blueprint (`scripts/blueprints/portfolio.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/portfolio` | GET | Portfolio summary (paper/live) | ✅ home.py | ✅ Yes | ✅ Complete |
| `/api/user/profile` | GET | User profile from Upstox | ❌ None | ❌ No | ⚠️ No UI |
| `/api/positions` | GET | All open positions + P&L | ✅ positions.py | ✅ Yes | ✅ Complete |
| `/api/positions/<symbol>` | GET | Position for specific symbol | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** Position detail page needed

---

### 3. Orders Blueprint (`scripts/blueprints/orders.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/orders` | GET | Get paper trading order history | ❌ None | ❌ No | ⚠️ No UI |
| `/api/orders` | POST | Place new paper order | ❌ None | ❌ No | ⚠️ No UI |
| `/api/orders/<int:order_id>` | DELETE | Cancel paper order | ❌ None | ❌ No | ⚠️ No UI |
| `/api/alerts` | GET | Get active price alerts | ❌ None | ❌ No | ⚠️ No UI |
| `/api/alerts` | POST | Create price alert | ❌ None | ❌ No | ⚠️ No UI |
| `/api/alerts/<int:alert_id>` | DELETE | Delete alert rule | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** 🔴 CRITICAL - Orders & Alerts management page completely missing

---

### 4. Data Blueprint (`scripts/blueprints/data.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/download/stocks` | POST | Download OHLC from Yahoo | ✅ downloads.py | ❌ No | ✅ Complete |
| `/api/download/history` | GET | List downloaded files | ✅ state.py | ❌ No | ✅ Complete |
| `/api/download/logs` | GET | Download operation logs | ❌ None | ❌ No | ⚠️ No UI |
| `/api/options/chain` | GET | Live options chain data | ✅ option_chain.py | ✅ Yes | ✅ Complete |
| `/api/options/market-status` | GET | Check if market open | ✅ option_chain.py | ❌ No | ✅ Complete |
| `/api/page/downloads` | GET | Render downloads template | ✅ downloads.py | ❌ No | ✅ Complete |
| `/api/expired/expiries` | GET | Expired option expiries | ⚠️ Partial | ❌ No | ⚠️ Incomplete |
| `/api/expired/download` | POST | Download expired chain | ⚠️ Partial | ❌ No | ⚠️ Incomplete |
| `/api/market-quote` | POST | Live market quotes | ✅ downloads.py | ❌ No | ✅ Complete |

**Gap:** Expired options UI needs completion

---

### 5. Order Placement Blueprint (`scripts/blueprints/order.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/order/place` | POST | Place LIVE Upstox order | ❌ None | ❌ No | ⚠️ No UI |
| `/api/order/cancel/<id>` | DELETE | Cancel LIVE order | ❌ None | ❌ No | ⚠️ No UI |
| `/api/order/modify/<id>` | PUT | Modify LIVE order | ❌ None | ❌ No | ⚠️ No UI |
| `/api/order/status/<id>` | GET | Get LIVE order status | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** 🔴 CRITICAL - Live order management UI completely missing

---

### 6. Upstox Integration Blueprint (`scripts/blueprints/upstox.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/upstox/profile` | GET | User profile (live API) | ❌ None | ❌ No | ⚠️ No UI |
| `/api/upstox/holdings` | GET | Long-term holdings | ❌ None | ❌ No | ⚠️ No UI |
| `/api/upstox/positions` | GET | Day/net positions | ❌ None | ❌ No | ⚠️ No UI |
| `/api/upstox/option-chain` | GET | Live option chain | ❌ None | ❌ No | ⚠️ No UI |
| `/api/upstox/market-quote` | GET | Real-time quote | ❌ None | ❌ No | ⚠️ No UI |
| `/api/upstox/funds` | GET | Account funds/margin | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** 🔴 CRITICAL - Live Upstox integration UI completely missing

---

### 7. Signals Blueprint (`scripts/blueprints/signals.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/signals` | GET | All trading signals | ❌ None | ✅ Yes | ⚠️ No UI |
| `/api/signals/<strategy>` | GET | Signals for strategy | ❌ None | ❌ No | ⚠️ No UI |
| `/api/instruments/nse-eq` | GET | NSE equity list | ❌ None | ✅ Yes | ⚠️ No UI |

**Gap:** Trading signals page needed

---

### 8. Strategies Blueprint (`scripts/blueprints/strategies.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/strategies/calendar-spread` | POST | Calendar spread | ❌ None | ❌ No | ⚠️ No UI |
| `/api/strategies/diagonal-spread` | POST | Diagonal spread | ❌ None | ❌ No | ⚠️ No UI |
| `/api/strategies/double-calendar` | POST | Double calendar | ❌ None | ❌ No | ⚠️ No UI |
| `/api/strategies/available` | GET | List strategies | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** Strategy builder UI completely missing

---

### 9. Backtest Blueprint (`scripts/blueprints/backtest.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/backtest/run` | POST | Run strategy backtest | ❌ None | ✅ Yes | ⚠️ No UI |
| `/api/backtest/strategies` | GET | Available strategies | ❌ None | ❌ No | ⚠️ No UI |
| `/api/backtest/results` | GET | Past results | ❌ None | ❌ No | ⚠️ No UI |
| `/api/backtest/multi-expiry` | POST | Multi-expiry backtest | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** Backtest UI needed (tests exist)

---

### 10. Analytics Blueprint (`scripts/blueprints/analytics.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/performance` | GET | 30-day performance | ❌ None | ❌ No | ⚠️ No UI |
| `/api/analytics/performance` | GET | Full analytics | ❌ None | ❌ No | ⚠️ No UI |
| `/api/analytics/equity-curve` | GET | Equity curve data | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** Analytics dashboard page needed

---

### 11. Expiry Management Blueprint (`scripts/blueprints/expiry.py`)

| Endpoint | Method | Purpose | Frontend | Tests | Status |
|----------|--------|---------|----------|-------|--------|
| `/api/expiry/roll` | POST | Roll to next expiry | ❌ None | ❌ No | ⚠️ No UI |
| `/api/expiry/next` | GET | Get next expiry | ❌ None | ❌ No | ⚠️ No UI |

**Gap:** Expiry management UI needed

---

## 🗂️ Frontend Pages Inventory

| Page | File | Endpoints Used | Status |
|------|------|---------------|--------|
| **Home Dashboard** | `home.py` | `/api/portfolio`, `/api/positions` | ✅ Complete |
| **Live Positions** | `positions.py` | `/api/positions` | ✅ Complete |
| **Downloads** | `downloads.py` | `/api/download/*`, `/api/market-quote` | ✅ Complete |
| **Option Chain** | `option_chain.py` | `/api/options/chain`, `/api/options/market-status` | ✅ Complete |
| **FNO Trading** | `fno.py` | ❌ None | ⚠️ Incomplete |
| **Historical Options** | `historical_options.py` | `/api/expired/*` (partial) | ⚠️ Incomplete |
| **Live Data** | `live_data.py` | Unknown | ⚠️ Unknown |
| **AI Chat** | `ai_chat.py` | Unknown | ⚠️ Unknown |
| **WIP** | `wip.py` | ❌ None | ⚠️ Placeholder |
| **Guide** | `guide.py` | ❌ None | ℹ️ Docs |
| **API Debugger** | `api_debugger.py` | ❌ None | 🔧 Tool |
| **Option Greeks** | `option_greeks.py` | Unknown | ⚠️ Unknown |

---

## 🔴 Critical Gaps

### Missing Frontend Pages (High Priority)

1. **Orders & Alerts Management** (6 endpoints orphaned)
   - View order history
   - Place/cancel/modify orders
   - Manage price alerts
   - Alert notifications

2. **Live Upstox Integration** (6 endpoints orphaned)
   - Live portfolio view
   - Holdings management
   - Real-time positions
   - Account funds/margin

3. **Strategy Builder** (4 endpoints orphaned)
   - Calendar spread creator
   - Diagonal spread creator
   - Strategy visualization
   - Multi-expiry support

4. **Backtest Interface** (4 endpoints orphaned)
   - Strategy selection
   - Backtest configuration
   - Results analysis
   - Performance charts

5. **Analytics Dashboard** (3 endpoints orphaned)
   - Performance metrics
   - Equity curve
   - Risk analytics
   - P&L breakdown

---

## 📝 Implementation Roadmap

### Phase 1: Quick Wins (1 week)
- [ ] Create Orders & Alerts page
- [ ] Add tests for orders endpoints
- [ ] Complete FNO page integration

### Phase 2: Core Features (2 weeks)
- [ ] Build Analytics dashboard
- [ ] Implement Strategy Builder
- [ ] Create Backtest interface
- [ ] Complete Historical Options page

### Phase 3: Live Integration (3 weeks)
- [ ] Build Upstox live integration page
- [ ] Add comprehensive E2E tests
- [ ] Implement error handling UI

### Phase 4: Polish (2 weeks)
- [ ] Add OpenAPI/Swagger docs
- [ ] Create API contract tests
- [ ] Implement caching strategies
- [ ] Add rate limiting UI feedback

---

## 🧪 Test Coverage Analysis

### Tests Present (7/52 = 13.5%)

- ✅ `test_integration.py::TestHealthEndpoints`
- ✅ `test_integration.py::TestAPIEndpoints::test_portfolio_endpoint`
- ✅ `test_integration.py::TestAPIEndpoints::test_positions_endpoint`
- ✅ `test_integration.py::TestAPIEndpoints::test_signals_endpoint`
- ✅ `test_integration.py::TestAPIEndpoints::test_instruments_endpoint`
- ✅ `test_options_chain.py::test_api_endpoint`
- ✅ `test_backtest_engine.py` (comprehensive)

### Tests Needed (45/52 = 86.5%)

**High Priority:**
- Orders (place, cancel, modify, status)
- Alerts (create, retrieve, delete)
- Live Upstox endpoints
- Strategy endpoints
- Analytics endpoints

**Medium Priority:**
- Data downloads
- Expired options
- Expiry management

---

## 🏗️ Architecture Observations

### ✅ Strengths
- Consistent Flask blueprint structure
- Proper error handling with trace IDs
- Database abstraction
- Clear separation of concerns
- RESTful API design

### ⚠️ Areas for Improvement
- 86.5% of endpoints lack tests
- Massive frontend-backend gap
- No OpenAPI/Swagger documentation
- Limited input validation visible
- No rate limiting implemented
- No caching strategy evident

---

## 💾 Database Dependencies

All endpoints use `market_data.db` with key tables:
- `paper_orders` - Paper trading orders
- `paper_positions` - Paper trading positions
- `alert_rules` - Price alert rules
- `trading_signals` - Generated signals
- `backtest_results` - Historical backtests
- `ohlc_data` - Market candle data
- `option_chain` - Options data

---

## 🔧 API Standards

### Request Format
```json
{
  "symbol": "INFY",
  "quantity": 100,
  "price": 1500.50
}
```

### Response Format
```json
{
  "status": "success",
  "data": {...},
  "trace_id": "abc-123"
}
```

### Error Format
```json
{
  "error": "Error message",
  "trace_id": "abc-123",
  "timestamp": "2026-02-03T09:00:00Z"
}
```

---

## 📞 API Testing

### Using API Debugger
Navigate to: http://localhost:5001/api-debugger

### Using cURL
```bash
# Health check
curl http://localhost:8000/api/health

# Get portfolio
curl http://localhost:8000/api/portfolio

# Place order
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"INFY","quantity":10,"price":1500}'
```

---

**Status:** Backend Complete, Frontend 13.5% Coverage  
**Next Priority:** Build missing UI pages for 45 orphaned endpoints

