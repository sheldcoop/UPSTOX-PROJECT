# 🚀 Zero-Error Architect - Quick Start Guide

**For Developers & AI Assistants**

---

## 30-Second Overview

The Zero-Error Architect is a safety system that prevents:
- ❌ UI freezing in NiceGUI
- ❌ Port mismatches between frontend/backend
- ❌ Missing dependencies
- ❌ Blocking code that crashes the app
- ❌ API v2/v3 incompatibilities

---

## Installation

```bash
# 1. Navigate to project directory
cd UPSTOX-PROJECT

# 2. Make scripts executable
chmod +x scripts/check_health.py
chmod +x scripts/preflight_check.py

# 3. Run health check
python scripts/check_health.py

# Expected output: Confidence score and system status
```

---

## Daily Workflow

### Before Starting Work
```bash
# Check system health
python scripts/check_health.py --quick
```

### Before Committing Code
```bash
# Run pre-flight checks
python scripts/preflight_check.py

# Should show: "✅ PRE-FLIGHT CHECK PASSED"
```

### After Adding Dependencies
```bash
# Verify dependencies
python scripts/preflight_check.py --dependency

# Then update requirements.txt
echo "new-package>=1.0.0" >> requirements.txt
```

### When Writing NiceGUI Code
```bash
# Check for blocking patterns
python scripts/preflight_check.py --nicegui
```

---

## Common Tasks

### Task 1: Add a New API Endpoint

```python
# 1. Write the endpoint in scripts/api_server.py
@app.route('/api/my-endpoint', methods=['GET'])
def my_endpoint():
    try:
        data = {'status': 'success', 'message': 'Hello!'}
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. Run health check
# $ python scripts/check_health.py

# 3. Test the endpoint
# $ curl http://localhost:8000/api/my-endpoint
```

### Task 2: Add a Frontend Button

```python
from scripts.utilities.async_helpers import safe_api_call, safe_notification

async def on_button_click():
    # Safe, non-blocking API call
    data = await safe_api_call('http://localhost:8000/api/my-endpoint')
    
    if 'error' in data:
        await safe_notification("Error occurred", type="error")
    else:
        await safe_notification("Success!", type="success")

# Add the button
ui.button('Click Me', on_click=on_button_click)
```

### Task 3: Fix a Blocking Operation

```python
# ❌ BEFORE (Blocks UI)
def load_data():
    import time
    time.sleep(2)
    return fetch_from_api()

# ✅ AFTER (Non-blocking)
from scripts.utilities.async_helpers import safe_sleep, safe_io_bound

async def load_data():
    await safe_sleep(2)
    return await safe_io_bound(fetch_from_api)
```

### Task 4: Database Query Without Freezing

```python
from scripts.utilities.async_helpers import safe_db_query

async def get_orders():
    def query():
        import sqlite3
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders LIMIT 10')
        return cursor.fetchall()
    
    orders = await safe_db_query(query)
    return orders
```

---

## CLI Reference

### Health Check
```bash
# Full check
python scripts/check_health.py

# Quick check (no API calls)
python scripts/check_health.py --quick

# Verbose output
python scripts/check_health.py --verbose

# JSON output (for CI/CD)
python scripts/check_health.py --json
```

**Exit Codes:**
- `0` = All passed ✅
- `1` = Warnings ⚠️
- `2` = Critical errors ❌

### Pre-Flight Check
```bash
# Full check
python scripts/preflight_check.py

# Integration only
python scripts/preflight_check.py --integration

# NiceGUI safety
python scripts/preflight_check.py --nicegui

# API v3 compliance
python scripts/preflight_check.py --api-v3

# Verbose output
python scripts/preflight_check.py --verbose
```

---

## Async Helpers Reference

### Import
```python
from scripts.utilities.async_helpers import (
    safe_sleep,
    safe_api_call,
    safe_notification,
    safe_io_bound,
    safe_cpu_bound,
    safe_db_query,
    AsyncTimer,
    async_event_handler
)
```

### Usage

#### 1. Safe Sleep
```python
# Instead of: time.sleep(2)
await safe_sleep(2)
```

#### 2. Safe API Call
```python
# Instead of: requests.get(url).json()
data = await safe_api_call('http://localhost:8000/api/data')
```

#### 3. Safe Notification
```python
# Instead of: ui.notify("Message")
await safe_notification("Message", type="success")
```

#### 4. Safe I/O Operation
```python
# For blocking I/O (file, network, DB)
result = await safe_io_bound(blocking_function, arg1, arg2)
```

#### 5. Safe CPU Operation
```python
# For heavy computation
result = await safe_cpu_bound(compute_function, data)
```

#### 6. Safe Database Query
```python
def query():
    conn = sqlite3.connect('db.sqlite')
    return conn.execute('SELECT * FROM table').fetchall()

data = await safe_db_query(query)
```

#### 7. Async Timer
```python
# Update every 5 seconds
async def update():
    data = await fetch_data()
    update_ui(data)

timer = AsyncTimer(update, interval=5.0)
await timer.start()

# Stop when done
await timer.stop()
```

#### 8. Event Handler Decorator
```python
@async_event_handler
async def on_click():
    await safe_sleep(1)
    await safe_notification("Done!")
```

---

## Troubleshooting

### Problem: UI Freezes on Button Click

**Cause:** Blocking operation in event handler

**Solution:**
```python
# Check for blocking patterns
python scripts/preflight_check.py --nicegui

# Replace time.sleep with safe_sleep
# Replace requests.get with safe_api_call
# Wrap blocking operations with safe_io_bound
```

### Problem: "Port already in use"

**Solution:**
```bash
# Find process on port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Restart services
python scripts/api_server.py
```

### Problem: Frontend can't reach backend

**Cause:** Port mismatch

**Solution:**
```bash
# Check integration
python scripts/preflight_check.py --integration

# Fix ports in code:
# Frontend: http://localhost:8000
# Backend: runs on port 8000
```

### Problem: Missing dependencies

**Solution:**
```bash
# Check dependencies
python scripts/check_health.py

# Install missing packages
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Zero-Error Check

on: [push, pull_request]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run health check
        run: python scripts/check_health.py --json
      
      - name: Run pre-flight check
        run: python scripts/preflight_check.py
```

---

## Best Practices

### ✅ DO

1. **Always use async helpers** in NiceGUI event handlers
2. **Run health check** before and after major changes
3. **Run pre-flight check** before committing
4. **Update requirements.txt** when adding dependencies
5. **Use try/except** for all API calls
6. **Test locally** before pushing

### ❌ DON'T

1. **Don't use `time.sleep()`** in NiceGUI code
2. **Don't use `requests.get()`** in event handlers
3. **Don't hardcode ports** - use constants
4. **Don't skip error handling**
5. **Don't commit without testing**
6. **Don't ignore warnings** from pre-flight check

---

## Success Metrics

Your code is ready when:
- ✅ Health check shows 90%+ confidence
- ✅ Pre-flight check passes
- ✅ No blocking patterns detected
- ✅ All dependencies in requirements.txt
- ✅ Ports correctly configured (5001 frontend, 8000 backend)
- ✅ API v3 compliance verified

---

## Getting Help

**Documentation:**
- 📖 [ZERO_ERROR_ARCHITECT.md](ZERO_ERROR_ARCHITECT.md) - Full guide
- 🐛 [debugging-protocol.md](../.github/debugging-protocol.md) - Debugging guide
- 🏠 [HOME.md](../HOME.md) - Main documentation

**Commands:**
```bash
# Quick help
python scripts/check_health.py --help
python scripts/preflight_check.py --help

# View async helpers examples
python scripts/utilities/async_helpers.py
```

---

**Remember:** If you see an error trace, the system failed. Smooth sailing only! 🎉
