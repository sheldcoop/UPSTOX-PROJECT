# 🚀 Production Deployment Checklist

**Date:** February 3, 2026  
**Version:** 2.0  
**Status:** Ready for Production ✅

---

## Pre-Deployment Checklist

### ✅ Code Quality (COMPLETE)
- [x] All Python files formatted with Black (57 files reformatted)
- [x] Zero Flake8 critical errors (E9, F63, F7, F82)
- [x] No backup files in repository (.bak, .bak2 removed)
- [x] No log files in repository (removed from git)
- [x] No debug dumps in repository (removed from git)
- [x] Project structure organized (examples/, scripts/utilities/)

### ✅ Testing (COMPLETE)
- [x] Comprehensive API endpoint tests created (24 test cases)
- [x] Frontend integration tests created (25+ test cases)
- [x] Health check endpoint verified
- [x] Test infrastructure configured (pytest.ini)
- [x] Test markers defined (unit, integration, api, live, slow)

### ✅ Documentation (COMPLETE)
- [x] COMPREHENSIVE_GUIDE.md created (master documentation)
- [x] Duplicate documentation removed
- [x] README.md comprehensive and up-to-date
- [x] API endpoints documented (60+ endpoints)
- [x] All 22 frontend pages documented
- [x] Quick start guides (local & Docker)
- [x] Troubleshooting section
- [x] FAQ section

### ✅ Frontend (VERIFIED - 22 Pages)
- [x] **Dashboard** (2 pages): Home, Health
- [x] **Trading** (3 pages): Positions, Orders & Alerts, Live Trading
- [x] **Data** (4 pages): Live Data, Option Chain, Historical Options, Downloads
- [x] **Strategies** (3 pages): Backtest, Signals, Strategy Builder
- [x] **Analytics** (2 pages): Performance, Option Greeks
- [x] **Upstox** (2 pages): Live Data, User Profile
- [x] **Tools** (3 pages): AI Chat, API Debugger, Guide
- [x] **F&O** (1 page): Instruments
- [x] **WIP** (1 page): Work in Progress placeholder

---

## Deployment Steps

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
cd UPSTOX-PROJECT

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```bash
# Upstox API Credentials
CLIENT_ID=your_upstox_client_id
CLIENT_SECRET=your_upstox_client_secret
REDIRECT_URI=http://localhost:8000/callback

# API Keys (Optional but recommended)
NEWS_API_KEY=your_newsapi_key
GOOGLE_AI_API_KEY=your_google_ai_key

# Database
DB_PATH=market_data.db

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=5001

# Security
ENCRYPTION_KEY=generate_with_scripts/generate_encryption_key.py
SECRET_KEY=your_random_secret_key
```

### 2. Dependencies Installation

```bash
# Install Python 3.11+
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Security Setup

```bash
# Generate encryption key
python scripts/generate_encryption_key.py

# Set file permissions
chmod 600 .env
chmod 755 scripts/*.py
chmod 755 *.sh

# Create necessary directories
mkdir -p logs cache downloads debug_dumps backups
```

### 4. Database Initialization

```bash
# Database will be created automatically on first run
# Verify schema
python scripts/check_schema.py

# Optional: Load sample data
python scripts/utilities/verify_backend.py
```

### 5. Service Configuration (Production)

**For systemd (Linux):**

```bash
# Run deployment script
sudo bash deploy/oracle_cloud_deploy.sh

# Enable services
sudo systemctl enable upstox-api
sudo systemctl enable upstox-frontend

# Start services
sudo systemctl start upstox-api
sudo systemctl start upstox-frontend

# Check status
sudo systemctl status upstox-api
sudo systemctl status upstox-frontend
```

**Service Files:**
- API: `/etc/systemd/system/upstox-api.service`
- Frontend: `/etc/systemd/system/upstox-frontend.service`

### 6. Docker Deployment (Alternative)

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### 7. Nginx Configuration (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Post-Deployment Verification

### ✅ Health Checks

```bash
# Check API server
curl http://localhost:8000/api/health

# Expected response:
# {"status": "healthy", "timestamp": "2026-02-03T...", ...}

# Check frontend
curl http://localhost:5001

# Expected: HTML response with NiceGUI content
```

### ✅ Service Status

```bash
# Check running processes
ps aux | grep python | grep -E "(api_server|nicegui_dashboard)"

# Check ports
netstat -tulpn | grep -E "(8000|5001)"

# Check logs
tail -f logs/api_server.log
tail -f logs/nicegui_dashboard.log
```

### ✅ Functional Testing

**Test Suite:**
```bash
# Run basic tests (skip live tests)
pytest -m "not live" -v

# Run API endpoint tests
pytest tests/test_api_endpoints.py -v

# Run frontend tests
pytest tests/test_frontend_pages.py -v
```

**Manual Testing:**
1. Open http://localhost:5001
2. Navigate through all pages:
   - ✅ Home page loads
   - ✅ Positions page displays
   - ✅ Orders & Alerts functional
   - ✅ Analytics shows data
   - ✅ Backtest runs
   - ✅ API Debugger works
3. Test a workflow:
   - Place a paper order
   - View in Positions
   - Check analytics update

---

## Monitoring Setup

### Log Files
- **API Server:** `logs/api_server.log`
- **Frontend:** `logs/nicegui_dashboard.log`
- **Data Sync:** `logs/data_sync.log`
- **Errors:** `debug_dumps/*.json`

### Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/upstox

# Add:
/path/to/UPSTOX-PROJECT/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 runner runner
}
```

### Monitoring Commands

```bash
# Disk usage
df -h

# Memory usage
free -m

# Process monitoring
top | grep python

# Real-time logs
tail -f logs/*.log

# Error monitoring
watch -n 60 'ls -lt debug_dumps/ | head -5'
```

---

## Backup Strategy

### Daily Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
cp market_data.db backups/market_data_$DATE.db
cp upstox.db backups/upstox_$DATE.db
tar -czf backups/logs_$DATE.tar.gz logs/
find backups/ -mtime +7 -delete  # Keep only 7 days
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/UPSTOX-PROJECT/backup.sh
```

---

## Rollback Procedure

### If deployment fails:

```bash
# Stop services
sudo systemctl stop upstox-api upstox-frontend

# Restore database from backup
cp backups/market_data_YYYYMMDD_HHMMSS.db market_data.db

# Checkout previous version
git log --oneline
git checkout <previous-commit-hash>

# Restart services
sudo systemctl start upstox-api upstox-frontend

# Verify
curl http://localhost:8000/api/health
```

---

## Performance Tuning

### Gunicorn Configuration

```python
# gunicorn_config.py
workers = 4  # 2-4 x CPU cores
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

### Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_date ON ohlc_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON paper_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_strategy ON trading_signals(strategy);

-- Vacuum database periodically
VACUUM;
ANALYZE;
```

---

## Security Hardening

### File Permissions
```bash
chmod 600 .env
chmod 600 market_data.db
chmod 700 backups/
chmod 644 logs/*.log
```

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### SSL/TLS Setup (Let's Encrypt)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

---

## Maintenance Schedule

### Daily
- ✅ Check service status
- ✅ Review error logs
- ✅ Monitor disk space
- ✅ Verify backups created

### Weekly
- ✅ Run full test suite
- ✅ Review performance metrics
- ✅ Update dependencies (security patches)
- ✅ Clean up old debug dumps

### Monthly
- ✅ Update NSE indices (`python scripts/update_nse_indices.py`)
- ✅ Database vacuum and optimize
- ✅ Review and archive logs
- ✅ Security audit (CodeQL scan)

---

## Support Contacts

**Documentation:**
- COMPREHENSIVE_GUIDE.md
- README.md
- docs/

**Issue Tracking:**
- GitHub Issues: https://github.com/sheldcoop/UPSTOX-PROJECT/issues

**Emergency Contacts:**
- System Admin: [Configure your contact]
- Database Admin: [Configure your contact]
- Developer: [Configure your contact]

---

## Deployment Sign-Off

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Verified By:** _______________  

**Checklist Completion:**
- [ ] All environment variables configured
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] Services started successfully
- [ ] Health checks passing
- [ ] Frontend accessible
- [ ] API endpoints responding
- [ ] Logs configured
- [ ] Backups scheduled
- [ ] Monitoring active

**Status:** 🟢 Production Ready

---

**Last Updated:** February 3, 2026  
**Version:** 2.0  
**Maintainer:** UPSTOX Project Team
