# 🔧 NiceGUI Dashboard Fixes - Status Report

## ✅ COMPLETED FIXES

### 1. API Port Configuration (FIXED)
**Issue**: All NiceGUI pages were trying to connect to `localhost:9000` but API server runs on `localhost:8000`

**Files Fixed**:
- `dashboard_ui/state.py` - Changed API_BASE from 9000 to 8000
- `dashboard_ui/pages/signals.py`
- `dashboard_ui/pages/upstox_live.py`
- `dashboard_ui/pages/live_trading.py`
- `dashboard_ui/pages/orders_alerts.py`
- `dashboard_ui/pages/strategies.py`
- `dashboard_ui/pages/analytics.py`
- `dashboard_ui/pages/backtest.py`

**Status**: ✅ Complete

### 2. Market Guide Path (FIXED)
**Issue**: `guide.py` was looking for `MARKET_INSTRUMENTS_GUIDE.md` in root, but file is in `docs/guides/`

**Fix**: Updated `dashboard_ui/pages/guide.py` to use correct path with Path object

**Status**: ✅ Complete

### 3. Instruments API Endpoint (CREATED)
**Issue**: Pages trying to call `/api/instruments/*` endpoints that didn't exist

**Fix**: Created new `scripts/blueprints/instruments.py` with:
- `/api/instruments/nse-eq` - Search NSE equity instruments
- `/api/instruments/<key>` - Get instrument details
- `/api/instruments/search` - Global instrument search

**Status**: ✅ Blueprint created, needs database integration

---

## ⚠️ CRITICAL ISSUES REQUIRING DATABASE SETUP

### ROOT CAUSE: Missing Market Data Tables

The `market_data.db` database only contains:
- `auth_tokens`
- `error_logs`
- `nse_announcements`
- `nse_financial_results`
- `nse_events`
- `nse_board_meetings`
- `scraping_status`
- `validation_rules`

**MISSING TABLES** (required by movers service and other features):
- `exchange_listings` - Instrument master data
- `master_stocks` - Stock metadata (FNO enabled, index membership)
- `stock_metadata` - Additional stock info (Nifty 50/500/Bank membership)
- `sectors` - Sector information
- `instruments` - General instruments table
- `derivatives_metadata` - F&O contracts data

---

## 🔴 REMAINING ISSUES (Blocked by Database)

### 1. Dashboard Movers Not Working
**Location**: `dashboard_ui/pages/home.py`
**Service**: `dashboard_ui/services/movers.py`

**Issue**: Movers service queries `exchange_listings`, `master_stocks`, `stock_metadata` tables that don't exist

**Required Tables**:
```sql
CREATE TABLE exchange_listings (
    instrument_key TEXT PRIMARY KEY,
    symbol TEXT,
    trading_symbol TEXT,
    segment TEXT,
    instrument_type TEXT
);

CREATE TABLE master_stocks (
    symbol TEXT PRIMARY KEY,
    is_fno_enabled INTEGER,
    sector_id INTEGER
);

CREATE TABLE stock_metadata (
    symbol TEXT PRIMARY KEY,
    is_nifty50 INTEGER,
    is_nifty500 INTEGER,
    is_nifty_bank INTEGER
);

CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    name TEXT
);
```

**Temporary Fix Options**:
1. Disable movers until database is populated
2. Use Upstox API directly (slower, rate-limited)
3. Create mock data for testing

### 2. Instrument Browser Error
**Location**: `dashboard_ui/pages/instruments_browser.py`

**Issue**: Calls `/api/instruments/nse-eq?query=RELIANCE` which now exists but returns empty data (no database)

**Fix Needed**: Populate instruments cache from Upstox API or database

### 3. Calculate Charges - Symbol Search
**Location**: `dashboard_ui/pages/charges_calc.py`

**Issue**: Symbol autocomplete likely uses instrument search which requires database

**Fix Needed**: Implement autocomplete using Upstox API or database

### 4. Trade P&L, Health Status, Margin Calculator
**Issue**: All making HTTP requests to endpoints that may not exist or return empty data

**Fix Needed**: Audit each page and ensure endpoints exist

### 5. Market Explorer
**Location**: `dashboard_ui/pages/market_explorer.py`

**Issue**: Not showing anything - likely missing data or broken API calls

**Fix Needed**: Check what data it's trying to fetch

### 6. Corporate Announcements
**Location**: `dashboard_ui/pages/corporate_announcements.py`

**Current Status**: Database has `nse_announcements` table with data

**Issue**: Need to verify if page is fetching and displaying correctly

**Improvement Needed**: Check if data is live/recent and add refresh functionality

---

## 📋 RECOMMENDED ACTION PLAN

### Phase 1: Quick Wins (Can do now)
1. ✅ Fix API port configuration (DONE)
2. ✅ Fix Market Guide path (DONE)
3. ✅ Create instruments blueprint (DONE)
4. 🔄 Test corporate announcements page
5. 🔄 Add graceful error handling to all pages when data is missing
6. 🔄 Display helpful messages instead of HTTP errors

### Phase 2: Database Setup (Required for full functionality)
1. Create database schema migration script
2. Fetch and populate instruments data from Upstox
3. Populate master_stocks, stock_metadata, sectors tables
4. Set up periodic data refresh

### Phase 3: Feature Restoration
1. Enable movers service with database
2. Implement instrument search with autocomplete
3. Fix charges calculator symbol lookup
4. Restore market explorer functionality
5. Enable all data-dependent features

### Phase 4: Enhancements
1. Add caching layer for frequently accessed data
2. Implement real-time data updates
3. Add data freshness indicators
4. Improve error messages and user feedback

---

## 🛠️ IMMEDIATE FIXES TO APPLY

### Fix 1: Add Graceful Error Handling to Instruments Browser

```python
# In dashboard_ui/pages/instruments_browser.py
try:
    response = await run.io_bound(requests.get, f"{API_BASE}/instruments/nse-eq")
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            # Display data
        else:
            ui.label("⚠️ No instruments data available. Database setup required.").classes("text-yellow-500")
    else:
        ui.label(f"❌ API Error: {response.status_code}").classes("text-red-500")
except Exception as e:
    ui.label(f"❌ Connection Error: Database not configured").classes("text-red-500")
```

### Fix 2: Disable Movers Temporarily

```python
# In dashboard_ui/pages/home.py
# Add at top of movers section:
ui.label("⚠️ Market Movers temporarily disabled - Database setup in progress").classes("text-yellow-500")
# Comment out movers service calls
```

### Fix 3: Add Database Status Indicator

```python
# Add to home page or health page:
def check_database_status():
    try:
        conn = sqlite3.connect("market_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        required_tables = ['exchange_listings', 'master_stocks', 'stock_metadata']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            return f"⚠️ Database incomplete. Missing: {', '.join(missing)}"
        else:
            return "✅ Database ready"
    except:
        return "❌ Database error"
```

---

## 📊 TESTING CHECKLIST

After applying fixes, test these pages:

- [ ] Home (Dashboard) - Movers section
- [ ] Instruments Browser - Search functionality
- [ ] Market Guide - Documentation display
- [ ] Calculate Charges - Symbol autocomplete
- [ ] Trade P&L - Data display
- [ ] Health Status - System checks
- [ ] Margin Calculator - Calculations
- [ ] Market Explorer - Market data
- [ ] Corporate Announcements - Live data
- [ ] All other NiceGUI pages

---

## 🎯 PRIORITY ORDER

1. **HIGH**: Fix HTTP connection errors (port configuration) ✅ DONE
2. **HIGH**: Add graceful error handling to prevent crashes
3. **MEDIUM**: Set up database schema
4. **MEDIUM**: Populate instruments data
5. **LOW**: Enable advanced features (movers, explorer, etc.)

---

## 📝 NOTES

- The platform is functional for basic operations
- Data-dependent features need database setup
- All API endpoints are now on correct port (8000)
- Instruments blueprint provides foundation for future features
- Consider using Upstox API directly as fallback when database is empty

---

**Last Updated**: 2026-02-03 21:15:00
**Status**: Port fixes complete, database setup required for full functionality
