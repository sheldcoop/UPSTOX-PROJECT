# 🛠️ Local Development Guide

**UPSTOX Trading Platform**  
**Last Updated:** February 3, 2026

This guide helps you set up and run the UPSTOX Trading Platform locally for development.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Project Structure](#project-structure)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Database Management](#database-management)
- [Debugging](#debugging)
- [Code Quality Tools](#code-quality-tools)
- [Common Tasks](#common-tasks)

---

## Prerequisites

### Required Software

- **Python 3.11+** (required)
- **Git** (required)
- **SQLite 3** (usually pre-installed)
- **Redis** (optional, for caching)

### Recommended Tools

- **VS Code** or **PyCharm**
- **Postman** or **Insomnia** (for API testing)
- **DB Browser for SQLite** (for database inspection)

---

## Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Minimum required variables:**
```env
UPSTOX_CLIENT_ID=your_client_id
UPSTOX_CLIENT_SECRET=your_client_secret
UPSTOX_REDIRECT_URI=http://localhost:5050/auth/callback
ENCRYPTION_KEY=generate_with_script
```

Generate encryption key:
```bash
python scripts/generate_encryption_key.py
```

### 5. Initialize Database

```bash
# Database will be created automatically on first run
# To manually initialize:
python scripts/database_validator.py
```

### 6. Start Development Servers

**Terminal 1 - API Server (port 8000):**
```bash
python scripts/api_server.py
```

**Terminal 2 - Frontend Dashboard (port 5001):**
```bash
python nicegui_dashboard.py
```

**Terminal 3 - OAuth Server (port 5050):**
```bash
python scripts/oauth_server.py
```

### 7. Access the Application

- **Frontend Dashboard:** http://localhost:5001
- **API Endpoint:** http://localhost:8000/api/health
- **OAuth Login:** http://localhost:5050/auth/start

---

## Project Structure

```
UPSTOX-PROJECT/
├── scripts/                    # Backend services and utilities
│   ├── auth_manager.py        # OAuth authentication
│   ├── risk_manager.py        # Risk management
│   ├── order_manager.py       # Order execution
│   ├── strategy_runner.py     # Trading strategies
│   ├── paper_trading.py       # Paper trading engine
│   ├── websocket_*.py         # WebSocket streaming
│   ├── blueprints/            # Flask API blueprints
│   │   ├── portfolio.py       # Portfolio endpoints
│   │   ├── orders.py          # Order endpoints
│   │   ├── data.py            # Market data endpoints
│   │   └── ...
│   └── ...
├── dashboard_ui/              # NiceGUI frontend
│   ├── pages/                 # UI pages
│   │   ├── home.py
│   │   ├── positions.py
│   │   ├── fno.py
│   │   └── ...
│   ├── services/              # Frontend services
│   └── common.py              # Shared UI components
├── tests/                     # Test suite
│   ├── test_auth.py
│   ├── test_*.py
│   └── manual/                # Manual integration tests
├── config/                    # Configuration files
│   └── trading.yaml           # Trading configuration
├── docs/                      # Documentation
├── logs/                      # Application logs
├── cache/                     # Cache directory
├── market_data.db            # SQLite database
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in Git)
└── .env.example              # Environment template
```

---

## Running the Application

### Development Mode (Recommended)

Run each component in a separate terminal:

#### API Server
```bash
python scripts/api_server.py
```

**Features:**
- Auto-reload on code changes
- Debug logging enabled
- Port: 8000

#### Frontend Dashboard
```bash
python nicegui_dashboard.py
```

**Features:**
- Hot reload on save
- Interactive debug console
- Port: 5001

#### OAuth Server
```bash
python scripts/oauth_server.py
```

**Features:**
- Handles Upstox OAuth flow
- Auto-redirects to dashboard
- Port: 5050

### Production Mode (Testing)

```bash
# Start all services with Gunicorn
./start_production.sh

# Or individually:
gunicorn --config gunicorn_config.py wsgi:application
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit files in your IDE. The development servers will auto-reload.

### 3. Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest tests/ --cov=scripts --cov-report=html
```

### 4. Format Code

```bash
# Format with Black
black .

# Check with Flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 6. Create Pull Request

- Go to GitHub repository
- Click "New Pull Request"
- CI/CD pipeline will run automatically

---

## Testing

See `TESTING.md` for comprehensive testing guide.

### Quick Test Commands

```bash
# Unit tests only
python -m pytest tests/ -m "not integration"

# Integration tests (requires valid API token)
python -m pytest tests/ -m integration

# Specific test
python -m pytest tests/test_auth.py::TestAuthManager::test_token_encryption

# With verbose output
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=scripts --cov-report=term-missing
```

---

## Database Management

### View Database

```bash
# Open in SQLite CLI
sqlite3 market_data.db

# Useful commands:
.tables                    # List all tables
.schema ohlc_data         # Show table schema
SELECT * FROM trading_signals LIMIT 10;  # Query data
.exit                      # Exit
```

### Database GUI Tools

- **DB Browser for SQLite** (recommended)
- **DBeaver**
- **DataGrip** (JetBrains)

### Backup Database

```bash
# Manual backup
sqlite3 market_data.db ".backup 'backups/dev_backup.db'"

# Or use backup script
./scripts/backup_db.sh
```

### Reset Database

```bash
# CAUTION: This deletes all data!
rm market_data.db upstox.db
python scripts/database_validator.py
```

### Run Database Validation

```bash
python scripts/database_validator.py
```

---

## Debugging

### Enable Debug Mode

```bash
# In .env file
export FLASK_DEBUG=True

# Run API server
python scripts/api_server.py
```

### Debug Logging

**Increase log verbosity:**

```python
# In your module
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Interactive Debugging

#### Using pdb

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

#### Using VS Code

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: API Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/scripts/api_server.py",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Frontend",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/nicegui_dashboard.py",
      "console": "integratedTerminal"
    }
  ]
}
```

### Debug API Calls

```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/health

# With authentication
curl -X GET http://localhost:8000/api/portfolio/positions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Use the API debugger page in the dashboard
# Navigate to: http://localhost:5001/api-debugger
```

---

## Code Quality Tools

### Black (Code Formatter)

```bash
# Format all files
black .

# Check without modifying
black --check .

# Format specific file
black scripts/auth_manager.py
```

### Flake8 (Linter)

```bash
# Run critical checks
flake8 . --count --select=E9,F63,F7,F82 --show-source

# Run all checks
flake8 . --count --max-line-length=100 --statistics

# Ignore specific errors
flake8 . --ignore=E501,W503
```

### Type Checking (mypy)

```bash
# Install mypy
pip install mypy

# Run type checking
mypy scripts/
```

---

## Common Tasks

### Update Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade flask

# Freeze current environment
pip freeze > requirements.txt
```

### Add New API Endpoint

1. Create blueprint in `scripts/blueprints/`:

```python
# scripts/blueprints/my_feature.py
from flask import Blueprint, jsonify

my_feature_bp = Blueprint('my_feature', __name__)

@my_feature_bp.route('/api/my-feature', methods=['GET'])
def get_feature():
    return jsonify({'status': 'ok'})
```

2. Register blueprint in `scripts/api_server.py`:

```python
from scripts.blueprints.my_feature import my_feature_bp

app.register_blueprint(my_feature_bp)
```

### Add New UI Page

1. Create page in `dashboard_ui/pages/`:

```python
# dashboard_ui/pages/my_page.py
from nicegui import ui

def create_page():
    with ui.card():
        ui.label('My New Page')
        # Add your UI components
```

2. Add route in `nicegui_dashboard.py`:

```python
from dashboard_ui.pages import my_page

@ui.page('/my-page')
def my_page_route():
    my_page.create_page()
```

### Run Background Tasks

```bash
# Sync market data
python scripts/data_sync_manager.py

# Fetch candle data
python scripts/candle_fetcher.py --symbol INFY --timeframe 1d

# Run strategy backtest
python run_backtest.py --strategy SMA --symbol INFY

# Paper trading
python scripts/paper_trading.py
```

### Clear Cache

```bash
# Clear application cache
rm -rf cache/*

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UPSTOX_CLIENT_ID` | ✅ | - | Upstox API client ID |
| `UPSTOX_CLIENT_SECRET` | ✅ | - | Upstox API client secret |
| `UPSTOX_REDIRECT_URI` | ✅ | localhost:5050/auth/callback | OAuth redirect URL |
| `ENCRYPTION_KEY` | ✅ | - | Fernet encryption key |
| `FLASK_PORT` | ❌ | 8000 | API server port |
| `FLASK_DEBUG` | ❌ | False | Enable debug mode |
| `NICEGUI_PORT` | ❌ | 5001 | Frontend port |
| `DATABASE_PATH` | ❌ | ./market_data.db | Database file path |
| `REDIS_URL` | ❌ | - | Redis connection URL |
| `NEWS_API_KEY` | ❌ | - | NewsAPI.org key |
| `TELEGRAM_BOT_TOKEN` | ❌ | - | Telegram bot token |

---

## Tips & Best Practices

### 1. Use Virtual Environment

**Always** activate virtual environment before working:

```bash
source .venv/bin/activate
```

### 2. Keep Dependencies Updated

Update regularly but test thoroughly:

```bash
pip list --outdated
pip install --upgrade package-name
```

### 3. Use .gitignore

Never commit:
- `.env` (secrets)
- `*.db` (databases)
- `logs/` (log files)
- `cache/` (cache files)
- `__pycache__/` (Python cache)

### 4. Write Tests

Add tests for new features:

```python
# tests/test_my_feature.py
def test_my_feature():
    result = my_function()
    assert result == expected_value
```

### 5. Follow Coding Standards

- Use **Black** for formatting
- Follow **PEP 8** style guide
- Write **docstrings** for functions
- Add **type hints** where appropriate

```python
def calculate_profit(entry: float, exit: float, quantity: int) -> float:
    """
    Calculate profit from a trade.
    
    Args:
        entry: Entry price
        exit: Exit price
        quantity: Number of shares
        
    Returns:
        Profit amount in currency
    """
    return (exit - entry) * quantity
```

---

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Locked

```bash
# Close all connections to database
# Remove WAL files
rm market_data.db-shm market_data.db-wal
```

### Module Not Found

```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Additional Resources

- `TESTING.md` - Comprehensive testing guide
- `DEPLOYMENT.md` - Production deployment
- `docs/ENDPOINTS.md` - API documentation
- `.github/debugging-protocol.md` - Debugging guide

---

**Happy Coding! 🚀**

