# Testing Guide

Complete guide to testing the Upstox backtesting project.

## Quick Start

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Suite
```bash
# Candle fetcher tests
python tests/run_tests.py --candle

# Option chain fetcher tests
python tests/run_tests.py --option-chain

# Option history fetcher tests
python tests/run_tests.py --option-history

# Backtest engine tests
python tests/run_tests.py --backtest

# Expired options fetcher tests
python tests/run_tests.py --expired-options
```

### Run Individual Test Files
```bash
python -m unittest tests.test_candle_fetcher
python -m unittest tests.test_option_chain_fetcher
python -m unittest tests.test_option_history_fetcher
python -m unittest tests.test_backtest_engine
python -m unittest tests.test_expired_options_fetcher
```

### Verbosity Options
```bash
# Verbose output (default)
python tests/run_tests.py -v

# Extra verbose
python tests/run_tests.py -vv

# Quiet mode
python tests/run_tests.py -q
```

---

## Test Modules

### 1. `test_candle_fetcher.py`

Tests for stock candle data retrieval and storage.

**Classes:**
- `TestCandleFetcher`: API data fetching tests
- `TestCandleStorage`: Database storage tests
- `TestCandleValidation`: OHLCV validation tests

**Key Tests:**
- ✅ Fetch candle data from API
- ✅ Symbol resolution to instrument keys
- ✅ Timeframe mapping (1m, 5m, 15m, 1h, 1d, 1w, 1mo)
- ✅ OHLC relationship validation
- ✅ Volume validation
- ✅ Date parsing

**Run:**
```bash
python tests/run_tests.py --candle
python -m unittest tests.test_candle_fetcher.TestCandleFetcher
```

**Example Output:**
```
test_fetch_candle_data (test_candle_fetcher.TestCandleFetcher) ... ok
test_ohlc_relationships (test_candle_fetcher.TestCandleValidation) ... ok
test_symbol_resolution (test_candle_fetcher.TestCandleFetcher) ... ok
test_timeframe_mapping (test_candle_fetcher.TestCandleFetcher) ... ok
```

---

### 2. `test_option_chain_fetcher.py`

Tests for current/live option chain data fetching.

**Classes:**
- `TestOptionChainFetcher`: API data fetching tests
- `TestOptionDataValidation`: Greeks and option data validation
- `TestOptionChainStructure`: Option chain structure verification

**Key Tests:**
- ✅ Fetch available option expiries
- ✅ Fetch option chain for underlying
- ✅ Option type validation (CE/PE)
- ✅ Greeks validation (delta, gamma, theta, vega, IV)
- ✅ Bid-ask spread validation
- ✅ Volume and OI validation
- ✅ Symmetric CE/PE chain validation

**Run:**
```bash
python tests/run_tests.py --option-chain
python -m unittest tests.test_option_chain_fetcher
```

**Example Output:**
```
test_get_option_expiries (test_option_chain_fetcher.TestOptionChainFetcher) ... ok
test_fetch_option_chain (test_option_chain_fetcher.TestOptionChainFetcher) ... ok
test_greeks_validation (test_option_chain_fetcher.TestOptionDataValidation) ... ok
test_iv_validation (test_option_chain_fetcher.TestOptionDataValidation) ... ok
```

---

### 3. `test_option_history_fetcher.py`

Tests for historical option candle data retrieval.

**Classes:**
- `TestOptionHistoryFetcher`: Historical data fetching tests
- `TestOptionCandleStorage`: Storage and structure tests
- `TestOptionExpiryManagement`: Expiry date management
- `TestOptionCandleTimeframes`: Timeframe support

**Key Tests:**
- ✅ Fetch historical option candles
- ✅ ISO8601 timestamp parsing
- ✅ OHLCV validation for options
- ✅ Option symbol format validation
- ✅ Expiry date ordering
- ✅ Timeframe support verification

**Run:**
```bash
python tests/run_tests.py --option-history
python -m unittest tests.test_option_history_fetcher
```

**Example Output:**
```
test_fetch_option_candles (test_option_history_fetcher.TestOptionHistoryFetcher) ... ok
test_timestamp_parsing (test_option_history_fetcher.TestOptionHistoryFetcher) ... ok
test_ohlc_validation (test_option_history_fetcher.TestOptionHistoryFetcher) ... ok
```

---

### 4. `test_backtest_engine.py`

Tests for backtesting engine and strategy execution.

**Classes:**
- `TestCandleDataLoading`: Candle data loading tests
- `TestSMAStrategy`: Simple Moving Average strategy tests
- `TestRSIStrategy`: RSI strategy tests
- `TestBacktestMetrics`: Metrics calculation tests
- `TestStrategyExecution`: Strategy execution tests
- `TestStrategyValidation`: Parameter validation tests

**Key Tests:**
- ✅ Load candle data from database
- ✅ Candle ordering verification
- ✅ SMA calculation
- ✅ RSI calculation
- ✅ Strategy initialization
- ✅ Signal generation
- ✅ Backtest metrics (Sharpe, Sortino, Calmar, max DD, etc.)
- ✅ Return calculation
- ✅ Win rate calculation
- ✅ Position management logic
- ✅ Period validation

**Run:**
```bash
python tests/run_tests.py --backtest
python -m unittest tests.test_backtest_engine
```

**Example Output:**
```
test_load_candle_data (test_backtest_engine.TestCandleDataLoading) ... ok
test_sma_calculation (test_backtest_engine.TestSMAStrategy) ... ok
test_return_calculation (test_backtest_engine.TestBacktestMetrics) ... ok
test_sharpe_ratio_bounds (test_backtest_engine.TestBacktestMetrics) ... ok
```

---

### 5. `test_expired_options_fetcher.py`

Tests for expired option contract data retrieval.

**Classes:**
- `TestExpiredOptionsFetcher`: API data fetching tests
- `TestOptionDataParsing`: Data parsing and extraction
- `TestExpiredOptionsStorage`: Storage and uniqueness
- `TestExpiredOptionsValidation`: Data validation

**Key Tests:**
- ✅ Fetch available expiry dates
- ✅ Fetch expired option contracts
- ✅ Option type filtering (CE/PE)
- ✅ Strike price filtering
- ✅ Option type extraction from symbol
- ✅ Strike extraction from symbol
- ✅ Table creation and uniqueness constraints
- ✅ Data validation (strike, type, date format)

**Run:**
```bash
python tests/run_tests.py --expired-options
python -m unittest tests.test_expired_options_fetcher
```

**Example Output:**
```
test_get_available_expiries (test_expired_options_fetcher.TestExpiredOptionsFetcher) ... ok
test_fetch_expired_option_contracts (test_expired_options_fetcher.TestExpiredOptionsFetcher) ... ok
test_parse_option_data (test_expired_options_fetcher.TestOptionDataParsing) ... ok
```

---

## Running Tests in Different Environments

### Using Python's unittest directly
```bash
# Run all tests
python -m unittest discover tests -p "test_*.py"

# Run specific test class
python -m unittest tests.test_candle_fetcher.TestCandleFetcher

# Run specific test method
python -m unittest tests.test_candle_fetcher.TestCandleFetcher.test_fetch_candle_data
```

### With coverage reporting (requires coverage package)
```bash
pip install coverage

# Run tests with coverage
coverage run -m unittest discover tests -p "test_*.py"

# Generate coverage report
coverage report
coverage html  # Creates htmlcov/index.html
```

### With pytest (requires pytest)
```bash
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific test
pytest tests/test_candle_fetcher.py

# Run with coverage
pytest --cov=scripts tests/
```

---

## Test Requirements

### API Access
Most tests require valid Upstox API credentials:
- Valid OAuth access token
- API keys configured in environment

**If API is unavailable:**
- Tests will be skipped with message: `Skipped: API unavailable`
- This is normal behavior and not a failure

### Database
Some tests use SQLite database:
- Database is created automatically if missing
- Use in-memory DB (`:memory:`) for isolated tests
- Some tests may modify the database

### Dependencies
Required packages:
```bash
pip install requests pandas numpy vectorbt python-dateutil
```

---

## Writing New Tests

### Template for New Test Module
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database

class TestNewFeature(unittest.TestCase):
    """Test suite for new feature."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        initialize_database()
    
    def test_feature_basic(self):
        """Test basic functionality."""
        # Arrange
        input_data = ...
        
        # Act
        result = my_function(input_data)
        
        # Assert
        self.assertEqual(result, expected_value)
    
    def test_feature_error_handling(self):
        """Test error handling."""
        with self.assertRaises(ValueError):
            my_function(invalid_input)

if __name__ == "__main__":
    unittest.main()
```

### Common Assertion Methods
```python
# Equality
self.assertEqual(a, b)
self.assertNotEqual(a, b)

# Truth
self.assertTrue(x)
self.assertFalse(x)
self.assertIsNone(x)
self.assertIsNotNone(x)

# Membership
self.assertIn(a, b)
self.assertNotIn(a, b)

# Type
self.assertIsInstance(a, type)
self.assertNotIsInstance(a, type)

# Comparison
self.assertGreater(a, b)
self.assertLess(a, b)
self.assertGreaterEqual(a, b)
self.assertLessEqual(a, b)

# Exceptions
self.assertRaises(ExceptionType, function, *args)
with self.assertRaises(ExceptionType):
    function()

# Floating point
self.assertAlmostEqual(a, b, places=7)
```

---

## Continuous Integration

### GitHub Actions Example
Create `.github/workflows/tests.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python tests/run_tests.py
```

---

## Troubleshooting

### Tests Fail with "API unavailable"
**Solution:** Ensure valid OAuth token exists
```bash
# Check if token file exists
cat oauth_token.json

# If missing, run OAuth flow
python scripts/oauth_server.py
```

### Database Locked Error
**Solution:** Close other connections and try again
```bash
# Remove existing database and let tests recreate
rm market_data.db
python tests/run_tests.py
```

### Import Errors
**Solution:** Ensure scripts directory is in Python path
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/UPSTOX-project"
```

### Timeframe Issues
**Solution:** Use correct format (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
```python
# Correct
fetch_candle_data("INFY", "1d", start_date, end_date)

# Incorrect
fetch_candle_data("INFY", "1 day", start_date, end_date)
```

---

## Best Practices

1. **Run tests before committing**
   ```bash
   python tests/run_tests.py
   ```

2. **Write tests for new features**
   - Test normal cases
   - Test edge cases
   - Test error handling

3. **Keep tests independent**
   - Don't rely on test execution order
   - Use setUp/tearDown for isolation

4. **Use descriptive test names**
   ```python
   # Good
   def test_fetch_option_chain_with_valid_underlying(self):
   
   # Bad
   def test_option_chain(self):
   ```

5. **Document complex tests**
   ```python
   def test_complex_feature(self):
       """Test complex feature with multiple steps.
       
       This test verifies that the feature handles edge cases
       correctly by testing with boundary values.
       """
   ```

---

## Contact & Support

For test-related issues:
1. Check existing test output
2. Review test comments and docstrings
3. Verify API credentials are valid
4. Check database is initialized

---

**Last Updated:** 2025-01-31
