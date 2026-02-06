# Upstox Service Architecture

## Purpose
This document defines a production-grade service boundary model for the Upstox integration and provides a migration checklist to move existing modules into `*Service` classes without breaking the current GUI.

## Service Overview (11 Core + 1 Support)

### 1) IdentityService
**Scope:** Session & authentication, user identity.

**Endpoints**
- GET /v2/login/authorization/dialog
- POST /v2/login/authorization/token
- POST /v2/logout
- GET /v2/user/profile
- GET /v2/user/balance

**Owns**
- Access token lifecycle
- User profile and funds

---

### 2) MarketDataService
**Scope:** Real-time quotes, LTP, OHLC, depth, and option Greeks snapshots.

**Endpoints**
- GET /v2/market-quote/quotes
- GET /v2/market-quote/ltp
- GET /v2/market-quote/ohlc
- GET /v2/market-quote/depth
- GET /v3/market-quote/option-greek

**Owns**
- Price snapshots (non-streaming)
- Short TTL caching and rate-limiting

---

### 3) HistoricalDataService
**Scope:** Time-series candle data for charting/backtesting.

**Endpoints**
- GET /v2/historical-candle/{instrument_key}/{interval}/{to_date}
- GET /v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}

**Owns**
- Historical OHLC retrieval
- Batching, pagination and range validation

---

### 4) MarketInformationService
**Scope:** Market status, holidays, and exchange timings.

**Endpoints**
- GET /v2/market/status/{exchange}
- GET /v2/market/holidays
- GET /v2/market/holidays/{date}
- GET /v2/market/timings/{date}

**Owns**
- Market session validation
- Long TTL cache (holidays/timings)

---

### 5) InstrumentService
**Scope:** Instrument master data and option chain discovery.

**Endpoints**
- GET /v2/market/instruments
- GET /v2/market/instruments/{date}
- GET /v2/option/chain

**Owns**
- Daily instrument master fetch + cache
- Option chain lookup

---

### 6) OrderExecutionService
**Scope:** Order lifecycle, order history, trade book.

**Endpoints**
- POST /v2/order/place
- POST /v3/order/place
- POST /v2/order/multi/place
- PUT /v2/order/modify
- PUT /v3/order/modify
- DELETE /v2/order/cancel
- DELETE /v3/order/cancel
- GET /v2/order/retrieve-all
- GET /v2/order/details
- GET /v2/order/history
- GET /v2/order/trades/get-trades-for-day
- GET /v2/order/trades/get-trades-by-order

**Owns**
- Place/modify/cancel
- Order book and trade book

---

### 7) GTTService
**Scope:** Good-Till-Triggered order lifecycle.

**Endpoints**
- POST /v2/gtt/create
- PUT /v2/gtt/modify
- DELETE /v2/gtt/cancel
- GET /v2/gtt/retrieve-all

**Owns**
- OCO and SINGLE trigger management

---

### 8) PortfolioService
**Scope:** Current holdings and positions.

**Endpoints**
- GET /v2/portfolio/short-term-positions
- GET /v2/portfolio/long-term-positions
- PUT /v2/portfolio/convert-position
- GET /v2/portfolio/holdings

**Owns**
- Positions, holdings, position conversions

---

### 9) TradePnLService
**Scope:** Historical P&L, charges breakdown for realized trades.

**Endpoints**
- GET /v2/trade/profit-loss/data
- GET /v2/trade/profit-loss/metadata
- GET /v2/trade/profit-loss/charges

**Owns**
- Realized P&L data and accounting breakdowns

---

### 10) RiskService
**Scope:** Pre-trade margin and charges calculation.

**Endpoints**
- POST /v2/charges/brokerage
- POST /v2/charges/margin

**Owns**
- Pre-trade validation, cost preview

---

### 11) FeedService
**Scope:** WebSocket streaming (market, order, portfolio feeds).

**Endpoints**
- wss://api.upstox.com/v2/feed/market-data-feed
- wss://api.upstox.com/v2/feed/order-update
- wss://api.upstox.com/v2/feed/portfolio-stream-feed

**Owns**
- Subscription management, reconnect logic
- Protobuf decoding

---

### 12) WebhookService (Support)
**Scope:** HTTP push notifications for order updates.

**Endpoints**
- POST {configured webhook URL}

**Owns**
- Signature verification, idempotency
- Backstop for websocket drops

---

## Service Dependencies (Allowed Direction)
- IdentityService can be used by any service for auth tokens.
- MarketInformationService can be used by OrderExecutionService and RiskService.
- InstrumentService can be used by MarketDataService and OrderExecutionService.
- RiskService can be used by OrderExecutionService (pre-trade validation).
- PortfolioService must not depend on OrderExecutionService.
- TradePnLService must not depend on PortfolioService.
- FeedService and WebhookService are event sources and should not import business services directly.

## Call Flows

### Order Placement (REST)
1. IdentityService.get_profile()
2. IdentityService.get_balance()
3. InstrumentService.lookup_instrument()
4. MarketInformationService.get_status()
5. RiskService.calculate_margin()
6. RiskService.calculate_brokerage()
7. OrderExecutionService.place_order()
8. OrderExecutionService.get_order_book()
9. PortfolioService.get_positions()

### Monitoring (Streaming)
- FeedService.connect_market_data() → live pricing
- FeedService.connect_order_updates() → order status
- FeedService.connect_portfolio() → P&L changes

### Monitoring (Webhook)
- WebhookService.receive_update() → order status updates

---

## Migration Checklist (Move Modules into `*Service` Classes)

### Phase 0 — Baseline Safety
- [ ] Freeze current API behavior with a small regression suite around GUI-critical flows.
- [ ] Identify all direct Upstox API calls and wrap them behind a single `ApiClient` interface.
- [ ] Confirm `AuthManager.get_valid_token()` is the only token source.

### Phase 1 — Create Service Stubs
- [ ] Create new `services/` package with empty classes for all 11 services.
- [ ] Define a shared `BaseService` for logging, retries, rate limiting, and caching hooks.
- [ ] Add a single `ServiceRegistry` or DI container to supply instances.

### Phase 2 — Migrate Endpoint Calls (No Call-Site Changes Yet)
- [ ] Move raw REST calls into their appropriate `*Service` class.
- [ ] Keep existing functions as thin wrappers that delegate to the new service method.
- [ ] Ensure response shapes remain identical to avoid UI breaks.

### Phase 3 — Update Call Sites
- [ ] Replace direct module calls with service instance calls in UI and backend modules.
- [ ] Keep compatibility wrappers for any external scripts.
- [ ] Add unit tests for each service method with mocked API responses.

### Phase 4 — Enforce Boundaries
- [ ] Add linting rules or code review checks that prevent cross‑service imports.
- [ ] Remove deprecated direct API functions after all call sites are migrated.
- [ ] Ensure all services go through a shared error handler and retry logic.

### Phase 5 — Observability & Ops
- [ ] Add structured logging for requests, latency, and Upstox errors.
- [ ] Add per‑service rate limiting and caching policies.
- [ ] Add metrics counters for order lifecycle, fills, and P&L fetches.

---

## File‑Level Mapping Template (Use During Migration)
Use this template to map each existing module to a target service class:

- **Source module:** <path/to/module.py>
- **Functions to move:** <function list>
- **Target service:** <ServiceName>
- **New method names:** <method list>
- **Compatibility wrapper kept?:** Yes/No
- **Call sites updated?:** Yes/No
- **Tests added?:** Yes/No

---

## Implementation Order
1. IdentityService
2. InstrumentService
3. MarketInformationService
4. MarketDataService
5. HistoricalDataService
6. OrderExecutionService
7. RiskService
8. PortfolioService
9. TradePnLService
10. GTTService
11. FeedService
12. WebhookService

## Rate Limits & Caching
- Order endpoints: 10 orders/sec per user
- Standard REST: 250 req/sec per user
- Instrument master: cache 24h
- Market status: cache 60s
- Quotes: cache 1s
- Positions: cache 5s

---

## Notes
- Use V3 for order place/modify/cancel and option-greek.
- Never log full access tokens.
- Webhook requests must verify signatures and be idempotent.
