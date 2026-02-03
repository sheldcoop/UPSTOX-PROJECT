# Quick Debugging Reference Card

**🚨 For immediate debugging help, use this quick reference**

## 🔍 Layer Identification Cheat Sheet

| Symptom | Layer | First Check |
|---------|-------|-------------|
| UI doesn't update after API call | UI (NiceGUI) | Missing `.refresh()` call? |
| UI freezes on button click | UI (NiceGUI) | Using blocking `time.sleep()` or sync I/O? |
| "Connection refused" in Docker | Communication | Using `localhost` instead of service name? |
| Flask returns 500 error | Logic (Flask) | Check `logs/api_server.log` for TraceID |
| "database is locked" error | Data (SQLite) | Concurrent writes? Enable WAL mode |
| 401 Unauthorized from Upstox | Data (External API) | Token expired? Check expiry time |

## 💥 Common Fix Patterns

### Pattern 1: NiceGUI State Not Updating
```python
# Add @ui.refreshable decorator
@ui.refreshable
def my_component(data):
    # render data
    pass

# Call .refresh() after async update
async def update_data():
    new_data = await async_get("/api/data")
    my_component.refresh()  # ← ADD THIS
```

### Pattern 2: UI Freezing
```python
# Change from sync to async with run.io_bound
async def on_click():
    # WRONG: result = requests.get(url)
    # RIGHT:
    result = await run.io_bound(requests.get, url)
```

### Pattern 3: Docker Networking
```python
# In dashboard_ui/state.py
import os
API_BASE = os.getenv("API_BASE", "http://localhost:9000")

# In docker-compose.yml
environment:
  - API_BASE=http://backend:9000  # Use service name!
```

### Pattern 4: SQLite Locks
```python
# Enable WAL mode once
conn = sqlite3.connect("market_data.db")
conn.execute("PRAGMA journal_mode=WAL")

# Increase timeout
conn = sqlite3.connect("market_data.db", timeout=10.0)
```

### Pattern 5: Token Expiry
```python
# Check before API call
def get_valid_token():
    if token_expired():
        refresh_token()
    return get_token()

# Handle 401 errors
if response.status_code == 401:
    refresh_token()
    retry_request()
```

## 🛠️ Essential Debug Commands

```bash
# Backend logs with TraceID
tail -f logs/api_server.log | grep "TraceID"

# Test API directly
curl -X GET http://localhost:9000/api/positions -v

# Database check
sqlite3 market_data.db "SELECT COUNT(*) FROM positions"

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Docker network test
docker-compose exec frontend ping backend
docker-compose exec frontend curl http://backend:9000/api/health
```

## 📋 Debugging Checklist

When you encounter an error:

- [ ] **Identify the layer** (UI, Communication, Logic, Data)
- [ ] **Check common patterns** (State Sync, Token Expiry, SQLite Locks, Docker, Async)
- [ ] **Check logs** with TraceID correlation
- [ ] **Add instrumentation** (logging, state dumps)
- [ ] **Create minimal repro** (isolate the issue)
- [ ] **Fix with validation** (assertions, type checks)
- [ ] **Add tests** (prevent regression)

## 🚀 Quick Fixes

| Error Message | Quick Fix |
|--------------|-----------|
| `database is locked` | Add `timeout=10.0` to sqlite3.connect() |
| `Connection refused` | Check API_BASE URL and port |
| `401 Unauthorized` | Check token expiry, refresh if needed |
| `UI not updating` | Add `@ui.refreshable` and call `.refresh()` |
| `UI freezes` | Wrap blocking I/O in `await run.io_bound()` |
| `CORS error` | Check Flask CORS configuration |
| `500 Internal Server Error` | Check backend logs for TraceID |

## 📚 Full Documentation

- **Complete Protocol:** [debugging-protocol.md](debugging-protocol.md)
- **Real Examples:** [debugging-examples.md](debugging-examples.md)
- **Architecture Guide:** [copilot-instructions.md](copilot-instructions.md)

---

**Need help?** Follow the complete protocol in `debugging-protocol.md` for step-by-step guidance.
