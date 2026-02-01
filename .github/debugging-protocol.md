# God-Mode Debugger - Upstox Trading Platform

> "It's not a bug. It's an undocumented feature... until we trace it, isolate it, and crush it."

## 🛡️ Mission
Grant omniscient visibility into the multi-layered trading platform: Python backend (Flask + SQLite), React frontend (TypeScript + Zustand), Yahoo Finance API, and real-time P&L calculations.

## ⚡ When to Use This Protocol

### Backend Bugs (Python)
- **ALWAYS** when Flask API returns 500 errors
- **ALWAYS** when OHLC validation fails (high < low detected)
- **ALWAYS** when paper trading P&L is incorrect
- **ALWAYS** when Yahoo Finance returns empty data
- **ALWAYS** when database constraints are violated
- **ALWAYS** when strategy signals don't match expected logic

### Frontend Bugs (React)
- **ALWAYS** when Zustand state is stale or missing
- **ALWAYS** when API calls fail silently
- **ALWAYS** when components render incorrect data
- **ALWAYS** when P&L colors don't match values (green on loss)
- **ALWAYS** when loading states never resolve

### Integration Bugs
- **ALWAYS** when backend works but frontend shows errors
- **ALWAYS** when CORS errors appear
- **ALWAYS** when data format mismatches (backend sends `datetime`, frontend expects `timestamp`)

## 📜 The God Protocol (Unified Workflow)

### Phase 1: Triage & Hypothesis (The "Sherlock Scan")

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

### Phase 2: Isolation & Reproduction (The "Clean Room")

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

**Frontend Isolation:**
```tsx
// Create: src/debug/TestComponent.tsx
import { usePortfolio } from '../hooks/usePortfolio';

export const DebugPortfolio = () => {
  const { portfolio, isLoading } = usePortfolio();
  
  // Log every render
  console.log('[RENDER]', { portfolio, isLoading });
  
  return <pre>{JSON.stringify(portfolio, null, 2)}</pre>;
};
```

**Database Isolation:**
```sql
-- Test query in SQLite directly
SELECT symbol, entry_price, current_price, pnl 
FROM paper_positions 
WHERE pnl < 0 AND current_price > entry_price;
-- If this returns rows, P&L calculation is broken
```

### Phase 3: Omniscient Instrumentation (The "Trace Bullets")

**Request Tracing (Flask API):**
```python
# Add to scripts/api_server.py
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

**React State Tracing:**
```typescript
// Add to stores/portfolioStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export const usePortfolioStore = create<PortfolioStore>()(
  devtools(
    (set) => ({
      portfolio: null,
      isLoading: false,
      error: null,
      setPortfolio: (portfolio) => {
        console.log('[STORE] setPortfolio called:', portfolio);
        set({ portfolio, error: null });
      },
      setError: (error) => {
        console.error('[STORE] setError called:', error);
        set({ error, isLoading: false });
      },
    }),
    { name: 'PortfolioStore' } // Shows in Redux DevTools
  )
);
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

### Phase 4: Strategy Selection (The "Weapon Rack")

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

**For Frontend Rendering Issues:**
- **Strategy:** Component Lifecycle Tracing
- **Example:**
  ```tsx
  import { useEffect } from 'react';
  
  export const PositionsTable = () => {
    const { positions, isLoading } = usePositions();
    
    useEffect(() => {
      console.log('[PositionsTable] Mounted');
      return () => console.log('[PositionsTable] Unmounted');
    }, []);
    
    useEffect(() => {
      console.log('[PositionsTable] positions changed:', positions.length);
    }, [positions]);
    
    useEffect(() => {
      console.log('[PositionsTable] isLoading changed:', isLoading);
    }, [isLoading]);
    
    // Rest of component
  };
  ```

### Phase 5: Fix & Verify (The "Double Tap")

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

## 🧰 Platform-Specific Debug Tools

### Backend Debugging
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
```

### Frontend Debugging
```bash
# Enable source maps (already in Vite)
npm run dev

# Browser console:
# - Redux DevTools for Zustand
# - Network tab for API calls
# - React DevTools for component tree
```

### Integration Debugging
```bash
# Terminal 1: Backend with trace logging
export TRACE_REQUESTS=true
python scripts/api_server.py

# Terminal 2: Frontend with network logging
npm run dev

# Terminal 3: Monitor logs
tail -f logs/*.log | grep TraceID
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
   @app.route('/api/orders', methods=['POST'])
   def place_order():
       logger.info(f"[TraceID: {g.trace_id}] Request body: {request.json}")
       result = execute_order(request.json)
       logger.info(f"[TraceID: {g.trace_id}] Order result: {result}")
       return jsonify(result)
   ```
2. Check frontend is sending correct data:
   ```typescript
   const placeOrder = async (order: Order) => {
     console.log('[API] Sending order:', order);
     const response = await axios.post('/api/orders', order);
     console.log('[API] Order response:', response.data);
   };
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

1. **I will analyze** using the 5 Whys technique
2. **I will instrument** the suspected code with trace_id logging and state snapshots
3. **I will create** a `repro_debug.py` to isolate the fault
4. **I will implement** the fix with assertions and validation
5. **I will verify** with both unit tests and integration tests
6. **I will add** the scenario to the permanent test suite

**Auto-Triggers:**
- Any 500 error → Full trace logging
- Any data validation failure → State dump
- Any test failure → Repro script generation
- Any user-reported bug → Hypothesis ranking

---

**Status:** ACTIVE  
**Visibility:** OMNISCIENT  
**Protocol:** GOD-TIER  
**Platform:** Upstox Trading (Python + React + SQLite)
