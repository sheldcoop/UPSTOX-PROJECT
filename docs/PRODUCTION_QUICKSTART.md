# 🚀 Production Quick Start Guide

## Your App is Ready for Oracle Cloud! ✅

Your UPSTOX Trading Platform is now **production-ready** with professional-grade deployment configuration.

---

## What's Been Added

### 1. Production Server Configuration
- ✅ **Gunicorn WSGI server** - Production-grade Python application server
- ✅ **Nginx reverse proxy** - Load balancing and SSL termination
- ✅ **Systemd services** - Auto-start on boot, automatic restart on failure
- ✅ **Health monitoring** - Automated health checks
- ✅ **Database backups** - Automated backup with retention policy

### 2. Deployment Files Created
```
gunicorn_config.py          # Gunicorn production config
wsgi.py                     # WSGI entry point
start_production.sh         # Start all services
stop_production.sh          # Stop all services
deploy/
  ├── oracle_cloud_deploy.sh    # Automated Oracle Cloud deployment
  ├── upstox-api.service        # API systemd service
  └── upstox-frontend.service   # Frontend systemd service
scripts/
  ├── backup_db.sh              # Database backup script
  └── health_check.sh           # Service health monitoring
```

---

## Quick Deploy to Oracle Cloud

### Option 1: Automated Deployment (Recommended)

```bash
# 1. SSH into your Oracle Cloud instance
ssh opc@<your-instance-ip>

# 2. Clone your repository
git clone https://github.com/your-username/UPSTOX-PROJECT-Oracle.git upstox-trading-platform
cd upstox-trading-platform

# 3. Run automated deployment
sudo bash deploy/oracle_cloud_deploy.sh

# 4. Configure your environment
cp .env.example .env
nano .env  # Add your Upstox credentials

# 5. Restart services
sudo systemctl restart upstox-api upstox-frontend

# 6. Done! Access your app at http://your-ip-address
```

### Option 2: Manual Deployment

See detailed instructions in `ORACLE_CLOUD_DEPLOYMENT.md`

---

## Local Testing (Before Deploying)

Test the production setup locally:

```bash
# 1. Install production dependencies
pip install -r requirements.txt

# 2. Test WSGI entry point
python wsgi.py

# 3. Test with Gunicorn
gunicorn --config gunicorn_config.py wsgi:application

# 4. Test health check
./scripts/health_check.sh

# 5. Test database backup
./scripts/backup_db.sh
```

---

## Production vs Development

| Feature | Development | Production |
|---------|-------------|------------|
| **Server** | Flask dev server | Gunicorn |
| **Processes** | Single process | Multiple workers |
| **Reload** | Auto-reload | Manual restart |
| **Logging** | Console | Files + journald |
| **Database** | SQLite | SQLite → PostgreSQL (recommended) |
| **Caching** | None | File/Redis (recommended) |
| **SSL** | HTTP only | HTTPS required |
| **Monitoring** | Manual | Automated |

---

## Service Management

### Start Services
```bash
# Development (local)
python app.py                    # Frontend on :5001
python scripts/api_server.py     # API on :8000

# Production (manual)
./start_production.sh

# Production (systemd - Oracle Cloud)
sudo systemctl start upstox-api upstox-frontend
```

### Check Status
```bash
# Development
ps aux | grep python

# Production
sudo systemctl status upstox-api
sudo systemctl status upstox-frontend
./scripts/health_check.sh
```

### View Logs
```bash
# Development
tail -f logs/api_server.log

# Production
sudo journalctl -u upstox-api -f
sudo journalctl -u upstox-frontend -f
tail -f logs/gunicorn_error.log
```

### Stop Services
```bash
# Development
# Ctrl+C in terminal

# Production (manual)
./stop_production.sh

# Production (systemd)
sudo systemctl stop upstox-api upstox-frontend
```

---

## Configuration

### Environment Variables (.env)

Required for production:
```env
# Upstox API
UPSTOX_CLIENT_ID=your_client_id
UPSTOX_CLIENT_SECRET=your_secret
UPSTOX_REDIRECT_URI=http://your-domain.com/auth/callback

# Security
ENCRYPTION_KEY=generate_with_fernet_generate_key

# Server
FLASK_PORT=8000
FLASK_DEBUG=False
```

Generate encryption key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Gunicorn Configuration

Edit `gunicorn_config.py` to customize:
- Number of workers (default: CPU cores * 2 + 1)
- Timeout settings
- Log levels
- Port binding

---

## Security Checklist

Before going live:

- [ ] Set `FLASK_DEBUG=False` in .env
- [ ] Generate strong `ENCRYPTION_KEY`
- [ ] Configure firewall (ports 80, 443 only)
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure OCI Security List
- [ ] Enable automatic security updates
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Review systemd service permissions
- [ ] Set strong passwords for all services

---

## Firewall Configuration

### Oracle Cloud (OCI Security List)
1. Go to OCI Console → Networking → VCN
2. Select your VCN → Security Lists
3. Add Ingress Rules:
   - Port 80 (HTTP) - Source: 0.0.0.0/0
   - Port 443 (HTTPS) - Source: 0.0.0.0/0

### Instance Firewall (firewalld)
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Free)
```bash
# 1. Install certbot
sudo yum install -y certbot python3-certbot-nginx

# 2. Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Using Custom Certificate
```bash
# 1. Copy certificate files
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-key.key /etc/ssl/private/

# 2. Update Nginx config
sudo nano /etc/nginx/conf.d/upstox.conf

# 3. Restart Nginx
sudo systemctl restart nginx
```

---

## Monitoring & Alerts

### Health Checks
```bash
# Manual check
./scripts/health_check.sh

# Automated (add to crontab)
*/5 * * * * /home/opc/upstox-trading-platform/scripts/health_check.sh
```

### Database Backups
```bash
# Manual backup
./scripts/backup_db.sh

# Automated (add to crontab)
0 2 * * * /home/opc/upstox-trading-platform/scripts/backup_db.sh
```

### Log Rotation
```bash
# Create /etc/logrotate.d/upstox
sudo nano /etc/logrotate.d/upstox

# Add:
/home/opc/upstox-trading-platform/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 opc opc
}
```

---

## Performance Tuning

### Gunicorn Workers
```python
# gunicorn_config.py
workers = multiprocessing.cpu_count() * 2 + 1  # Default

# For I/O intensive (API calls):
workers = multiprocessing.cpu_count() * 4

# For CPU intensive (calculations):
workers = multiprocessing.cpu_count() * 2
```

### Database Optimization
```bash
# Vacuum database periodically
sqlite3 market_data.db "VACUUM;"

# Run integrity check
python scripts/database_validator.py
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check logs
sudo journalctl -u upstox-api -n 50
sudo journalctl -u upstox-frontend -n 50

# Check permissions
ls -la /home/opc/upstox-trading-platform
```

### Can't Access from Internet
1. Check OCI Security List (most common)
2. Check firewall: `sudo firewall-cmd --list-all`
3. Check Nginx: `sudo systemctl status nginx`
4. Check services: `sudo systemctl status upstox-*`

### Port Already in Use
```bash
# Find process
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or stop properly
sudo systemctl stop upstox-api
```

---

## Backup & Recovery

### Backup
```bash
# Backup database
./scripts/backup_db.sh

# Backup entire application
tar -czf upstox-backup-$(date +%Y%m%d).tar.gz \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='cache' \
  /home/opc/upstox-trading-platform
```

### Restore
```bash
# Stop services
sudo systemctl stop upstox-api upstox-frontend

# Restore database
gunzip -c backups/market_data_20260201_120000.db.gz > market_data.db

# Start services
sudo systemctl start upstox-api upstox-frontend
```

---

## Scaling

### Current Setup: Single Server
- **Capacity:** ~100 concurrent users
- **Components:** Gunicorn + Nginx + SQLite
- **Cost:** ~$10-20/month

### Next Level: Optimized Single Server
- **Capacity:** ~500 concurrent users
- **Add:** Redis cache, PostgreSQL
- **Cost:** ~$30-50/month

### Enterprise: Multi-Server
- **Capacity:** 5000+ concurrent users
- **Components:** Load balancer, multiple app servers, DB cluster
- **Cost:** $200+/month

---

## What You DON'T Need to Change

Your application code works perfectly as-is! The deployment configuration:
- ✅ Works with existing Flask apps
- ✅ No code changes required
- ✅ Same database structure
- ✅ Same API endpoints
- ✅ Same frontend

---

## Support & Documentation

- **Full Deployment Guide:** `ORACLE_CLOUD_DEPLOYMENT.md`
- **Improvements & Suggestions:** `IMPROVEMENTS_SUGGESTIONS.md`
- **API Documentation:** `ENDPOINTS.md`
- **Backend Features:** `PRODUCTION_FEATURES.md`

---

## Quick Commands Reference

```bash
# Start production
./start_production.sh

# Stop production
./stop_production.sh

# Check health
./scripts/health_check.sh

# Backup database
./scripts/backup_db.sh

# View API logs
sudo journalctl -u upstox-api -f

# View frontend logs
sudo journalctl -u upstox-frontend -f

# Restart services
sudo systemctl restart upstox-api upstox-frontend

# Check status
sudo systemctl status upstox-api upstox-frontend nginx
```

---

## 🎉 You're Ready!

Your app is now production-ready for Oracle Cloud deployment. The setup includes:

✅ Professional-grade server configuration  
✅ Automatic service management  
✅ Security hardening  
✅ Health monitoring  
✅ Database backups  
✅ Comprehensive documentation  

**Next Steps:**
1. Deploy to Oracle Cloud using automated script
2. Configure SSL certificate
3. Set up monitoring alerts
4. Review `IMPROVEMENTS_SUGGESTIONS.md` for optimization ideas

---

**Questions?** Check the documentation files or review the deployment logs.

**Status:** Production Ready ✅  
**Last Updated:** February 2, 2026
