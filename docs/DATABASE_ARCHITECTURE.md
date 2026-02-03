# Database Architecture Documentation

**Last Updated:** February 3, 2026  
**Database Engine:** SQLite 3  
**Total Tables:** 78+

---

## 🎯 Overview

The UPSTOX Trading Platform uses a **single SQLite database** (`market_data.db`) with a comprehensive relational schema covering all aspects of algorithmic trading.

### Why SQLite?

**Advantages:**
- ✅ Zero configuration
- ✅ ACID compliant
- ✅ Perfect for single-server deployments
- ✅ Fast for read-heavy workloads
- ✅ No separate database server needed
- ✅ Easy backups (single file)

**Production Considerations:**
- ⚠️ Single writer at a time (write lock)
- ⚠️ Not suitable for high-concurrency writes
- ⚠️ Limited to ~1TB database size (SQLite limit)
- ✅ Handles 100K+ reads/second easily
- ✅ PostgreSQL migration path available (see `scripts/migrate_to_postgres.py`)

---

## 📦 Database Files

### Primary Database: `market_data.db`

**Location:** Project root  
**Size:** ~50MB - 5GB (depends on historical data)  
**Tables:** 78+ tables across 9 categories  
**Purpose:** All application data (market data, trading, analytics, auth)

### Secondary Files

1. **`market_data.db-wal`** - Write-Ahead Log (WAL mode)
   - Improves concurrency
   - Enables multiple readers during write operations
   - Automatically managed by SQLite

2. **`market_data.db-shm`** - Shared Memory File
   - Used by WAL mode
   - Temporary file, automatically managed

3. **`cache/yahoo_cache.sqlite`** - Yahoo Finance Cache
   - Caches Yahoo Finance API responses
   - Reduces API calls
   - Can be safely deleted (will regenerate)

4. **`upstox.db`** - Legacy/Placeholder
   - Currently unused (0 tables)
   - May be used in future for auth isolation
   - Safe to ignore

---

## 🗂️ Database Schema Organization

### Category 1: Market Data Foundation (6 tables)

**Purpose:** Normalized master data for instruments and exchanges

| Table | Rows | Purpose |
|-------|------|---------|
| `exchanges` | ~10 | Exchange definitions (NSE, BSE, MCX) |
| `segments` | ~20 | Market segments (NSE_EQ, NFO, CDS) |
| `instrument_types` | ~15 | Asset types (EQ, FUT, CE, PE, IDX) |
| `instruments` | ~500K | All tradable instruments |
| `equities_metadata` | ~5K | Stock details (sector, industry, market cap) |
| `derivatives_metadata` | ~100K | F&O contract specifications |

**Key Relationships:**
```
instruments
  ├─> exchanges (exchange_id)
  ├─> segments (segment_id)
  └─> instrument_types (instrument_type_id)
```

---

### Category 2: Real-Time Market Data (9 tables)

**Purpose:** Live quotes, candles, order book depth

| Table | Rows | Update Frequency | Purpose |
|-------|------|------------------|---------|
| `quote_cache_v3` | ~10K | Real-time | Latest quotes (LTP, bid/ask) |
| `quote_metrics` | ~10K | 1 min | Quote statistics |
| `quote_ticks` | ~1M | Real-time | Tick-by-tick data |
| `candles_new` | ~50M | 1 min - 1 day | OHLCV candles |
| `option_candles` | ~10M | 1 min - 1 day | Options OHLCV |
| `expired_candles` | ~100M | Historical | Expired contracts data |
| `websocket_ticks_v3` | ~5M | Real-time | WebSocket stream data |
| `market_depth` | ~10K | Real-time | Order book (5 levels) |
| `order_book` | ~10K | Real-time | Full order book |

**Data Retention:**
- Intraday: 30 days
- Daily: 10 years
- Expired options: 5 years

---

### Category 3: Trading & Order Management (10 tables)

**Purpose:** Order lifecycle, paper trading, GTT orders

| Table | Rows | Purpose |
|-------|------|---------|
| `orders` | ~100K | Live order history |
| `orders_v3` | ~100K | API v3 orders |
| `order_updates` | ~500K | Order state changes |
| `bracket_orders` | ~10K | Bracket order definitions |
| `gtt_orders` | ~5K | Good-Till-Triggered orders |
| `gtt_triggers` | ~20K | GTT trigger events |
| `paper_portfolio` | 1 | Virtual portfolio state |
| `paper_positions` | ~100 | Paper trading positions |
| `paper_orders` | ~50K | Simulated orders |
| `paper_executions` | ~50K | Paper trade fills |

**Order State Machine:**
```
PENDING → PLACED → PARTIALLY_FILLED → FILLED
    ↓         ↓           ↓
  REJECTED  CANCELLED  CANCELLED
```

---

### Category 4: Portfolio & Holdings (6 tables)

**Purpose:** Position tracking, P&L calculation, holdings

| Table | Rows | Purpose |
|-------|------|---------|
| `holdings` | ~100 | Current holdings (stocks) |
| `holdings_history` | ~10K | Daily holdings snapshots |
| `positions` | ~50 | Open futures/options positions |
| `pnl_reports` | ~1K | Daily P&L summaries |
| `position_conversions` | ~1K | Intraday to delivery conversions |
| `trade_charges` | ~100K | Brokerage, taxes, charges |

**P&L Calculation:**
```python
realized_pnl = sell_value - buy_value - total_charges
unrealized_pnl = (current_price - avg_price) * quantity
```

---

### Category 5: Risk Management (4 tables)

**Purpose:** Position limits, stop losses, circuit breakers

| Table | Rows | Purpose |
|-------|------|---------|
| `risk_configs` | ~10 | Risk parameters per strategy |
| `stop_loss_orders` | ~1K | Active stop loss orders |
| `circuit_breaker_events` | ~100 | Market halt events |
| `risk_metrics` | ~365 | Daily VaR, Sharpe, max drawdown |

**Risk Controls:**
- Max position size per symbol
- Max daily loss limit
- Max portfolio exposure
- Margin requirements
- Volatility-based position sizing

---

### Category 6: Analytics & Performance (6 tables)

**Purpose:** Strategy backtesting, performance tracking

| Table | Rows | Purpose |
|-------|------|---------|
| `trade_journal` | ~100K | Trade-by-trade log |
| `daily_performance` | ~365 | Daily metrics (P&L, returns) |
| `monthly_performance` | ~12 | Monthly aggregates |
| `strategies` | ~20 | Strategy definitions (RSI, MACD, SMA) |
| `trading_signals` | ~50K | Generated signals (BUY, SELL) |
| `strategy_performance` | ~1K | Backtest results |

**Performance Metrics:**
- Win rate, profit factor
- Sharpe ratio, Sortino ratio
- Max drawdown, recovery time
- Alpha, beta vs benchmark

---

### Category 7: Corporate Intelligence (10 tables)

**Purpose:** Corporate actions, earnings, economic events

| Table | Rows | Purpose |
|-------|------|---------|
| `corporate_announcements` | ~50K | Dividends, splits, bonuses |
| `earnings_calendar` | ~5K | Quarterly results schedule |
| `announcement_alerts` | ~1K | Custom alerts on events |
| `board_meetings` | ~10K | Board meeting schedule |
| `economic_events` | ~5K | GDP, inflation, policy rates |
| `rbi_policy_decisions` | ~100 | Monetary policy changes |
| `economic_alerts` | ~500 | Economic event notifications |
| `market_impact_history` | ~10K | Event impact analysis |

**Data Sources:**
- NSE corporate actions (web scraping)
- BSE announcements
- RBI website (policy decisions)
- Economic calendars (Investing.com)

---

### Category 8: Market Reference Data (5 tables)

**Purpose:** Index constituents, sectors, market hours

| Table | Rows | Purpose |
|-------|------|---------|
| `nse_index_membership` | ~3K | NIFTY50, NIFTY500, etc. |
| `nse_sector_info` | ~5K | Sector and industry mapping |
| `market_status` | 1 | Current market state (OPEN/CLOSED) |
| `market_holidays` | ~100 | Trading holidays calendar |
| `market_timings` | ~10 | Session timings per segment |

**Index Coverage:**
- NIFTY50, NIFTY100, NIFTY200, NIFTY500
- NIFTYMIDCAP50, NIFTYMIDCAP100
- NIFTYSMALLCAP50, NIFTYSMALLCAP100

---

### Category 9: System & Operations (18 tables)

**Purpose:** Auth, logging, alerts, news, sync jobs

#### Authentication & User (3 tables)
| Table | Rows | Purpose |
|-------|------|---------|
| `auth_tokens` | ~10 | OAuth tokens (encrypted) |
| `account_info` | 1 | User profile, preferences |
| `margin_history` | ~365 | Daily margin snapshots |

#### Alerts & Notifications (3 tables)
| Table | Rows | Purpose |
|-------|------|---------|
| `alert_rules` | ~100 | Alert conditions (price, RSI, volume) |
| `alert_history` | ~10K | Triggered alerts log |
| `alert_notifications` | ~10K | Sent notifications (email, SMS) |

#### News & Sentiment (4 tables)
| Table | Rows | Purpose |
|-------|------|---------|
| `news_articles` | ~50K | NewsAPI articles |
| `news_alerts` | ~1K | News-based alerts |
| `news_watchlist` | ~100 | Tracked symbols for news |
| `sentiment_history` | ~10K | FinBERT sentiment scores |

#### System Operations (8 tables)
| Table | Rows | Purpose |
|-------|------|---------|
| `error_logs` | ~100K | Application errors, stack traces |
| `api_cache` | ~10K | Cached API responses (TTL: 5 min) |
| `validation_rules` | ~50 | Data validation constraints |
| `application_logs` | ~1M | General application logs |
| `system_metrics` | ~10K | CPU, memory, disk usage |
| `sync_jobs` | ~20 | Background job definitions |
| `sync_history` | ~10K | Job execution history |
| `data_gaps` | ~1K | Detected data gaps for backfill |

---

## 🔄 Data Flow Architecture

### 1. Market Data Ingestion

```
Upstox WebSocket → websocket_ticks_v3 → candles_new
                 → quote_cache_v3
                 → market_depth

NSE Website → corporate_announcements
           → earnings_calendar
           → nse_index_membership

NewsAPI → news_articles → sentiment_history (FinBERT)
```

### 2. Trading Flow

```
User → nicegui_dashboard.py
    → scripts/api_server.py (Flask)
      → scripts/order_manager_v3.py
        → Upstox API
          → orders_v3 table
            → order_updates table
              → pnl_reports table
```

### 3. Strategy Execution Flow

```
strategy_runner.py
  ↓
Read: candles_new + quote_cache_v3
  ↓
Calculate: RSI, MACD, SMA indicators
  ↓
Generate: trading_signals
  ↓
Check: risk_configs + risk_metrics
  ↓
Place: orders (or paper_orders)
  ↓
Track: strategy_performance
```

---

## 🔐 Data Security

### Encryption

**Sensitive Data:**
- `auth_tokens.access_token` - Encrypted (Fernet)
- `auth_tokens.refresh_token` - Encrypted (Fernet)
- API keys in environment variables (not in DB)

**Encryption Key:**
- Stored in `.env` as `ENCRYPTION_KEY`
- Generated via `scripts/generate_encryption_key.py`
- 32-byte Fernet key (base64 encoded)

### Access Control

**No Built-in Users:** SQLite has no user auth
- Application-level auth only
- Access controlled via filesystem permissions
- Recommended: `chmod 600 market_data.db`

---

## 💾 Backup Strategy

### Automated Backups

**Script:** `scripts/backup_db.sh`

**What it backs up:**
1. `market_data.db` (full database)
2. `upstox.db` (if exists)
3. `cache/yahoo_cache.sqlite` (optional)

**Backup Location:** `backups/YYYY-MM-DD_HH-MM-SS/`

**Retention:**
- Keep last 7 daily backups
- Keep last 4 weekly backups
- Keep last 12 monthly backups

**Scheduling (cron):**
```bash
# Daily at 2 AM
0 2 * * * /path/to/scripts/backup_db.sh

# Before database changes
./scripts/backup_db.sh
python scripts/schema_migration_v2.py
```

### Manual Backup

```bash
# SQLite built-in backup
sqlite3 market_data.db ".backup market_data_backup.db"

# Or simple copy (ensure no active writes)
cp market_data.db market_data_$(date +%Y%m%d).db
```

---

## 📊 Database Maintenance

### Vacuum (Reclaim Space)

```bash
sqlite3 market_data.db "VACUUM;"
```

**When to run:**
- After deleting large amounts of data
- Monthly maintenance window
- When disk space is low

### Analyze (Update Statistics)

```bash
sqlite3 market_data.db "ANALYZE;"
```

**Purpose:** Update query planner statistics for better performance

### Integrity Check

```bash
sqlite3 market_data.db "PRAGMA integrity_check;"
```

**When to run:**
- After unexpected shutdown
- Before production deployment
- Monthly health check

### Indexes

**Script:** `scripts/add_database_indexes.py`

**What it does:**
- Adds indexes on frequently queried columns
- Improves query performance 10-100x
- Safe to run multiple times (idempotent)

**Usage:**
```bash
python scripts/add_database_indexes.py --db-type sqlite
```

**Key Indexes:**
- `idx_candles_symbol_timestamp` - Fast candle lookups
- `idx_orders_status` - Active orders query
- `idx_signals_timestamp` - Recent signals
- `idx_quotes_symbol` - Quote cache lookup

---

## 🔧 Schema Evolution

### Current Version: v2

**Migration Script:** `scripts/schema_migration_v2.py`

**Changes in v2:**
- Added WebSocket v3 tables
- Split candles table into `candles_new` + `option_candles`
- Added `quote_cache_v3` for API v3
- Added `orders_v3` for new order format
- Added composite indexes for performance

### Future Migrations

**Planned v3 Changes:**
1. Add `users` table for multi-user support
2. Add `api_keys` table for API key management
3. Add `webhooks` table for event notifications
4. Partition large tables (`candles_new`, `trade_journal`)

### Migration Process

**Before Migration:**
```bash
# 1. Backup database
./scripts/backup_db.sh

# 2. Run migration
python scripts/schema_migration_v2.py

# 3. Verify
python scripts/database_validator.py --validate-all

# 4. Test application
pytest tests/test_database.py
```

---

## 🚀 PostgreSQL Migration Path

**When to Migrate:**
- Trading volume > 1000 orders/day
- Multiple concurrent users
- Need replication/high availability
- Database size > 100GB

**Migration Script:** `scripts/migrate_to_postgres.py`

**Steps:**
1. Export SQLite schema and data
2. Convert SQLite types to PostgreSQL types
3. Create PostgreSQL database
4. Import data with constraints
5. Add PostgreSQL-specific indexes (GiST, BRIN)
6. Update connection strings in code

**Performance Comparison:**

| Metric | SQLite | PostgreSQL |
|--------|--------|------------|
| Writes/sec | 1K-10K | 10K-100K |
| Concurrent writes | 1 | Unlimited |
| Database size limit | 281 TB | Unlimited |
| Full-text search | Limited | Excellent |
| JSON queries | Basic | Advanced |

---

## 🔍 Querying the Database

### Direct SQLite Access

```bash
# Open database
sqlite3 market_data.db

# List tables
.tables

# Describe table
.schema candles_new

# Query data
SELECT * FROM candles_new 
WHERE symbol = 'RELIANCE' 
AND timestamp > date('now', '-7 days')
ORDER BY timestamp DESC
LIMIT 10;

# Export to CSV
.mode csv
.output candles.csv
SELECT * FROM candles_new WHERE symbol = 'TCS';
.output stdout
```

### Python Access

```python
import sqlite3

conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Query
cursor.execute("""
    SELECT symbol, close, volume 
    FROM candles_new 
    WHERE timestamp > ? 
    ORDER BY volume DESC 
    LIMIT 10
""", ('2026-01-01',))

for row in cursor.fetchall():
    print(row)

conn.close()
```

### Using Pandas

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('market_data.db')

# Read table into DataFrame
df = pd.read_sql_query("""
    SELECT * FROM candles_new 
    WHERE symbol = 'NIFTY' 
    AND timestamp > '2026-01-01'
""", conn)

print(df.head())
conn.close()
```

---

## 📈 Performance Optimization

### WAL Mode (Write-Ahead Logging)

**Status:** Enabled by default

**Benefits:**
- Multiple readers during writes
- Better concurrency
- Faster writes (no sync on every commit)

**Verification:**
```bash
sqlite3 market_data.db "PRAGMA journal_mode;"
# Should return: wal
```

### Connection Pooling

**Script:** `scripts/database_pool.py`

**Features:**
- Reuses connections (reduces overhead)
- Thread-safe
- Automatic connection management
- Max pool size: 10 connections

### Query Optimization Tips

1. **Use indexes** - Always index WHERE clauses
2. **Limit results** - Use LIMIT for pagination
3. **Avoid SELECT *** - Query only needed columns
4. **Use prepared statements** - Prevents SQL injection, better performance
5. **Batch inserts** - Use transactions for bulk inserts

**Example Batch Insert:**
```python
conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Bad: Individual commits (slow)
for row in data:
    cursor.execute("INSERT INTO candles_new VALUES (?,?,?)", row)
    conn.commit()  # ❌ Slow!

# Good: Single transaction (fast)
cursor.execute("BEGIN TRANSACTION")
for row in data:
    cursor.execute("INSERT INTO candles_new VALUES (?,?,?)", row)
conn.commit()  # ✅ 100x faster!
```

---

## 🔗 Related Documentation

- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Database setup for development
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production database configuration
- **[TESTING.md](TESTING.md)** - Database testing strategies
- **[SHELL_SCRIPTS.md](SHELL_SCRIPTS.md)** - Database backup scripts
- **[BACKEND_README.md](BACKEND_README.md)** - Database integration in backend

---

## 🎯 Quick Reference

### Essential Queries

**Get latest quote:**
```sql
SELECT * FROM quote_cache_v3 WHERE symbol = 'RELIANCE' LIMIT 1;
```

**Get today's candles:**
```sql
SELECT * FROM candles_new 
WHERE symbol = 'NIFTY' 
AND date(timestamp) = date('now')
ORDER BY timestamp;
```

**Get active orders:**
```sql
SELECT * FROM orders_v3 
WHERE status IN ('PENDING', 'PLACED', 'PARTIALLY_FILLED');
```

**Get holdings:**
```sql
SELECT * FROM holdings WHERE quantity > 0;
```

**Get performance:**
```sql
SELECT * FROM daily_performance 
WHERE date > date('now', '-30 days')
ORDER BY date DESC;
```

### Database Health Check

```bash
# Size
du -h market_data.db

# Table count
sqlite3 market_data.db "SELECT count(*) FROM sqlite_master WHERE type='table';"

# Row counts
sqlite3 market_data.db "SELECT name, (SELECT count(*) FROM " || name || ") as count FROM sqlite_master WHERE type='table' ORDER BY count DESC;"

# Integrity
sqlite3 market_data.db "PRAGMA integrity_check;"
```

---

**Database Status:** ✅ Production Ready  
**Total Tables:** 78+  
**Storage:** Single SQLite file  
**Migration Path:** PostgreSQL ready
