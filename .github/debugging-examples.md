# Debugging Protocol - Real-World Examples

This document demonstrates the Full-Stack Debugging Protocol with actual scenarios from the UPSTOX-PROJECT.

---

## Example 1: UI Not Updating After API Call

### 🐛 Bug Report
**Symptom:** User clicks "Refresh Positions" button, but the positions table doesn't update even though the API returns new data.

### 🔍 Step 1: Layer Identification

**Layer:** UI Layer (NiceGUI) - binding/reactivity issue

**Evidence:**
- Backend logs show successful API call
- Data is returned correctly (verified with curl)
- UI remains unchanged

### 💥 Step 2: Check Common Failure Patterns

**Pattern Match:** State Sync (NiceGUI state not updating)

### 🛠️ Step 3: The Fix

**🔴 The Error:** Positions table shows stale data after successful API refresh

**🧐 Root Cause:** The `load_positions_data()` function updates data but doesn't trigger UI refresh. NiceGUI components need explicit `.refresh()` call on `@ui.refreshable` decorated functions.

**✅ The Fix:**

```python
# BEFORE (Bug):
async def load_positions_data():
    positions_data = await async_get("/api/positions")
    positions_container.clear()
    with positions_container:
        render_positions(positions_data)  # ❌ Not refreshable

# AFTER (Fix):
@ui.refreshable
def positions_table(positions_data):
    """Refreshable component for positions"""
    with ui.column().classes("w-full"):
        render_positions(positions_data)

async def load_positions_data():
    positions_data = await async_get("/api/positions")
    positions_table.refresh()  # ✅ Trigger refresh
```

**🛡️ Prevention:** 
- Always use `@ui.refreshable` for data-driven components
- Call `.refresh()` after async data updates
- Use container patterns for dynamic content

---

## Example 2: UI Freezes When Downloading Data

### 🐛 Bug Report
**Symptom:** When user clicks "Download Historical Data", the entire UI freezes for 30 seconds and becomes unresponsive.

### 🔍 Step 1: Layer Identification

**Layer:** UI Layer (NiceGUI) - blocking operation in async context

**Evidence:**
- Button click doesn't return immediately
- All other buttons become unresponsive
- Browser shows "Page Unresponsive" warning

### 💥 Step 2: Check Common Failure Patterns

**Pattern Match:** Async Awareness - Blocking Operations

### 🛠️ Step 3: The Fix

**🔴 The Error:** UI freezes during data download operation

**🧐 Root Cause:** The download function uses synchronous `requests.get()` directly in the event handler, which blocks the entire asyncio event loop. All UI updates are blocked until the download completes.

**✅ The Fix:**

```python
# BEFORE (Bug):
def on_download_click():
    ui.notify("Downloading...")
    response = requests.get(f"{API_BASE}/download/data", timeout=30)  # ❌ BLOCKS!
    data = response.json()
    ui.notify("Download complete!")

# AFTER (Fix):
async def on_download_click():
    ui.notify("Downloading...")
    # Run blocking I/O in thread pool
    response = await run.io_bound(
        requests.get, 
        f"{API_BASE}/download/data", 
        timeout=30
    )
    data = response.json()
    ui.notify("Download complete!")

# Usage:
ui.button('Download', on_click=on_download_click)  # ✅ async handler
```

**🛡️ Prevention:**
- NEVER use `time.sleep()` or blocking I/O directly in NiceGUI
- ALWAYS use `await run.io_bound()` for synchronous operations
- Make event handlers `async def` if they do I/O
- Test UI responsiveness during long operations

---

## Example 3: API Returns 500 Error

### 🐛 Bug Report
**Symptom:** Frontend shows "Error: Status 500" when trying to fetch positions. Backend logs show exception.

### 🔍 Step 1: Layer Identification

**Layer:** Logic Layer (Flask/Python) - route handler crash

**Evidence:**
```bash
# Backend log excerpt:
[TraceID: abc123] GET /api/positions
[TraceID: abc123] Unhandled exception: division by zero
Traceback (most recent call last):
  File "scripts/api_server.py", line 245, in get_positions
    pnl_pct = (position.pnl / position.entry_value) * 100
ZeroDivisionError: division by zero
[TraceID: abc123] Response: 500
```

### 🛠️ Step 3: The Fix

**🔴 The Error:** API crashes with ZeroDivisionError when calculating P&L percentage

**🧐 Root Cause:** Some positions have `entry_value = 0` (possible for certain corporate actions or stock splits). The P&L percentage calculation doesn't handle this edge case.

**✅ The Fix:**

```python
# BEFORE (Bug):
def get_positions():
    positions = Position.query.all()
    result = []
    for position in positions:
        pnl_pct = (position.pnl / position.entry_value) * 100  # ❌ Crashes if entry_value = 0
        result.append({
            'symbol': position.symbol,
            'pnl': position.pnl,
            'pnl_pct': pnl_pct
        })
    return jsonify(result)

# AFTER (Fix):
def get_positions():
    positions = Position.query.all()
    result = []
    for position in positions:
        # Safe division with None fallback
        if position.entry_value and position.entry_value != 0:
            pnl_pct = (position.pnl / position.entry_value) * 100
        else:
            pnl_pct = None  # ✅ Handle edge case
            
        result.append({
            'symbol': position.symbol,
            'pnl': float(position.pnl) if position.pnl else 0,
            'pnl_pct': pnl_pct
        })
    return jsonify(result)
```

**🛡️ Prevention:**
- Add validation for division operations
- Use assertions in development: `assert entry_value != 0`
- Add unit tests for edge cases
- Log warnings for unusual data

---

## Example 4: Docker Networking Issue

### 🐛 Bug Report
**Symptom:** Frontend works fine locally, but when running in Docker, it shows "Connection refused" errors when calling the backend API.

### 🔍 Step 1: Layer Identification

**Layer:** Communication Layer (HTTP/Requests) - Docker networking

**Evidence:**
```python
# Frontend log:
[API] Calling GET http://localhost:9000/api/positions
[API] Exception calling /api/positions: Connection refused
```

### 💥 Step 2: Check Common Failure Patterns

**Pattern Match:** Docker Networking

### 🛠️ Step 3: The Fix

**🔴 The Error:** Frontend container cannot reach backend API

**🧐 Root Cause:** `localhost` inside a Docker container refers to the container itself, not the host machine. Containers need to use the service name defined in `docker-compose.yml` to communicate.

**✅ The Fix:**

```python
# dashboard_ui/state.py

# BEFORE (Bug):
API_BASE = "http://localhost:9000"  # ❌ Wrong in Docker

# AFTER (Fix):
import os

# Use environment variable with fallback
API_BASE = os.getenv("API_BASE", "http://localhost:9000")

# In docker-compose.yml:
services:
  frontend:
    environment:
      - API_BASE=http://backend:9000  # ✅ Use service name
  
  backend:
    ports:
      - "9000:9000"
```

**Alternative for Docker Desktop:**
```python
# For Docker Desktop on Mac/Windows
API_BASE = "http://host.docker.internal:9000"
```

**🛡️ Prevention:**
- Always use environment variables for URLs
- Document environment variables in `.env.example`
- Test in Docker environment before deployment
- Use service names in `docker-compose.yml`

---

## Example 5: SQLite Database Lock

### 🐛 Bug Report
**Symptom:** API intermittently returns "database is locked" errors during market hours when multiple requests are happening.

### 🔍 Step 1: Layer Identification

**Layer:** Data Layer (SQLite) - concurrency issue

**Evidence:**
```python
# Backend log:
sqlite3.OperationalError: database is locked
```

### 💥 Step 2: Check Common Failure Patterns

**Pattern Match:** Concurrency - SQLite Locks

### 🛠️ Step 3: The Fix

**🔴 The Error:** SQLite database locks during concurrent writes

**🧐 Root Cause:** Multiple processes/threads trying to write to SQLite simultaneously. SQLite only supports one writer at a time, and the default timeout (5 seconds) is being exceeded.

**✅ The Fix:**

```python
# BEFORE (Bug):
conn = sqlite3.connect("market_data.db")
cursor = conn.cursor()
cursor.execute("INSERT INTO positions ...")
conn.commit()

# AFTER (Fix 1 - Add retry logic):
import time

def connect_with_retry(db_path, max_retries=5):
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            else:
                raise

# AFTER (Fix 2 - Enable WAL mode):
conn = sqlite3.connect("market_data.db")
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
conn.execute("PRAGMA busy_timeout=10000")  # 10 second timeout
```

**🛡️ Prevention:**
- Enable WAL mode for better concurrency
- Increase timeout for database connections
- Consider PostgreSQL for production (unlimited concurrent readers/writers)
- Use connection pooling
- Add retry logic with exponential backoff

---

## Example 6: Token Expiry Not Handled

### 🐛 Bug Report
**Symptom:** User gets "401 Unauthorized" errors from Upstox API after 24 hours. They have to manually re-authenticate.

### 🔍 Step 1: Layer Identification

**Layer:** Logic Layer + Data Layer - authentication token management

**Evidence:**
```python
# Backend log:
[API] Upstox API returned 401: Unauthorized
```

### 💥 Step 2: Check Common Failure Patterns

**Pattern Match:** Token Expiry

### 🛠️ Step 3: The Fix

**🔴 The Error:** Upstox API calls fail with 401 after token expires

**🧐 Root Cause:** OAuth tokens from Upstox expire after 24 hours. The application doesn't check token expiry before making API calls and doesn't handle 401 errors gracefully.

**✅ The Fix:**

```python
# In scripts/auth_manager.py (or equivalent)

from datetime import datetime, timedelta

class AuthManager:
    def get_valid_token(self):
        """Get a valid access token, refreshing if necessary"""
        token_data = self.get_token_from_db()
        
        # Check if token is expired
        expiry_time = datetime.fromisoformat(token_data['expiry'])
        if datetime.now() >= expiry_time - timedelta(minutes=5):
            # Token expired or expiring soon, refresh it
            logger.info("Token expired, refreshing...")
            token_data = self.refresh_token()
        
        return token_data['access_token']
    
    def refresh_token(self):
        """Refresh the access token"""
        refresh_token = self.get_refresh_token_from_db()
        
        response = requests.post(
            'https://api.upstox.com/v2/login/authorization/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': os.getenv('UPSTOX_API_KEY'),
                'client_secret': os.getenv('UPSTOX_API_SECRET')
            }
        )
        
        new_token = response.json()
        self.save_token_to_db(new_token)
        return new_token

# In API calls:
def fetch_positions():
    token = auth_manager.get_valid_token()  # ✅ Always get valid token
    response = requests.get(
        'https://api.upstox.com/v2/portfolio/positions',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 401:
        # Token might have been revoked, force refresh
        logger.warning("Got 401, forcing token refresh")
        auth_manager.force_refresh()
        token = auth_manager.get_valid_token()
        response = requests.get(
            'https://api.upstox.com/v2/portfolio/positions',
            headers={'Authorization': f'Bearer {token}'}
        )
    
    return response.json()
```

**🛡️ Prevention:**
- Always check token expiry before API calls
- Implement automatic token refresh
- Handle 401 errors with retry logic
- Store token expiry in database
- Set up monitoring for auth failures

---

## Summary of Debugging Steps

For any error, follow this checklist:

1. **Layer Identification** - Which layer is failing? (UI, Communication, Logic, Data)
2. **Check Common Patterns** - Does it match a known failure pattern?
3. **Structured Fix** - Use the format: 🔴 Error → 🧐 Root Cause → ✅ Fix → 🛡️ Prevention
4. **Add Instrumentation** - TraceID, logging, state dumps
5. **Create Reproduction** - Minimal `repro_debug.py` script
6. **Verify Fix** - Unit tests + integration tests
7. **Add Regression Test** - Prevent the bug from returning

---

**For the complete debugging protocol, see:** [debugging-protocol.md](debugging-protocol.md)
