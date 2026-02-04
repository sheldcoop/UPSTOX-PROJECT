# 🧪 Testing Guide

**UPSTOX Trading Platform**  
**Last Updated:** February 3, 2026

Comprehensive guide for testing the UPSTOX Trading Platform.

---

## Table of Contents

- [Overview](#overview)
- [Test Infrastructure](#test-infrastructure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Mocking External APIs](#mocking-external-apis)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Common Testing Patterns](#common-testing-patterns)

---

## Overview

### Test Framework

- **Framework:** `pytest` (primary) and `unittest` (legacy)
- **Coverage Tool:** `pytest-cov`
- **Mocking:** `unittest.mock` and `pytest-mock`
- **API Testing:** `requests` library
- **Database:** In-memory SQLite for tests

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_utils.py            # Test utilities and helpers
├── test_auth.py             # Authentication tests
├── test_risk_manager.py     # Risk management tests
├── test_order_manager.py    # Order execution tests
├── test_strategy_runner.py  # Strategy tests
├── test_api_*.py            # API endpoint tests
├── test_*.py                # Component tests
└── manual/                  # Manual integration tests
    ├── test_live_data.py    # Requires live credentials
    └── test_nse_inventory.py
```

---

## Test Infrastructure

### Setup Test Environment

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Or install from requirements
pip install -r requirements.txt
```

### Test Configuration

Create `pytest.ini` in project root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require external services)
    slow: Slow-running tests
    live: Tests that require live API credentials
```

### Test Fixtures

Located in `tests/conftest.py`:

```python
import pytest
import sqlite3
from scripts.auth_manager import AuthManager

@pytest.fixture
def auth_manager():
    """Provide AuthManager instance for testing."""
    return AuthManager()

@pytest.fixture
def test_db():
    """Provide in-memory database for tests."""
    conn = sqlite3.connect(':memory:')
    # Initialize schema
    yield conn
    conn.close()

@pytest.fixture
def mock_api_response():
    """Provide mock API responses."""
    return {
        'status': 'success',
        'data': {'test': 'value'}
    }
```

---

## Running Tests

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With summary
pytest -v --tb=short
```

### Run Specific Tests

```bash
# Run specific file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestAuthManager

# Run specific test method
pytest tests/test_auth.py::TestAuthManager::test_token_encryption

# Run tests matching pattern
pytest -k "auth"
pytest -k "test_fetch"
```

### Run by Category

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Exclude live tests (requires credentials)
pytest -m "not live"
```

### Run with Coverage

```bash
# Basic coverage
pytest --cov=scripts

# With HTML report
pytest --cov=scripts --cov-report=html

# With term report showing missing lines
pytest --cov=scripts --cov-report=term-missing

# Coverage threshold (fail if below 80%)
pytest --cov=scripts --cov-fail-under=80
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Auto-detect CPU cores
pytest -n auto
```

---

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions/methods in isolation  
**Marker:** `@pytest.mark.unit`  
**Speed:** Fast (< 1 second each)  
**Dependencies:** None (fully mocked)

**Example:**

```python
import pytest
from scripts.risk_manager import RiskManager

@pytest.mark.unit
def test_calculate_position_size():
    """Test position size calculation."""
    rm = RiskManager()
    size = rm.calculate_position_size(
        account_value=100000,
        risk_percent=2,
        entry_price=100,
        stop_loss=95
    )
    assert size == 400  # (100000 * 0.02) / (100 - 95)
```

### 2. Integration Tests

**Purpose:** Test interactions between components  
**Marker:** `@pytest.mark.integration`  
**Speed:** Medium (1-10 seconds each)  
**Dependencies:** Database, mocked external APIs

**Example:**

```python
@pytest.mark.integration
def test_order_flow(test_db, mock_api):
    """Test complete order placement flow."""
    # Setup
    order_manager = OrderManager(test_db)
    risk_manager = RiskManager(test_db)
    
    # Execute
    order = order_manager.place_order(...)
    risk_check = risk_manager.validate_order(order)
    
    # Assert
    assert order.status == 'placed'
    assert risk_check.passed is True
```

### 3. API Tests

**Purpose:** Test Flask API endpoints  
**Marker:** `@pytest.mark.api`  
**Speed:** Fast-Medium  
**Dependencies:** Flask test client, mocked services

**Example:**

```python
import pytest
from scripts.api_server import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.mark.api
def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'running'
```

### 4. Manual Tests

**Purpose:** Tests requiring live credentials or human verification  
**Marker:** `@pytest.mark.live`  
**Speed:** Slow (10+ seconds)  
**Dependencies:** Valid Upstox API credentials

**Example:**

```python
@pytest.mark.live
def test_live_market_data():
    """Fetch real market data from Upstox API."""
    # Skip if no credentials
    if not os.getenv('UPSTOX_CLIENT_ID'):
        pytest.skip("No live credentials available")
    
    # Test with real API
    auth = AuthManager()
    token = auth.get_valid_token()
    assert token is not None
```

---

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange: Set up test data and conditions
    account = Account(balance=10000)
    
    # Act: Execute the code being tested
    result = account.withdraw(500)
    
    # Assert: Verify the results
    assert result is True
    assert account.balance == 9500
```

### Using Fixtures

```python
@pytest.fixture
def sample_account():
    """Provide test account."""
    return Account(balance=10000)

def test_with_fixture(sample_account):
    """Test using fixture."""
    sample_account.withdraw(500)
    assert sample_account.balance == 9500
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (100, 105),  # 5% gain
    (200, 210),  # 5% gain
    (50, 52.5),  # 5% gain
])
def test_calculate_gain(input, expected):
    """Test gain calculation with multiple inputs."""
    result = calculate_gain(input, profit_percent=5)
    assert result == expected
```

### Testing Exceptions

```python
def test_invalid_order():
    """Test that invalid order raises exception."""
    with pytest.raises(ValueError, match="Invalid quantity"):
        place_order(quantity=-10)
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous function."""
    result = await fetch_data_async()
    assert result is not None
```

---

## Mocking External APIs

### Mock Upstox API Responses

```python
from unittest.mock import Mock, patch

@patch('scripts.auth_manager.requests.post')
def test_token_exchange(mock_post):
    """Test token exchange with mocked API."""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        'access_token': 'test_token',
        'expires_in': 86400
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # Test
    auth = AuthManager()
    token_data = auth.exchange_code_for_token('test_code')
    
    # Assert
    assert token_data['access_token'] == 'test_token'
    mock_post.assert_called_once()
```

### Mock Database Operations

```python
@patch('scripts.database_pool.get_connection')
def test_database_operation(mock_db):
    """Test with mocked database."""
    # Setup mock
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [(1, 'INFY', 1500.0)]
    mock_conn.cursor.return_value = mock_cursor
    mock_db.return_value = mock_conn
    
    # Test
    result = fetch_holdings()
    
    # Assert
    assert len(result) == 1
    assert result[0]['symbol'] == 'INFY'
```

### Mock Time-Dependent Functions

```python
from datetime import datetime
from unittest.mock import patch

@patch('scripts.strategy_runner.datetime')
def test_time_dependent(mock_datetime):
    """Test function that depends on current time."""
    # Fix time to specific value
    mock_datetime.now.return_value = datetime(2026, 2, 3, 9, 15, 0)
    
    # Test
    result = check_market_hours()
    
    # Assert
    assert result is True  # Market is open at 9:15 AM
```

---

## Coverage Reports

### Generate HTML Coverage Report

```bash
# Run tests with coverage
pytest --cov=scripts --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = scripts
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

### View Coverage in Terminal

```bash
pytest --cov=scripts --cov-report=term-missing
```

---

## CI/CD Integration

### GitHub Actions Configuration

Already configured in `.github/workflows/ci-cd.yml`:

```yaml
- name: Run pytest
  run: pytest tests/ -v --tb=short || echo "Tests completed"
  env:
    REDIS_URL: redis://localhost:6379/0
```

### Tests That Run in CI

- ✅ Unit tests (all)
- ✅ Integration tests with mocked APIs
- ❌ Live tests (skipped - no credentials)
- ❌ Manual tests (skipped - require human input)

### Skip Tests in CI

```python
import os
import pytest

@pytest.mark.skipif(
    os.getenv('CI') == 'true',
    reason="Requires live credentials not available in CI"
)
def test_live_api():
    """Test that only runs locally."""
    pass
```

---

## Common Testing Patterns

### 1. Database Testing Pattern

```python
@pytest.fixture
def test_database():
    """Create in-memory test database."""
    conn = sqlite3.connect(':memory:')
    # Create tables
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE positions (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            quantity INTEGER
        )
    ''')
    conn.commit()
    yield conn
    conn.close()

def test_insert_position(test_database):
    """Test database insertion."""
    cursor = test_database.cursor()
    cursor.execute(
        "INSERT INTO positions (symbol, quantity) VALUES (?, ?)",
        ('INFY', 100)
    )
    test_database.commit()
    
    cursor.execute("SELECT * FROM positions WHERE symbol = ?", ('INFY',))
    result = cursor.fetchone()
    assert result[1] == 'INFY'
    assert result[2] == 100
```

### 2. API Endpoint Testing Pattern

```python
def test_api_endpoint_success(client):
    """Test successful API call."""
    response = client.get('/api/portfolio/positions')
    assert response.status_code == 200
    assert 'positions' in response.json

def test_api_endpoint_error(client):
    """Test API error handling."""
    response = client.post('/api/orders', json={})
    assert response.status_code == 400
    assert 'error' in response.json
```

### 3. Strategy Testing Pattern

```python
def test_strategy_signal():
    """Test strategy signal generation."""
    # Arrange: Create test OHLC data
    data = [
        {'timestamp': 1, 'close': 100},
        {'timestamp': 2, 'close': 105},
        {'timestamp': 3, 'close': 110},
    ]
    
    # Act: Run strategy
    strategy = MomentumStrategy()
    signal = strategy.generate_signal(data)
    
    # Assert: Check signal
    assert signal == 'BUY'  # Upward momentum
```

---

## Test Data Management

### Test Fixtures Location

```
tests/
├── fixtures/
│   ├── sample_ohlc.json      # Sample candle data
│   ├── sample_positions.json  # Sample positions
│   └── sample_orders.json     # Sample orders
```

### Load Test Data

```python
import json

@pytest.fixture
def sample_ohlc_data():
    """Load sample OHLC data from fixture."""
    with open('tests/fixtures/sample_ohlc.json') as f:
        return json.load(f)

def test_with_sample_data(sample_ohlc_data):
    """Test using fixture data."""
    assert len(sample_ohlc_data) > 0
```

---

## Debugging Failed Tests

### Run Single Failing Test

```bash
# Run with more verbose output
pytest tests/test_auth.py::test_token_refresh -vv

# Show local variables on failure
pytest tests/test_auth.py::test_token_refresh -l

# Drop into debugger on failure
pytest tests/test_auth.py::test_token_refresh --pdb
```

### Print Debug Information

```python
def test_calculation():
    """Test with debug output."""
    result = calculate(10, 20)
    print(f"Result: {result}")  # Shown with pytest -s
    assert result == 30
```

### Use Logging in Tests

```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    with caplog.at_level(logging.INFO):
        perform_operation()
    
    assert "Operation completed" in caplog.text
```

---

## Best Practices

1. **Test One Thing Per Test**
   - Each test should verify one behavior
   - Makes failures easier to diagnose

2. **Use Descriptive Names**
   ```python
   # Good
   def test_order_placement_validates_quantity_is_positive():
       pass
   
   # Bad
   def test_order():
       pass
   ```

3. **Keep Tests Independent**
   - Tests should not depend on each other
   - Can run in any order

4. **Mock External Dependencies**
   - Don't rely on external APIs in tests
   - Use mocks and fixtures

5. **Test Edge Cases**
   ```python
   @pytest.mark.parametrize("quantity", [0, -1, 1000000])
   def test_quantity_edge_cases(quantity):
       # Test boundary conditions
       pass
   ```

6. **Clean Up After Tests**
   ```python
   @pytest.fixture
   def temp_file():
       f = open('test.txt', 'w')
       yield f
       f.close()
       os.remove('test.txt')  # Clean up
   ```

---

## Additional Resources

- **pytest Documentation:** https://docs.pytest.org/
- **unittest Documentation:** https://docs.python.org/3/library/unittest.html
- **pytest-cov:** https://pytest-cov.readthedocs.io/
- **Testing Best Practices:** https://docs.python-guide.org/writing/tests/

---

**Test Status:** See CI/CD pipeline for latest results  
**Coverage Goal:** 80%+ for critical modules  
**CI/CD:** Tests run automatically on every PR

