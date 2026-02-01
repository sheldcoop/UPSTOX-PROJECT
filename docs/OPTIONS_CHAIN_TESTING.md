# Options Chain Viewer - Testing & Documentation

## 🎯 Overview

The Live Options Chain Viewer displays real-time option prices, Greeks (Delta, Gamma, Theta, Vega), Open Interest (OI), Volume, and Implied Volatility (IV) for Indian indices and stocks via Upstox API integration.

**File:** `frontend/src/components/OptionsChainViewer.tsx` (320+ lines)

**Backend Service:** `scripts/options_chain_service.py` (370+ lines)

**API Endpoints:**
- `GET /api/options/chain?symbol=NIFTY&expiry_date=2025-02-06`
- `GET /api/options/market-status`

---

## 🏗️ Architecture

### Data Flow

```
User Selects Symbol → Frontend Request
  ↓
GET /api/options/chain?symbol=NIFTY
  ↓
OptionsChainService.get_option_chain()
  ↓
Check: is_market_open() (NSE hours 9:15-15:30)
  ↓
IF market_open:
  Try: Upstox API /v2/option/chain
    ↓
    IF 401 (token expired):
      AuthManager.refresh_token()
      Retry API call
    ↓
    IF success: Return live data
    ELSE: Fallback to mock data
ELSE:
  Return mock data with 15 strikes
  ↓
Frontend displays strikes table with Greeks
```

### Market Hours Detection

**NSE Trading Hours:**
- Monday-Friday: 9:15 AM - 3:30 PM IST
- Weekends: Closed
- Holidays: Closed (not detected yet, requires NSE holiday calendar)

**Implementation:**
```python
def is_market_open(self) -> Tuple[bool, str]:
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    
    # Weekend check
    if now.weekday() in [5, 6]:
        return False, "Market closed (Weekend)"
    
    # Hours check (9:15 - 15:30)
    market_open_time = now.replace(hour=9, minute=15)
    market_close_time = now.replace(hour=15, minute=30)
    
    if market_open_time <= now <= market_close_time:
        return True, "Market is open"
    else:
        return False, "Market closed (Out of trading hours)"
```

---

## 🧪 Testing Checklist

### ✅ 1. Backend Service Testing

**Test Market Hours Detection:**
```bash
# From project root
source .venv/bin/activate
python -c "
from scripts.options_chain_service import OptionsChainService
service = OptionsChainService()
is_open, msg = service.is_market_open()
print(f'Market Status: {msg}')
print(f'Is Open: {is_open}')
"
```

**Expected Output:**
- Weekday 9:15-15:30: `Market is open`, `True`
- Weekday outside hours: `Market closed (Out of trading hours)`, `False`
- Weekend: `Market closed (Weekend)`, `False`

**Test Mock Data Generation:**
```bash
python -c "
from scripts.options_chain_service import OptionsChainService
service = OptionsChainService()
chain = service._mock_option_chain('NIFTY', '2025-02-06', False)
print(f'Underlying: {chain[\"underlying_price\"]}')
print(f'Strikes: {len(chain[\"strikes\"])}')
print(f'Data Source: {chain[\"data_source\"]}')
print(f'First Strike: {chain[\"strikes\"][0][\"strike\"]}')
print(f'Call Delta: {chain[\"strikes\"][7][\"call\"][\"delta\"]}')  # ATM strike
"
```

**Expected Output:**
```
Underlying: 21500 (NIFTY example)
Strikes: 15
Data Source: mock
First Strike: 21100
Call Delta: 0.50 (ATM should be ~0.5)
```

**Test API Endpoint (with cURL):**
```bash
# Market Status
curl "http://localhost:5001/api/options/market-status"

# Expected Response:
{
  "market_open": false,
  "message": "Market closed (Out of trading hours)",
  "timestamp": "2025-01-31T22:00:00+05:30"
}

# Options Chain
curl "http://localhost:5001/api/options/chain?symbol=NIFTY&expiry_date=2025-02-06"

# Expected Response (truncated):
{
  "success": true,
  "data": {
    "symbol": "NIFTY",
    "expiry_date": "2025-02-06",
    "underlying_price": 21500,
    "timestamp": "2025-01-31T22:00:00",
    "market_open": false,
    "data_source": "mock",
    "strikes": [
      {
        "strike": 21100,
        "call": {
          "ltp": 450.25,
          "volume": 150000,
          "oi": 1200000,
          "iv": 18.5,
          "delta": 0.75,
          "gamma": 0.003,
          "theta": -12.5,
          "vega": 8.2,
          "bid": 448.0,
          "ask": 452.5
        },
        "put": {
          "ltp": 15.75,
          "volume": 50000,
          "oi": 400000,
          "iv": 17.2,
          "delta": -0.25,
          ...
        }
      },
      ...
    ]
  },
  "trace_id": "abc123ef"
}
```

### ✅ 2. Frontend Component Testing

**Start Frontend:**
```bash
cd frontend
npm run dev
# Opens http://localhost:5173
```

**Manual Test Steps:**

1. **Navigation**
   - [ ] Click "Options Chain" in sidebar
   - [ ] Component loads without errors
   - [ ] Market status banner shows correct message

2. **Symbol Selection**
   - [ ] Dropdown shows 6 symbols (NIFTY, BANKNIFTY, FINNIFTY, RELIANCE, INFY, TCS)
   - [ ] Change symbol → New chain loads
   - [ ] Loading spinner appears during fetch
   - [ ] Last update time shows current time

3. **Data Display**
   - [ ] Underlying price displays correctly (₹ formatted)
   - [ ] Expiry date formatted (e.g., "6 Feb 2025")
   - [ ] Total strikes count matches (15 for indices)
   - [ ] Mock data warning shows when market closed

4. **Options Chain Table**
   - [ ] All columns visible: OI, Vol, IV%, Δ, LTP (both sides)
   - [ ] Call side highlighted green
   - [ ] Put side highlighted red
   - [ ] ATM strike has colored badge
   - [ ] Numbers formatted correctly:
     - LTP: ₹450.25 (2 decimals)
     - OI: 1,200,000 (comma-separated)
     - IV: 18.5% (1 decimal)
     - Delta: 0.50 (2 decimals)

5. **Tooltips** (Hover over column headers)
   - [ ] "OI" → Shows Open Interest explanation
   - [ ] "Vol" → Shows Volume explanation
   - [ ] "IV%" → Shows Implied Volatility explanation
   - [ ] "Δ" → Shows Delta explanation
   - [ ] "LTP" → Shows Last Traded Price explanation
   - [ ] "Strike" → Shows Strike Price explanation
   - [ ] All tooltips use `tradingGlossary.ts` definitions

6. **Auto-Refresh**
   - [ ] Toggle disabled when market closed
   - [ ] Enable auto-refresh → Checkbox checked
   - [ ] Data updates every 5 seconds
   - [ ] Last update time changes
   - [ ] Loading spinner does NOT appear (non-blocking)
   - [ ] Disable → Polling stops

7. **Manual Refresh**
   - [ ] Click "Refresh" button
   - [ ] Loading spinner appears
   - [ ] Button disabled during fetch
   - [ ] Data reloads successfully

8. **Error Handling**
   - [ ] Stop API server → Error banner shows
   - [ ] Error message includes trace_id
   - [ ] Red alert icon displays
   - [ ] Restart server → Refresh works again

9. **Responsiveness**
   - [ ] Table scrolls horizontally on mobile
   - [ ] Layout adapts to screen size
   - [ ] All interactive elements clickable

### ✅ 3. Debugging Features Testing

**Check TraceID Logging:**
```bash
# In browser DevTools → Network tab
# Click on /api/options/chain request
# Check Response Headers:
X-Trace-ID: abc123ef

# Check logs:
tail -f logs/api_server.log

# Look for:
[TraceID: abc123ef] GET /api/options/chain - symbol=NIFTY
[TraceID: abc123ef] OPTIONS: Market status: Market closed
[TraceID: abc123ef] OPTIONS: Using mock data for NIFTY
[TraceID: abc123ef] OPTIONS: Generated 15 strikes
```

**Test Error State Dumping:**
```bash
# Simulate error (e.g., invalid symbol in backend)
# Check debug_dumps/ folder:
ls -lah debug_dumps/

# Should see:
error_2025-01-31_220000_abc123ef.json

# Inspect dump:
cat debug_dumps/error_*.json | python -m json.tool
```

**Expected Dump Structure:**
```json
{
  "timestamp": "2025-01-31T22:00:00",
  "trace_id": "abc123ef",
  "endpoint": "/api/options/chain",
  "method": "GET",
  "params": {
    "symbol": "INVALID"
  },
  "error": "Symbol not found",
  "stack_trace": "..."
}
```

### ✅ 4. Integration Testing

**Test Full User Flow:**

1. **User Story: View NIFTY Options Chain**
   ```
   GIVEN: User is on dashboard
   WHEN: User clicks "Options Chain" in sidebar
   AND: Selects "NIFTY" from dropdown
   THEN: 
     - Market status shows "Market closed" (if after hours)
     - Mock data warning displays
     - 15 strikes appear in table
     - ATM strike (closest to underlying) is highlighted
     - Call Greeks show positive Delta (0.5-0.75 for ITM)
     - Put Greeks show negative Delta (-0.5 to -0.75 for ITM)
     - All tooltips work on hover
   ```

2. **User Story: Enable Auto-Refresh (Market Open)**
   ```
   GIVEN: Market is open (9:15-15:30 weekday)
   WHEN: User enables "Auto-refresh (5s)" checkbox
   THEN:
     - Checkbox becomes checked
     - Data refreshes every 5 seconds
     - Last update time increments
     - No loading spinner blocks UI
     - User can still interact with page
   ```

3. **User Story: Compare Strike Prices**
   ```
   GIVEN: Options chain is loaded
   WHEN: User scans ATM strikes
   THEN:
     - ATM call has higher LTP than OTM calls
     - ATM put has higher LTP than OTM puts
     - IV% is similar across nearby strikes
     - OI is highest at ATM strikes
   ```

---

## 📊 Greeks Validation

### Call Options Greeks (Expected Behavior)

| Moneyness | Delta | Gamma | Theta | Vega |
|-----------|-------|-------|-------|------|
| **Deep ITM** | 0.75-0.95 | Low (0.001-0.003) | Negative (-5 to -15) | Low (5-10) |
| **ATM** | ~0.50 | High (0.005-0.010) | Most Negative (-15 to -25) | High (15-25) |
| **Deep OTM** | 0.05-0.25 | Low (0.001-0.003) | Negative (-2 to -8) | Low (3-8) |

### Put Options Greeks (Expected Behavior)

| Moneyness | Delta | Gamma | Theta | Vega |
|-----------|-------|-------|-------|------|
| **Deep ITM** | -0.75 to -0.95 | Low | Negative | Low |
| **ATM** | ~-0.50 | High | Most Negative | High |
| **Deep OTM** | -0.05 to -0.25 | Low | Negative | Low |

**Mock Data Calculations:**
```python
# In options_chain_service.py _mock_option_chain()

distance = abs(strike - underlying_price) / underlying_price
moneyness = 'ITM' if strike < underlying_price else ('OTM' if strike > underlying_price else 'ATM')

# Delta calculation
if moneyness == 'ITM':
    call_delta = 0.75 - (distance * 5)  # Decreases as distance increases
    put_delta = -(0.25 + (distance * 5))
elif moneyness == 'ATM':
    call_delta = 0.50
    put_delta = -0.50
else:  # OTM
    call_delta = 0.25 - (distance * 5)
    put_delta = -(0.75 - (distance * 5))

# Gamma (highest at ATM)
gamma = 0.010 if moneyness == 'ATM' else 0.003

# Theta (most negative at ATM)
theta = -25.0 if moneyness == 'ATM' else -12.5
```

**Validation Tests:**
```python
# Test in Python REPL:
from scripts.options_chain_service import OptionsChainService
service = OptionsChainService()
chain = service._mock_option_chain('NIFTY', '2025-02-06', False)

# Find ATM strike
underlying = chain['underlying_price']
atm_strike = min(chain['strikes'], key=lambda x: abs(x['strike'] - underlying))

print(f"ATM Strike: {atm_strike['strike']}")
print(f"Call Delta: {atm_strike['call']['delta']}")  # Should be ~0.50
print(f"Put Delta: {atm_strike['put']['delta']}")    # Should be ~-0.50
print(f"Call Gamma: {atm_strike['call']['gamma']}")  # Should be highest
```

---

## 🔧 Troubleshooting

### Issue: "Failed to fetch options chain"

**Symptoms:**
- Red error banner in UI
- Network request fails in DevTools

**Diagnosis:**
1. Check API server running: `curl http://localhost:5001/api/health`
2. Check logs: `tail -f logs/api_server.log`
3. Check for CORS errors in browser console

**Solution:**
- Restart API server: `python scripts/api_server.py`
- Verify CORS enabled in `api_server.py`: `CORS(app)`
- Check frontend API URL: Should be `http://localhost:5001`

### Issue: "Market status always shows closed"

**Symptoms:**
- Market status never shows "open" even during trading hours

**Diagnosis:**
```python
from datetime import datetime
import pytz

now = datetime.now(pytz.timezone('Asia/Kolkata'))
print(f"Current IST time: {now}")
print(f"Weekday: {now.weekday()}")  # 0=Mon, 5=Sat, 6=Sun
print(f"Hour: {now.hour}, Minute: {now.minute}")
```

**Solution:**
- Verify system timezone: `timedatectl` (Linux) or `date` (Mac)
- Check Python timezone: `import pytz; pytz.timezone('Asia/Kolkata')`
- NSE holidays not implemented yet (will show open on market holidays)

### Issue: "Auto-refresh not working"

**Symptoms:**
- Checkbox enabled but data doesn't update

**Diagnosis:**
1. Open DevTools → Network tab
2. Enable auto-refresh
3. Watch for periodic GET requests every 5 seconds

**Solution:**
- Check `useEffect` dependencies in OptionsChainViewer.tsx
- Verify `marketStatus?.market_open` is true
- Check browser console for JavaScript errors

### Issue: "Greeks not displaying"

**Symptoms:**
- Delta, Gamma columns show "-"

**Diagnosis:**
```bash
curl "http://localhost:5001/api/options/chain?symbol=NIFTY" | python -m json.tool | grep delta
```

**Solution:**
- Check backend response includes Greeks in OptionData
- Verify TypeScript interface matches backend structure
- Check optional chaining: `strike.call.delta?.toFixed(2)`

---

## 📝 API Reference

### GET /api/options/chain

**Parameters:**
- `symbol` (required): Stock/index symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)
- `expiry_date` (optional): YYYY-MM-DD format (default: nearest expiry)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "NIFTY",
    "expiry_date": "2025-02-06",
    "underlying_price": 21500,
    "timestamp": "2025-01-31T14:30:00",
    "market_open": true,
    "data_source": "upstox",  // or "mock"
    "strikes": [...]
  },
  "trace_id": "abc123ef"
}
```

**Errors:**
- 400: Missing symbol parameter
- 500: API failure (returns mock data as fallback)

### GET /api/options/market-status

**Response:**
```json
{
  "market_open": false,
  "message": "Market closed (Out of trading hours)",
  "timestamp": "2025-01-31T22:00:00+05:30"
}
```

---

## 🚀 Production Deployment

**Before going live:**

1. **Add NSE Holiday Calendar:**
   ```python
   # In options_chain_service.py
   NSE_HOLIDAYS_2025 = [
       datetime(2025, 1, 26),  # Republic Day
       datetime(2025, 3, 14),  # Holi
       # ... add all NSE holidays
   ]
   
   def is_market_open(self):
       now = datetime.now(pytz.timezone('Asia/Kolkata'))
       if now.date() in [h.date() for h in NSE_HOLIDAYS_2025]:
           return False, "Market closed (Holiday)"
   ```

2. **Rate Limiting:**
   ```python
   from flask_limiter import Limiter
   
   limiter = Limiter(app, default_limits=["60 per minute"])
   
   @app.route('/api/options/chain')
   @limiter.limit("30 per minute")  # Upstox rate limit
   def get_option_chain():
       ...
   ```

3. **Caching (Redis):**
   ```python
   import redis
   
   cache = redis.Redis(host='localhost', port=6379, db=0)
   
   def get_option_chain(symbol):
       cache_key = f"options:{symbol}:{expiry}"
       cached = cache.get(cache_key)
       if cached:
           return json.loads(cached)
       
       # Fetch from API
       data = upstox_api.fetch()
       cache.setex(cache_key, 5, json.dumps(data))  # 5 second TTL
       return data
   ```

4. **Error Monitoring (Sentry):**
   ```python
   import sentry_sdk
   
   sentry_sdk.init(dsn="YOUR_DSN")
   ```

---

## 📈 Future Enhancements

**Phase 2 Features:**
1. **Greeks Chart** - Plot Delta/Gamma/Theta curves across strikes
2. **Option Strategy Builder** - Multi-leg strategies (Iron Condor, Butterfly, etc.)
3. **P&L Calculator** - Real-time P&L for selected strikes
4. **IV Rank/Percentile** - Historical IV comparison
5. **Option Flow** - Large block trades detection
6. **Max Pain** - Calculate max pain strike price
7. **Put-Call Ratio (PCR)** - Sentiment indicator
8. **Expiry Calendar** - Show all available expiries with selection
9. **Export to CSV** - Download chain data for analysis
10. **Alerts** - Notify on IV spike, OI changes, price crosses

**Backend Optimizations:**
1. WebSocket streaming instead of polling
2. Database caching for historical chains
3. Batch API calls for multiple symbols
4. Greeks calculation on backend (not mock)
5. Real-time OI change tracking

---

## 🐛 Known Limitations

1. **Mock Data Only (Currently):**
   - Upstox API integration requires live auth token
   - Greeks are calculated estimates, not real-time
   - No historical data or expiry selection yet

2. **No Holiday Calendar:**
   - Will show "market open" on NSE holidays
   - Needs manual NSE holiday list integration

3. **No WebSocket Support:**
   - Uses HTTP polling (5s interval)
   - WebSocket would reduce latency and server load

4. **Single Expiry:**
   - Currently defaults to nearest expiry
   - No UI to select different expiry dates

5. **No Advanced Greeks:**
   - Missing: Charm, Vanna, Vomma, Color
   - Only basic Greeks implemented

---

## ✅ Sign-Off Checklist

Before marking Options Chain feature complete:

- [ ] Backend tests pass (market hours, mock data, API endpoints)
- [ ] Frontend displays without errors
- [ ] All 20+ tooltips work (Options, Greeks, Data terms)
- [ ] Auto-refresh works when market open
- [ ] TraceID appears in all API responses
- [ ] Error handling tested (API down scenario)
- [ ] Loading states work correctly
- [ ] Mock data warning shows when market closed
- [ ] ATM strike highlighted correctly
- [ ] Greeks values make sense (Delta ~0.5 at ATM)
- [ ] Responsive on mobile devices
- [ ] No TypeScript errors
- [ ] No Python errors in logs
- [ ] Documentation complete (this file)

---

**Last Updated:** 2025-01-31  
**Version:** 1.0  
**Author:** GitHub Copilot (Claude Sonnet 4.5)
