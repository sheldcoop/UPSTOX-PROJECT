# API Endpoint Usage Guide - Why We Need Each Endpoint

This document explains **WHY** each API endpoint exists and provides **real-world use cases** with examples.

**Note:** Basic endpoints like login/logout/authentication are self-explanatory and omitted.

---

## Market Quote & Pricing Endpoints

### GET /v3/market-quote/ltp - Last Traded Price (v3)

**Why we need this:**
- Real-time price tracking for trading strategies
- Quick price checks without full market data overhead
- Lightweight endpoint for high-frequency updates
- Support for multiple symbols in single call (efficient)

**Real-world example:**
```python
# Scenario: Check if INFY crossed ₹1,500
response = requests.get("/api/v3/market-quote/ltp?symbol=NSE_EQ|INE009A01021")
ltp = response.json()["data"]["INE009A01021"]["last_price"]

if ltp >= 1500:
    # Trigger buy alert or execute strategy
    place_order("INFY", "BUY", 100)
```

**Use cases:**
1. **Alert System**: Trigger price alerts when target hit
2. **Dashboard Updates**: Show live prices on dashboard
3. **Strategy Validation**: Check if entry/exit conditions met
4. **P&L Calculation**: Calculate real-time position value

---

### GET /v3/market-quote/ohlc - OHLC Data (v3)

**Why we need this:**
- Technical analysis requires OHLC (Open, High, Low, Close)
- Pattern recognition (doji, hammer, engulfing, etc.)
- Support/resistance level calculation
- Volatility analysis (high-low range)

**Real-world example:**
```python
# Scenario: Detect breakout candle
response = requests.get("/api/v3/market-quote/ohlc?symbol=NSE_EQ|INE002A01018")
ohlc = response.json()["data"]["INE002A01018"]

# Breakout if: Close > High of previous candle AND Volume > Avg
if ohlc["close"] > ohlc["high"] and ohlc["volume"] > avg_volume:
    send_alert("RELIANCE breakout detected!")
```

**Use cases:**
1. **Candlestick Patterns**: Identify reversal/continuation patterns
2. **Range Trading**: Calculate support/resistance from H/L
3. **Volatility Filter**: Skip trading on low-volatility days
4. **Session Analysis**: Compare pre-market, regular, post-market

---

### GET /v3/market-quote/option-greek - Option Greeks (v3)

**Why we need this:**
- Options pricing and risk assessment
- Hedge ratio calculation (Delta hedging)
- Time decay monitoring (Theta)
- Volatility impact analysis (Vega)

**Real-world example:**
```python
# Scenario: Delta-neutral strategy
call_greeks = get_option_greeks("NSE_FO|NIFTY24FEB24000CE")
put_greeks = get_option_greeks("NSE_FO|NIFTY24FEB24000PE")

# Calculate hedge ratio
call_delta = call_greeks["delta"]  # e.g., 0.6
put_delta = put_greeks["delta"]    # e.g., -0.4

# To neutralize: buy 4 calls, sell 6 puts (6*0.6 ≈ 4*-0.4)
hedge_ratio = call_delta / abs(put_delta)
```

**Use cases:**
1. **Delta Hedging**: Maintain market-neutral positions
2. **Theta Decay**: Monitor option value erosion
3. **IV Rank**: Compare implied vs historical volatility
4. **Risk Management**: Calculate Greeks portfolio-wide
5. **Strategy Selection**: Choose strategies based on Greeks profile

---

## Historical Data Endpoints

### GET /v3/historical-candle/... - Historical Candles (v3)

**Why we need this:**
- Backtesting trading strategies
- Pattern recognition on historical data
- Support/resistance identification
- Volatility calculation (ATR, Bollinger Bands)

**Real-world example:**
```python
# Scenario: Backtest RSI strategy on INFY (last 100 days)
candles = get_historical_candles(
    "NSE_EQ|INE009A01021",
    interval="days/1",
    count=100,
    to_date="2024-01-31"
)

# Calculate RSI from historical closes
closes = [c[4] for c in candles]  # Close is 5th element
rsi_values = calculate_rsi(closes, period=14)

# Test strategy: Buy when RSI < 30, Sell when RSI > 70
backtest_results = simulate_trades(candles, rsi_values)
print(f"Win rate: {backtest_results['win_rate']}")
print(f"Sharpe ratio: {backtest_results['sharpe']}")
```

**Use cases:**
1. **Backtesting**: Test strategies before going live
2. **Technical Indicators**: Calculate MA, RSI, MACD, etc.
3. **Chart Visualization**: Display price charts
4. **Pattern Detection**: Find head-and-shoulders, triangles
5. **Volatility Analysis**: Calculate standard deviation, ATR

---

### GET /v3/historical-candle/intraday/... - Intraday Candles (v3)

**Why we need this:**
- Intraday strategy development (scalping, day trading)
- Opening range breakout strategies
- VWAP (Volume Weighted Average Price) calculation
- High-frequency pattern recognition

**Real-world example:**
```python
# Scenario: Opening Range Breakout strategy
# Get first 30-min candle after market open
candles_30min = get_intraday_candles(
    "NSE_EQ|INE002A01018",
    interval="minutes/30",
    count=1  # Just the opening range candle
)

opening_high = candles_30min[0]["high"]
opening_low = candles_30min[0]["low"]

# Now monitor 5-min candles for breakout
candles_5min = get_intraday_candles(..., interval="minutes/5", count=78)
for candle in candles_5min:
    if candle["close"] > opening_high:
        place_order("RELIANCE", "BUY", quantity=100)
        break
```

**Use cases:**
1. **Opening Range Breakout**: Trade breakouts from first 30-min
2. **VWAP Strategy**: Buy below VWAP, sell above
3. **Scalping**: Quick in-and-out trades using 1/5-min data
4. **Momentum Trading**: Identify intraday trends
5. **Time-based Analysis**: Study market behavior by hour

---

## Market Information Endpoints

### GET /api/market/status/<exchange> - Market Status

**Why we need this:**
- Prevent orders during market closure
- Display market status on dashboard
- Schedule automated tasks (run only when market open)
- Handle different market segments (EQ, FO) separately

**Real-world example:**
```python
# Scenario: Automated strategy should only trade when market open
def run_trading_strategy():
    market_status = get_market_status("NSE", "EQ")
    
    if not market_status["is_open"]:
        logger.info(f"Market closed. Next open: {market_status['next_open_time']}")
        return  # Don't execute strategy
    
    # Market is open, proceed with trading logic
    signals = generate_trading_signals()
    execute_signals(signals)

# Run every 5 minutes
schedule.every(5).minutes.do(run_trading_strategy)
```

**Use cases:**
1. **Order Validation**: Block orders when market closed
2. **Strategy Scheduling**: Run strategies only during market hours
3. **User Notifications**: Alert users when market opens/closes
4. **Data Collection**: Download EOD data when market closes

---

### GET /api/market/holidays - Market Holidays

**Why we need this:**
- Skip backtesting on holiday dates
- Schedule maintenance during holidays
- Calculate trading days for time-based strategies
- Display holiday calendar to users

**Real-world example:**
```python
# Scenario: Calculate "20 trading days" for moving average
holidays = get_market_holidays(year=2024)
holiday_dates = [h["date"] for h in holidays]

today = date.today()
trading_days = []
current_date = today

while len(trading_days) < 20:
    current_date -= timedelta(days=1)
    
    # Skip weekends
    if current_date.weekday() >= 5:
        continue
    
    # Skip holidays
    if current_date.strftime("%Y-%m-%d") in holiday_dates:
        continue
    
    trading_days.append(current_date)

# Now fetch data for these 20 trading days
for date in trading_days:
    data = fetch_historical_data(date)
```

**Use cases:**
1. **Trading Day Calculation**: Accurate period calculations
2. **Backtesting**: Exclude holidays from historical tests
3. **Calendar Display**: Show holidays on trading calendar
4. **Reminder System**: Notify users of upcoming holidays

---

### GET /api/market/timings/<date> - Market Timings

**Why we need this:**
- Pre-market strategy execution (9:00-9:15 AM)
- Post-market analysis (after 3:30 PM)
- Different segments have different timings
- Special sessions (Muhurat trading, etc.)

**Real-world example:**
```python
# Scenario: Place orders during pre-market session
timings = get_market_timings("2024-01-31", exchange="NSE", segment="EQ")

pre_market_start = timings["pre_open_start"]  # "09:00"
pre_market_end = timings["pre_open_end"]      # "09:15"

now = datetime.now().time()
if pre_market_start <= now <= pre_market_end:
    # Pre-market: only LIMIT orders allowed
    place_limit_order("INFY", 1500, quantity=100)
else:
    # Regular market: can use MARKET orders
    place_market_order("INFY", quantity=100)
```

**Use cases:**
1. **Pre-Market Orders**: Place orders before 9:15 AM
2. **Session Analysis**: Track pre-market, regular, post-market
3. **Algorithm Scheduling**: Run strategies at specific times
4. **Order Type Validation**: Different order types for different sessions

---

## Charges & Cost Calculation Endpoints

### GET /api/charges/brokerage - Brokerage Calculator

**Why we need this:**
- Calculate EXACT cost BEFORE placing order
- Compare strategies by cost (MIS vs CNC)
- Breakeven price calculation
- Batch order cost estimation

**Real-world example:**
```python
# Scenario: Should I use MIS or CNC for this trade?
symbol = "NSE_EQ|INE009A01021"
quantity = 1000
price = 1500

# Calculate for CNC (Delivery)
cnc_charges = calculate_brokerage(symbol, quantity, price, product="D")
cnc_total = cnc_charges["total_charges"]  # ₹150

# Calculate for MIS (Intraday)
mis_charges = calculate_brokerage(symbol, quantity, price, product="I")
mis_total = mis_charges["total_charges"]  # ₹80

# Decision: If holding < 1 day, use MIS to save ₹70
if holding_period < 1:
    use_product = "MIS"  # Save money
else:
    use_product = "CNC"  # Hold delivery

# Show user exact costs
print(f"Total cost: ₹{price * quantity + chosen_charges['total_charges']:,.2f}")
print(f"Breakeven: ₹{chosen_charges['breakeven_price']:.2f}")
```

**Use cases:**
1. **Cost Estimation**: Know exact charges before trading
2. **Strategy Comparison**: MIS vs CNC cost analysis
3. **Breakeven Calculation**: Find required profit price
4. **Batch Orders**: Calculate total cost for basket orders
5. **P&L Accuracy**: Account for all charges in P&L

---

### GET /api/charges/margin - Margin Calculator

**Why we need this:**
- Check if sufficient funds before ordering
- Leverage calculation (F&O)
- Risk assessment (margin = risk)
- Portfolio optimization (maximize positions within margin)

**Real-world example:**
```python
# Scenario: How many NIFTY futures can I buy with ₹1,00,000?
available_funds = 100000
symbol = "NSE_FO|NIFTY24FEB"
price = 21500

# Calculate margin for 1 lot (50 qty)
margin = calculate_margin(symbol, quantity=50, price=price)
margin_per_lot = margin["required_margin"]  # ₹1,20,000

# Can't buy even 1 lot! Need ₹20,000 more
if available_funds < margin_per_lot:
    send_alert("Insufficient funds for NIFTY Futures")
    
    # Alternative: Try options (lower margin)
    option_margin = calculate_margin("NSE_FO|NIFTY24FEB21500CE", quantity=50)
    # ₹15,000 - Affordable!
```

**Use cases:**
1. **Fund Check**: Validate sufficient margin before order
2. **Position Sizing**: Calculate max positions with available funds
3. **Leverage Planning**: Understand leverage in F&O
4. **Risk Management**: Margin = maximum risk exposure
5. **Portfolio Allocation**: Distribute capital across positions

---

## WebSocket Feed Endpoints

### GET /api/feed/portfolio-stream-feed/authorize - Portfolio WebSocket

**Why we need this:**
- Real-time order updates (filled, rejected, etc.)
- Live position P&L tracking
- Instant trade confirmations
- Portfolio value updates

**Real-world example:**
```python
# Scenario: Monitor order execution in real-time
ws_auth = get_portfolio_stream_auth()
websocket_url = ws_auth["websocket_url"]

# Connect to WebSocket
ws = connect_websocket(websocket_url, token=ws_auth["access_token"])

@ws.on_message
def handle_update(message):
    if message["type"] == "order":
        order_id = message["order_id"]
        status = message["status"]
        
        if status == "complete":
            send_notification(f"Order {order_id} filled!")
            update_dashboard_positions()
        elif status == "rejected":
            send_alert(f"Order {order_id} rejected: {message['reason']}")
    
    elif message["type"] == "position":
        # Real-time P&L update
        position_pnl = message["pnl"]
        update_pnl_display(position_pnl)
```

**Use cases:**
1. **Order Tracking**: Real-time order status updates
2. **Position Monitoring**: Live P&L tracking
3. **Trade Confirmations**: Instant execution notifications
4. **Risk Alerts**: Immediate notification of losses
5. **Dashboard Updates**: Real-time portfolio value

---

### GET /api/feed/market-data-feed/authorize - Market Data WebSocket

**Why we need this:**
- Live price streaming (no polling needed)
- Option chain real-time updates
- Order book depth streaming
- Tick-by-tick data for algos

**Real-world example:**
```python
# Scenario: Scalping strategy needs tick-by-tick prices
ws_auth = get_market_data_feed_auth()
ws = connect_websocket(ws_auth["websocket_url"])

# Subscribe to INFY for real-time ticks
ws.subscribe("NSE_EQ|INE009A01021")

@ws.on_tick
def on_price_update(tick):
    ltp = tick["last_price"]
    
    # Scalping: Buy on 0.1% dip, sell on 0.1% rise
    if ltp < entry_price * 0.999:
        place_order("INFY", "BUY", 1000)
    elif ltp > entry_price * 1.001:
        place_order("INFY", "SELL", 1000)
```

**Use cases:**
1. **Scalping**: Requires sub-second price updates
2. **Option Chain**: Live Greeks and premium updates
3. **Order Book Analysis**: Track bid-ask spread changes
4. **Algo Trading**: Feed real-time data to algorithms
5. **Dashboard**: Show live prices without API polling

---

## Summary - Why These Endpoints Matter

| Endpoint Category | Primary Use Case | Business Impact |
|------------------|------------------|-----------------|
| **Market Quotes v3** | Real-time pricing & Greeks | Enable options trading & risk management |
| **Historical v3** | Backtesting & analysis | Validate strategies before risking capital |
| **Market Info** | Trading calendar & hours | Prevent errors, schedule correctly |
| **Charges** | Cost calculation | Transparent pricing, informed decisions |
| **WebSocket** | Real-time updates | Professional-grade trading experience |

**Key Benefits:**
1. **Risk Reduction**: Know costs and margins before trading
2. **Strategy Validation**: Backtest before going live
3. **Operational Efficiency**: Automate based on market status
4. **User Experience**: Real-time updates via WebSocket
5. **Cost Transparency**: Exact charges for every trade

---

**Document Version:** 1.0  
**Last Updated:** February 3, 2026  
**Purpose:** Explain practical value of each API endpoint
