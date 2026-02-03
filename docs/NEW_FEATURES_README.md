# 🚀 New Features Implementation Guide

This document describes all the new features and improvements implemented based on `IMPROVEMENTS_SUGGESTIONS.md`.

## 📋 Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [PostgreSQL Migration](#postgresql-migration)
3. [Redis Caching](#redis-caching)
4. [Monitoring & Metrics](#monitoring--metrics)
5. [Rate Limiting](#rate-limiting)
6. [Error Tracking](#error-tracking)
7. [Input Validation](#input-validation)
8. [Async Operations](#async-operations)
9. [Notifications](#notifications)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Database Optimizations](#database-optimizations)

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Included

- **API Server** (port 8000) - Backend REST API
- **Frontend** (port 5001) - Web interface
- **Redis** (port 6379) - Caching layer
- **PostgreSQL** (port 5432) - Database (optional)
- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3000) - Monitoring dashboards

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your credentials
```

---

## 🗄️ PostgreSQL Migration

### Why PostgreSQL?

- Better concurrent write performance
- Advanced querying capabilities
- ACID compliance at scale
- Production-ready

### Migration Steps

1. **Start PostgreSQL** (via Docker or local)
   ```bash
   docker-compose up -d postgres
   ```

2. **Run migration script**
   ```bash
   python scripts/migrate_to_postgres.py
   ```

3. **Update DATABASE_URL**
   ```bash
   DATABASE_URL=postgresql://upstox:upstox_password@localhost:5432/upstox_trading
   ```

### Rollback to SQLite

Simply update `DATABASE_URL` back to SQLite path:
```bash
DATABASE_URL=sqlite:///market_data.db
```

---

## ⚡ Redis Caching

### Features

- **API Response Caching** - Reduces database load
- **Rate Limiting** - Uses Redis for distributed rate limiting
- **Session Storage** - Fast session management

### Configuration

```python
# In .env
REDIS_URL=redis://localhost:6379/0
```

### Cache Timeouts

- Portfolio data: 30 seconds
- Positions data: 30 seconds
- Market indices: 60 seconds

### Manual Cache Clear

```python
from config.enhancements import setup_all_enhancements

app = Flask(__name__)
enhancements = setup_all_enhancements(app)
cache = enhancements['cache']

# Clear all cache
cache.clear()

# Clear specific key
cache.delete('portfolio')
```

---

## 📊 Monitoring & Metrics

### Prometheus Metrics

Access metrics at: `http://localhost:8000/metrics`

**Available Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Active requests

### Grafana Dashboards

1. Access Grafana: `http://localhost:3000`
2. Login: `admin` / `admin`
3. Add Prometheus datasource (auto-configured)
4. Import dashboards

**Key Dashboards:**
- API Performance
- Request Rate & Latency
- Error Rates
- Cache Hit Rates

---

## 🚦 Rate Limiting

### Default Limits

- 200 requests per day
- 50 requests per hour

### Per-Endpoint Limits

```python
from flask_limiter import Limiter

@app.route('/api/orders')
@limiter.limit("10 per minute")
def create_order():
    pass
```

### Whitelist IPs

```python
@limiter.request_filter
def whitelist():
    return request.remote_addr == '127.0.0.1'
```

---

## 🔍 Error Tracking (Sentry)

### Setup

1. Create Sentry account: https://sentry.io
2. Get DSN from project settings
3. Set environment variable:
   ```bash
   SENTRY_DSN=https://your-dsn@sentry.io/project-id
   ```

### Features

- Real-time error notifications
- Stack trace capture
- Performance monitoring
- User feedback

### Manual Error Capture

```python
import sentry_sdk

try:
    # risky operation
    pass
except Exception as e:
    sentry_sdk.capture_exception(e)
```

---

## ✅ Input Validation

### Using Marshmallow Schemas

```python
from config.validation_schemas import OrderSchema, validate_request_data

@app.route('/api/orders', methods=['POST'])
def place_order():
    try:
        data = validate_request_data(OrderSchema, request.json)
        # Process validated data
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
```

### Available Schemas

- `OrderSchema` - Order placement
- `SymbolSchema` - Symbol queries
- `DateRangeSchema` - Date range queries
- `AlertRuleSchema` - Alert configuration
- `StrategyConfigSchema` - Strategy setup

---

## ⚡ Async Operations

### Fetch Multiple Symbols

```python
from config.async_operations import fetch_multiple_symbols_sync

symbols = ['RELIANCE', 'TCS', 'INFY']
data = fetch_multiple_symbols_sync(symbols, 'http://localhost:8000/api/quote')

for symbol, quote in data.items():
    print(f"{symbol}: {quote}")
```

### Using AsyncAPIClient

```python
import asyncio
from config.async_operations import AsyncAPIClient

async def fetch_data():
    client = AsyncAPIClient('http://localhost:8000')
    portfolio = await client.fetch_portfolio_data()
    return portfolio

result = asyncio.run(fetch_data())
```

---

## 📬 Notifications

### Email Notifications

```python
from config.email_notifications import get_email_notifier

notifier = get_email_notifier()

# Send price alert
notifier.send_price_alert_email(
    symbol='RELIANCE',
    price=2650.50,
    condition='ABOVE',
    threshold=2600.00
)

# Send daily summary
notifier.send_daily_summary_email(summary_data)
```

### Telegram Alerts

```python
from config.telegram_integration import get_telegram_notifier

notifier = get_telegram_notifier()

# Send price alert
notifier.send_price_alert('RELIANCE', 2650.50, 'ABOVE', 2600.00)

# Send order notification
notifier.send_order_notification(
    order_id='ORD123',
    symbol='TCS',
    action='BUY',
    quantity=10,
    price=3900.00,
    status='COMPLETE'
)
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Automatically runs on push to `main` or `develop`:

1. **Lint** - Code quality checks
2. **Test** - Run test suite
3. **Build** - Build Docker image
4. **Security Scan** - Trivy vulnerability scan
5. **Deploy** - Deploy to Oracle Cloud (main branch only)

### Required Secrets

Set in GitHub repository settings:

- `OCI_HOST` - Oracle Cloud IP address
- `OCI_USERNAME` - SSH username (usually 'opc')
- `OCI_SSH_KEY` - Private SSH key

### Manual Deployment

```bash
# SSH to server
ssh opc@your-oracle-cloud-ip

# Navigate to project
cd /home/opc/upstox-trading-platform

# Pull changes
git pull origin main

# Install dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart upstox-api upstox-frontend
```

---

## 🗃️ Database Optimizations

### Add Indexes

```bash
# For SQLite
python scripts/add_database_indexes.py --db-type sqlite

# For PostgreSQL
python scripts/add_database_indexes.py --db-type postgresql
```

### Connection Pooling

```python
from config.database_pool import get_database_pool, DatabaseSession

# Get pool instance
pool = get_database_pool()

# Use with context manager
with DatabaseSession() as session:
    result = session.execute("SELECT * FROM ohlc_data LIMIT 10")
    data = result.fetchall()

# Check pool stats
stats = pool.get_pool_stats()
print(f"Active connections: {stats['checked_out']}")
```

---

## 🔧 Configuration

### Full Configuration Example

```python
# app.py
from config.enhancements import setup_all_enhancements

app = Flask(__name__)

# Setup all enhancements at once
enhancements = setup_all_enhancements(app)

# Access components
cache = enhancements['cache']
limiter = enhancements['limiter']
csrf = enhancements['csrf']
```

---

## 📈 Performance Tips

1. **Enable Redis** for production
2. **Use PostgreSQL** for high-traffic deployments
3. **Add database indexes** for frequently queried tables
4. **Enable compression** (automatically enabled)
5. **Monitor with Prometheus** to identify bottlenecks
6. **Use async operations** for multiple API calls

---

## 🔒 Security Best Practices

1. **Set strong SECRET_KEY** in production
2. **Use API_KEY** for protected endpoints
3. **Enable CSRF protection** for forms
4. **Use HTTPS** with SSL certificate
5. **Rotate credentials** regularly
6. **Monitor Sentry** for security issues
7. **Keep dependencies updated**

---

## 🐛 Troubleshooting

### Redis Connection Failed

```bash
# Start Redis
docker-compose up -d redis

# Or install locally
sudo apt-get install redis-server
redis-server
```

### Database Migration Issues

```bash
# Check current database
python -c "import sqlite3; print(sqlite3.connect('market_data.db').execute('SELECT COUNT(*) FROM sqlite_master').fetchone())"

# Backup before migration
cp market_data.db market_data.db.backup
```

### Docker Issues

```bash
# View logs
docker-compose logs -f api

# Restart specific service
docker-compose restart api

# Rebuild image
docker-compose build --no-cache api
```

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Redis Documentation](https://redis.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Sentry Documentation](https://docs.sentry.io/)

---

## 🤝 Support

For issues or questions:
1. Check existing documentation
2. Review error logs
3. Check Sentry for error details
4. Open GitHub issue

---

**Last Updated:** February 2, 2026  
**Version:** 2.0.0 (Enhanced)
