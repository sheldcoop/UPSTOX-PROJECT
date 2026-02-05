# Full-Stack Debugging Protocol - UPSTOX-PROJECT v2.0

> **Lead Architect and Elite Debugger Protocol**
> 
> "It's not a bug. It's an undocumented feature... until we trace it, isolate it, and crush it."

## 🎯 Mission
Grant omniscient visibility into the multi-layered trading platform architecture:
- **Frontend:** NiceGUI (Python-based reactive UI on port 5001)
- **Backend:** Flask REST API (port 8000/9000)
- **Database:** SQLite (market_data.db)
- **External APIs:** Upstox (OAuth 2.0), NewsAPI, FinBERT
- **Infrastructure:** Docker/Docker Compose

## 📋 The Debugging Protocol (Follow Strictly)

When presented with an error or code snippet from any of the 31 pages, perform a **Full-Stack Root Cause Analysis** using the following steps:

## ⚡ When to Use This Protocol

### Backend Bugs (Python/Flask)
- **ALWAYS** when Flask API returns 500 errors
- **ALWAYS** when OHLC validation fails (high < low detected)
- **ALWAYS** when paper trading P&L is incorrect
- **ALWAYS** when Upstox/Yahoo Finance returns empty data
- **ALWAYS** when database constraints are violated (SQLite locks)
- **ALWAYS** when strategy signals don't match expected logic
- **ALWAYS** when authentication token expires (401 Unauthorized)

### Frontend Bugs (NiceGUI)
- **ALWAYS** when NiceGUI components don't update after async API calls
- **ALWAYS** when event handlers freeze the UI (blocking operations)
- **ALWAYS** when UI bindings break (reactivity issues)
- **ALWAYS** when `@ui.refreshable` decorators don't trigger updates
- **ALWAYS** when components render incorrect data
- **ALWAYS** when P&L colors don't match values (green on loss)
- **ALWAYS** when loading states never resolve
- **ALWAYS** when `time.sleep()` freezes the entire interface

### Integration Bugs
- **ALWAYS** when backend works but frontend shows errors
- **ALWAYS** when CORS errors appear
- **ALWAYS** when API_BASE URL is wrong (localhost vs host.docker.internal)
- **ALWAYS** when data format mismatches (backend sends `datetime`, frontend expects `timestamp`)
- **ALWAYS** when Docker networking fails (containers can't communicate)

## 📜 The God Protocol (Unified Workflow)

### Step 1: 🔍 Layer Identification

When an error occurs, **identify which layer** is failing:

#### **UI Layer (NiceGUI)**
Symptoms:
- Binding issues: UI doesn't update when data changes
- Layout breaks: Components misaligned or overlapping
- Unresponsive event handlers: Buttons don't trigger actions
- Frozen interface: UI becomes unresponsive after action

**Quick Check:**
```python
# Add debug logging to event handlers
async def on_button_click():
    logger.debug("Button clicked - starting action")
    # ... your code
    logger.debug("Button action completed")
```

#### **Communication Layer (HTTP/Requests)**
Symptoms:
- `requests.get/post` calls fail silently
- CORS errors in browser console
- Wrong API_BASE URL (port mismatch)
- Timeout errors (backend not responding)

**Quick Check:**
```python
# In dashboard_ui/state.py, check:
API_BASE = "http://localhost:9000"  # Should match Flask port

# In async_get/async_post, check response:
logger.debug(f"API Response: {response.status_code} - {response.text[:200]}")
```

#### **Logic Layer (Flask/Python)**
Symptoms:
- Route crashes with traceback
- Payload validation fails
- Business logic errors (wrong P&L calculation)
- Database query errors

**Quick Check:**
```python
# In scripts/api_server.py, check logs:
tail -f logs/api_server.log | grep "TraceID"
# Look for 500 errors and exception tracebacks
```

#### **Data Layer (SQLite/Upstox)**
Symptoms:
- `database is locked` errors (concurrent writes)
- API rate limits (429 errors)
- Expired OAuth tokens (401 errors)
- Missing data (empty query results)

**Quick Check:**
```bash
# Check database
sqlite3 market_data.db "SELECT COUNT(*) FROM ohlc_data"

# Check API token
sqlite3 market_data.db "SELECT token_expiry FROM oauth_tokens ORDER BY id DESC LIMIT 1"
```

---

### Step 2: 💥 Common Failure Patterns (Check These First)

#### **Pattern 1: State Sync (NiceGUI state not updating)**
**🔴 The Error:** UI shows stale data after successful API call

**🧐 Root Cause:** NiceGUI components not refreshed after async operation

**✅ The Fix:**
```python
# BEFORE (Bug):
async def load_data():
    data = await async_get("/api/positions")
    # UI not updated!

# AFTER (Fix):
@ui.refreshable
def positions_table(data):
    # Render table
    pass

async def load_data():
    data = await async_get("/api/positions")
    positions_table.refresh()  # Trigger UI update
```

**🛡️ Prevention:** Always use `@ui.refreshable` decorators and call `.refresh()` after async updates

#### **Pattern 2: Token Expiry**
**🔴 The Error:** API returns 401 Unauthorized from Upstox

**🧐 Root Cause:** OAuth token expired (tokens last 24 hours)

**✅ The Fix:**
```python
# Remind user to re-authenticate
ui.notify("Session expired. Please re-authenticate.", type="negative")
ui.navigate.to("/authenticate")
```

**🛡️ Prevention:** Implement auto-refresh logic in AuthManager or periodic token check

#### **Pattern 3: Concurrency - SQLite Locks**
**🔴 The Error:** `database is locked` during high-frequency writes

**🧐 Root Cause:** Multiple processes writing to SQLite simultaneously

**✅ The Fix:**
```python
# Add retry logic with exponential backoff
import time
max_retries = 5
for attempt in range(max_retries):
    try:
        conn = sqlite3.connect("market_data.db", timeout=10.0)
        # ... perform operation
        break
    except sqlite3.OperationalError as e:
        if "locked" in str(e) and attempt < max_retries - 1:
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
        else:
            raise
```

**🛡️ Prevention:** Use WAL mode: `PRAGMA journal_mode=WAL;` or migrate to PostgreSQL for production

#### **Pattern 4: Docker Networking**
**🔴 The Error:** Frontend can't reach backend API when running in Docker

**🧐 Root Cause:** Using `localhost` instead of Docker service name or `host.docker.internal`

**✅ The Fix:**
```python
# In docker-compose.yml environment or dashboard_ui/state.py:
# BEFORE (Bug):
API_BASE = "http://localhost:9000"

# AFTER (Fix - Docker):
API_BASE = os.getenv("API_BASE", "http://backend:9000")  # Use service name

# AFTER (Fix - Docker Desktop):
API_BASE = "http://host.docker.internal:9000"
```

**🛡️ Prevention:** Use environment variables for API_BASE and configure differently for Docker vs local

#### **Pattern 5: Async Awareness - Blocking Operations**
**🔴 The Error:** UI freezes when button is clicked

**🧐 Root Cause:** Using blocking synchronous function in NiceGUI event handler

**✅ The Fix:**
```python
# BEFORE (Bug - freezes UI):
def on_download_click():
    time.sleep(10)  # BLOCKS entire UI thread!
    download_data()

# AFTER (Fix 1 - use asyncio):
async def on_download_click():
    await asyncio.sleep(10)  # Non-blocking
    await run.io_bound(download_data)  # Run sync code in thread pool

# AFTER (Fix 2 - use run.io_bound for CPU-bound work):
async def on_download_click():
    result = await run.io_bound(heavy_calculation, data)
```

**🛡️ Prevention:** 
- **NEVER** use `time.sleep()` in NiceGUI - use `await asyncio.sleep()`
- **ALWAYS** wrap blocking I/O in `await run.io_bound()`
- **ALWAYS** make event handlers `async def` if they do I/O

---

### Step 3: 🛠️ The Fix Format

For every error found, provide the solution in this structure:

**Template:**
```
🔴 The Error: [One-sentence summary of what broke]

🧐 Root Cause: [Technical deep dive - why it broke]

✅ The Fix: [The exact corrected code block]

🛡️ Prevention: [Quick tip to prevent this from happening again]
```

**Example:**
```
🔴 The Error: Positions table shows 0% P&L despite 10% price movement

🧐 Root Cause: current_price column in database not updating because 
the price update job is not scheduled. The calculate_pnl() function 
uses stale prices from initial entry.

✅ The Fix:
# In paper_trading.py, update_position_prices():
def update_position_prices():
    positions = get_all_positions()
    for pos in positions:
        current_price = fetch_live_price(pos.symbol)  # API call
        pos.current_price = current_price
        pos.pnl = (current_price - pos.entry_price) * pos.quantity
        db.session.commit()
    logger.info(f"Updated {len(positions)} position prices")

# Schedule this job to run every minute
scheduler.add_job(update_position_prices, 'interval', minutes=1)

🛡️ Prevention: Always implement scheduled jobs for real-time data 
updates. Add monitoring to alert if jobs stop running.
```

---

### Step 4: Triage & Hypothesis (The "Sherlock Scan")

**Context:** Don't guess. Deduce.

**For Backend Errors:**
1. **Check Logs First:**
   ```bash
   tail -f logs/data_downloader.log  # Data fetch errors
   tail -f logs/api_server.log       # API endpoint errors
   tail -f logs/paper_trading.log    # Order execution errors
   ```

2. **Parse & Rank Hypotheses:**
   ```
   Example Error: "Portfolio P&L is -₹50,000 but positions show profit"
   
   Hypotheses (ranked):
   [90%] P&L calculation bug - summing unrealized + realized incorrectly
   [70%] Database has stale current_price - not updating from API
   [30%] Frontend formatting error - displaying negative of actual value
   [10%] Timezone mismatch - using wrong day's closing price
   ```

3. **Evidence Collection:**
   ```python
   # Add to suspectcode:
   logger.debug(f"P&L Calc: unrealized={unrealized}, realized={realized}, total={total}")
   logger.debug(f"DB current_price={pos.current_price}, API price={api_price}")
   ```

### Step 5: Isolation & Reproduction (The "Clean Room")

**Backend Isolation:**
```python
# Create: scripts/repro_bug.py
import sys
sys.path.insert(0, '.')
from scripts.data_downloader import StockDownloader

# Minimal repro - just the failing part
downloader = StockDownloader()
result = downloader.download_and_process(
    symbols=['INFY'],
    start_date='2025-01-01',
    end_date='2025-01-31',
    interval='1d'
)
print(f"Result: {result}")  # Should show gap detection issue
```

**Frontend Isolation (NiceGUI):**
```python
# Create: dashboard_ui/debug/test_positions.py
from nicegui import ui, run
from ..state import async_get

@ui.page('/debug/positions')
async def debug_positions_page():
    """Minimal reproduction of positions bug"""
    
    # Log every state change
    async def load_positions():
        print('[DEBUG] Loading positions...')
        data = await async_get('/api/positions')
        print(f'[DEBUG] Received data: {data}')
        return data
    
    # Test the component
    positions = await load_positions()
    ui.label(f'Positions: {positions}')
    
    # Re-render on button click
    @ui.refreshable
    def positions_display():
        ui.json(positions)
    
    ui.button('Refresh', on_click=lambda: positions_display.refresh())
```

**Database Isolation:**
```sql
-- Test query in SQLite directly
SELECT symbol, entry_price, current_price, pnl 
FROM paper_positions 
WHERE pnl < 0 AND current_price > entry_price;
-- If this returns rows, P&L calculation is broken
```

**API Isolation:**
```bash
# Test API endpoint directly with curl
curl -X GET http://localhost:9000/api/positions \
  -H "Content-Type: application/json" \
  -v

# Should return JSON array of positions
# Check: Status code, response body, headers
```

---

### Step 6: Omniscient Instrumentation (The "Trace Bullets")

**Request Tracing (Flask API):**
```python
# Already implemented in scripts/api_server.py!
import uuid
from flask import request, g

@app.before_request
def inject_trace_id():
    g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])
    logger.info(f"[TraceID: {g.trace_id}] {request.method} {request.path}")

@app.after_request
def log_response(response):
    logger.info(f"[TraceID: {g.trace_id}] Response: {response.status_code}")
    response.headers['X-Trace-ID'] = g.trace_id
    return response

# In route handlers:
@app.route('/api/portfolio')
def get_portfolio():
    logger.debug(f"[TraceID: {g.trace_id}] Fetching portfolio from database")
    # ... rest of code
```

**State Snapshots (Python):**
```python
# Add to critical functions in paper_trading.py
def calculate_pnl(position):
    try:
        unrealized = (position.current_price - position.entry_price) * position.quantity
        logger.debug(f"P&L Calc: entry={position.entry_price}, current={position.current_price}, qty={position.quantity}, result={unrealized}")
        return unrealized
    except Exception as e:
        # DUMP EVERYTHING
        dump_state({
            'position': position.__dict__,
            'locals': locals(),
            'timestamp': datetime.now().isoformat()
        }, f"crash_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        raise

def dump_state(state_dict, filename):
    import json
    Path('debug_dumps').mkdir(exist_ok=True)
    with open(f"debug_dumps/{filename}", 'w') as f:
        json.dump(state_dict, f, indent=2, default=str)
    logger.error(f"State dumped to {filename}")
```

**NiceGUI State Tracing:**
```python
# Add to dashboard_ui/state.py for debugging
import logging
logger = logging.getLogger(__name__)

async def async_get(endpoint: str, timeout: int = 5) -> Dict[str, Any]:
    logger.debug(f"[API] Calling GET {API_BASE}{endpoint}")
    try:
        response = await run.io_bound(
            requests.get, f"{API_BASE}{endpoint}", timeout=timeout
        )
        logger.debug(f"[API] GET {endpoint} -> Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"[API] Response data type: {type(data)}, length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
            return data
        else:
            logger.error(f"[API] Error {response.status_code}: {response.text[:200]}")
            return {"error": f"Status {response.status_code}"}
    except Exception as e:
        logger.error(f"[API] Exception calling {endpoint}: {str(e)}", exc_info=True)
        return {"error": str(e)}

# Add to UI components for reactivity debugging
@ui.refreshable
def positions_table(positions_data):
    logger.debug(f"[UI] Rendering positions_table with {len(positions_data)} positions")
    # ... render logic
    logger.debug("[UI] positions_table render complete")
```

**Component Lifecycle Tracing (NiceGUI):**
```python
# In dashboard_ui/pages/positions.py
async def load_positions_data():
    """Load positions with full tracing"""
    logger.info("[LIFECYCLE] load_positions_data() called")
    
    try:
        positions_data = await async_get("/api/positions")
        logger.info(f"[LIFECYCLE] Received {len(positions_data) if isinstance(positions_data, list) else 'error'}")
        
        # Clear and re-render container
        positions_container.clear()
        logger.debug("[LIFECYCLE] Container cleared")
        
        with positions_container:
            if "error" in positions_data:
                logger.error(f"[LIFECYCLE] Error in data: {positions_data['error']}")
                # ... render error UI
            elif isinstance(positions_data, list):
                logger.info(f"[LIFECYCLE] Rendering {len(positions_data)} positions")
                # ... render positions
        
        logger.info("[LIFECYCLE] load_positions_data() complete")
    except Exception as e:
        logger.error(f"[LIFECYCLE] Exception in load_positions_data: {str(e)}", exc_info=True)
        raise
```
```

**OHLC Data Validation Logging:**
```python
# Already in data_downloader.py - enhance it:
def validate_ohlc(self, df: pd.DataFrame) -> pd.DataFrame:
    logger.debug(f"[VALIDATION] Validating {len(df)} rows of OHLC data")
    
    # Log every single violation
    invalid_high_low = df[df['high'] < df['low']]
    if len(invalid_high_low) > 0:
        for idx, row in invalid_high_low.iterrows():
            logger.warning(f"[VIOLATION] Row {idx}: {row['symbol']} {row['datetime']} - high={row['high']} < low={row['low']}")
    
    # Log data range
    logger.info(f"[VALIDATION] Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    logger.info(f"[VALIDATION] Symbols: {df['symbol'].unique().tolist()}")
    
    return df
```

---

### Step 7: Strategy Selection (The "Weapon Rack")

**For Trading Logic Bugs:**
- **Strategy:** Assertion Injection
- **Example:**
  ```python
  # In paper_trading.py
  def place_order(symbol, side, quantity, price):
      assert quantity > 0, f"Invalid quantity: {quantity}"
      assert price > 0, f"Invalid price: {price}"
      assert side in ['buy', 'sell'], f"Invalid side: {side}"
      
      # Check portfolio balance
      cash = get_cash_available()
      if side == 'buy':
          required = quantity * price
          assert cash >= required, f"Insufficient funds: need {required}, have {cash}"
  ```

**For Intermittent API Failures:**
- **Strategy:** Chaos Engineering
- **Example:**
  ```python
  # Add to api_server.py for testing
  import random
  
  @app.route('/api/portfolio')
  def get_portfolio():
      # Inject random failures in dev mode
      if os.getenv('CHAOS_MODE') == 'true' and random.random() < 0.2:
          logger.warning("[CHAOS] Injecting random API failure")
          return jsonify({'error': 'Chaos injection'}), 500
      
      # Normal logic
      return jsonify(portfolio_data)
  ```

**For State Synchronization Issues:**
- **Strategy:** Time Travel (Event Replay)
- **Example:**
  ```python
  # Record all state changes
  class StateRecorder:
      def __init__(self):
          self.events = []
      
      def record(self, event_type, data):
          self.events.append({
              'timestamp': datetime.now().isoformat(),
              'type': event_type,
              'data': data
          })
      
      def replay(self):
          for event in self.events:
              logger.info(f"Replaying: {event['type']} at {event['timestamp']}")
              # Re-execute the action
  ```

**For Frontend Rendering Issues (NiceGUI):**
- **Strategy:** Component Lifecycle Tracing + Refresh Debugging
- **Example:**
  ```python
  # Track when components are created and refreshed
  @ui.refreshable
  def positions_table(positions_data):
      refresh_count = getattr(positions_table, '_refresh_count', 0)
      positions_table._refresh_count = refresh_count + 1
      logger.debug(f"[RENDER] positions_table refresh #{refresh_count}, data items: {len(positions_data)}")
      
      # ... render logic
      
      logger.debug(f"[RENDER] positions_table refresh #{refresh_count} complete")
  
  # Track event handler calls
  async def on_refresh_click():
      logger.info("[EVENT] Refresh button clicked")
      try:
          data = await async_get("/api/positions")
          logger.info(f"[EVENT] Got data, triggering refresh")
          positions_table.refresh()
          logger.info("[EVENT] Refresh complete")
      except Exception as e:
          logger.error(f"[EVENT] Error during refresh: {str(e)}", exc_info=True)
  ```

**For Async/Blocking Issues (NiceGUI):**
- **Strategy:** Async Awareness Checks
- **Example:**
  ```python
  # WRONG - Will freeze UI:
  def slow_operation():
      time.sleep(5)  # ❌ BLOCKS ENTIRE UI
      result = heavy_calculation()
      return result
  
  # RIGHT - Non-blocking:
  async def slow_operation():
      await asyncio.sleep(5)  # ✅ Non-blocking wait
      result = await run.io_bound(heavy_calculation)  # ✅ Run in thread pool
      return result
  
  # Use in button handler:
  ui.button('Calculate', on_click=slow_operation)  # Must be async def!
  ```

### Step 8: Fix & Verify (The "Double Tap")

1. **Implement Fix:**
   ```python
   # BEFORE (Bug):
   def calculate_pnl(position):
       return position.quantity * position.current_price - position.entry_price  # WRONG
   
   # AFTER (Fix):
   def calculate_pnl(position):
       return position.quantity * (position.current_price - position.entry_price)  # CORRECT
   ```

2. **Validation (Test Script):**
   ```python
   # tests/test_pnl_calculation.py
   def test_pnl_calculation():
       position = Position(
           symbol='INFY',
           quantity=10,
           entry_price=1450,
           current_price=1500
       )
       
       pnl = calculate_pnl(position)
       expected = 10 * (1500 - 1450)  # 500
       
       assert pnl == expected, f"Expected {expected}, got {pnl}"
       print("✅ P&L calculation test passed")
   ```

3. **Regression Test:**
   ```python
   # Add to tests/test_suite.py
   pytest.mark.parametrize("entry,current,qty,expected", [
       (1450, 1500, 10, 500),   # Profit
       (1500, 1450, 10, -500),  # Loss
       (1450, 1450, 10, 0),     # Break-even
   ])
   def test_pnl_scenarios(entry, current, qty, expected):
       position = Position(entry_price=entry, current_price=current, quantity=qty)
       assert calculate_pnl(position) == expected
   ```

---

## ⚠️ CRITICAL RULES

### 🔴 Async Awareness (NiceGUI-Specific)

**Remember: NiceGUI is async by nature. Violating async patterns will FREEZE the entire UI.**

#### Rule 1: NEVER use blocking operations in event handlers
```python
# ❌ WRONG - Freezes UI
def on_button_click():
    time.sleep(5)  # BLOCKS ENTIRE UI THREAD
    result = requests.get('http://api.example.com')  # BLOCKS
    heavy_calculation()  # BLOCKS

# ✅ CORRECT - Non-blocking
async def on_button_click():
    await asyncio.sleep(5)  # Non-blocking wait
    result = await run.io_bound(requests.get, 'http://api.example.com')  # Run in thread pool
    result = await run.io_bound(heavy_calculation)  # Run in thread pool
```

#### Rule 2: Always use `await run.io_bound()` for I/O operations
```python
# ❌ WRONG
def load_data():
    response = requests.get(f"{API_BASE}/api/data")
    return response.json()

# ✅ CORRECT
async def load_data():
    response = await run.io_bound(requests.get, f"{API_BASE}/api/data")
    return response.json()
```

#### Rule 3: Event handlers must be `async def` if they do I/O
```python
# ❌ WRONG
ui.button('Load', on_click=lambda: load_data())  # Will block!

# ✅ CORRECT
async def handle_load():
    data = await load_data()
    update_ui(data)

ui.button('Load', on_click=handle_load)  # async handler
```

#### Rule 4: Use `@ui.refreshable` + `.refresh()` for reactive updates
```python
# ❌ WRONG - UI doesn't update
async def refresh_positions():
    positions = await async_get("/api/positions")
    # UI not updated!

# ✅ CORRECT
@ui.refreshable
def positions_display(positions):
    # Render positions
    pass

async def refresh_positions():
    positions = await async_get("/api/positions")
    positions_display.refresh()  # Trigger UI update
```

### 🔴 API Consistency

**Frontend (NiceGUI) and Backend (Flask) must have matching data contracts.**

#### Rule 1: Check API_BASE matches Flask port
```python
# dashboard_ui/state.py
API_BASE = "http://localhost:9000"  # Must match Flask port in scripts/api_server.py

# scripts/api_server.py  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)  # Must match API_BASE
```

#### Rule 2: Response formats must match expectations
```python
# Backend (Flask) - scripts/api_server.py
@app.route('/api/positions')
def get_positions():
    positions = query_positions()
    return jsonify([  # Return list of dicts
        {
            'symbol': p.symbol,
            'quantity': p.quantity,
            'pnl': float(p.pnl),  # Convert Decimal to float!
            'entry_price': float(p.entry_price),
            'current_price': float(p.current_price)
        }
        for p in positions
    ])

# Frontend (NiceGUI) - dashboard_ui/pages/positions.py
async def load_positions():
    data = await async_get("/api/positions")
    if isinstance(data, list):  # Expect list
        for position in data:
            assert 'symbol' in position  # Validate keys exist
            assert 'pnl' in position
```

#### Rule 3: Handle errors consistently
```python
# Backend - Always return error dict
@app.route('/api/positions')
def get_positions():
    try:
        positions = query_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Frontend - Always check for 'error' key
async def load_positions():
    data = await async_get("/api/positions")
    if 'error' in data:
        ui.notify(f"Error: {data['error']}", type='negative')
        return []
    return data
```

### 🔴 Tone: Technical, Precise, Authoritative, Yet Helpful

When debugging:
- **Be specific:** "P&L calculation in line 245 uses wrong formula" (not "P&L is broken")
- **Show evidence:** Include log excerpts, stack traces, data dumps
- **Explain why:** Root cause analysis, not just symptoms
- **Provide fixes:** Exact code snippets with before/after
- **Add prevention:** How to avoid this in the future

**Example Response:**
```
🔴 The Error: Positions table shows empty despite 5 active positions in database

🧐 Root Cause: The /api/positions endpoint is running on port 8000, but 
dashboard_ui/state.py has API_BASE="http://localhost:9000". The frontend is 
calling the wrong port, so requests.get() times out after 5 seconds and 
returns {"error": "Connection refused"}.

✅ The Fix:
# In dashboard_ui/state.py, change:
API_BASE = "http://localhost:9000"  # ❌ Wrong port
# To:
API_BASE = "http://localhost:8000"  # ✅ Matches Flask port

# Verify:
curl http://localhost:8000/api/positions
# Should return: [{"symbol": "INFY", "quantity": 10, ...}]

🛡️ Prevention: Use environment variables for API_BASE to avoid hardcoding:
# dashboard_ui/state.py
import os
API_BASE = os.getenv("API_BASE", "http://localhost:9000")

# Then set in .env or docker-compose.yml:
API_BASE=http://localhost:8000  # or http://backend:8000 in Docker
```

---

## 🧰 Platform-Specific Debug Tools

### Backend Debugging (Flask)
```bash
# Enable debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG

# Run with verbose logging
python scripts/api_server.py 2>&1 | tee logs/debug_session.log

# Database inspection
sqlite3 market_data.db
.schema paper_positions
SELECT * FROM paper_positions WHERE pnl < 0;

# Check specific TraceID across all logs
grep "TraceID: abc123" logs/*.log
```

### Frontend Debugging (NiceGUI)
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python nicegui_dashboard.py

# Check browser console for JavaScript errors:
# - Open DevTools (F12)
# - Look for CORS errors, network failures
# - Check WebSocket connections

# Monitor NiceGUI logs
tail -f logs/nicegui.log | grep -E "ERROR|WARNING|LIFECYCLE"
```

### Integration Debugging (Full Stack)
```bash
# Terminal 1: Backend with trace logging
export TRACE_REQUESTS=true
export LOG_LEVEL=DEBUG
python scripts/api_server.py

# Terminal 2: Frontend with verbose logging
export LOG_LEVEL=DEBUG  
python nicegui_dashboard.py

# Terminal 3: Monitor both logs with correlation
tail -f logs/*.log | grep -E "TraceID|ERROR|API"

# Terminal 4: Test API directly
curl -X GET http://localhost:9000/api/positions -H "X-Trace-ID: test123" -v
# Then search for test123 in backend logs
```

### Docker Debugging
```bash
# Check container logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Test network connectivity between containers
docker-compose exec frontend ping backend
docker-compose exec frontend curl http://backend:9000/api/health

# Check environment variables
docker-compose exec frontend env | grep API_BASE
docker-compose exec backend env | grep FLASK

# Inspect network
docker network inspect upstox-project_default
```

## 📊 Trading-Specific Debug Patterns

### Pattern 1: "Phantom P&L" Bug
**Symptom:** P&L shows 0% change despite price movement

**Debug Steps:**
1. Check if `current_price` is updating:
   ```sql
   SELECT symbol, entry_price, current_price, updated_at 
   FROM paper_positions 
   ORDER BY updated_at DESC;
   ```
2. Verify API is returning prices:
   ```python
   logger.debug(f"Yahoo API returned: {df[['symbol', 'close']].to_dict()}")
   ```
3. Check calculation:
   ```python
   logger.debug(f"P&L = {qty} * ({current} - {entry}) = {pnl}")
   ```

### Pattern 2: "Ghost Orders" Bug
**Symptom:** Orders appear in UI but not in database

**Debug Steps:**
1. Add request/response logging:
   ```python
   # Backend - scripts/api_server.py
   @app.route('/api/orders', methods=['POST'])
   def place_order():
       logger.info(f"[TraceID: {g.trace_id}] Request body: {request.json}")
       result = execute_order(request.json)
       logger.info(f"[TraceID: {g.trace_id}] Order result: {result}")
       return jsonify(result)
   ```
2. Check frontend is sending correct data:
   ```python
   # Frontend - dashboard_ui/pages/orders_alerts.py
   async def place_order(order_data):
       logger.debug(f'[API] Sending order: {order_data}')
       response = await run.io_bound(
           requests.post, 
           f"{API_BASE}/orders", 
           json=order_data
       )
       logger.debug(f'[API] Order response: {response.status_code} - {response.text}')
       return response.json()
   ```
3. Verify database commit:
   ```python
   # In order execution code
   db.session.add(new_order)
   db.session.commit()  # Must commit!
   logger.info(f"Order {new_order.id} saved to database")
   ```

### Pattern 3: "Data Gap" Detection
**Symptom:** Missing candles in OHLC data

**Debug Steps:**
1. Already implemented in `data_downloader.py`:
   ```python
   gaps = self.detect_gaps(df, interval='1d')
   for gap in gaps:
       logger.warning(f"Gap: {gap['start']} to {gap['end']}, missing {gap['missing_periods']} periods")
   ```
2. Trigger backfill:
   ```python
   if len(gaps) > 0:
       logger.info("Triggering backfill for detected gaps")
       backfill_gaps(gaps)
   ```

## 🛠️ Execution Instructions

**When you invoke this protocol ("Debug this error"):**

1. **I will perform layer identification** to determine if it's UI, Communication, Logic, or Data layer
2. **I will check common failure patterns** (State Sync, Token Expiry, SQLite Locks, Docker Networking, Async Awareness)
3. **I will provide structured fixes** using the format: 🔴 Error → 🧐 Root Cause → ✅ Fix → 🛡️ Prevention
4. **I will instrument** the suspected code with trace_id logging and state snapshots
5. **I will create** a `repro_debug.py` to isolate the fault
6. **I will verify** with both unit tests and integration tests
7. **I will add** the scenario to the permanent test suite

**Auto-Triggers:**
- Any Flask 500 error → Full trace logging
- Any OHLC validation failure → State dump
- Any P&L calculation error → Hypothesis ranking
- Any NiceGUI state issue → Component lifecycle tracing
- Any blocking operation detected → Async awareness warning
- Any Docker networking issue → Container connectivity check

---

**Status:** ✅ ACTIVE  
**Visibility:** 👁️ OMNISCIENT  
**Protocol:** 🔥 GOD-TIER  
**Architecture:** NiceGUI (Frontend) + Flask (Backend) + SQLite (Database) + Docker  
**Version:** 2.0 (Updated for UPSTOX-PROJECT)
