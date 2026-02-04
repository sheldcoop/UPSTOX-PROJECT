# 🚀 UPSTOX Trading Platform - Deployment Guide

**Last Updated:** February 3, 2026  
**Status:** Production Ready ✅

This is the **single source of truth** for deploying the UPSTOX Trading Platform.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Environment Configuration](#environment-configuration)
- [Service Management](#service-management)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)
- [Scaling & Performance](#scaling--performance)

---

## Quick Start

### One-Command Deployment (Oracle Cloud)

```bash
# SSH into your Oracle Cloud instance
ssh opc@<your-instance-ip>

# Clone and deploy
cd /home/opc
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git upstox-trading-platform
cd upstox-trading-platform
sudo bash deploy/oracle_cloud_deploy.sh

# Configure credentials
cp .env.example .env
nano .env  # Add your Upstox API credentials

# Restart services
sudo systemctl restart upstox-api upstox-frontend

# Verify deployment
curl http://localhost/api/health
```

**Time to Deploy:** ~15 minutes  
**Deployment Type:** Automated

---

## Prerequisites

### 1. Infrastructure Requirements

#### Oracle Cloud (Recommended)
- **Instance Type:** VM.Standard.E4.Flex or higher
- **OS:** Oracle Linux 8 or compatible
- **vCPUs:** 2+ cores recommended
- **RAM:** 4GB+ recommended
- **Storage:** 50GB+ available

#### Alternative Cloud Providers
- AWS EC2 (t3.medium or higher)
- Google Cloud Compute Engine (e2-medium or higher)
- Azure VM (B2s or higher)
- Any VPS with Ubuntu 20.04+ or RHEL 8+

### 2. Required Software

```bash
# Installed automatically by deployment script
- Python 3.11+
- Nginx (reverse proxy)
- SQLite 3
- Git
- systemd
```

### 3. Required Information

- ✅ Upstox API Client ID
- ✅ Upstox API Client Secret
- ✅ Domain name (optional but recommended)
- ✅ Server public IP address

### 4. Network Configuration

**OCI Security List Ingress Rules:**
- Port 80 (HTTP) - Source: 0.0.0.0/0
- Port 443 (HTTPS) - Source: 0.0.0.0/0

**Firewall Ports:**
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (API - internal)
- 5001 (Frontend - internal)

---

## Deployment Options

### Option 1: Automated Deployment (Recommended)

**Best for:** Quick setup, production deployment

```bash
# Run the automated script
sudo bash deploy/oracle_cloud_deploy.sh
```

**What it does:**
- ✅ Installs system dependencies
- ✅ Sets up Python virtual environment
- ✅ Installs Python packages
- ✅ Configures Nginx reverse proxy
- ✅ Creates systemd services
- ✅ Configures firewall rules
- ✅ Starts all services

### Option 2: Manual Deployment

**Best for:** Custom setups, learning, troubleshooting

See [Manual Deployment Steps](#manual-deployment-steps) below.

### Option 3: Docker Deployment

**Best for:** Containerized environments, K8s

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 4: Local Development

**Best for:** Testing, development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python scripts/api_server.py

# Run frontend (in another terminal)
python nicegui_dashboard.py
```

---

## Environment Configuration

### 1. Create Environment File

```bash
cp .env.example .env
nano .env
```

### 2. Required Environment Variables

```env
# ===== Upstox API Credentials =====
UPSTOX_CLIENT_ID=your_client_id_here
UPSTOX_CLIENT_SECRET=your_client_secret_here
UPSTOX_REDIRECT_URI=http://your-domain.com/auth/callback

# ===== Security =====
ENCRYPTION_KEY=your_generated_fernet_key

# ===== Server Configuration =====
FLASK_PORT=8000
FLASK_DEBUG=False
NICEGUI_PORT=5001

# ===== Database =====
DATABASE_PATH=./market_data.db

# ===== Optional: External Services =====
REDIS_URL=redis://localhost:6379/0
NEWS_API_KEY=your_newsapi_key
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### 3. Generate Encryption Key

```bash
python scripts/generate_encryption_key.py
```

Or manually:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 4. Secrets Management

**DO NOT commit secrets to Git!**

**Production secrets should be stored in:**
- Environment variables (recommended)
- OCI Vault / AWS Secrets Manager / Azure Key Vault
- HashiCorp Vault
- Encrypted .env file with restricted permissions

```bash
# Set proper permissions on .env
chmod 600 .env
```

---

## Service Management

### Production (Systemd)

#### Start Services
```bash
sudo systemctl start upstox-api upstox-frontend
# Or enable to start on boot
sudo systemctl enable upstox-api upstox-frontend
```

#### Stop Services
```bash
sudo systemctl stop upstox-api upstox-frontend
```

#### Restart Services
```bash
sudo systemctl restart upstox-api upstox-frontend
```

#### Check Status
```bash
sudo systemctl status upstox-api
sudo systemctl status upstox-frontend
sudo systemctl status nginx
```

#### View Logs
```bash
# Real-time logs
sudo journalctl -u upstox-api -f
sudo journalctl -u upstox-frontend -f

# Last 100 lines
sudo journalctl -u upstox-api -n 100

# Application logs
tail -f logs/gunicorn_error.log
tail -f logs/gunicorn_access.log
```

### Manual Production Scripts

```bash
# Start all services
./start_production.sh

# Stop all services
./stop_production.sh

# Health check
./scripts/health_check.sh
```

### Development Mode

```bash
# API server (port 8000)
python scripts/api_server.py

# Frontend (port 5001)
python nicegui_dashboard.py

# OAuth server (port 5050)
python scripts/oauth_server.py
```

---

## SSL/HTTPS Setup

### Option 1: Let's Encrypt (Free & Automated)

```bash
# Install Certbot
sudo yum install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Option 2: Custom Certificate

```bash
# Copy certificate files
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-key.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/your-key.key

# Update Nginx configuration
sudo nano /etc/nginx/conf.d/upstox.conf

# Add SSL configuration:
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # ... rest of configuration
}

# Restart Nginx
sudo systemctl restart nginx
```

### Verify SSL

```bash
# Check certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test with curl
curl -I https://your-domain.com
```

---

## Monitoring & Health Checks

### Automated Health Checks

```bash
# Run health check script
./scripts/health_check.sh

# Add to crontab for automated monitoring (every 5 minutes)
*/5 * * * * /home/opc/upstox-trading-platform/scripts/health_check.sh
```

### API Health Endpoint

```bash
# Check API health
curl http://localhost/api/health

# Expected response:
{
  "status": "running",
  "timestamp": "2026-02-03T09:00:00Z",
  "uptime": "2h 15m 30s",
  "version": "1.0.0"
}
```

### Service Health Monitoring

```bash
# Check all services
sudo systemctl status upstox-api upstox-frontend nginx

# Check resource usage
htop
df -h
free -h

# Check network ports
sudo netstat -tlnp | grep -E '80|443|8000|5001'
```

### Application Metrics (Optional)

Platform includes Prometheus + Grafana configuration:

```bash
# Start monitoring stack
docker-compose -f docker-compose.yml up -d prometheus grafana

# Access Grafana: http://your-ip:3000
# Default login: admin/admin
```

---

## Backup & Recovery

### Automated Database Backups

```bash
# Enable automated backups (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/opc/upstox-trading-platform/scripts/backup_db.sh") | crontab -

# Manual backup
./scripts/backup_db.sh
```

**Backup Location:** `backups/market_data_YYYYMMDD_HHMMSS.db.gz`  
**Retention:** 30 days (configurable in backup_db.sh)

### Manual Database Backup

```bash
# SQLite backup
sqlite3 market_data.db ".backup 'backups/manual_backup.db'"

# Compressed backup
tar -czf backups/full_backup_$(date +%Y%m%d).tar.gz \
  market_data.db upstox.db config/ .env
```

### Restore Procedure

```bash
# 1. Stop all services
sudo systemctl stop upstox-api upstox-frontend

# 2. Restore database
gunzip -c backups/market_data_20260203_020000.db.gz > market_data.db

# 3. Verify integrity
sqlite3 market_data.db "PRAGMA integrity_check;"

# 4. Restart services
sudo systemctl start upstox-api upstox-frontend

# 5. Verify
curl http://localhost/api/health
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs for errors
sudo journalctl -u upstox-api -n 50
sudo journalctl -u upstox-frontend -n 50

# Check Python dependencies
/home/opc/upstox-trading-platform/.venv/bin/pip list

# Check permissions
ls -la /home/opc/upstox-trading-platform

# Verify .env file exists
cat .env | grep UPSTOX_CLIENT_ID
```

#### 2. Can't Access from Internet

**Most Common Cause:** OCI Security List not configured

```bash
# 1. Check OCI Security List (OCI Console)
#    Networking → VCN → Security Lists → Add Ingress Rules

# 2. Check local firewall
sudo firewall-cmd --list-all

# 3. Check if ports are listening
sudo netstat -tlnp | grep -E '80|443'

# 4. Check Nginx status
sudo systemctl status nginx
```

#### 3. Nginx 502 Bad Gateway

```bash
# Check if backend services are running
sudo systemctl status upstox-api upstox-frontend

# Check SELinux (if enabled)
sudo setsebool -P httpd_can_network_connect 1

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### 4. Database Locked

```bash
# Check for WAL files
ls -la market_data.db*

# Stop services and remove WAL files
sudo systemctl stop upstox-api upstox-frontend
rm market_data.db-shm market_data.db-wal
sudo systemctl start upstox-api upstox-frontend
```

#### 5. Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000

# Kill process (replace PID)
sudo kill -9 <PID>

# Or properly stop service
sudo systemctl stop upstox-api
```

### Debug Mode

```bash
# Enable debug logging
export FLASK_DEBUG=True

# Run API server in foreground
python scripts/api_server.py

# Check database
python scripts/database_validator.py
```

---

## Rollback Procedures

### Emergency Rollback

```bash
# 1. Stop all services
sudo systemctl stop upstox-api upstox-frontend

# 2. Restore previous version from Git
cd /home/opc/upstox-trading-platform
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>

# 3. Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt

# 4. Restore database backup
gunzip -c backups/market_data_<date>.db.gz > market_data.db

# 5. Restart services
sudo systemctl start upstox-api upstox-frontend

# 6. Verify
./scripts/health_check.sh
```

### Gradual Rollback

```bash
# 1. Test rollback in staging first (if available)

# 2. Schedule maintenance window
# 3. Backup current state
./scripts/backup_db.sh
git log -1 > backups/current_commit.txt

# 4. Perform rollback
git checkout <stable-commit>
pip install -r requirements.txt
sudo systemctl restart upstox-api upstox-frontend

# 5. Monitor for 30 minutes
watch -n 10 './scripts/health_check.sh'

# 6. If issues, roll forward
git checkout main
```

---

## Scaling & Performance

### Current Architecture (Single Server)

```
Internet → Nginx → Gunicorn (multi-worker) → SQLite
```

**Capacity:** ~100 concurrent users  
**Cost:** $10-20/month

### Performance Tuning

#### 1. Optimize Gunicorn Workers

Edit `gunicorn_config.py`:

```python
import multiprocessing

# For CPU-intensive workloads
workers = multiprocessing.cpu_count() * 2 + 1

# For I/O-intensive workloads (API calls)
workers = multiprocessing.cpu_count() * 4 + 1

# Timeout for long-running requests
timeout = 120

# Worker connections
worker_connections = 1000
```

#### 2. Enable Nginx Caching

```nginx
# Add to /etc/nginx/conf.d/upstox.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 60s;
    proxy_cache_key "$request_uri";
}
```

#### 3. Database Optimization

```bash
# Vacuum database
sqlite3 market_data.db "VACUUM;"

# Run integrity check
sqlite3 market_data.db "PRAGMA integrity_check;"

# Analyze query performance
python scripts/database_validator.py
```

### Horizontal Scaling

For larger deployments (500+ concurrent users):

1. **Load Balancer**
   - Oracle Cloud Load Balancer
   - AWS ELB / ALB
   - Nginx as load balancer

2. **Multiple App Servers**
   - Deploy same app on multiple instances
   - Share session state via Redis

3. **Database Migration**
   - Migrate from SQLite to PostgreSQL
   - Use connection pooling
   - Enable read replicas

4. **Caching Layer**
   - Redis for API responses
   - Memcached for sessions

---

## Manual Deployment Steps

### 1. Install System Dependencies

```bash
# Oracle Linux / RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel git nginx sqlite

# Ubuntu / Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git nginx sqlite3
```

### 2. Clone Repository

```bash
cd /home/opc  # or your preferred directory
git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git upstox-trading-platform
cd upstox-trading-platform
```

### 3. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Directories

```bash
mkdir -p logs cache debug_dumps downloads backups
chmod 755 logs cache debug_dumps downloads backups
```

### 5. Configure Environment

```bash
cp .env.example .env
nano .env  # Add your credentials
chmod 600 .env
```

### 6. Install Systemd Services

```bash
sudo cp deploy/upstox-api.service /etc/systemd/system/
sudo cp deploy/upstox-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable upstox-api upstox-frontend
```

### 7. Configure Nginx

```bash
sudo nano /etc/nginx/conf.d/upstox.conf
# Copy configuration from deploy/nginx.conf

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 8. Configure Firewall

```bash
# Firewalld (Oracle Linux / RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 9. Start Services

```bash
sudo systemctl start upstox-api upstox-frontend nginx
```

### 10. Verify

```bash
curl http://localhost/api/health
./scripts/health_check.sh
```

---

## Post-Deployment Checklist

- [ ] All services running (upstox-api, upstox-frontend, nginx)
- [ ] API health endpoint responding
- [ ] Frontend accessible via web browser
- [ ] SSL certificate configured (if using HTTPS)
- [ ] Firewall rules configured
- [ ] OCI Security List configured
- [ ] Environment variables set correctly
- [ ] Upstox OAuth authentication working
- [ ] Database backups scheduled (cron job)
- [ ] Health monitoring configured
- [ ] Log rotation configured
- [ ] DNS records pointing to server (if using domain)

---

## Additional Resources

| Document | Purpose |
|----------|---------|
| `LOCAL_DEVELOPMENT.md` | Local development setup |
| `TESTING.md` | Testing guide |
| `docs/ORACLE_CLOUD_DEPLOYMENT.md` | Detailed Oracle Cloud guide |
| `docs/PRODUCTION_QUICKSTART.md` | Quick reference |
| `docs/ENDPOINTS.md` | API documentation |
| `.env.example` | Environment variables template |

---

## Support

**For deployment issues:**
1. Check this deployment guide
2. Review troubleshooting section
3. Check application logs (`logs/` directory)
4. Check system logs (`journalctl`)
5. Review OCI Security List configuration

**For application issues:**
1. Check `TESTING.md` for running tests
2. Review API documentation in `docs/ENDPOINTS.md`
3. Check application logs

---

**Deployment Status:** ✅ Production Ready  
**Estimated Deployment Time:** 15-30 minutes  
**Maintenance Level:** Low (automated backups and restarts)

