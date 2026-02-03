# Shell Scripts Documentation

This document provides a comprehensive guide to all shell scripts in the UPSTOX Trading Platform, explaining their purpose, usage, and when to use them.

## 📋 Overview

The platform includes several shell scripts for different deployment scenarios and operational tasks:

| Script | Purpose | Environment | Status |
|--------|---------|-------------|--------|
| `setup.sh` | Initial project setup | All | ✅ Active |
| `authenticate.sh` | OAuth authentication | All | ✅ Active |
| `start_nicegui.sh` | Local development | Development | ⚠️ Needs improvement |
| `start_nicegui_prod.sh` | Production NiceGUI | Production | ✅ Active |
| `start_production.sh` | Production API | Production | ✅ Active |
| `stop_production.sh` | Stop production services | Production | ✅ Active |
| `scripts/backup_db.sh` | Database backup | All | ✅ Active |
| `scripts/health_check.sh` | System health check | All | ✅ Active |
| `scripts/start_ai_assistant.sh` | AI assistant bot | Optional | ✅ Active |

---

## 🚀 Quick Start Scripts

### 1. `setup.sh` - Initial Setup

**Purpose:** One-time setup script that prepares the development environment.

**What it does:**
- Checks Python version (requires 3.11+)
- Creates virtual environment (`.venv`)
- Installs dependencies from `requirements.txt`
- Copies `.env.example` to `.env`
- Creates required directories (`logs`, `cache`, `downloads`, `debug_dumps`)
- Adds database indexes (if `market_data.db` exists)

**When to use:**
- First time setting up the project
- After a fresh clone
- When dependencies are updated

**Usage:**
```bash
./setup.sh
```

**Post-setup:**
1. Edit `.env` with your Upstox credentials
2. Choose deployment method (see below)

**Idempotency:** ✅ Safe to run multiple times
- Won't recreate virtual environment if exists
- Won't overwrite existing `.env`
- Will skip database indexes if they exist

---

### 2. `authenticate.sh` - Upstox Authentication

**Purpose:** Interactive OAuth 2.0 authentication with Upstox API.

**What it does:**
- Checks for `.env` file
- Activates virtual environment
- Starts OAuth server on port 5050
- Opens browser for Upstox login
- Handles OAuth callback
- Stores encrypted access/refresh tokens

**When to use:**
- First time connecting to Upstox
- When access token expires (every 24 hours)
- When refresh token expires
- After changing Upstox credentials

**Usage:**
```bash
./authenticate.sh
```

**Authentication Flow:**
1. Script starts OAuth server
2. Browser opens to Upstox login page
3. User logs in and authorizes app
4. Upstox redirects to OAuth server with authorization code
5. Server exchanges code for tokens
6. Tokens are encrypted and stored in database
7. OAuth server can be stopped after authentication

**Security:**
- ✅ Tokens are encrypted using Fernet (symmetric encryption)
- ✅ No tokens stored in plain text
- ✅ Uses environment variables from `.env`
- ❌ Currently requires manual browser interaction (no headless option)

**Troubleshooting:**
- **Port 5050 in use:** Kill existing process or change port in `.env`
- **Credentials error:** Check `UPSTOX_CLIENT_ID` and `UPSTOX_CLIENT_SECRET` in `.env`
- **Redirect URI mismatch:** Ensure `UPSTOX_REDIRECT_URI` in `.env` matches Upstox developer settings

---

## 🖥️ Development Scripts

### 3. `start_nicegui.sh` - Local Development

**Purpose:** Start all services for local development with NiceGUI dashboard.

**Current Issues:** ⚠️
1. **Hardcoded path:** `/Users/prince/Desktop/UPSTOX-project` (line 15)
2. **Uses `pkill`:** Potentially dangerous (kills all matching processes)
3. **Fixed ports:** Not configurable via environment
4. **No error handling:** Doesn't check if services started successfully

**What it does:**
- Kills existing processes (Flask, NiceGUI, OAuth, Telegram)
- Activates virtual environment
- Starts Flask API server (port 9000)
- Starts OAuth server (port 5050)
- Starts Telegram bot (if configured)
- Starts NiceGUI dashboard (port 8080)
- Opens services in browser

**Services Started:**
1. **Flask API** → Port 9000
2. **OAuth Server** → Port 5050
3. **NiceGUI Dashboard** → Port 8080
4. **Telegram Bot** → Background (optional)

**Current Usage:**
```bash
./start_nicegui.sh
```

**Recommended Improvements:**
1. Remove hardcoded path, use `cd "$(dirname "$0")"` or `$PWD`
2. Use specific PIDs instead of `pkill`
3. Make ports configurable via `.env`
4. Add health checks after starting services
5. Add error handling and rollback on failure

**Proposed Better Approach:**
```bash
# Option 1: Use make commands
make dev-start

# Option 2: Use Docker Compose
docker-compose up -d

# Option 3: Manual (2 terminals)
# Terminal 1
python scripts/api_server.py --port 9000

# Terminal 2
python nicegui_dashboard.py
```

**When to use:**
- Local development
- Testing UI changes
- Debugging with console logs visible

**When NOT to use:**
- Production deployment
- CI/CD pipelines
- On servers other than your local machine

---

## 🚀 Production Scripts

### 4. `start_nicegui_prod.sh` - Production NiceGUI

**Purpose:** Start NiceGUI dashboard in production mode.

**What it does:**
- Loads environment variables from `.env`
- Stops existing instances (ports 9000, 5001, 8080)
- Starts API server with Gunicorn (port 9000)
- Starts OAuth server (port 5050)
- Starts NiceGUI dashboard (port 8080)
- All services run as daemons with logs

**Services Configuration:**
- **API:** Gunicorn with `gunicorn_config.py`
- **OAuth:** Python direct (nohup)
- **NiceGUI:** Python direct (nohup)

**Advantages:**
- ✅ Uses environment variables
- ✅ Creates log files
- ✅ Production-ready Gunicorn config
- ✅ Safer port cleanup (lsof + kill)

**Usage:**
```bash
./start_nicegui_prod.sh
```

**Logs:**
- API: `logs/api_access.log`, `logs/api_error.log`
- OAuth: `logs/oauth.log`
- NiceGUI: `logs/nicegui.log`

**When to use:**
- Production deployment with NiceGUI UI
- Staging environment
- Oracle Cloud deployment

---

### 5. `start_production.sh` - Production API Only

**Purpose:** Start API server in production mode (without NiceGUI).

**What it does:**
- Creates required directories
- Loads environment variables
- Validates required configs
- Starts API with Gunicorn
- Performs health checks
- Stores PIDs for management

**Features:**
- ✅ Health check endpoint testing
- ✅ PID file management
- ✅ Configurable ports via environment
- ✅ Production-grade error handling

**Default Ports:**
- API: 8000 (configurable via `API_PORT`)

**Usage:**
```bash
# Default ports
./start_production.sh

# Custom ports
API_PORT=9000 ./start_production.sh
```

**Health Check:**
```bash
curl http://localhost:8000/api/health
```

**When to use:**
- Production API-only deployment
- When using separate frontend (React, Vue, etc.)
- Microservices architecture

---

### 6. `stop_production.sh` - Stop Production Services

**Purpose:** Gracefully stop all production services.

**What it does:**
- Reads PID files
- Sends SIGTERM to processes
- Removes PID files
- Confirms shutdown

**Usage:**
```bash
./stop_production.sh
```

**Safe Shutdown:**
- Waits for graceful termination
- Doesn't use `pkill` (safer)
- Cleans up PID files

---

## 🛠️ Utility Scripts

### 7. `scripts/backup_db.sh` - Database Backup

**Purpose:** Create timestamped backups of SQLite databases.

**What it backs up:**
- `upstox.db` (auth tokens, settings)
- `market_data.db` (historical data, analytics)
- `cache/yahoo_cache.sqlite` (cache data)

**Backup Location:** `backups/YYYY-MM-DD_HH-MM-SS/`

**Usage:**
```bash
./scripts/backup_db.sh
```

**Scheduling (cron):**
```bash
# Daily at 2 AM
0 2 * * * /path/to/UPSTOX-PROJECT/scripts/backup_db.sh
```

**When to use:**
- Before database schema changes
- Before major updates
- Scheduled daily backups
- Before data migrations

---

### 8. `scripts/health_check.sh` - System Health Check

**Purpose:** Check if all services are running and healthy.

**What it checks:**
- API server connectivity
- Database accessibility
- Disk space
- Process status
- Log file growth

**Usage:**
```bash
./scripts/health_check.sh
```

**Exit codes:**
- `0` - All healthy
- `1` - One or more services down
- `2` - Critical failure

**Integration:**
```bash
# Monitoring cron job
*/5 * * * * /path/to/health_check.sh || /path/to/alert.sh

# Docker health check
HEALTHCHECK CMD ./scripts/health_check.sh
```

---

### 9. `scripts/start_ai_assistant.sh` - AI Assistant Bot

**Purpose:** Start Telegram bot for trading assistant.

**Requirements:**
- `TELEGRAM_BOT_TOKEN` in `.env`
- `TELEGRAM_CHAT_ID` in `.env`

**What it does:**
- Validates Telegram credentials
- Starts AI assistant bot
- Monitors for commands

**Usage:**
```bash
./scripts/start_ai_assistant.sh
```

**Features:**
- Portfolio queries
- Market alerts
- Trade notifications
- AI-powered insights

---

## 📊 Recommended Deployment Strategies

### Local Development (Recommended)

**Option A: Shell Script (Quick)**
```bash
./setup.sh
./authenticate.sh
./start_nicegui.sh
```

**Option B: Manual Control (Better)**
```bash
# Terminal 1: API
source .venv/bin/activate
python scripts/api_server.py

# Terminal 2: Frontend
source .venv/bin/activate
python nicegui_dashboard.py
```

**Option C: Docker (Isolated)**
```bash
docker-compose up -d
```

---

### Production Deployment (Recommended)

**Option A: Shell Scripts**
```bash
./setup.sh
./authenticate.sh
./start_nicegui_prod.sh
```

**Option B: Systemd Services (Best for Linux)**
```bash
# See docs/DEPLOYMENT.md for systemd setup
sudo systemctl start upstox-api
sudo systemctl start upstox-frontend
```

**Option C: Docker + Docker Compose**
```bash
docker-compose -f docker-compose.yml up -d
```

---

## 🔒 Security Best Practices

### Environment Variables
- ✅ Never commit `.env` to Git (in `.gitignore`)
- ✅ Use `.env.example` as template
- ✅ Rotate secrets regularly
- ✅ Use strong encryption keys

### Script Permissions
```bash
chmod +x *.sh
chmod +x scripts/*.sh
chmod 600 .env  # Restrict .env access
```

### Production Hardening
- Use systemd instead of shell scripts (better process management)
- Run services as non-root user
- Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Enable log rotation
- Monitor PID files for tampering

---

## 🐛 Troubleshooting

### Common Issues

**1. "Permission denied" when running script**
```bash
chmod +x script_name.sh
```

**2. "Port already in use"**
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

**3. "Virtual environment not found"**
```bash
./setup.sh  # Recreate environment
```

**4. "Authentication failed"**
```bash
# Check credentials
cat .env | grep UPSTOX

# Re-authenticate
./authenticate.sh
```

**5. Services not starting**
```bash
# Check logs
tail -f logs/*.log

# Verify environment
source .venv/bin/activate
python --version  # Should be 3.11+
```

---

## 📚 Related Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Development workflow
- **[README.md](../README.md)** - Quick start guide
- **[AUTH_GUIDE.md](AUTH_GUIDE.md)** - Authentication details

---

## 🔄 Maintenance & Updates

### When Scripts Need Updates

1. **Port changes** → Update `.env` and documentation
2. **New services** → Add to appropriate startup scripts
3. **Security patches** → Review and apply to all scripts
4. **Python version** → Update `setup.sh` version check

### Script Testing Checklist

Before committing script changes:
- [ ] Test on fresh clone
- [ ] Test with missing dependencies
- [ ] Test with invalid credentials
- [ ] Test port conflicts
- [ ] Test on Linux/macOS
- [ ] Update this documentation

---

**Last Updated:** February 3, 2026  
**Maintainer:** Development Team
