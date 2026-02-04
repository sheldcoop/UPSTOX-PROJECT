# 🛠️ Utility Scripts

This folder contains utility scripts for maintenance, debugging, and administrative tasks.

## Maintenance Scripts

### update_indices_db.py
**Purpose:** Update NSE index constituent data

**Usage:**
```bash
python scripts/utilities/update_indices_db.py
```

**Features:**
- Downloads latest NSE index data
- Updates database with constituents
- Supports NIFTY 50, 100, 200, 500, etc.

**Schedule:** Run monthly

---

### verify_backend.py
**Purpose:** Verify backend services are working correctly

**Usage:**
```bash
python scripts/utilities/verify_backend.py
```

**Checks:**
- Database connectivity
- API server endpoints
- Service initialization
- Data integrity

---

### run_backtest.py
**Purpose:** Run strategy backtests from command line

**Usage:**
```bash
python scripts/utilities/run_backtest.py --strategy SMA --symbol NIFTY --start 2024-01-01 --end 2024-12-31
```

---

## Debugging Scripts

### debug_movers_db.py
**Purpose:** Debug top movers database issues

**Usage:**
```bash
python scripts/utilities/debug_movers_db.py
```

---

### check_*.py Scripts

Collection of quick check scripts:

- **check_fo_eq.py** - Verify F&O vs Equity mapping
- **check_fo_match.py** - Check F&O instrument matching  
- **check_futures.py** - Verify futures data
- **check_segments.py** - Check market segments
- **check_token.py** - Verify authentication token
- **check_ufbl.py** - Check Upstox FNO Balance

**Usage:**
```bash
python scripts/utilities/check_*.py
```

---

## Data Scripts

### download_friday.py
**Purpose:** Download Friday expiry options data

**Usage:**
```bash
python scripts/utilities/download_friday.py
```

---

### downloads.py
**Purpose:** Generic download utility

**Usage:**
```bash
python scripts/utilities/downloads.py
```

---

## Testing Scripts

### test_movers_service.py
**Purpose:** Test top movers service functionality

**Usage:**
```bash
python scripts/utilities/test_movers_service.py
```

---

## Documentation

### CREATION_SUMMARY.py
**Purpose:** Generate project creation summary

**Usage:**
```bash
python scripts/utilities/CREATION_SUMMARY.py
```

---

## Management Scripts

### store_token.py
**Purpose:** Securely store authentication tokens

**Usage:**
```bash
python scripts/utilities/store_token.py
```

---

## Best Practices

### Running Utilities

1. **Always run from project root:**
   ```bash
   cd /path/to/UPSTOX-PROJECT
   python scripts/utilities/script_name.py
   ```

2. **Check environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Review output:**
   - Check console for errors
   - Verify database changes
   - Monitor logs/

### Safety

- **Backup before running:** `cp market_data.db market_data.db.backup`
- **Test on copy first:** Copy database, test, then apply to production
- **Read the code:** Understand what each utility does

---

## Scheduling

Some utilities should run regularly:

```bash
# Crontab examples

# Update indices (monthly, 1st day at 2 AM)
0 2 1 * * cd /path/to/UPSTOX-PROJECT && .venv/bin/python scripts/utilities/update_indices_db.py

# Verify backend (daily at 8 AM)
0 8 * * * cd /path/to/UPSTOX-PROJECT && .venv/bin/python scripts/utilities/verify_backend.py

# Download Friday data (every Friday at 3:30 PM)
30 15 * * 5 cd /path/to/UPSTOX-PROJECT && .venv/bin/python scripts/utilities/download_friday.py
```

---

## Troubleshooting

### Import Errors
```bash
# Run from project root, not utilities folder
cd /path/to/UPSTOX-PROJECT
python scripts/utilities/script.py  # ✅ Correct
```

### Database Locked
```bash
# Stop all services first
sudo systemctl stop upstox-api upstox-frontend
# Then run utility
# Then restart services
```

### Permission Denied
```bash
chmod +x scripts/utilities/*.py
```

---

## Integration

These utilities support the main application:

| Utility | Main Application Component |
|---------|---------------------------|
| update_indices_db.py | Signals page, Strategy filters |
| verify_backend.py | Health monitoring, CI/CD |
| run_backtest.py | Backtest page |
| check_token.py | Authentication system |
| store_token.py | OAuth flow |

---

## Contributing

To add new utilities:

1. Create descriptive filename (e.g., `analyze_performance.py`)
2. Add docstrings and comments
3. Include usage examples
4. Add error handling
5. Update this README
6. Submit pull request

---

## Support

- **Main Docs:** `/COMPREHENSIVE_GUIDE.md`
- **Issues:** https://github.com/sheldcoop/UPSTOX-PROJECT/issues

---

**Last Updated:** February 3, 2026
