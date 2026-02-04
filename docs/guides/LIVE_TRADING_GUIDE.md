# Live Trading System - Complete Guide

**Upstox Backend Integration for Professional Traders**

Date: January 31, 2026 | Status: Production Ready

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Feature 1: Websocket Real-time Quotes](#feature-1-websocket-real-time-quotes)
3. [Feature 2: Order Management](#feature-2-order-management)
4. [Feature 3: GTT Orders](#feature-3-gtt-orders)
5. [Feature 4: Account & Margin](#feature-4-account--margin)
6. [Feature 5: Market Depth](#feature-5-market-depth)
7. [Integrated Workflows](#integrated-workflows)
8. [Database Schema](#database-schema)
9. [API Reference](#api-reference)
10. [Best Practices](#best-practices)

---

## System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UPSTOX API v2                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Websocket   │  │  REST API    │  │   REST API   │     │
│  │  (Live Data) │  │  (Orders)    │  │  (Account)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │             │
├─────────┼─────────────────┼─────────────────┼─────────────┤
│  5 Python Scripts                                          │
│  ├─ websocket_quote_streamer.py                           │
│  ├─ order_manager.py                                      │
│  ├─ gtt_orders_manager.py                                 │
│  ├─ account_fetcher.py                                    │
│  └─ market_depth_fetcher.py                               │
├─────────────────────────────────────────────────────────────┤
│  SQLite Database (market_data.db)                          │
│  ├─ quote_ticks (real-time price data)                    │
│  ├─ orders (order history)                                │
│  ├─ gtt_orders (conditional orders)                       │
│  ├─ market_depth (order book data)                        │
│  └─ margin_history (account history)                      │
└─────────────────────────────────────────────────────────────┘
```

### Quick Start

```bash
# 1. Set access token
export UPSTOX_ACCESS_TOKEN="your_token_here"

# 2. Check account status
python scripts/account_fetcher.py --action margin

# 3. Start real-time quotes
python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 300

# 4. Create GTT order
python scripts/gtt_orders_manager.py --action create \
  --symbol NIFTY --quantity 25 --trigger-price 23500 \
  --condition GTE --order-type LIMIT --order-price 23500

# 5. Place order
python scripts/order_manager.py --action place \
  --symbol INFY --side BUY --qty 1 --type MARKET

# 6. Check market depth
python scripts/market_depth_fetcher.py --symbol NIFTY --action spread
```

---

## Feature 1: Websocket Real-time Quotes

### Overview

Connect directly to Upstox websocket for real-time tick-by-tick market data.
Ideal for algorithmic trading, live monitoring, and high-frequency analysis.

### Key Features

- **Real-time Updates**: Receive price updates every 100ms
- **Multi-symbol Support**: Subscribe to multiple symbols simultaneously
- **Auto-reconnect**: Automatic reconnection with exponential backoff
- **Persistent Storage**: All ticks saved in database for historical analysis
- **Live Display**: Real-time quote visualization in terminal
- **Bid-Ask Tracking**: Monitor bid-ask spread changes

### Installation & Setup

```bash
# Install websocket library (if not already installed)
pip install websocket-client requests

# Test connection
python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 10
```

### Usage Examples

#### Basic Usage - Stream for Duration

```bash
# Stream NIFTY for 5 minutes (300 seconds)
python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 300

# Stream multiple symbols
python scripts/websocket_quote_streamer.py \
  --symbols NIFTY,BANKNIFTY,INFY,TCS --duration 300
```

#### Live Display - Real-time Updates

```bash
# Show live quotes with automatic refresh (every 2 seconds)
python scripts/websocket_quote_streamer.py \
  --symbols NIFTY,BANKNIFTY,INFY \
  --live-display \
  --duration 300

# Output:
# ═════════════════════════════════════════════════════════════════════════════
# LIVE QUOTES - 2026-01-31 14:30:45
# ═════════════════════════════════════════════════════════════════════════════
# NIFTY        | LTP:     23500.00 | Bid:     23499.50 | Ask:     23500.50 | Spread:  0.004% | Vol:  1250000 | OI:        0
# BANKNIFTY    | LTP:     47250.00 | Bid:     47249.75 | Ask:     47250.50 | Spread:  0.002% | Vol:   850000 | OI:        0
# INFY         | LTP:      1800.50 | Bid:      1800.25 | Ask:      1800.75 | Spread:  0.028% | Vol:  2500000 | OI:        0
# ═════════════════════════════════════════════════════════════════════════════
# Ticks received: 1250 | Uptime: 300s
```

#### Query Tick History

```bash
# Get last 100 ticks for NIFTY
python scripts/websocket_quote_streamer.py \
  --query-ticks NIFTY \
  --limit 100

# Query database directly
sqlite3 market_data.db \
  "SELECT timestamp, ltp, bid_price, ask_price, volume FROM quote_ticks \
   WHERE symbol='NIFTY' \
   ORDER BY timestamp DESC \
   LIMIT 20"
```

#### Statistics and Monitoring

```bash
# View streaming statistics
python scripts/websocket_quote_streamer.py --stats

# Output:
# Connected: True
# Subscribed symbols: 2
# Total ticks: 1250
# Uptime: 300s
# Current quotes: 2
# Reconnect attempts: 0
```

### Database Schema

```sql
CREATE TABLE quote_ticks (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,          -- When tick received
    symbol TEXT,                 -- Trading symbol
    ltp REAL,                    -- Last Traded Price
    bid_price REAL,              -- Current bid price
    bid_qty INTEGER,             -- Bid quantity
    ask_price REAL,              -- Current ask price
    ask_qty INTEGER,             -- Ask quantity
    volume INTEGER,              -- Total volume
    oi INTEGER,                  -- Open interest
    day_high REAL,               -- Day's high price
    day_low REAL,                -- Day's low price
    exchange TEXT,               -- NSE/BSE/MCX
    UNIQUE(timestamp, symbol)
);

CREATE INDEX idx_symbol_timestamp ON quote_ticks(symbol, timestamp);
```

### Common Queries

```sql
-- Get average bid-ask spread for symbol
SELECT symbol, 
       AVG(ask_price - bid_price) as avg_spread,
       AVG((ask_price - bid_price) / ltp * 100) as avg_spread_pct
FROM quote_ticks
WHERE symbol = 'NIFTY' AND timestamp > datetime('now', '-1 hour')
GROUP BY symbol;

-- Find volume spikes
SELECT timestamp, symbol, volume
FROM quote_ticks
WHERE symbol = 'NIFTY' 
  AND volume > (SELECT AVG(volume) FROM quote_ticks WHERE symbol='NIFTY') * 1.5
ORDER BY timestamp DESC
LIMIT 10;

-- Get price movement analysis
SELECT symbol,
       (SELECT ltp FROM quote_ticks WHERE symbol='NIFTY' ORDER BY timestamp DESC LIMIT 1) as current,
       (SELECT ltp FROM quote_ticks WHERE symbol='NIFTY' ORDER BY timestamp ASC LIMIT 1) as open,
       MAX(ltp) as high,
       MIN(ltp) as low
FROM quote_ticks
WHERE symbol = 'NIFTY' AND timestamp > datetime('now', '-1 hour');
```

### Advanced Patterns

#### Pattern 1: Real-time Alert System

```python
# Pseudo-code for price alert
while streaming:
    quote = streamer.get_quote('NIFTY')
    if quote['ltp'] >= 23500 and not entry_triggered:
        place_order('NIFTY', 'BUY', 25, 'MARKET')
        entry_triggered = True
```

#### Pattern 2: Spread Analysis

```python
# Monitor spread changes
spreads = []
for i in range(100):
    bid_ask = streamer.get_bid_ask_spread('NIFTY')
    spreads.append(bid_ask['spread_pct'])
    
avg_spread = np.mean(spreads)
if current_spread > avg_spread * 1.5:
    print("Wide spread detected - avoid large orders")
```

---

## Feature 2: Order Management

### Overview

Complete order lifecycle management with support for market, limit, and stop-loss orders.
Includes bracket orders, order modification, and full tracking.

### Key Features

- **Order Types**: Market, Limit, Stop-Loss
- **Order Actions**: Place, Modify (price/qty), Cancel
- **Bracket Orders**: Entry + Stop Loss + Target
- **Order Tracking**: Real-time status, fills, pending
- **History**: Complete order audit trail
- **Product Types**: MIS (intraday), CNC (delivery), MTF (margin trading)

### Usage Examples

#### Place Market Order

```bash
# Buy 1 share of INFY at market price
python scripts/order_manager.py --action place \
  --symbol INFY \
  --side BUY \
  --qty 1 \
  --type MARKET

# Output:
# ✅ Order placed successfully
#    Order ID: ORD_ABC123
#    Symbol: INFY
#    Side: BUY
#    Quantity: 1
#    Type: MARKET
```

#### Place Limit Order

```bash
# Sell 25 NIFTY contracts at 23,500
python scripts/order_manager.py --action place \
  --symbol NIFTY \
  --side SELL \
  --qty 25 \
  --type LIMIT \
  --price 23500

# Executed only if price reaches 23,500 or better
```

#### Modify Order

```bash
# Change limit price from 1750 to 1760
python scripts/order_manager.py --action modify \
  --order-id ORD_ABC123 \
  --new-price 1760

# Change quantity from 1 to 2
python scripts/order_manager.py --action modify \
  --order-id ORD_ABC123 \
  --new-qty 2
```

#### Cancel Order

```bash
# Cancel pending order
python scripts/order_manager.py --action cancel \
  --order-id ORD_ABC123

# Output:
# ✅ Order ORD_ABC123 cancelled successfully
```

#### Place Bracket Order

```bash
# Entry at 1800, Stop-Loss at 1750, Target at 1850
python scripts/order_manager.py --action place-bracket \
  --symbol INFY \
  --qty 1 \
  --entry-price 1800 \
  --stop-loss 1750 \
  --target 1850

# Creates 3 related orders:
# 1. Main entry: BUY 1 @ 1800
# 2. Stop-Loss: SELL 1 @ 1750 (auto-trigger if entry filled)
# 3. Target: SELL 1 @ 1850 (auto-trigger if entry filled)
```

#### Get Order Status

```bash
python scripts/order_manager.py --action status \
  --order-id ORD_ABC123

# Output:
# 📋 ORDER DETAILS
# ════════════════════════════════════════════════════
# order_id: ORD_ABC123
# symbol: INFY
# side: BUY
# quantity: 1
# order_type: LIMIT
# price: 1750
# order_status: PENDING
# created_at: 2026-01-31 14:30:00
# ...
```

#### List Active Orders

```bash
python scripts/order_manager.py --action list-active

# Output:
# ════════════════════════════════════════════════════════════════════════════════
# Order ID    | Symbol | Side | Qty  | Type    | Price      | Status     | Created
# ════════════════════════════════════════════════════════════════════════════════
# ORD_ABC123  | INFY   | BUY  |    1 | LIMIT   |    1750.00 | PENDING    | 2026-01-31 14:30:00
# ORD_DEF456  | NIFTY  | SELL |   25 | MARKET  |       0.00 | FILLED     | 2026-01-31 14:31:00
```

#### Get Order History

```bash
# Get last 50 orders
python scripts/order_manager.py --action history --limit 50

# Get orders for specific symbol
python scripts/order_manager.py --action history \
  --symbol INFY \
  --limit 100

# Database query
sqlite3 market_data.db \
  "SELECT * FROM orders \
   WHERE symbol='INFY' \
   ORDER BY created_at DESC \
   LIMIT 20"
```

### Database Schema

```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    exchange TEXT,
    symbol TEXT,
    side TEXT,                      -- BUY or SELL
    quantity INTEGER,
    filled_quantity INTEGER,
    pending_quantity INTEGER,
    order_type TEXT,                -- MARKET, LIMIT, STOP_LOSS
    price REAL,                     -- Limit price
    trigger_price REAL,             -- For STOP_LOSS
    order_status TEXT,              -- PENDING, FILLED, CANCELLED, etc.
    created_at DATETIME,
    updated_at DATETIME,
    product_type TEXT,              -- MIS, CNC, MTF
    time_in_force TEXT,             -- IOC, GTD, etc.
    UNIQUE(order_id)
);

CREATE TABLE bracket_orders (
    bracket_id TEXT PRIMARY KEY,
    entry_order_id TEXT,
    stop_loss_order_id TEXT,
    target_order_id TEXT,
    symbol TEXT,
    quantity INTEGER,
    entry_price REAL,
    stop_loss_price REAL,
    target_price REAL,
    status TEXT,
    created_at DATETIME,
    UNIQUE(bracket_id)
);
```

### Common Queries

```sql
-- Get today's P&L
SELECT side,
       SUM(quantity * COALESCE(average_price, price)) as total_value,
       SUM(CASE WHEN side='BUY' THEN -quantity ELSE quantity END) as net_qty
FROM orders
WHERE DATE(created_at) = DATE('now') AND order_status='FILLED';

-- Find pending orders
SELECT * FROM orders
WHERE order_status IN ('PENDING', 'PARTIALLY_FILLED')
ORDER BY created_at DESC;

-- Get order execution speed
SELECT 
    DATETIME(filled_at) - DATETIME(created_at) as execution_time,
    COUNT(*) as order_count
FROM orders
WHERE order_status='FILLED'
GROUP BY ROUND((JULIANDAY(filled_at) - JULIANDAY(created_at)) * 86400 / 5) * 5
ORDER BY execution_time;
```

---

## Feature 3: GTT Orders

### Overview

Good-Till-Triggered orders automatically execute when price reaches specified levels.
Perfect for "set and forget" strategies requiring no manual monitoring.

### Key Features

- **Trigger Conditions**: >=, <=, >, <
- **Order Types**: Market or Limit execution
- **Auto-Trigger**: Automatic execution when condition met
- **Modifiable**: Change trigger price/quantity anytime
- **Monitoring**: Real-time trigger checking
- **History**: Complete GTT order audit trail

### Usage Examples

#### Create Basic GTT Order

```bash
# Buy 1 INFY when price falls to 1750
python scripts/gtt_orders_manager.py --action create \
  --symbol INFY \
  --quantity 1 \
  --trigger-price 1750 \
  --trigger-type LTP \
  --condition LTE \
  --order-type LIMIT \
  --order-price 1750

# Output:
# ✅ GTT Order created successfully
#    GTT ID: GTT_ABCD1234
#    Trigger: LTP <= 1750
#    Action: BUY 1 @ 1750
```

#### Create Sell-on-Target GTT

```bash
# Sell 25 NIFTY when price reaches 23,600
python scripts/gtt_orders_manager.py --action create \
  --symbol NIFTY \
  --quantity 25 \
  --trigger-price 23600 \
  --condition GTE \
  --order-type MARKET \
  --side SELL
```

#### Conditions Explained

```
GTE (>=): Trigger when price >= specified price
  • Use for: Sell targets, resistance breakout buys
  • Example: Sell when price >= 1850 (take profit)

LTE (<=): Trigger when price <= specified price
  • Use for: Buy dips, support level buys
  • Example: Buy when price <= 1750 (dip buy)

GT (>): Trigger when price > specified price
  • Similar to GTE but strictly greater
  • Use for: More precise trigger points

LT (<): Trigger when price < specified price
  • Similar to LTE but strictly less
  • Use for: More precise trigger points
```

#### Modify GTT Order

```bash
# Change trigger price from 1750 to 1800
python scripts/gtt_orders_manager.py --action modify \
  --gtt-id GTT_ABCD1234 \
  --new-trigger-price 1800

# Change execution price and trigger simultaneously
python scripts/gtt_orders_manager.py --action modify \
  --gtt-id GTT_ABCD1234 \
  --new-trigger-price 1800 \
  --new-order-price 1800
```

#### Cancel GTT Order

```bash
python scripts/gtt_orders_manager.py --action cancel \
  --gtt-id GTT_ABCD1234

# Output:
# ✅ GTT Order GTT_ABCD1234 cancelled successfully
```

#### List All GTT Orders

```bash
# Show all GTT orders with status
python scripts/gtt_orders_manager.py --action list

# Output:
# ════════════════════════════════════════════════════════════════════════════════════════════
# GTT ID     | Symbol | Qty | Trigger  | Condition | Price  | Type   | Status  | Created
# ════════════════════════════════════════════════════════════════════════════════════════════
# GTT_ABC    | INFY   |  1  |  1750.00 | LTE       | 1750.00| LIMIT  | ACTIVE  | 2026-01-31 14:30
# GTT_DEF    | NIFTY  | 25  | 23600.00| GTE       |  0.00  | MARKET | ACTIVE  | 2026-01-31 14:31
```

#### Get GTT Details

```bash
python scripts/gtt_orders_manager.py --action details \
  --gtt-id GTT_ABCD1234

# Output:
# 📋 GTT ORDER DETAILS
# ════════════════════════════════════════════════
# gtt_id: GTT_ABCD1234
# symbol: INFY
# quantity: 1
# trigger_price: 1750.00
# condition: LTE
# order_type: LIMIT
# order_price: 1750.00
# status: ACTIVE
# created_at: 2026-01-31 14:30:00
```

#### Monitor GTT Execution

```bash
# Check if GTT orders are being triggered (real-time)
python scripts/gtt_orders_manager.py --action monitor \
  --check-interval 5 \
  --duration 3600

# Monitors every 5 seconds for 1 hour
# Output:
# 📍 GTT_ABC: INFY Trigger: LTE 1750 Status: ACTIVE
# 📍 GTT_DEF: NIFTY Trigger: GTE 23600 Status: ACTIVE
# ... (continues checking every 5 seconds)
```

#### Get GTT History

```bash
# Get last 50 GTT orders
python scripts/gtt_orders_manager.py --action history --limit 50

# Get GTT history for specific symbol
python scripts/gtt_orders_manager.py --action history \
  --symbol INFY \
  --limit 100
```

### Database Schema

```sql
CREATE TABLE gtt_orders (
    gtt_id TEXT PRIMARY KEY,
    symbol TEXT,
    quantity INTEGER,
    trigger_price REAL,
    trigger_type TEXT,                -- LTP (Last Traded Price)
    condition TEXT,                   -- GTE, LTE, GT, LT
    order_type TEXT,                  -- MARKET or LIMIT
    order_price REAL,                 -- Execution price for LIMIT
    side TEXT,                        -- BUY or SELL
    status TEXT,                      -- ACTIVE, TRIGGERED, CANCELLED
    triggered_order_id TEXT,          -- Order ID when triggered
    created_at DATETIME,
    triggered_at DATETIME,
    expires_at DATETIME,
    remarks TEXT,
    UNIQUE(gtt_id)
);

CREATE TABLE gtt_triggers (
    id INTEGER PRIMARY KEY,
    gtt_id TEXT,
    timestamp DATETIME,
    event_type TEXT,                  -- CREATED, TRIGGERED, MODIFIED, CANCELLED
    message TEXT,
    FOREIGN KEY(gtt_id) REFERENCES gtt_orders(gtt_id)
);
```

### Real-World GTT Strategies

#### Strategy 1: Range Trading

```bash
# Buy when price breaks above 1800
python scripts/gtt_orders_manager.py --action create \
  --symbol INFY --quantity 1 --trigger-price 1800 \
  --condition GT --order-type LIMIT --order-price 1800

# Sell when price reaches 1850
python scripts/gtt_orders_manager.py --action create \
  --symbol INFY --quantity 1 --trigger-price 1850 \
  --condition GTE --order-type MARKET --side SELL
```

#### Strategy 2: Dip Buying

```bash
# Buy when price dips to support level
python scripts/gtt_orders_manager.py --action create \
  --symbol NIFTY --quantity 25 --trigger-price 23000 \
  --condition LTE --order-type LIMIT --order-price 23000

# Sell at resistance level
python scripts/gtt_orders_manager.py --action create \
  --symbol NIFTY --quantity 25 --trigger-price 23500 \
  --condition GTE --order-type MARKET --side SELL
```

#### Strategy 3: Trailing Stop-Loss

```bash
# Create initial GTT for entry
python scripts/gtt_orders_manager.py --action create \
  --symbol INFY --quantity 1 --trigger-price 1700 \
  --condition LTE --order-type LIMIT --order-price 1700

# After entry, modify stop-loss progressively
# As price rises, move stop-loss up to lock in profits
```

---

## Feature 4: Account & Margin

### Overview

Real-time account information including margin, buying power, and balance.
Essential for risk management and position sizing.

### Key Features

- **Account Profile**: User, email, client ID, status
- **Margin Info**: Available, used, required for each segment
- **Buying Power**: Calculated for equity, commodity, MTF
- **Account Alerts**: Low margin warnings, liquidation risk
- **History Tracking**: Margin changes throughout the day
- **Real-time Monitoring**: Continuous margin level checking

### Usage Examples

#### Get Account Profile

```bash
python scripts/account_fetcher.py --action profile

# Output:
# ════════════════════════════════════════════════════════════
# ACCOUNT PROFILE
# ════════════════════════════════════════════════════════════
#
# User ID:           USR123456
# Email:             trader@example.com
# Client ID:         CLT123456
# Status:            ACTIVE
# Account Type:      Individual
```

#### Get Current Margin

```bash
python scripts/account_fetcher.py --action margin

# Output:
# ════════════════════════════════════════════════════════════
# MARGIN DETAILS
# ════════════════════════════════════════════════════════════
#
# 📊 AVAILABLE MARGIN:
#   Equity:          500,000.00
#   Commodity:       100,000.00
#   MTF:              50,000.00
#   Total:           650,000.00
#
# 📊 UTILISED MARGIN:
#   Equity:          250,000.00
#   Commodity:            0.00
#   MTF:                  0.00
#   Total:           250,000.00
#
# 📈 Margin Utilization: 27.78%
```

#### Get Buying Power

```bash
python scripts/account_fetcher.py --action buying-power

# Output:
# ════════════════════════════════════════════════════════════
# BUYING POWER
# ════════════════════════════════════════════════════════════
#
# 💰 EQUITY SEGMENT (NSE/BSE):
#   Available Margin:     500,000.00
#   Buying Power (2x):  1,000,000.00
#
# 💰 COMMODITY SEGMENT (MCX):
#   Available Margin:     100,000.00
#   Buying Power (5x):    500,000.00
#
# 💰 MARGIN TRADING (MTF):
#   Available Margin:      50,000.00
#   Buying Power (1x):     50,000.00
#
# 💰 TOTAL:
#   Total Available:     650,000.00
#   Total Buying Power: 1,550,000.00
```

#### Get Full Account Summary

```bash
python scripts/account_fetcher.py --action summary

# Shows profile + margin + calculated buying power
```

#### Get Account Holdings

```bash
python scripts/account_fetcher.py --action holdings

# Output:
# ✅ Holdings: 15 positions
# (Details of all holdings in portfolio)
```

#### View Margin History

```bash
# Get last 100 margin snapshots
python scripts/account_fetcher.py --action history --limit 100

# Output:
# ════════════════════════════════════════════════════════════════
# Timestamp           | Available  | Used       | Util % | Buying Power
# ════════════════════════════════════════════════════════════════
# 2026-01-31 14:30:00 |    500000  |     250000 |  33.33 |   1000000.00
# 2026-01-31 14:31:00 |    480000  |     270000 |  36.00 |    960000.00
# 2026-01-31 14:32:00 |    450000  |     300000 |  40.00 |    900000.00
```

#### Monitor Account Real-time

```bash
# Check margin every 30 seconds for 1 hour
python scripts/account_fetcher.py --action monitor \
  --interval 30 \
  --duration 3600

# Output (every 30 seconds):
# 📊 Account update at 2026-01-31 14:30:00
#   Available: ₹500,000 | Used: ₹250,000 | Util: 33.33%
# 📊 Account update at 2026-01-31 14:30:30
#   Available: ₹495,000 | Used: ₹255,000 | Util: 34.01%
```

### Margin Levels Explained

#### Available Margin

Maximum amount you can deploy without risking liquidation.

```
Available Margin = Account Balance - Utilised Margin
```

For different product types:
- **Equity (MIS)**: 2x leverage (use ₹1L to trade ₹2L worth)
- **Commodity**: 5x leverage (use ₹20K to trade ₹1L worth)
- **MTF**: 1x leverage (direct 1:1 margin)

#### Margin Utilization %

```
Margin Util % = (Utilised Margin / Total Margin) × 100

Safe Zone:      < 50%  (✓ Safe, comfortable)
Caution Zone:   50-80% (⚠️  Monitor closely)
Warning Zone:   80-90% (🚨 High risk)
Critical Zone:  > 90%  (💥 Liquidation imminent)
```

#### Buying Power Calculation

```
Buying Power = Available Margin × Leverage Multiplier

Equity:    Available × 2 (intraday leverage)
Commodity: Available × 5 (commodity leverage)
MTF:       Available × 1 (no leverage)

Example:
Available Equity Margin:  ₹5,00,000
Buying Power (Equity):    ₹5,00,000 × 2 = ₹10,00,000
```

### Database Schema

```sql
CREATE TABLE margin_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    available_margin REAL,
    used_margin REAL,
    margin_utilization_pct REAL,
    buying_power REAL
);

-- Indexed for fast queries on margin trends
CREATE INDEX idx_timestamp ON margin_history(timestamp);
```

### Common Queries

```sql
-- Get margin trend over last hour
SELECT timestamp, available_margin, used_margin, margin_utilization_pct
FROM margin_history
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp;

-- Find margin peaks and lows
SELECT 
    MAX(used_margin) as peak_usage,
    MIN(available_margin) as minimum_available,
    MAX(margin_utilization_pct) as peak_utilization
FROM margin_history
WHERE DATE(timestamp) = DATE('now');

-- Margin deterioration alerts
SELECT 
    LAG(margin_utilization_pct) OVER (ORDER BY timestamp) as prev_util,
    margin_utilization_pct as current_util,
    CASE 
        WHEN margin_utilization_pct > 80 AND prev_util <= 80 THEN 'WARN'
        WHEN margin_utilization_pct > 90 AND prev_util <= 90 THEN 'CRITICAL'
    END as alert
FROM margin_history
WHERE timestamp > datetime('now', '-1 hour');
```

### Risk Management Practices

#### Practice 1: Position Sizing

```
Max Position Size = Available Margin / Entry Price

Example:
Available Margin: ₹5,00,000
INFY Entry Price: ₹1,800
Max Position:     ₹5,00,000 / ₹1,800 = 278 shares

But factor in:
- Stop-loss distance
- Volatility buffer
- Reserve margin (20-30%)

Conservative Position: 200 shares (uses 40% margin)
```

#### Practice 2: Risk per Trade

```
Never risk more than 1-2% of total margin on single trade

Example:
Account Margin: ₹5,00,000
Risk per Trade: 1% = ₹5,000

INFY Trade:
Entry: 1,800
Stop Loss: 1,750
Loss per share: ₹50
Max Position: ₹5,000 / ₹50 = 100 shares
```

#### Practice 3: Margin Utilization Targets

```
Safe:      < 30% (Plenty of buffer)
Moderate:  30-50% (Comfortable for traders)
Active:    50-70% (For active traders only)
Aggressive: 70-85% (High risk, close monitoring)
Critical:  > 85% (Risk of liquidation)
```

---

## Feature 5: Market Depth

### Overview

Real-time order book data including bid-ask spreads, order book levels, and liquidity analysis.
Essential for analyzing market microstructure and finding optimal prices.

### Key Features

- **Level 1 Depth**: Top bid/ask with volumes
- **Level 2 Depth**: 5-10 levels of bid/ask
- **Spread Analysis**: Bid-ask spread percentage
- **Liquidity Scoring**: 0-100 score based on depth
- **Order Imbalance**: Detect market sentiment
- **Visualization**: Text-based depth display
- **History Tracking**: Spread changes throughout day

### Usage Examples

#### Get Level 1 Market Depth

```bash
python scripts/market_depth_fetcher.py --symbol INFY --action depth --level 1

# Output:
# ════════════════════════════════════════════════════════════════════════════════════
# MARKET DEPTH - INFY
# ════════════════════════════════════════════════════════════════════════════════════
#
#              BID SIDE                    |              ASK SIDE
#     Price        Qty           Vol        |          Vol           Qty      Price
# ────────────────────────────────────────────────────────────────────────────────
#   1800.25      1500                       |                       1500     1800.75
#   1800.00      2000                       |                       2000     1801.00
#   1799.75      2500                       |                       2500     1801.25
```

#### Get Level 2 Market Depth

```bash
python scripts/market_depth_fetcher.py --symbol NIFTY --action depth --level 2

# Shows 10 levels of bid/ask orders
```

#### Get Bid-Ask Spread

```bash
python scripts/market_depth_fetcher.py --symbol NIFTY --action spread

# Output:
# ════════════════════════════════════════════════════════════
# BID-ASK SPREAD - NIFTY
# ════════════════════════════════════════════════════════════
#
# Last Traded Price (LTP): 23500.00
# Mid Price:               23500.25
#
# BID SIDE            | ASK SIDE
#   Price: 23499.50   |   Price: 23500.50
#   Qty:   1200       |   Qty:   1200
#
# 📊 SPREAD ANALYSIS:
#   Absolute Spread: 1.00
#   Spread %:        0.00426%
```

#### Analyze Liquidity

```bash
python scripts/market_depth_fetcher.py --symbol INFY --action liquidity

# Output:
# ════════════════════════════════════════════════════════════
# LIQUIDITY ANALYSIS - INFY
# ════════════════════════════════════════════════════════════
#
# 📊 VOLUME AT 5 LEVELS:
#   Bid Volume:      150,000
#   Ask Volume:      155,000
#   Total Depth Vol: 305,000
#
# 📈 ORDER IMBALANCE:
#   Imbalance Ratio: -0.016
#   Direction:       BALANCED
#
# 💧 LIQUIDITY SCORE:
#   Score:           85.5/100
#   Rating:          🟢 Excellent
```

#### Compare Spreads

```bash
python scripts/market_depth_fetcher.py \
  --symbols NIFTY,BANKNIFTY,FINNIFTY \
  --action compare

# Output:
# ════════════════════════════════════════════════════════════════════════════════
# SPREAD COMPARISON
# ════════════════════════════════════════════════════════════════════════════════
# Symbol     | Bid        | Ask        | Spread     | Spread %
# ────────────────────────────────────────────────────────────────
# NIFTY      |  23499.50  |  23500.50  |      1.00  |  0.00426%
# BANKNIFTY  |  47249.75  |  47250.50  |      0.75  |  0.00159%
# FINNIFTY   |   7999.90  |   8000.10  |      0.20  |  0.00250%
```

#### View Spread History

```bash
python scripts/market_depth_fetcher.py \
  --symbol NIFTY \
  --action history \
  --limit 100

# Shows spread evolution throughout the day
```

#### Monitor Depth Real-time

```bash
# Monitor NIFTY depth every 5 seconds for 5 minutes
python scripts/market_depth_fetcher.py \
  --symbol NIFTY \
  --action monitor \
  --interval 5 \
  --duration 300

# Output:
# 2026-01-31 14:30:00 | Bid: 23499.50 | Ask: 23500.50 | Spread:  0.004%
# 2026-01-31 14:30:05 | Bid: 23499.75 | Ask: 23500.75 | Spread:  0.004%
# 2026-01-31 14:30:10 | Bid: 23499.25 | Ask: 23500.25 | Spread:  0.004%
```

### Spread Analysis

#### Spread Interpretation

```
Tight Spread (< 0.05%):
  • Good liquidity
  • Low transaction costs
  • Good for entering/exiting large positions

Normal Spread (0.05% - 0.2%):
  • Average liquidity
  • Regular market conditions
  • Standard for most stocks

Wide Spread (0.2% - 0.5%):
  • Lower liquidity
  • Higher transaction costs
  • Avoid large orders

Very Wide Spread (> 0.5%):
  • Very poor liquidity
  • High risk of slippage
  • Possibly illiquid stock
```

#### Example: Spread Impact on Trades

```
INFY Trading Scenario:
Entry Price: 1,800
Position Size: 100 shares
Entry Cost: 100 × 1,800 = ₹1,80,000

Scenario 1: Tight Spread (0.01%)
Bid-Ask: 1,799.90 - 1,800.10
Entry at Ask: 1,800.10
Cost: 100 × 1,800.10 = ₹1,80,010
Spread Cost: ₹10 (0.0056%)

Scenario 2: Wide Spread (0.5%)
Bid-Ask: 1,799.00 - 1,801.00
Entry at Ask: 1,801.00
Cost: 100 × 1,801.00 = ₹1,80,100
Spread Cost: ₹100 (0.056%)

Difference: ₹90 or 0.05% extra cost!
```

### Database Schema

```sql
CREATE TABLE market_depth (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    level INTEGER,                   -- Depth level 1-10
    bid_price REAL,
    bid_qty INTEGER,
    ask_price REAL,
    ask_qty INTEGER,
    bid_volume REAL,
    ask_volume REAL,
    spread REAL,
    spread_pct REAL,
    market_type TEXT,
    UNIQUE(timestamp, symbol, level)
);

CREATE TABLE spread_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    bid_price REAL,
    ask_price REAL,
    spread REAL,
    spread_pct REAL,
    mid_price REAL,
    top_bid_qty INTEGER,
    top_ask_qty INTEGER,
    UNIQUE(timestamp, symbol)
);

-- Create indexes
CREATE INDEX idx_depth_symbol ON market_depth(symbol, timestamp);
CREATE INDEX idx_spread_symbol ON spread_history(symbol, timestamp);
```

### Common Queries

```sql
-- Find tightest spreads (best liquidity)
SELECT symbol, AVG(spread_pct) as avg_spread
FROM spread_history
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY symbol
ORDER BY avg_spread ASC
LIMIT 10;

-- Detect spread widening (potential volatility)
SELECT s2.symbol, s1.spread_pct as prev_spread, s2.spread_pct as current_spread,
       (s2.spread_pct - s1.spread_pct) as spread_change
FROM spread_history s1
JOIN spread_history s2 ON s1.symbol = s2.symbol 
   AND s1.timestamp = (SELECT MAX(timestamp) FROM spread_history WHERE timestamp < s2.timestamp)
WHERE s2.timestamp > datetime('now', '-1 hour')
   AND (s2.spread_pct - s1.spread_pct) > 0.05
ORDER BY spread_change DESC;

-- Liquidity score over time
SELECT symbol,
       COUNT(*) as ticks,
       AVG(spread_pct) as avg_spread,
       SUM(top_bid_qty + top_ask_qty) / COUNT(*) as avg_depth_qty
FROM spread_history
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY symbol;
```

---

## Integrated Workflows

### Workflow 1: Complete Day Trading Setup

```
MORNING (Pre-Market)
└─ Check Account Margin
   └─ Determine max position size
└─ Setup GTT Orders
   └─ Buy limit at support
   └─ Sell limit at resistance

MARKET HOURS (9:15 AM - 3:30 PM)
├─ Start Websocket Streaming
│  └─ Monitor NIFTY real-time quotes
├─ Check Market Depth
│  └─ Analyze liquidity, spreads
├─ When Entry Signal:
│  ├─ Check Available Buying Power
│  ├─ Check Market Depth (avoid wide spreads)
│  └─ Place Order
├─ Monitor Position
│  ├─ Track Order Status
│  ├─ Monitor Margin Utilization
│  └─ Get Real-time Quotes
└─ When Exit Signal:
   ├─ Check Order Book
   ├─ Place Exit Order
   └─ Verify Fill

CLOSING (After 3:30 PM)
└─ Analyze Day
   ├─ Get Order History
   ├─ Calculate P&L
   ├─ Review Margin Usage
   └─ Plan Next Day
```

### Workflow 2: Breakout Trading

```
SETUP:
  Identify resistance level: 23,500

PRE-MARKET:
  python scripts/gtt_orders_manager.py --action create \
    --symbol NIFTY --quantity 25 --trigger-price 23500 \
    --condition GTE --order-type LIMIT --order-price 23500

DURING MARKET:
  python scripts/websocket_quote_streamer.py \
    --symbols NIFTY --live-display

  When price approaches 23,500:
  1. Check market depth:
     python scripts/market_depth_fetcher.py \
       --symbol NIFTY --action liquidity

  2. If liquidity score > 75: GTT likely to execute well
  3. Monitor position if GTT fills

EXIT:
  Option 1: GTT target (if setup)
  Option 2: Manual exit
    python scripts/order_manager.py --action place \
      --symbol NIFTY --side SELL --qty 25 \
      --type LIMIT --price 23600
```

### Workflow 3: Multi-Leg Hedging

```
MAIN POSITION:
  Long 1 INFY @ 1,800

HEDGE SETUP:
  GTT Sell if price falls:
    python scripts/gtt_orders_manager.py --action create \
      --symbol INFY --quantity 1 --trigger-price 1750 \
      --condition LTE --order-type MARKET

  GTT Take Profit if price rises:
    python scripts/gtt_orders_manager.py --action create \
      --symbol INFY --quantity 1 --trigger-price 1850 \
      --condition GTE --order-type MARKET

MONITORING:
  python scripts/gtt_orders_manager.py --action monitor \
    --check-interval 5 --duration 28800  # Full market hours

RESULT:
  • Price falls to 1,750 → Stop-loss triggers automatically
  • Price rises to 1,850 → Profit target triggers automatically
  • Hands-free protection!
```

---

## Database Schema

### Complete Entity-Relationship

```
quote_ticks
├── symbol
├── ltp
├── bid_price, ask_price
├── volume
└── timestamp

orders
├── order_id (PK)
├── symbol
├── side, quantity
├── order_type, price
├── order_status
└── created_at

gtt_orders
├── gtt_id (PK)
├── symbol
├── trigger_price, condition
├── order_type, order_price
├── status
└── created_at

market_depth
├── symbol
├── bid_price, bid_qty
├── ask_price, ask_qty
├── spread, spread_pct
└── timestamp

margin_history
├── timestamp
├── available_margin
├── used_margin
├── margin_utilization_pct
└── buying_power
```

---

## API Reference

### Websocket Quote Streamer

```bash
python scripts/websocket_quote_streamer.py [OPTIONS]

Options:
  --symbols TEXT              Comma-separated symbols
  --duration INT              Stream duration in seconds
  --live-display              Show live quote display
  --stats                     Show streaming statistics
  --query-ticks TEXT          Query tick history
  --limit INT                 Tick history limit (default: 10)
  --token TEXT                Access token
```

### Order Manager

```bash
python scripts/order_manager.py --action ACTION [OPTIONS]

Actions:
  place                       Place new order
  modify                      Modify existing order
  cancel                      Cancel order
  status                      Get order status
  list-active                 List active orders
  history                     Get order history
  place-bracket               Place bracket order

Options:
  --symbol TEXT              Trading symbol
  --side {BUY,SELL}          Buy or Sell
  --qty INT                  Quantity
  --type {MARKET,LIMIT,STOP} Order type
  --price FLOAT              Limit price
  --trigger-price FLOAT      Stop trigger price
  --order-id TEXT            Order ID (for modify/cancel/status)
```

### GTT Orders Manager

```bash
python scripts/gtt_orders_manager.py --action ACTION [OPTIONS]

Actions:
  create                      Create GTT order
  modify                      Modify GTT order
  cancel                      Cancel GTT order
  list                        List all GTT orders
  details                     Get GTT details
  history                     Get GTT history
  monitor                     Monitor GTT orders

Options:
  --symbol TEXT              Trading symbol
  --quantity INT             Order quantity
  --trigger-price FLOAT      Trigger price
  --condition {GTE,LTE,GT,LT} Trigger condition
  --order-type {MARKET,LIMIT} Order type
  --order-price FLOAT        Execution price
```

### Account Fetcher

```bash
python scripts/account_fetcher.py --action ACTION [OPTIONS]

Actions:
  profile                     Get account profile
  margin                      Get margin details
  buying-power                Get buying power
  summary                     Full account summary
  holdings                    Get holdings
  history                     Get margin history
  monitor                     Monitor account real-time

Options:
  --interval INT              Monitor interval (seconds)
  --duration INT              Monitor duration (seconds)
  --limit INT                 History limit
```

### Market Depth Fetcher

```bash
python scripts/market_depth_fetcher.py --action ACTION [OPTIONS]

Actions:
  depth                       Get market depth
  spread                      Get bid-ask spread
  liquidity                   Analyze liquidity
  history                     Get spread history
  compare                     Compare spreads
  monitor                     Monitor depth real-time

Options:
  --symbol TEXT              Trading symbol
  --symbols TEXT             Comma-separated symbols
  --level {1,2}              Depth level
  --interval INT             Monitor interval (seconds)
  --duration INT             Monitor duration (seconds)
  --limit INT                History limit
```

---

## Best Practices

### 1. Risk Management

```
✓ Never trade without stop-loss
✓ Risk 1-2% per trade maximum
✓ Monitor margin utilization constantly
✓ Set daily loss limits
✓ Use position sizing formula:
  Position Size = (Account Size × Risk %) / Stop Loss Distance
```

### 2. Order Placement

```
✓ Check market depth before large orders
✓ Use limit orders when possible (control price)
✓ Avoid placing orders during high-spread times
✓ Scale into positions rather than one large order
✓ Always set stop-loss before entering
```

### 3. GTT Order Setup

```
✓ Use GTE/LTE for range-based strategies
✓ Setup GTT orders before market open
✓ Modify GTT if market conditions change
✓ Monitor GTT execution in real-time
✓ Review GTT history for performance
```

### 4. Account Monitoring

```
✓ Check margin before market open
✓ Monitor margin utilization every 30 mins
✓ Alert if utilization > 80%
✓ Reduce positions if margin low
✓ Track historical margin for analysis
```

### 5. Real-time Monitoring

```
✓ Use websocket for active trading
✓ Check market depth for liquidity
✓ Monitor bid-ask spreads
✓ Watch order book imbalance
✓ React to volume changes
```

### 6. Database Maintenance

```
✓ Regularly archive old data (>3 months)
✓ Index queries on symbol and timestamp
✓ Backup database daily
✓ Analyze database for slow queries
✓ Clean up duplicate/invalid records
```

---

## Troubleshooting

### Connection Issues

```
Error: "Failed to connect to websocket"
Solution: 
  - Check internet connection
  - Verify UPSTOX_ACCESS_TOKEN is set
  - Token may have expired (regenerate)
  - Try reconnecting after 30 seconds
```

### Margin Issues

```
Error: "Insufficient margin to place order"
Solution:
  - Check available margin: account_fetcher.py --action margin
  - Reduce position size
  - Square off existing positions
  - Deposit more margin
```

### Order Placement Failures

```
Error: "Order rejected by API"
Common reasons:
  - Market closed (place only during 9:15-15:30)
  - Insufficient margin
  - Invalid symbol
  - Quantity exceeds limits
  - GTT already exists for symbol
```

### Performance Optimization

```
Slow queries?
  - Index on (symbol, timestamp)
  - Archive old data
  - Partition large tables
  - Use LIMIT in queries

High CPU usage?
  - Reduce streaming frequency
  - Batch database writes
  - Optimize callback functions
```

---

## Conclusion

You now have a complete, production-ready live trading system with all essential features for professional trading:

✅ **Real-time Data**: Websocket streaming with persistent storage
✅ **Order Execution**: Place, modify, cancel with full tracking
✅ **Automation**: GTT orders for conditional execution
✅ **Risk Management**: Account/margin monitoring
✅ **Market Analysis**: Order book depth & liquidity analysis

**Next Steps:**
1. Generate Upstox API credentials
2. Test in SANDBOX mode first
3. Start with small positions
4. Monitor all systems carefully
5. Scale up as you gain confidence

**Happy Trading! 🚀**
