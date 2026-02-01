# Upstox API v2 Endpoints Reference

Complete reference of all Upstox API v2 endpoints with descriptions, parameters, and usage examples.

**Base URL:** `https://api.upstox.com/v2/`

**Authentication:** Bearer token in `Authorization: Bearer <access_token>` header

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Instrument Endpoints](#instrument-endpoints)
3. [Historical Data Endpoints](#historical-data-endpoints)
4. [Market Data Endpoints](#market-data-endpoints)
5. [Option Chain Endpoints](#option-chain-endpoints)
6. [Order Management Endpoints](#order-management-endpoints)
7. [Portfolio Endpoints](#portfolio-endpoints)
8. [User & Account Endpoints](#user--account-endpoints)
9. [WebSocket Endpoints](#websocket-endpoints)
10. [Market Information Endpoints](#market-information-endpoints)

---

## Authentication Endpoints

### Login
**Endpoint:** `POST /auth/login`

**Description:** Initiate OAuth login flow

**Parameters:**
- `client_id` (query): Your API client ID
- `redirect_uri` (query): OAuth callback URL
- `response_type` (query): Should be `code`

**Example:**
```
POST https://api.upstox.com/v2/auth/login?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&response_type=code
```

**Response:** Redirects to Upstox login page

---

### Authorize
**Endpoint:** `GET /auth/authorize`

**Description:** Get authorization code after user login

**Parameters:**
- `client_id` (query): Your API client ID
- `redirect_uri` (query): OAuth callback URL
- `response_type` (query): Should be `code`

**Example:**
```
GET https://api.upstox.com/v2/auth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&response_type=code
```

**Response:** Redirects with authorization code in `code` parameter

---

### Get Access Token
**Endpoint:** `POST /auth/token`

**Description:** Exchange authorization code for access token

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
- `grant_type` (body): Should be `authorization_code`
- `code` (body): Authorization code from authorize endpoint
- `client_id` (body): Your API client ID
- `client_secret` (body): Your API client secret
- `redirect_uri` (body): Your OAuth callback URL

**Example:**
```bash
curl -X POST https://api.upstox.com/v2/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=AUTH_CODE&client_id=CLIENT_ID&client_secret=CLIENT_SECRET&redirect_uri=http://localhost:8080/callback"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "refresh_token": "REFRESH_TOKEN"
}
```

---

### Logout
**Endpoint:** `POST /auth/logout`

**Description:** Logout and invalidate access token

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X POST https://api.upstox.com/v2/auth/logout \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success"
}
```

---

## Instrument Endpoints

### Get Instruments
**Endpoint:** `GET /market-quote/instruments`

**Description:** Get list of all available instruments (stocks, derivatives, options)

**Parameters:**
- None (returns all instruments)

**Query Parameters:**
- `exchange` (optional): Filter by exchange (NSE, BSE, MCX, etc.)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/instruments" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "exchange_token": "1",
      "tradingsymbol": "INFY",
      "name": "Infosys Limited",
      "expiry": null,
      "strike": null,
      "lotsize": 1,
      "instrumenttype": "EQUITY",
      "segment": "NSE",
      "exchange": "NSE"
    },
    ...
  ]
}
```

---

### Get Expired Instruments
**Endpoint:** `GET /market-quote/instruments/expired`

**Description:** Get list of expired instruments (expired options/futures)

**Parameters:**
- None

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/instruments/expired" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:** Same format as instruments list, filtered for expired contracts

---

### Get Option Expiries
**Endpoint:** `GET /option/expiry`

**Description:** Get available expiry dates for options on a given underlying

**Query Parameters:**
- `underlying_symbol` (required): Symbol of underlying (e.g., NIFTY, BANKNIFTY, INFY)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/option/expiry?underlying_symbol=NIFTY" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    "2025-01-30",
    "2025-02-06",
    "2025-02-13",
    "2025-02-20",
    ...
  ]
}
```

---

### Get Expired Option Contracts
**Endpoint:** `GET /option/contract`

**Description:** Get historical/expired option contract data for specific expiry

**Query Parameters:**
- `underlying_symbol` (required): Symbol of underlying
- `expiry_date` (required): Option expiry date (YYYY-MM-DD)
- `option_type` (optional): CE or PE filter
- `strike_price` (optional): Filter by strike price

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/option/contract?underlying_symbol=NIFTY&expiry_date=2026-01-22" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "tradingsymbol": "NIFTY22JAN23400CE",
      "exchange_token": "12345",
      "strike_price": 23400,
      "option_type": "CE",
      "expiry_date": "2026-01-22",
      "exchange": "NFO"
    },
    ...
  ]
}
```

---

### Get Expired Future Contracts
**Endpoint:** `GET /future/contract`

**Description:** Get historical/expired future contract data for specific expiry

**Query Parameters:**
- `underlying_symbol` (required): Symbol of underlying
- `expiry_date` (required): Contract expiry date (YYYY-MM-DD)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/future/contract?underlying_symbol=NIFTY&expiry_date=2026-01-22" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:** Similar to option contract response, with futures-specific data

---

## Historical Data Endpoints

### Get Historical Candle Data (v3)
**Endpoint:** `GET /market-quote/candles/v3/{instrument_key}`

**Description:** Get historical OHLCV candle data with multiple timeframes

**Path Parameters:**
- `instrument_key` (required): Instrument key (format: exchange#tradingsymbol)

**Query Parameters:**
- `interval` (required): Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
- `to_date` (required): End date (YYYY-MM-DD HH:MM:SS format or epoch)
- `from_date` (optional): Start date (YYYY-MM-DD HH:MM:SS format or epoch)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/candles/v3/NSE_EQ%7CINFY?interval=1d&to_date=2025-01-31&from_date=2024-01-01" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "candles": [
      [
        1704067200,
        3425.50,
        3452.00,
        3420.00,
        3445.50,
        2341000,
        0,
        0
      ],
      ...
    ]
  }
}
```

**Array Format:** `[timestamp, open, high, low, close, volume, open_interest, oi]`

---

### Get Intra-day Candle Data (v3)
**Endpoint:** `GET /market-quote/candles/v3/intraday/{instrument_key}`

**Description:** Get intra-day candle data (same day only)

**Path Parameters:**
- `instrument_key` (required): Instrument key (format: exchange#tradingsymbol)

**Query Parameters:**
- `interval` (required): Candle interval (1m, 5m, 15m, 30m, 1h)
- `to_date` (required): End timestamp (epoch)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/candles/v3/intraday/NSE_EQ%7CINFY?interval=5m&to_date=1704067200" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:** Same format as historical candles

---

### Get Historical Candle Data
**Endpoint:** `GET /market-quote/candles/{instrument_key}`

**Description:** Get historical candles (v2, deprecated - use v3)

**Path Parameters:**
- `instrument_key` (required): Instrument key

**Query Parameters:**
- `interval` (required): Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
- `to_date` (required): End date (epoch)
- `from_date` (optional): Start date (epoch)

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/candles/NSE_EQ%7CINFY?interval=1d&to_date=1704067200&from_date=1672531200" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

---

### Get Intra-day Candle Data
**Endpoint:** `GET /market-quote/candles/intraday/{instrument_key}`

**Description:** Get intra-day candles (v2, deprecated - use v3)

**Path Parameters:**
- `instrument_key` (required): Instrument key

**Query Parameters:**
- `interval` (required): Candle interval (1m, 5m, 15m, 30m, 1h)
- `to_date` (required): End timestamp (epoch)

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/candles/intraday/NSE_EQ%7CINFY?interval=5m&to_date=1704067200" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

---

### Get Expired Historical Candle Data
**Endpoint:** `GET /market-quote/candles/expired/{instrument_key}`

**Description:** Get candles for expired derivatives (options/futures after expiry)

**Path Parameters:**
- `instrument_key` (required): Expired instrument key

**Query Parameters:**
- `interval` (required): Candle interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
- `to_date` (required): End date (epoch or YYYY-MM-DD)
- `from_date` (optional): Start date (epoch or YYYY-MM-DD)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/candles/expired/NFO_EQ%7CNIFTY22JAN23000CE?interval=1h&to_date=2025-01-22&from_date=2025-01-15" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:** Historical OHLCV data for the expired contract

---

## Market Data Endpoints

### Get Full Market Quote
**Endpoint:** `GET /market-quote/quotes/`

**Description:** Get comprehensive market data including LTP, bid-ask, volume, OI, depth

**Query Parameters:**
- `mode` (required): Mode of data (LTP, QUOTE, FULL)
- `instrument_keys` (required): Comma-separated list of instrument keys

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/quotes/?mode=FULL&instrument_keys=NSE_EQ%7CINFY,NSE_EQ%7CTCS" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "NSE_EQ|INFY": {
      "instrument_key": "NSE_EQ|INFY",
      "ltp": 3445.50,
      "ltq": 1000,
      "ltt": 1704067200,
      "bid_price": 3445.00,
      "bid_qty": 5000,
      "ask_price": 3446.00,
      "ask_qty": 7000,
      "oi": 0,
      "volume": 5000000,
      "iv": null,
      "open": 3425.50,
      "high": 3452.00,
      "low": 3420.00,
      "close": 3440.00,
      "prev_close": 3440.00
    }
  }
}
```

---

### Get Market Quote (OHLC v3)
**Endpoint:** `GET /market-quote/quotes/v3/`

**Description:** Get OHLC market data (v3)

**Query Parameters:**
- `mode` (required): OHLC or FULL
- `instrument_keys` (required): Comma-separated instrument keys

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/quotes/v3/?mode=OHLC&instrument_keys=NSE_EQ%7CINFY" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

---

### Get LTP (v3)
**Endpoint:** `GET /market-quote/ltp/v3/`

**Description:** Get Last Traded Price only (minimal data)

**Query Parameters:**
- `mode` (required): Should be LTP
- `instrument_keys` (required): Comma-separated instrument keys

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/ltp/v3/?mode=LTP&instrument_keys=NSE_EQ%7CINFY,NSE_EQ%7CTCS" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "NSE_EQ|INFY": {
      "instrument_key": "NSE_EQ|INFY",
      "ltp": 3445.50,
      "ltq": 1000,
      "ltt": 1704067200,
      "bid_price": 3445.00,
      "bid_qty": 5000,
      "ask_price": 3446.00,
      "ask_qty": 7000,
      "oi": 0,
      "volume": 5000000,
      "iv": null,
      "depth": {
        "buy": [...],
        "sell": [...]
      }
    }
  }
}
```

---

### Get Option Greeks
**Endpoint:** `GET /market-quote/quotes/`

**Description:** Get option Greeks (delta, gamma, theta, vega, IV)

**Query Parameters:**
- `mode` (required): FULL
- `instrument_keys` (required): Option contract keys

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/market-quote/quotes/?mode=FULL&instrument_keys=NFO_EQ%7CNIFTY23JAN23000CE" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response Includes:**
```json
{
  "greeks": {
    "iv": 0.2145,
    "delta": 0.6234,
    "gamma": 0.0012,
    "theta": -0.0123,
    "vega": 0.0456
  }
}
```

---

## Option Chain Endpoints

### Get Option Contracts
**Endpoint:** `GET /option/contract`

**Description:** Get option chain data for given underlying and expiry

**Query Parameters:**
- `underlying_symbol` (required): Symbol (NIFTY, BANKNIFTY, INFY, etc.)
- `expiry_date` (required): Expiry date (YYYY-MM-DD)
- `option_type` (optional): CE or PE
- `strike_price` (optional): Specific strike price

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/option/contract?underlying_symbol=NIFTY&expiry_date=2025-01-30" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "tradingsymbol": "NIFTY30JAN23000CE",
      "exchange_token": "12345",
      "strike_price": 23000,
      "option_type": "CE",
      "expiry_date": "2025-01-30",
      "exchange": "NFO",
      "name": "NIFTY Options"
    },
    ...
  ]
}
```

---

### Get PC (Put-Call) Option Chain
**Endpoint:** `GET /option/contract/pc`

**Description:** Get Put-Call ratio for option chain

**Query Parameters:**
- `underlying_symbol` (required): Symbol
- `expiry_date` (required): Expiry date (YYYY-MM-DD)
- `strike_price` (optional): Specific strike

**Headers:**
```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "https://api.upstox.com/v2/option/contract/pc?underlying_symbol=NIFTY&expiry_date=2025-01-30&strike_price=23000" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "strike": 23000,
    "ce_oi": 5000000,
    "pe_oi": 7000000,
    "pcr": 1.4
  }
}
```

---

## Order Management Endpoints

### Place Order (v3)
**Endpoint:** `POST /orders/v3/regular/create`

**Description:** Place a regular stock or derivative order

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "quantity": 1,
  "price": 3445.50,
  "product": "MIS",
  "order_type": "REGULAR",
  "validity": "DAY",
  "validity_days": 1,
  "order_side": "BUY",
  "instrument_token": "NSE_EQ|INFY",
  "user_order_id": "order123"
}
```

**Parameters:**
- `instrument_token` (required): Instrument key
- `quantity` (required): Order quantity
- `price` (required): Limit price (0 for market order)
- `order_side` (required): BUY or SELL
- `order_type` (required): REGULAR, BRACKET, COVER
- `product` (required): MIS, CNC, NRML
- `validity` (required): DAY, IOC, GTT
- `user_order_id` (optional): Custom order ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "order_id": "250131000000001",
    "order_timestamp": 1704067200
  }
}
```

---

### Modify Order
**Endpoint:** `PUT /orders/v3/regular/modify`

**Description:** Modify a pending order

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "order_id": "250131000000001",
  "price": 3450.00,
  "quantity": 2,
  "validity": "DAY"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "order_id": "250131000000001"
  }
}
```

---

### Cancel Order
**Endpoint:** `DELETE /orders/v3/regular/cancel/{order_id}`

**Description:** Cancel a pending order

**Path Parameters:**
- `order_id` (required): Order ID to cancel

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "order_id": "250131000000001"
  }
}
```

---

### Get Order Details
**Endpoint:** `GET /orders/details`

**Description:** Get details of a specific order

**Query Parameters:**
- `order_id` (required): Order ID

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "order_id": "250131000000001",
    "order_timestamp": 1704067200,
    "status": "COMPLETE",
    "quantity": 1,
    "price": 3445.50,
    "filled_quantity": 1,
    "pending_quantity": 0
  }
}
```

---

### Get Order Book
**Endpoint:** `GET /orders`

**Description:** Get all orders for the account

**Query Parameters:**
- `page` (optional): Page number
- `pagesize` (optional): Orders per page

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "order_id": "250131000000001",
      "status": "COMPLETE",
      "quantity": 1,
      "price": 3445.50
    }
  ]
}
```

---

### Get Order History
**Endpoint:** `GET /orders/history`

**Description:** Get historical order execution details

**Query Parameters:**
- `order_id` (required): Order ID

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Get Trade History
**Endpoint:** `GET /trades`

**Description:** Get all trades

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Get Trades by Order
**Endpoint:** `GET /trades/orders/{order_id}`

**Description:** Get trades for specific order

**Path Parameters:**
- `order_id` (required): Order ID

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Get Historical Trades
**Endpoint:** `GET /trades/historical`

**Description:** Get historical trades with filters

**Query Parameters:**
- `from_date` (optional): Start date
- `to_date` (optional): End date
- `page` (optional): Page number

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Exit All Positions
**Endpoint:** `POST /orders/exit/all`

**Description:** Close all open positions

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Portfolio Endpoints

### Get Positions
**Endpoint:** `GET /portfolio/positions`

**Description:** Get all open positions

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "exchange_token": "12345",
      "tradingsymbol": "INFY",
      "quantity": 10,
      "avg_price": 3425.50,
      "ltp": 3445.50,
      "pl": 200.00,
      "pl_percentage": 0.58
    }
  ]
}
```

---

### Get MTF Positions
**Endpoint:** `GET /portfolio/positions/convert`

**Description:** Get positions available for conversion between products

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Convert Position
**Endpoint:** `POST /portfolio/positions/convert`

**Description:** Convert position from one product to another (MIS to CNC, etc.)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "tradingsymbol": "INFY",
  "exchange": "NSE",
  "order_side": "BUY",
  "quantity": 10,
  "old_product": "MIS",
  "new_product": "CNC"
}
```

---

### Get Holdings
**Endpoint:** `GET /portfolio/holdings`

**Description:** Get long-term holdings

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** Similar to positions with additional holding-specific fields

---

### Get Profit & Loss Report
**Endpoint:** `GET /portfolio/trades/p-and-l`

**Description:** Get P&L report with trade details

**Query Parameters:**
- `from_date` (optional): Start date
- `to_date` (optional): End date
- `page` (optional): Page number

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Get Trade Charges
**Endpoint:** `GET /portfolio/trades/charges`

**Description:** Get charges breakdown for trades

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## User & Account Endpoints

### Get Profile
**Endpoint:** `GET /user/profile`

**Description:** Get user account information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "USER123",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210",
    "broker": "UPSTOX",
    "exchanges": ["NSE", "BSE", "NFO", "MCX"],
    "products": ["MIS", "CNC", "NRML"],
    "roles": ["individual"]
  }
}
```

---

### Get User Fund and Margin
**Endpoint:** `GET /user/fund-and-margin`

**Description:** Get account balance and margin information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "available_balance": 500000.00,
    "used_margin": 100000.00,
    "unrealised_pnl": 5000.00,
    "equity": 505000.00,
    "margin_utilised": 0.20
  }
}
```

---

### Get Brokerage
**Endpoint:** `GET /user/brokerage`

**Description:** Get brokerage charges for given trade parameters

**Query Parameters:**
- `instrument_token` (required): Instrument key
- `quantity` (required): Order quantity
- `price` (required): Order price
- `product` (required): MIS, CNC, NRML
- `order_side` (required): BUY or SELL

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "brokerage": 15.00,
    "exchange_charges": 5.00,
    "stt": 0,
    "total_charges": 20.00
  }
}
```

---

### Get Margin
**Endpoint:** `GET /user/margin`

**Description:** Get margin requirement for given parameters

**Query Parameters:**
- `instrument_token` (required): Instrument key
- `quantity` (required): Order quantity
- `price` (required): Order price
- `product` (required): MIS, CNC, NRML

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "margin_required": 10000.00,
    "margin_available": 50000.00,
    "margin_utilised": 0.20
  }
}
```

---

## Market Information Endpoints

### Get Market Status
**Endpoint:** `GET /market-status`

**Description:** Get current market status (open/closed)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "exchange": "NSE",
    "status": "OPEN",
    "timestamp": 1704067200
  }
}
```

---

### Get Market Holidays
**Endpoint:** `GET /market-holidays`

**Description:** Get market holidays schedule

**Query Parameters:**
- `month` (optional): Month (1-12)
- `year` (optional): Year

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "holiday_date": "2025-01-26",
      "holiday_type": "Republic Day",
      "exchange": "NSE"
    }
  ]
}
```

---

### Get Market Timings
**Endpoint:** `GET /market-timings`

**Description:** Get market session timings

**Query Parameters:**
- `exchange` (optional): Exchange code

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "exchange": "NSE",
      "trading_session": "MARKET",
      "open_time": "09:15",
      "close_time": "15:30"
    }
  ]
}
```

---

## WebSocket Endpoints

### Get Market Data Feed (v3)
**Endpoint:** `GET /feed/market-data-feed/authorize/v3`

**Description:** Get authorization for market data WebSocket feed

**Query Parameters:**
- `mode` (required): LTP, QUOTE, or FULL

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "authorized_redirect_uri": "wss://feed.upstox.com/feed/market-data-feed/v3",
    "request_key": "KEY123"
  }
}
```

---

### Get Market Data Feed
**Endpoint:** `GET /feed/market-data-feed/authorize`

**Description:** Get authorization for market data WebSocket feed (v2)

**Query Parameters:**
- `mode` (required): LTP or QUOTE

**Headers:**
```
Authorization: Bearer <access_token>
```

---

### Get Portfolio Stream Feed
**Endpoint:** `GET /feed/portfolio-stream-feed/authorize`

**Description:** Get authorization for portfolio updates WebSocket feed

**Headers:**
```
Authorization: Bearer <access_token>
```

---

## Rate Limiting

- **Rate Limit:** 100 requests per second per API client
- **Burst Limit:** 300 requests per second (temporary burst)
- **Headers Returned:**
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Field Patterns

### Instrument Key Format
```
{EXCHANGE}#{TRADINGSYMBOL}
Examples:
- NSE_EQ|INFY (Equity)
- NFO_EQ|NIFTY25JAN23000CE (Option)
- NFO_FUT|NIFTY25JAN (Future)
```

### Date Format
- ISO 8601: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`
- Unix Timestamp (epoch): Seconds since 1970-01-01

### Candle Intervals
- Intraday: 1m, 5m, 15m, 30m, 1h
- Daily+: 1d, 1w, 1mo

### Product Types
- MIS: Margin Intraday Square-off
- CNC: Cash and Carry (delivery)
- NRML: Normal (derivatives)

---

## Commonly Used Instrument Keys

| Exchange | Format | Example |
|----------|--------|---------|
| NSE Equity | NSE_EQ\|SYMBOL | NSE_EQ\|INFY |
| BSE Equity | BSE_EQ\|SYMBOL | BSE_EQ\|SBIN |
| NFO Options | NFO_EQ\|NIFTY25JAN23000CE | Option contract |
| NFO Futures | NFO_FUT\|NIFTY25JAN | Futures contract |
| MCX Commodities | MCX\|SYMBOL | MCX\|GOLD |

---

**Last Updated:** 2025-01-31

For complete API documentation, visit: https://upstox.com/developer/api-documentation/
