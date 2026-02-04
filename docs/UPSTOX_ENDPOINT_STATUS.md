# Upstox API Endpoints - Implementation Status

**Last Updated:** February 3, 2026  
**Total Upstox Endpoints:** 60+  
**Backend Implemented:** 18 endpoints  
**Frontend Integrated:** 15 endpoints  

---

## Implementation Summary

### Coverage Statistics
| Category | Total | Backend | Frontend | Coverage % |
|----------|-------|---------|----------|------------|
| **Authentication** | 4 | 2 | 1 | 50% |
| **User Profile** | 2 | 2 | 2 | 100% |
| **Orders (Live)** | 12 | 4 | 4 | 33% |
| **Portfolio** | 4 | 3 | 3 | 75% |
| **Market Quotes** | 6 | 3 | 3 | 50% |
| **Historical Data** | 4 | 2 | 1 | 25% |
| **Option Chain** | 3 | 2 | 2 | 67% |
| **Market Info** | 4 | 2 | 0 | 0% |
| **Charges/Margin** | 2 | 0 | 0 | 0% |
| **GTT Orders** | 4 | 0 | 0 | 0% |
| **Expired Instruments** | 4 | 2 | 1 | 25% |
| **Trades/P&L** | 3 | 0 | 0 | 0% |
| **WebSocket** | 1 | 1 | 0 | 0% |
| **TOTAL** | **53** | **23** | **17** | **32%** |

---

## Detailed Endpoint Status

### 1. AUTHENTICATION ✅ 50% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/login/authorization/dialog` | ✅ | ✅ | OAuth flow implemented |
| `POST /v2/login/authorization/token` | ✅ | ⚠️ | Backend auto-handles token refresh |
| `DELETE /v2/logout` | ❌ | ❌ | **TODO:** Add logout functionality |
| `POST /v3/login/auth/token/request/` | ❌ | ❌ | **Not Needed:** v2 token sufficient |

**Implementation:** `scripts/auth_manager.py`, OAuth server on port 5050

---

### 2. USER PROFILE ✅ 100% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/user/profile` | ✅ | ✅ | Fully implemented |
| `GET /v2/user/get-funds-and-margin` | ✅ | ✅ | Shown in Upstox Live page |

**Backend:** `scripts/blueprints/upstox.py`  
**Frontend:** `dashboard_ui/pages/user_profile.py`, `upstox_live.py`

---

### 3. ORDERS (LIVE TRADING) ⚠️ 33% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `POST /v2/order/place` | ✅ | ✅ | Live order placement working |
| `PUT /v2/order/modify` | ✅ | ✅ | Order modification working |
| `DELETE /v2/order/cancel` | ✅ | ✅ | Order cancellation working |
| `GET /v2/order/details` | ✅ | ✅ | Order status check working |
| `GET /v2/order/history` | ❌ | ❌ | **TODO:** Show full order history |
| `GET /v2/order/retrieve-all` | ❌ | ❌ | **TODO:** Show all day's orders |
| `GET /v2/order/book` | ❌ | ❌ | **TODO:** Order book page |
| `POST /v2/order/multi/place` | ❌ | ❌ | **Advanced:** Multi-order placement |
| `DELETE /v2/order/multi/cancel` | ❌ | ❌ | **Advanced:** Batch cancel |
| `POST /v3/order/place` | ❌ | ❌ | **Advanced:** Auto-slicing |
| `PUT /v3/order/modify` | ❌ | ❌ | **Advanced:** v3 modify |
| `DELETE /v3/order/cancel` | ❌ | ❌ | **Advanced:** v3 cancel |

**Backend:** `scripts/blueprints/order.py`, `scripts/order_manager.py`  
**Frontend:** `dashboard_ui/pages/live_trading.py`

**Why Some Not Implemented:**
- Multi-order endpoints: Advanced feature, most users place single orders
- v3 endpoints: v2 is sufficient for current use case
- Order book: Can be added if users request detailed order management

---

### 4. PORTFOLIO ✅ 75% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/portfolio/short-term-positions` | ✅ | ✅ | Day positions shown |
| `GET /v2/portfolio/long-term-holdings` | ✅ | ✅ | Holdings page working |
| `PUT /v2/portfolio/convert-position` | ❌ | ❌ | **TODO:** MIS↔CNC conversion |
| `GET /v3/portfolio/mtf-positions` | ❌ | ❌ | **Not Needed:** MTF not commonly used |

**Backend:** `scripts/blueprints/upstox.py`, `portfolio.py`  
**Frontend:** `dashboard_ui/pages/upstox_live.py`, `positions.py`

**Why Some Not Implemented:**
- Position conversion: Advanced feature, can add if requested
- MTF positions: Margin Trading Facility not widely used

---

### 5. MARKET QUOTES ✅ 50% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/market-quote/quotes` | ✅ | ✅ | Full quotes working |
| `GET /v2/market-quote/ltp` | ✅ | ✅ | LTP in live data page |
| `GET /v2/market-quote/ohlc` | ✅ | ✅ | OHLC data shown |
| `GET /v3/market-quote/ltp` | ❌ | ❌ | **Duplicate:** v2 sufficient |
| `GET /v3/market-quote/ohlc` | ❌ | ❌ | **Duplicate:** v2 sufficient |
| `GET /v3/market-quote/option-greek` | ❌ | ❌ | **TODO:** Add Greeks calculator |

**Backend:** `scripts/market_quote_fetcher.py`, `market_quote_v3.py`  
**Frontend:** `dashboard_ui/pages/live_data.py`, `upstox_live.py`

**Why Some Not Implemented:**
- v3 endpoints: v2 versions work fine
- Option Greeks: Can be added to option chain page

---

### 6. HISTORICAL DATA ⚠️ 25% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/historical-candle/...` | ✅ | ⚠️ | Backend working, partial frontend |
| `GET /v3/historical-candle/...` | ❌ | ❌ | **Duplicate:** v2 works |
| `GET /v3/historical-candle/intraday/...` | ❌ | ❌ | **TODO:** Intraday charts |
| `GET /v2/expired-instruments/historical-candle/...` | ✅ | ⚠️ | Expired options page partial |

**Backend:** `scripts/candle_fetcher.py`, `candle_fetcher_v3.py`  
**Frontend:** `dashboard_ui/pages/downloads.py` (partial)

**Why Some Not Implemented:**
- v3 candles: v2 endpoint provides same data
- Intraday: Can add charting library for visualization
- Frontend integration: Need chart visualization library

---

### 7. OPTION CHAIN ✅ 67% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/option/contract` | ✅ | ✅ | Working in option chain page |
| `GET /v2/option/chain` | ✅ | ✅ | Full chain shown |
| `GET /v2/expired-instruments/option/contract` | ❌ | ❌ | **TODO:** Add to expired options page |

**Backend:** `scripts/option_chain_fetcher.py`, `options_chain_service.py`  
**Frontend:** `dashboard_ui/pages/option_chain.py`, `historical_options.py`

---

### 8. MARKET INFORMATION ❌ 0% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/market/holidays` | ❌ | ❌ | **Low Priority:** Static data |
| `GET /v2/market/holidays/{date}` | ❌ | ❌ | **Low Priority:** Can hardcode |
| `GET /v2/market/timings/{date}` | ❌ | ❌ | **Low Priority:** Known schedule |
| `GET /v2/market/status/{exchange}` | ⚠️ | ⚠️ | **Partial:** Market status check exists |

**Why Not Implemented:**
- Holidays: Static data, can be hardcoded or updated monthly
- Timings: Indian markets have fixed schedule (9:15 AM - 3:30 PM)
- Status: Basic check already implemented in option chain

**Could Add:** Market calendar page showing holidays and special timings

---

### 9. CHARGES & MARGIN ❌ 0% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/charges/brokerage` | ❌ | ❌ | **TODO:** Brokerage calculator |
| `GET /v2/charges/margin` | ❌ | ❌ | **TODO:** Margin calculator |

**Why Not Implemented:**
- Not critical for basic trading functionality
- Brokerage is standardized (₹20 per order)
- Margin info available in funds endpoint

**Could Add:** Calculator page for brokerage and margin estimates

---

### 10. GTT ORDERS ❌ 0% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `POST /v3/order/gtt/place` | ❌ | ❌ | **Advanced:** Good-Till-Triggered |
| `PUT /v3/order/gtt/modify` | ❌ | ❌ | **Advanced:** GTT modify |
| `DELETE /v3/order/gtt/cancel` | ❌ | ❌ | **Advanced:** GTT cancel |
| `GET /v3/order/gtt` | ❌ | ❌ | **Advanced:** GTT status |

**Why Not Implemented:**
- GTT is an advanced feature
- Most retail traders use regular limit/stop-loss orders
- Our alert system provides similar functionality

**Could Add:** GTT order management page for advanced users

---

### 11. TRADES & P&L ❌ 0% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/order/trades` | ❌ | ❌ | **TODO:** Trade history per order |
| `GET /v2/order/trades/get-trades-for-day` | ❌ | ❌ | **TODO:** Daily trades view |
| `GET /v2/charges/historical-trades` | ❌ | ❌ | **TODO:** Historical P&L |

**Why Not Implemented:**
- We have paper trading P&L tracking
- Live P&L can be calculated from positions
- Historical trades less critical for algorithmic trading

**Could Add:** Comprehensive trade journal/P&L tracking page

---

### 12. EXPIRED INSTRUMENTS ⚠️ 25% Complete

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/expired-instruments/expiries` | ✅ | ⚠️ | Backend works, partial frontend |
| `GET /v2/expired-instruments/option/contract` | ❌ | ❌ | **TODO:** Add to historical page |
| `GET /v2/expired-instruments/future/contract` | ❌ | ❌ | **TODO:** Expired futures |
| `GET /v2/expired-instruments/historical-candle/...` | ✅ | ⚠️ | Backend works |

**Backend:** `scripts/expired_options_fetcher.py`  
**Frontend:** `dashboard_ui/pages/historical_options.py` (partial)

**Why Partial:**
- Historical options page needs enhancement
- Futures trading less common for our use case
- Focus has been on live options trading

---

### 13. WEBSOCKET FEEDS ⚠️ Backend Only

| Endpoint | Backend | Frontend | Reason for Status |
|----------|---------|----------|-------------------|
| `GET /v2/feed/portfolio-stream-feed/authorize` | ✅ | ❌ | **Backend Ready:** No frontend integration |

**Backend:** `scripts/websocket_v3_streamer.py`, `websocket_server.py`  
**Frontend:** WebSocket client not integrated with NiceGUI

**Why Not Integrated:**
- WebSocket server implemented but no frontend Socket.IO client
- NiceGUI framework doesn't have built-in WebSocket support
- Would require JavaScript Socket.IO client integration
- Current polling approach works for most use cases

**Could Add:** Real-time updates using WebSocket for live_data and positions pages

---

## Priority Recommendations

### High Priority (Should Implement)
1. ✅ **Order History** - `GET /v2/order/history` - Users need to see past orders
2. ✅ **Brokerage Calculator** - `GET /v2/charges/brokerage` - Cost estimation
3. ✅ **Option Greeks** - `GET /v3/market-quote/option-greek` - Greeks in option chain
4. ✅ **Trade Journal** - `GET /v2/order/trades/get-trades-for-day` - P&L tracking

### Medium Priority (Nice to Have)
5. **Position Conversion** - `PUT /v2/portfolio/convert-position` - MIS ↔ CNC
6. **Multi-Order Placement** - `POST /v2/order/multi/place` - Batch orders
7. **Market Calendar** - `GET /v2/market/holidays` - Holiday tracking
8. **Intraday Charts** - `GET /v3/historical-candle/intraday/...` - Chart visualization

### Low Priority (Advanced Features)
9. **GTT Orders** - All GTT endpoints - Advanced order types
10. **WebSocket Integration** - Real-time feeds - Performance optimization
11. **v3 Endpoints** - Alternative to v2 - Same functionality
12. **MTF Positions** - `GET /v3/portfolio/mtf-positions` - Niche feature

---

## Why Endpoints Were Not Implemented

### 1. **Duplicate Functionality (v2 vs v3)**
- v3 endpoints often provide same data as v2
- v2 is stable and well-tested
- No significant benefit to implementing both

### 2. **Advanced Features Not Critical**
- GTT orders, MTF positions, multi-order placement
- These serve advanced traders
- Our focus is algorithmic trading, not manual trading

### 3. **Static/Low-Change Data**
- Market holidays, timings
- Can be hardcoded or updated periodically
- API call overhead not worth it

### 4. **Technical Limitations**
- WebSocket frontend integration requires JavaScript
- NiceGUI doesn't have native WebSocket support
- Would need custom Socket.IO client

### 5. **Alternative Solutions Exist**
- Our alert system replaces GTT functionality
- Paper trading provides P&L tracking
- Polling works well enough for quotes

---

## Implementation Files Reference

### Backend Files
- **Authentication:** `scripts/auth_manager.py`
- **Orders:** `scripts/blueprints/order.py`, `scripts/order_manager.py`
- **Portfolio:** `scripts/blueprints/portfolio.py`, `scripts/blueprints/upstox.py`
- **Market Data:** `scripts/market_quote_fetcher.py`, `scripts/market_quote_v3.py`
- **Historical:** `scripts/candle_fetcher.py`, `scripts/get_historical_data.py`
- **Options:** `scripts/option_chain_fetcher.py`, `scripts/options_chain_service.py`
- **WebSocket:** `scripts/websocket_v3_streamer.py`, `scripts/websocket_server.py`

### Frontend Files
- **Live Trading:** `dashboard_ui/pages/live_trading.py`
- **Portfolio:** `dashboard_ui/pages/upstox_live.py`, `positions.py`
- **Market Data:** `dashboard_ui/pages/live_data.py`
- **Options:** `dashboard_ui/pages/option_chain.py`, `historical_options.py`
- **Downloads:** `dashboard_ui/pages/downloads.py`

---

## Next Steps

To increase Upstox API coverage from 32% to 70%+:

1. **Implement Order History Page** (3 endpoints)
2. **Add Brokerage/Margin Calculator** (2 endpoints)
3. **Enhance Historical Options Page** (3 endpoints)
4. **Add Trade Journal** (2 endpoints)
5. **Implement Market Calendar** (3 endpoints)
6. **Add Greeks to Option Chain** (1 endpoint)

**Total:** 14 additional endpoints = ~58% coverage

---

**Document Version:** 1.0  
**Last Updated:** February 3, 2026  
**Maintainer:** Trading Platform Team
