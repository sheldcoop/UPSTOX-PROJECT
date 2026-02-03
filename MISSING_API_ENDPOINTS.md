# Missing Upstox API Endpoints - Quick Reference

**Date:** 2026-02-03  
**Branch:** `analysis-and-safety-branch`

---

## 🎯 Priority Classification

- 🔴 **HIGH** - Critical for trading operations (8 endpoints)
- 🟡 **MEDIUM** - Important for full feature parity (14 endpoints)
- 🟢 **LOW** - Nice to have, not critical (8 endpoints)

**Total Missing:** 30 endpoints

---

## 🔴 HIGH Priority (Implement First)

### Order Management v3
| Endpoint | Method | Current Status | Reason |
|----------|--------|----------------|--------|
| `/orders/v3/regular/create` | POST | ❌ Using v2 `/order/place` | v2 deprecated, v3 is current |
| `/orders/v3/regular/modify` | PUT | ❌ Using v2 `/order/modify` | v2 deprecated |
| `/orders/v3/regular/cancel/{order_id}` | DELETE | ❌ Using v2 `/order/{id}` | v2 deprecated |

**Impact:** Using outdated API version, risk of losing support

---

### Order & Trade History
| Endpoint | Method | Purpose | Why High Priority |
|----------|--------|---------|-------------------|
| `/orders` | GET | Get all orders | Can't display order history in frontend |
| `/orders/details` | GET | Get order details | No order tracking |
| `/trades` | GET | Get all trades | No trade log available |

**Impact:** Missing critical order tracking features

---

### Portfolio P&L
| Endpoint | Method | Purpose | Why High Priority |
|----------|--------|---------|-------------------|
| `/portfolio/trades/p-and-l` | GET | P&L reports | Using local calculations, may be inaccurate |

**Impact:** P&L calculations might not match Upstox backend

---

### WebSocket Authorization
| Endpoint | Method | Purpose | Why High Priority |
|----------|--------|---------|-------------------|
| `/feed/market-data-feed/authorize/v3` | GET | v3 market data feed auth | Required for v3 websocket (current using deprecated v1) |

**Impact:** Using legacy websocket connection

---

## 🟡 MEDIUM Priority

### Portfolio Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/portfolio/positions/convert` | GET | MTF positions lookup |
| `/portfolio/positions/convert` | POST | Convert position (MIS↔CNC) |
| `/portfolio/trades/charges` | GET | Charge breakdown |
| `/portfolio/holdings` | GET | Long-term holdings (proper endpoint) |

**Impact:** Missing advanced portfolio features

---

### Order History & Details
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/orders/history` | GET | Order execution history |
| `/trades/orders/{order_id}` | GET | Trades by order ID |
| `/trades/historical` | GET | Historical trades with filters |

**Impact:** Limited order tracking capabilities

---

### Market Information
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/market-status` | GET | Market open/closed status |

**Impact:** Can't determine if market is open programmatically

---

### User Account
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/user/brokerage` | GET | Brokerage charges (API-based) |
| `/user/margin` | GET | Margin requirements (API-based) |

**Impact:** Using local calculations instead of API

---

### Advanced Orders
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/orders/v3/bracket/create` | POST | Place bracket order |
| `/orders/exit/all` | POST | Close all positions |

**Impact:** Missing advanced order types

---

### WebSocket Feeds
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/feed/market-data-feed/authorize` | GET | v2 feed auth (fallback) |
| `/feed/portfolio-stream-feed/authorize` | GET | Portfolio updates feed |

**Impact:** Missing real-time portfolio updates

---

### Market Data v3 Upgrades
| Endpoint | Method | Current Alternative |
|----------|--------|---------------------|
| `/market-quote/candles/v3/{instrument_key}` | GET | Using v2 `/historical-candle` |
| `/market-quote/candles/v3/intraday/{instrument_key}` | GET | Using v2 `/historical-candle` |
| `/market-quote/quotes/v3/` | GET | Using v2 `/market-quote/quotes` |

**Impact:** Missing v3 performance improvements

---

## 🟢 LOW Priority

### Market Information
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/market-holidays` | GET | Holiday calendar |
| `/market-timings` | GET | Session timings |

**Impact:** Minor, static data

---

### Authentication
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/logout` | POST | Logout & invalidate token |

**Impact:** Token expires naturally, manual logout not critical

---

### Option Chain Enhancements
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/option/expiry` | GET | Available expiry dates |
| `/option/contract` | GET | Expired contracts |
| `/option/contract/pc` | GET | Put-Call ratio |

**Impact:** Nice to have, not critical (can calculate locally)

---

### Instruments
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/market-quote/instruments` | GET | All instruments list |
| `/market-quote/instruments/expired` | GET | Expired instruments |

**Impact:** Already using local instrument database

---

### Market Data v3
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/market-quote/ltp/v3/` | GET | LTP (v3 version) |

**Impact:** v2 LTP works fine

---

## 📋 Implementation Checklist

### Sprint 1: Order Management v3 (Week 1)
- [ ] Implement `POST /orders/v3/regular/create`
- [ ] Implement `PUT /orders/v3/regular/modify`
- [ ] Implement `DELETE /orders/v3/regular/cancel/{order_id}`
- [ ] Implement `GET /orders` (order book)
- [ ] Implement `GET /trades` (trade history)
- [ ] Update `scripts/order_manager.py` to use v3
- [ ] Add v2 fallback for backward compatibility
- [ ] Update frontend order pages

**Deliverables:**
- Updated order manager
- Frontend order history page
- Migration guide

---

### Sprint 2: Portfolio & P&L (Week 2)
- [ ] Implement `GET /portfolio/trades/p-and-l`
- [ ] Implement `POST /portfolio/positions/convert`
- [ ] Implement `GET /portfolio/trades/charges`
- [ ] Add frontend P&L report page
- [ ] Add position conversion dialog

**Deliverables:**
- P&L report API integration
- Position converter
- Frontend P&L dashboard

---

### Sprint 3: WebSocket v3 (Week 3)
- [ ] Implement `GET /feed/market-data-feed/authorize/v3`
- [ ] Migrate websocket to v3 endpoint
- [ ] Add protobuf message parsing
- [ ] Test multi-symbol subscriptions

**Deliverables:**
- v3 websocket implementation
- Performance benchmark report
- Migration guide

---

### Sprint 4: Market Information (Week 4)
- [ ] Implement `GET /market-status`
- [ ] Implement `GET /market-holidays`
- [ ] Implement `GET /market-timings`
- [ ] Add market status widget to frontend

**Deliverables:**
- Market info service
- Frontend market status indicator

---

### Sprint 5: User Account APIs (Week 5)
- [ ] Implement `GET /user/brokerage`
- [ ] Implement `GET /user/margin`
- [ ] Replace local calculators with API calls

**Deliverables:**
- API-based calculators
- Validation against local calculations

---

### Sprint 6: Portfolio Feed (Week 6)
- [ ] Implement `GET /feed/portfolio-stream-feed/authorize`
- [ ] Implement portfolio websocket feed
- [ ] Add real-time P&L calculator
- [ ] Add order status notifications

**Deliverables:**
- Portfolio feed websocket
- Real-time P&L updates
- Order notification system

---

## 🎯 Quick Decision Matrix

### Should I implement this endpoint?

**YES if:**
- Current implementation uses v2 (deprecated) → Migrate to v3
- No alternative exists → Must implement
- Accuracy is critical (P&L, charges) → Use API instead of local

**MAYBE if:**
- Nice to have feature → Prioritize based on user needs
- Performance improvement (v3 upgrades) → Test if needed
- Better UX → Balance effort vs benefit

**NO if:**
- Duplicate of existing working endpoint
- Static data already available locally
- Low user value

---

## 📊 Effort Estimation

| Priority | Endpoints | Estimated Days | Complexity |
|----------|-----------|----------------|------------|
| 🔴 HIGH | 8 | 5-7 days | Medium |
| 🟡 MEDIUM | 14 | 7-10 days | Medium |
| 🟢 LOW | 8 | 3-5 days | Low |
| **TOTAL** | **30** | **15-22 days** | **Mixed** |

**Note:** Assumes 1 developer, includes testing & documentation

---

## 🚀 Recommended Implementation Order

1. **Order Management v3** (Days 1-3) - Critical, blocks other features
2. **Order/Trade History** (Days 4-5) - High user value
3. **Portfolio P&L** (Day 6) - Accuracy critical
4. **WebSocket v3 Auth** (Days 7-8) - Foundation for real-time features
5. **Position Conversion** (Day 9) - High user value
6. **Market Status** (Day 10) - Quick win
7. **WebSocket Portfolio Feed** (Days 11-13) - Real-time updates
8. **Market Data v3** (Days 14-16) - Performance optimization
9. **Market Info** (Days 17-18) - Nice to have
10. **Option Chain Extras** (Days 19-20) - Polish

**Minimum Viable:** Items 1-6 (10 days)  
**Full Feature Parity:** All items (20 days)

---

## ✅ Success Criteria

**After implementation, we should have:**

### For Users
- ✅ Can view complete order history
- ✅ Can see real-time P&L updates
- ✅ Can convert positions (MIS↔CNC)
- ✅ Know if market is open/closed
- ✅ Get instant order notifications
- ✅ See accurate brokerage charges

### For System
- ✅ Using latest v3 API endpoints
- ✅ No deprecated API usage
- ✅ Real-time data via v3 websocket
- ✅ API-based calculations (not local)
- ✅ 100% Upstox feature parity

### For Developers
- ✅ All endpoints documented
- ✅ Unit tests for all endpoints
- ✅ Error handling & retry logic
- ✅ Migration guides for v2→v3

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-03  
**Status:** Ready for implementation planning
