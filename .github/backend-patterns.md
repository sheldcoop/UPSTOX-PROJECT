# Backend Development Patterns — Upstox Trading Platform

## 🏗️ Architecture Overview

**Stack:** Python 3.x + SQLite + Upstox API
**Pattern:** Script-based modular architecture with CLI interfaces
**Database:** Single SQLite file (`market_data.db`) with 40+ tables
**Config:** YAML-based (`config/trading.yaml`)

---

## 📁 Project Structure

```
scripts/
├── auth_manager.py          # OAuth tokens, encryption
├── error_handler.py         # Retry logic, caching
├── risk_manager.py          # Position sizing, circuit breaker
├── database_validator.py    # Data quality, constraints
├── strategy_runner.py       # Trading strategies (RSI, MACD)
├── alert_system.py          # Price/volume alerts
├── data_sync_manager.py     # Scheduled data refresh
├── logger_config.py         # Centralized logging
├── performance_analytics.py # Trading metrics, Sharpe ratio
├── paper_trading.py         # Virtual portfolio
├── news_alerts_manager.py   # NewsAPI + FinBERT sentiment
├── corporate_announcements_fetcher.py  # NSE scraping
├── brokerage_calculator.py  # Fee calculation
└── holdings_manager.py      # Portfolio tracking

config/
└── trading.yaml             # All configuration

.github/
├── copilot-instructions.md  # Main project context
├── frontend-guidelines.md   # UI development rules
└── backend-patterns.md      # This file
```

---

## 🔑 Core Design Patterns

### 1. CLI-First Design

Every script has a standalone CLI interface for testing/debugging:

```python
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Module description")
    parser.add_argument('--action', choices=['action1', 'action2'], required=True)
    parser.add_argument('--symbols', help="Comma-separated symbols")
    args = parser.parse_args()
    
    if args.action == 'action1':
        # Execute action
```

**Benefits:**
- Test individual components without full system
- Debug issues in isolation
- Create cron jobs easily
- Use in shell scripts

### 2. Database-Centric State

All state persists in SQLite (no in-memory caches that disappear):

```python
import sqlite3

def get_connection(db_path='market_data.db'):
    """Centralized connection with row factory"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def execute_query(query, params=None, db_path='market_data.db'):
    """Execute with automatic commit/close"""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    result = cursor.execute(query, params or [])
    conn.commit()
    data = result.fetchall()
    conn.close()
    return data
```

**Schema Patterns:**
- Timestamps: `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- IDs: Auto-increment INTEGER PRIMARY KEY
- Indexes: Create on foreign keys and frequently queried columns
- Constraints: Use CHECK for data validation (e.g., `CHECK(high >= low)`)

### 3. Decorator-Based Error Handling

Use decorators to wrap API calls with retry logic:

```python
from scripts.error_handler import with_retry, safe_api_call

@with_retry(max_attempts=3, use_cache=True)
def fetch_upstox_data(endpoint, params):
    """Automatically retries on failure, uses cache"""
    token = AuthManager.get_valid_token()
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'https://api.upstox.com/v2/{endpoint}', 
                           headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# Alternative: Use safe_api_call for graceful degradation
@safe_api_call(default_return={})
def get_market_data(symbol):
    # Returns {} on error instead of raising
    return fetch_upstox_data('market-quote', {'symbol': symbol})
```

### 4. Configuration-Driven Behavior

All configurable values in `config/trading.yaml`:

```python
import yaml

def load_config(config_path='config/trading.yaml'):
    """Load YAML configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Usage
config = load_config()
max_position = config['risk']['max_position_size']
rsi_period = config['strategies']['rsi']['period']
```

**What goes in config:**
- API credentials (not hardcoded!)
- Risk limits (max loss, position size)
- Strategy parameters (RSI periods, MACD settings)
- Alert thresholds
- Logging levels
- Feature flags (enable/disable paper trading)

### 5. Logging Everything

Use centralized logger from `logger_config.py`:

```python
from scripts.logger_config import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

def process_trade(symbol, quantity):
    logger.info(f"Processing trade: {symbol} x {quantity}")
    try:
        # Execute trade
        logger.debug(f"Trade details: {trade_data}")
    except Exception as e:
        logger.error(f"Trade failed: {symbol}", exc_info=True)
```

**Log Levels:**
- DEBUG: Detailed diagnostics (API responses, calculations)
- INFO: Key events (trades executed, signals generated)
- WARNING: Recoverable issues (rate limits, stale data)
- ERROR: Failures (API errors, validation failures)
- CRITICAL: System failures (DB corruption, auth failures)

### 6. Risk Checks Before Every Trade

Always validate with `risk_manager.py` before placing orders:

```python
from scripts.risk_manager import RiskManager

def place_order(symbol, quantity, price):
    risk_mgr = RiskManager()
    
    # Check daily loss limit
    if not risk_mgr.check_daily_loss():
        logger.error("Daily loss limit exceeded, order blocked")
        return False
    
    # Calculate position size
    allowed_qty = risk_mgr.calculate_position_size(
        symbol=symbol,
        entry_price=price,
        stop_loss_price=price * 0.98  # 2% stop
    )
    
    if quantity > allowed_qty:
        logger.warning(f"Requested {quantity}, risk allows {allowed_qty}")
        quantity = allowed_qty
    
    # Place order...
    return True
```

---

## 🔌 Integration Patterns

### Authentication Flow

```python
from scripts.auth_manager import AuthManager

# Step 1: Initialize (one-time setup)
# User runs: python scripts/auth_manager.py --action init --code AUTH_CODE

# Step 2: Use in scripts
auth = AuthManager()
token = auth.get_valid_token()  # Auto-refreshes if expired

# Step 3: Make API calls
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://api.upstox.com/v2/portfolio/holdings', headers=headers)
```

### Database Access Pattern

```python
# Bad: Direct SQL everywhere
conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM ohlc_data WHERE symbol=?", (symbol,))
# Forgot to close connection!

# Good: Use helper functions or context managers
def get_latest_ohlc(symbol):
    query = """
        SELECT * FROM ohlc_data 
        WHERE symbol = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(query, (symbol,)).fetchone()
    return dict(result) if result else None
```

### Strategy Integration

```python
from scripts.strategy_runner import StrategyRunner

# Generate signals
runner = StrategyRunner()
signals = runner.generate_rsi_signals(symbol='INFY', period=14)

# Execute signals (dry-run or live)
for signal in signals:
    if signal.action == 'BUY':
        runner.execute_signal(signal, live=False)  # Paper trade
```

### Alert Checking

```python
from scripts.alert_system import AlertSystem

# Add alert
alerts = AlertSystem()
alerts.add_price_alert(
    symbol='TCS',
    price_threshold=3500,
    alert_type='PRICE_ABOVE',
    priority='HIGH'
)

# Check alerts (in background job)
alerts.check_price_alerts()  # Triggers notifications
```

---

## 📊 Database Table Conventions

### Naming
- Tables: `lowercase_with_underscores`
- Columns: `lowercase_with_underscores`
- Indexes: `idx_{table}_{column}`

### Common Columns
Every table should have:
```sql
CREATE TABLE example_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- other columns
);

-- Trigger to update updated_at
CREATE TRIGGER update_example_timestamp 
AFTER UPDATE ON example_table
BEGIN
    UPDATE example_table SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### Key Tables Reference

**Market Data:**
- `ohlc_data` - Candlestick data (open, high, low, close, volume)
- `market_quotes` - Real-time quotes
- `historical_data` - Archived price data

**Trading:**
- `paper_orders` - Virtual orders (paper trading)
- `paper_executions` - Trade fills
- `paper_positions` - Open positions
- `trading_signals` - Strategy-generated signals
- `stop_loss_orders` - Automated stop losses

**Risk & Performance:**
- `risk_metrics` - Daily risk calculations
- `circuit_breaker_events` - Loss limit triggers
- `trade_journal` - All trades with P&L
- `daily_performance` - Aggregated daily stats
- `monthly_performance` - Monthly summaries

**System:**
- `auth_tokens` - Encrypted access tokens
- `error_logs` - API errors and retries
- `application_logs` - General logs
- `sync_jobs` - Data synchronization tracking

---

## 🛠️ Development Workflows

### Adding a New Feature

1. **Create script in `scripts/` directory**
2. **Add database tables if needed**
   ```python
   def create_tables(conn):
       conn.execute("""
           CREATE TABLE IF NOT EXISTS feature_data (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               -- columns
           )
       """)
   ```
3. **Add configuration to `config/trading.yaml`**
4. **Implement CLI interface**
5. **Add logging**
6. **Write integration with existing systems**
7. **Test standalone** (`python scripts/new_feature.py --action test`)
8. **Document in PRODUCTION_FEATURES.md**

### Extending Existing Feature

1. **Read the script** (understand current implementation)
2. **Check database schema** (what tables are affected?)
3. **Update configuration** (new parameters?)
4. **Add new methods/functions**
5. **Update CLI arguments** (new actions?)
6. **Test backward compatibility**
7. **Update logs/error handling**

### Debugging Issues

1. **Check logs:** `logs/application.log`
2. **Query database:** `sqlite3 market_data.db`
   ```sql
   SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 10;
   ```
3. **Test script standalone:** `python scripts/module.py --action test`
4. **Check configuration:** Verify `config/trading.yaml`
5. **Validate token:** `python scripts/auth_manager.py --action status`

---

## 🚨 Error Handling Best Practices

### Always Catch Specific Exceptions

```python
# Bad
try:
    data = fetch_api()
except:  # Too broad!
    pass

# Good
try:
    data = fetch_api()
except requests.exceptions.Timeout:
    logger.warning("API timeout, using cached data")
    data = get_cached_data()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        logger.error("Rate limited, waiting 60s")
        time.sleep(60)
    else:
        raise
```

### Use Error Handler Decorators

```python
from scripts.error_handler import with_retry, RateLimitError

@with_retry(max_attempts=3, backoff_base=2)
def critical_api_call():
    # Automatically retries with exponential backoff
    pass

# For graceful degradation
@safe_api_call(default_return=None)
def optional_data():
    # Returns None on error instead of crashing
    pass
```

### Log with Context

```python
# Bad
logger.error("Order failed")

# Good
logger.error(f"Order failed: symbol={symbol}, qty={qty}, reason={e}", 
             exc_info=True,  # Include stack trace
             extra={'symbol': symbol, 'user_id': user_id})
```

---

## 🔐 Security Best Practices

### Never Hardcode Credentials

```python
# Bad
API_KEY = "your_api_key_here"

# Good
config = load_config()
API_KEY = config['api']['key']
```

### Encrypt Sensitive Data

```python
from scripts.auth_manager import AuthManager

# Tokens are Fernet encrypted before storage
auth = AuthManager()
auth.store_token(access_token, refresh_token)  # Auto-encrypted
```

### Validate All Inputs

```python
def calculate_position_size(capital, risk_percent):
    # Validate
    if capital <= 0:
        raise ValueError("Capital must be positive")
    if not 0 < risk_percent < 100:
        raise ValueError("Risk percent must be between 0 and 100")
    
    # Calculate
    return capital * (risk_percent / 100)
```

---

## ⚡ Performance Optimization

### Database Indexes

```sql
-- Create indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timestamp 
ON ohlc_data(symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_signals_generated_at 
ON trading_signals(generated_at DESC);
```

### Query Optimization

```python
# Bad: N+1 queries
for symbol in symbols:
    price = conn.execute("SELECT close FROM ohlc_data WHERE symbol=?", (symbol,)).fetchone()

# Good: Single query
placeholders = ','.join('?' * len(symbols))
query = f"SELECT symbol, close FROM ohlc_data WHERE symbol IN ({placeholders})"
prices = conn.execute(query, symbols).fetchall()
```

### Caching Strategy

```python
from scripts.error_handler import error_handler

# API responses cached for 1 hour
@with_retry(use_cache=True)
def get_market_data(symbol):
    # Cached in api_cache table
    return fetch_upstox_data('market-quote', {'symbol': symbol})

# Manual cache control
error_handler.clear_cache()  # Clear all cached API responses
```

---

## 📝 Code Style Guidelines

### Docstrings

```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
    """
    Calculate annualized Sharpe ratio.
    
    Args:
        returns (list): Daily returns as decimals (e.g., 0.02 for 2%)
        risk_free_rate (float): Annual risk-free rate (default: 5%)
    
    Returns:
        float: Annualized Sharpe ratio
        
    Raises:
        ValueError: If returns list is empty
    """
    if not returns:
        raise ValueError("Returns list cannot be empty")
    
    # Implementation...
```

### Type Hints (Preferred)

```python
from typing import List, Dict, Optional

def get_positions(symbol: Optional[str] = None) -> List[Dict[str, any]]:
    """Fetch positions, optionally filtered by symbol"""
    query = "SELECT * FROM paper_positions"
    params = []
    
    if symbol:
        query += " WHERE symbol = ?"
        params.append(symbol)
    
    return execute_query(query, params)
```

### Constants

```python
# At top of file
DB_PATH = 'market_data.db'
API_BASE_URL = 'https://api.upstox.com/v2/'
DEFAULT_TIMEFRAME = '1day'
MAX_RETRIES = 3
CACHE_TTL = 3600  # 1 hour in seconds
```

---

## 🧪 Testing Patterns

### CLI Testing

```bash
# Test individual components
python scripts/auth_manager.py --action status
python scripts/risk_manager.py --action metrics
python scripts/strategy_runner.py --action performance --strategy rsi

# Dry-run mode for testing
python scripts/strategy_runner.py --action run --symbols INFY --live=false
python scripts/paper_trading.py --action order --symbol TCS --action BUY --quantity 10
```

### Database Validation

```bash
# Check data quality
python scripts/database_validator.py --action validate --tables ohlc_data,trading_signals

# Repair issues
python scripts/database_validator.py --action repair
```

### Integration Testing

```python
# test_integration.py
from scripts.strategy_runner import StrategyRunner
from scripts.paper_trading import PaperTradingSystem

def test_signal_to_execution():
    """Test full flow: signal generation → order placement → execution"""
    # Generate signal
    runner = StrategyRunner()
    signals = runner.generate_rsi_signals('INFY', period=14)
    
    # Place order in paper trading
    paper = PaperTradingSystem()
    for signal in signals:
        if signal.action == 'BUY':
            order = paper.place_order(
                symbol=signal.symbol,
                side='buy',
                quantity=10,
                order_type='market'
            )
            assert order['status'] == 'COMPLETE'
```

---

## 🔄 Background Jobs & Scheduling

### Cron Pattern for Data Sync

```bash
# crontab -e
# Sync market data every 15 minutes during trading hours (9:15 AM - 3:30 PM IST)
*/15 9-15 * * 1-5 cd /path/to/project && python scripts/data_sync_manager.py --action sync

# Check alerts every 5 minutes
*/5 * * * * cd /path/to/project && python scripts/alert_system.py --action check

# Daily performance calculation at 4 PM
0 16 * * 1-5 cd /path/to/project && python scripts/performance_analytics.py --action report
```

### Systemd Service (Alternative)

```ini
# /etc/systemd/system/upstox-sync.service
[Unit]
Description=Upstox Data Sync
After=network.target

[Service]
Type=simple
User=prince
WorkingDirectory=/Users/prince/Desktop/UPSTOX-project
ExecStart=/Users/prince/Desktop/UPSTOX-project/.venv/bin/python scripts/data_sync_manager.py --action sync
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 📦 Deployment Checklist

Before going live:

- [ ] Update `config/trading.yaml` with production credentials
- [ ] Run database validation: `python scripts/database_validator.py --action validate`
- [ ] Test authentication: `python scripts/auth_manager.py --action status`
- [ ] Enable circuit breaker in risk_manager
- [ ] Set `paper_trading.enabled: false` for live trading
- [ ] Configure alert notifications (email/Telegram)
- [ ] Set up log rotation (10MB max, 5 backups)
- [ ] Create database backup: `sqlite3 market_data.db ".backup market_data_backup.db"`
- [ ] Test error recovery: Simulate API failures
- [ ] Set up monitoring: Check `system_metrics` table regularly

---

## 🆘 Common Issues & Solutions

### Issue: Token Expired
```bash
# Solution: Refresh token
python scripts/auth_manager.py --action refresh
```

### Issue: Rate Limited (429 Error)
- **Automatic:** ErrorHandler waits 60s and retries
- **Manual:** Check error_logs table for frequency
- **Solution:** Reduce API call frequency in data_sync_manager

### Issue: Database Locked
```python
# Solution: Increase timeout
conn = sqlite3.connect('market_data.db', timeout=30.0)
```

### Issue: Missing Data Gaps
```bash
# Detect gaps
python scripts/data_sync_manager.py --action gaps --symbols INFY,TCS

# Fill gaps
python scripts/data_sync_manager.py --action sync --backfill=true
```

---

## 🔗 Quick Reference Links

- **Backend Features:** `PRODUCTION_FEATURES.md`
- **API Documentation:** `Upstox.md`
- **Configuration:** `config/trading.yaml`
- **Database Schema:** Check table creation in each script
- **Logs:** `logs/application.log`

---

**Remember:** This backend is production-ready. Handle real money with care. Test in paper trading first!
