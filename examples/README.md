# 📚 Example Scripts

This folder contains demonstration scripts showing how to use various features of the UPSTOX trading platform.

## Files

### DEMO_EXPIRED_OPTIONS.py
**Purpose:** Demonstrates how to fetch and work with expired options data

**Features:**
- Fetch expired options for specific dates
- Filter by symbol and expiry
- Store data in database
- Generate reports

**Usage:**
```bash
python examples/DEMO_EXPIRED_OPTIONS.py
```

---

### DEMO_LIVE_TRADING.py  
**Purpose:** Demonstrates live trading capabilities with Upstox API

**Features:**
- Real-time order placement
- Position management
- P&L calculation
- Risk validation

**⚠️ WARNING:** This uses real API calls and can place actual orders. Use with caution!

**Usage:**
```bash
# Ensure .env is configured with valid credentials
python examples/DEMO_LIVE_TRADING.py
```

---

### DEMO_NEWS_AND_ANNOUNCEMENTS.py
**Purpose:** Demonstrates integration with NewsAPI and NSE corporate announcements

**Features:**
- Fetch latest market news
- Get corporate announcements
- AI-powered sentiment analysis (FinBERT)
- Store news data in database

**Requirements:**
- NEWS_API_KEY in .env file
- Internet connection

**Usage:**
```bash
python examples/DEMO_NEWS_AND_ANNOUNCEMENTS.py
```

---

## Prerequisites

All demo scripts require:

1. **Python Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Database:**
   ```bash
   # Database will be created automatically
   # Located at: market_data.db
   ```

---

## Best Practices

### When Running Demos

1. **Test Environment First:** Use paper trading before live trading
2. **Check Credentials:** Ensure API keys are valid
3. **Review Output:** Check console output for errors
4. **Monitor Database:** Verify data is being stored correctly
5. **Read the Code:** Understand what each demo does before running

### Safety Tips for DEMO_LIVE_TRADING.py

⚠️ **IMPORTANT:** This script places REAL orders!

- Start with small quantities
- Use limit orders (not market orders)
- Test with liquid stocks (high volume)
- Monitor positions immediately after execution
- Have stop-losses in place
- Never run unattended

---

## Learning Path

**Recommended Order:**

1. **Start Here:** `DEMO_NEWS_AND_ANNOUNCEMENTS.py`
   - No trading risk
   - Learn data fetching

2. **Next:** `DEMO_EXPIRED_OPTIONS.py`
   - Learn options data handling
   - Understand data structures

3. **Advanced:** `DEMO_LIVE_TRADING.py`
   - Only after understanding the platform
   - Start with paper trading mode

---

## Customization

All demo scripts can be customized:

```python
# Example: Modify symbol list
SYMBOLS = ['RELIANCE', 'TCS', 'INFY']  # Change these

# Example: Modify date range
start_date = '2024-01-01'
end_date = '2024-12-31'

# Example: Modify order quantities
qty = 10  # Adjust based on capital
```

---

## Troubleshooting

### Import Errors
```bash
# Ensure you're in project root
cd /path/to/UPSTOX-PROJECT
python examples/DEMO_*.py  # Run from project root
```

### API Errors
```bash
# Check credentials
cat .env | grep -E "CLIENT_ID|CLIENT_SECRET"

# Verify token
python scripts/auth_manager.py
```

### Database Errors
```bash
# Check database exists
ls -lh market_data.db

# Verify schema
python scripts/check_schema.py
```

---

## Integration with Main Application

These demos show patterns used in the main application:

| Demo Feature | Main Application Location |
|--------------|---------------------------|
| Options fetching | `scripts/expired_options_fetcher.py` |
| Order placement | `scripts/order_manager_v3.py` |
| News integration | `scripts/news_alerts_manager.py` |
| Data storage | `scripts/data_sync_manager.py` |
| Sentiment analysis | `scripts/ai_service.py` |

---

## Additional Examples

For more examples, see:

- **API Server:** `scripts/api_server.py` - Complete API implementation
- **Backtesting:** `scripts/backtest_engine.py` - Strategy testing
- **Paper Trading:** `scripts/paper_trading.py` - Virtual trading
- **Frontend:** `dashboard_ui/pages/` - UI integration examples

---

## Contributing

To add new demo scripts:

1. Create `DEMO_YOUR_FEATURE.py`
2. Add comprehensive comments
3. Include error handling
4. Update this README
5. Submit pull request

---

## Support

- **Documentation:** See `/COMPREHENSIVE_GUIDE.md`
- **API Docs:** See `/API_ENDPOINTS.md`
- **Issues:** https://github.com/sheldcoop/UPSTOX-PROJECT/issues

---

**Note:** These are educational examples. Always test in a safe environment before using with real money.

**Last Updated:** February 3, 2026
