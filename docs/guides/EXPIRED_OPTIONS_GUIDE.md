# Expired Options Fetcher - Usage Guide

## ✅ Yes! Multiple Options & Expiries Support

The enhanced `expired_options_fetcher.py` **now supports**:
- ✅ **Multiple underlyings** (comma-separated)
- ✅ **Multiple expiries** (comma-separated)
- ✅ **Batch mode** (fetch all available expiries)
- ✅ **Filtering** by option type (CE/PE) and strike
- ✅ **Single or combined** configurations

---

## 🚀 Quick Examples

### 1. Single Underlying, Single Expiry (Basic)
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY --expiry 2025-01-22
```
**Output:**
- Fetches all CE and PE options for NIFTY expiring on 2025-01-22
- Stores in database with complete option chain

---

### 2. Single Underlying, Multiple Expiries
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY --expiry 2025-01-22,2025-02-19,2025-03-26
```
**Output:**
- Fetches 3 option chains (one for each expiry)
- Stores 3 × (number of strikes × 2) records in database
- Example: 3 expiries × 97 strikes × 2 types = ~582 records

---

### 3. Multiple Underlyings, Single Expiry
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY,INFY --expiry 2025-01-22
```
**Output:**
- Fetches options for all 3 underlyings on the same expiry date
- Stores all combinations in database
- Example: 3 underlyings × 97 strikes × 2 types = ~582 records

---

### 4. Multiple Underlyings, Multiple Expiries (Batch Mode)
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY --batch
```
**Output:**
- Automatically fetches ALL available expiries for each underlying
- Fetches 2 underlyings × (multiple expiries per underlying)
- Example: 2 underlyings × 4 expiries × 97 strikes × 2 types = ~1,552 records

---

### 5. Batch with Option Type Filter
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY,INFY --batch --option-type CE
```
**Output:**
- Fetches only CALL options (CE) for all combinations
- Reduces storage: 3 underlyings × expiries × 97 strikes × 1 type

---

### 6. Batch with Strike Filter
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY --batch --strike 23000
```
**Output:**
- Fetches only options with 23000 strike price across all expiries

---

### 7. List Available Expiries for Multiple Underlyings
```bash
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY,INFY --list-expiries
```
**Output:**
```
📅 Available Expiry Dates for NIFTY:
   2025-01-22
   2025-02-19
   2025-03-26
   2025-04-23

📅 Available Expiry Dates for BANKNIFTY:
   2025-01-22
   2025-02-19
   ...
```

---

### 8. Query Stored Options
```bash
# Single underlying and expiry
python scripts/expired_options_fetcher.py --query NIFTY@2025-01-22

# Just underlying (all stored expiries)
python scripts/expired_options_fetcher.py --query NIFTY
```
**Output:**
- Shows strike chain summary
- Call and Put options for each strike
- Total statistics

---

## 📊 Performance Examples

### Scenario 1: Quick Snapshot
```bash
# Downloads 1 underlying × 1 expiry
python scripts/expired_options_fetcher.py --underlying INFY --expiry 2025-01-22

# ~45 options stored (all strikes × 2 types)
# Time: ~2-3 seconds
```

### Scenario 2: Medium Batch
```bash
# Downloads 2 underlyings × 3 expiries each
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY --expiry 2025-01-22,2025-02-19,2025-03-26

# ~600 options stored
# Time: ~10-15 seconds
```

### Scenario 3: Full Batch Download
```bash
# Downloads 3 underlyings × all available expiries
python scripts/expired_options_fetcher.py --underlying NIFTY,BANKNIFTY,INFY --batch

# ~1500-2000 options stored
# Time: ~30-60 seconds
```

### Scenario 4: Large-Scale Batch
```bash
# Stock indices + stocks + all expiries
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY,FINNIFTY,INFY,TCS,RELIANCE,WIPRO \
  --batch

# 7000+ options stored
# Time: ~3-5 minutes
```

---

## 🎯 Advanced Workflows

### Workflow 1: Backtest Data Collection
```bash
#!/bin/bash

# Fetch all options from last 3 months for main underlyings
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY \
  --expiry 2024-11-21,2024-12-19,2025-01-22,2025-02-19,2025-03-26

# Now query for specific analysis
python scripts/expired_options_fetcher.py --query NIFTY
```

### Workflow 2: Incremental Updates
```bash
# Day 1: Fetch current week options
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY,INFY \
  --expiry 2025-02-05

# Day 2: Add next week options
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY,INFY \
  --expiry 2025-02-12

# Day 3: Add monthly options
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY,INFY \
  --expiry 2025-02-26
```

### Workflow 3: Comparative Analysis
```bash
# Fetch same expiry across multiple underlyings
python scripts/expired_options_fetcher.py \
  --underlying NIFTY,BANKNIFTY,FINNIFTY \
  --expiry 2025-02-19

# Fetch same underlying across multiple expiries
python scripts/expired_options_fetcher.py \
  --underlying NIFTY \
  --expiry 2025-01-22,2025-02-19,2025-03-26,2025-04-23
```

---

## 💾 Database Storage

All fetched options are stored in SQLite with this structure:

```sql
CREATE TABLE expired_options (
    id INTEGER PRIMARY KEY,
    underlying_symbol TEXT,          -- NIFTY, BANKNIFTY, INFY
    option_type TEXT,                -- CE or PE
    strike_price REAL,               -- 23000, 24000, etc.
    expiry_date TEXT,                -- 2025-01-22
    tradingsymbol TEXT,              -- NIFTY22JAN23000CE
    exchange_token TEXT,
    exchange TEXT,
    last_trading_price REAL,
    settlement_price REAL,
    open_interest INTEGER,
    last_volume INTEGER,
    fetch_timestamp INTEGER,
    UNIQUE(underlying_symbol, strike_price, option_type, expiry_date)
)
```

### Query Examples
```python
import sqlite3

conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Get all NIFTY options
cursor.execute("SELECT * FROM expired_options WHERE underlying_symbol = 'NIFTY'")

# Get specific expiry
cursor.execute("SELECT * FROM expired_options WHERE expiry_date = '2025-01-22'")

# Get only CE options
cursor.execute("SELECT * FROM expired_options WHERE option_type = 'CE'")

# Get specific strike
cursor.execute("SELECT * FROM expired_options WHERE strike_price = 23000")

# Complex query: NIFTY CE options on specific expiry
cursor.execute("""
    SELECT * FROM expired_options 
    WHERE underlying_symbol = 'NIFTY' 
    AND option_type = 'CE' 
    AND expiry_date = '2025-01-22'
    ORDER BY strike_price
""")

results = cursor.fetchall()
```

---

## ⚡ Argument Reference

```
--underlying    Comma-separated list of underlyings
                Example: NIFTY,BANKNIFTY,INFY
                
--expiry        Comma-separated list of expiry dates (YYYY-MM-DD)
                If not provided, uses first available
                Example: 2025-01-22,2025-02-19
                
--batch         Automatically fetch all available expiries
                Requires --underlying
                Example: --batch
                
--option-type   Filter by type: CE or PE
                Example: --option-type CE
                
--strike        Filter by strike price
                Example: --strike 23000
                
--list-expiries List available expiries
                Example: --list-expiries
                
--query         Query stored options
                Format: UNDERLYING@EXPIRY or just UNDERLYING
                Example: --query NIFTY@2025-01-22
```

---

## 📈 Expected Database Growth

| Scenario | Underlyings | Expiries | Strikes | Total Records |
|----------|-------------|----------|---------|---------------|
| Single | 1 | 1 | ~100 | ~200 |
| Weekly | 2 | 1 | ~100 | ~400 |
| Monthly | 2 | 4 | ~100 | ~1,600 |
| Full Batch | 5 | 5 | ~100 | ~5,000 |
| Large Batch | 10 | 6 | ~100 | ~12,000 |

---

## ✅ Verification Checklist

After running batch fetches, verify data:

```bash
# Check total records
sqlite3 market_data.db "SELECT COUNT(*) FROM expired_options"

# Check unique underlyings
sqlite3 market_data.db "SELECT DISTINCT underlying_symbol FROM expired_options"

# Check unique expiries
sqlite3 market_data.db "SELECT DISTINCT expiry_date FROM expired_options"

# Check strikes for a symbol
sqlite3 market_data.db "SELECT COUNT(DISTINCT strike_price) FROM expired_options WHERE underlying_symbol = 'NIFTY'"

# Check CE/PE ratio
sqlite3 market_data.db "SELECT option_type, COUNT(*) FROM expired_options GROUP BY option_type"
```

---

## 🎯 Recommendations

### For Backtesting
1. Start with single underlying, single expiry
2. Gradually expand to multiple expiries
3. Add more underlyings as needed
4. Use `--batch` for complete historical data

### For Production
1. Run batch downloads during off-market hours
2. Use `--option-type CE` or `PE` to reduce database size
3. Schedule periodic updates with `--batch`
4. Query database for analysis instead of re-fetching

### For Analysis
1. Fetch multiple underlyings same expiry for comparison
2. Fetch same underlying multiple expiries for trends
3. Combine with candle_fetcher for complete analysis
4. Use filters to reduce noise

---

**Created:** 2025-01-31
**Status:** ✨ Enhanced & Ready
