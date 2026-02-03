# 🚀 Oracle Cloud Deployment Guide

## Overview
This guide will help you deploy the UPSTOX Trading Platform on Oracle Cloud Infrastructure (OCI).

## Prerequisites

### 1. Oracle Cloud Account
- An active Oracle Cloud account
- A compute instance (VM.Standard.E4.Flex or similar)
- Oracle Linux 8 or compatible OS

### 2. Domain & SSL (Optional but Recommended)
- A domain name pointed to your instance IP
- SSL certificate (Let's Encrypt recommended)

### 3. Required Information
- Upstox API credentials (Client ID, Client Secret)
- Your server's public IP address

---

## Quick Deployment (Automated)

### Step 1: Clone Repository
```bash
# SSH into your Oracle Cloud instance
ssh opc@<your-instance-ip>

# Clone the repository
cd /home/opc
git clone https://github.com/your-username/UPSTOX-PROJECT-Oracle.git upstox-trading-platform
cd upstox-trading-platform
```

### Step 2: Run Automated Deployment
```bash
# Run the deployment script as root
sudo bash deploy/oracle_cloud_deploy.sh
```

This script will:
- ✅ Install system dependencies (Python, Nginx, etc.)
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Configure systemd services
- ✅ Set up Nginx reverse proxy
- ✅ Configure firewall rules
- ✅ Start all services

### Step 3: Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your Upstox credentials:
```env
UPSTOX_CLIENT_ID=your_client_id_here
UPSTOX_CLIENT_SECRET=your_secret_here
UPSTOX_REDIRECT_URI=http://your-domain.com/auth/callback
ENCRYPTION_KEY=your_generated_key
FLASK_PORT=8000
FLASK_DEBUG=False
```

### Step 4: Restart Services
```bash
sudo systemctl restart upstox-api
sudo systemctl restart upstox-frontend
```

### Step 5: Verify Deployment
```bash
# Check API service
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:5001/

# Check via Nginx
curl http://localhost/api/health
```

---

## Manual Deployment (Step-by-Step)

If you prefer manual control or the automated script fails:

### 1. Install System Dependencies
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel git nginx sqlite
```

### 2. Set Up Application
```bash
cd /home/opc/upstox-trading-platform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create Directories
```bash
mkdir -p logs cache debug_dumps downloads
chmod 755 logs cache debug_dumps downloads
```

### 4. Install Systemd Services
```bash
sudo cp deploy/upstox-api.service /etc/systemd/system/
sudo cp deploy/upstox-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 5. Configure Nginx
```bash
sudo nano /etc/nginx/conf.d/upstox.conf
```

Copy the configuration from `deploy/nginx.conf` (created by deployment script).

```bash
# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 6. Configure Firewall
```bash
# Oracle Cloud uses firewalld
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

### 7. Configure OCI Security List
**Important:** Oracle Cloud has additional network security at the subnet level.

1. Go to OCI Console → Networking → Virtual Cloud Networks
2. Select your VCN → Security Lists
3. Add Ingress Rules:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `80` (HTTP)
   - Destination Port: `443` (HTTPS)

### 8. Start Services
```bash
sudo systemctl enable upstox-api upstox-frontend
sudo systemctl start upstox-api upstox-frontend
```

---

## Service Management

### Check Status
```bash
# API Server
sudo systemctl status upstox-api

# Frontend Server
sudo systemctl status upstox-frontend

# Nginx
sudo systemctl status nginx
```

### View Logs
```bash
# API Server logs
sudo journalctl -u upstox-api -f

# Frontend logs
sudo journalctl -u upstox-frontend -f

# Application logs
tail -f /home/opc/upstox-trading-platform/logs/gunicorn_error.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart API
sudo systemctl restart upstox-api

# Restart Frontend
sudo systemctl restart upstox-frontend

# Restart all
sudo systemctl restart upstox-api upstox-frontend nginx
```

### Stop Services
```bash
sudo systemctl stop upstox-api upstox-frontend
```

---

## SSL Configuration (HTTPS)

### Using Let's Encrypt (Certbot)

1. **Install Certbot**
```bash
sudo yum install -y certbot python3-certbot-nginx
```

2. **Obtain Certificate**
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. **Auto-renewal**
Certbot automatically sets up renewal. Test it:
```bash
sudo certbot renew --dry-run
```

### Manual SSL Certificate

If you have your own certificate:

1. Copy certificate files:
```bash
sudo cp your-cert.crt /etc/ssl/certs/
sudo cp your-key.key /etc/ssl/private/
```

2. Update Nginx configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Database Management

### Backup Database
```bash
# Manual backup
sqlite3 market_data.db ".backup '/home/opc/backups/market_data_$(date +%Y%m%d).db'"

# Automated backup script (add to crontab)
echo "0 2 * * * /home/opc/upstox-trading-platform/scripts/backup_db.sh" | crontab -
```

### Restore Database
```bash
# Stop services first
sudo systemctl stop upstox-api upstox-frontend

# Restore
cp /home/opc/backups/market_data_20260201.db market_data.db

# Start services
sudo systemctl start upstox-api upstox-frontend
```

---

## Monitoring & Maintenance

### Health Checks
```bash
# API health
curl http://localhost/api/health

# Expected response:
# {"status": "running", "timestamp": "...", ...}
```

### Resource Monitoring
```bash
# CPU and Memory usage
htop

# Disk usage
df -h

# Service resource usage
systemctl status upstox-api
```

### Log Rotation
Logs are automatically rotated by journald. For application logs:

Create `/etc/logrotate.d/upstox`:
```
/home/opc/upstox-trading-platform/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 opc opc
    sharedscripts
    postrotate
        systemctl reload upstox-api upstox-frontend
    endscript
}
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u upstox-api -n 50

# Check permissions
ls -la /home/opc/upstox-trading-platform

# Check Python dependencies
/home/opc/upstox-trading-platform/.venv/bin/pip list
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Database Locked
```bash
# Check for lock files
ls -la market_data.db*

# Remove lock files (when services are stopped)
sudo systemctl stop upstox-api upstox-frontend
rm market_data.db-shm market_data.db-wal
sudo systemctl start upstox-api upstox-frontend
```

### Nginx 502 Bad Gateway
```bash
# Check if backend services are running
sudo systemctl status upstox-api upstox-frontend

# Check SELinux (if enabled)
sudo setsebool -P httpd_can_network_connect 1

# Check logs
sudo tail -f /var/log/nginx/error.log
```

### Can't Access from Internet
1. Check OCI Security List (most common issue)
2. Check firewall: `sudo firewall-cmd --list-all`
3. Check Nginx is running: `sudo systemctl status nginx`
4. Check if port is listening: `sudo netstat -tlnp | grep 80`

---

## Performance Optimization

### Gunicorn Workers
Edit `/home/opc/upstox-trading-platform/gunicorn_config.py`:

```python
# For CPU-intensive workloads
workers = multiprocessing.cpu_count() * 2 + 1

# For I/O-intensive workloads
workers = multiprocessing.cpu_count() * 4 + 1
```

### Database Optimization
```bash
# Run database validation
python scripts/database_validator.py

# Vacuum database
sqlite3 market_data.db "VACUUM;"
```

### Nginx Caching
Add to Nginx configuration:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 60s;
    proxy_cache_key "$request_uri";
    # ... rest of config
}
```

---

## Security Best Practices

1. **Change Default Ports** (optional)
   - Edit `gunicorn_config.py` and systemd service files
   
2. **Set Up Firewall Rules**
   - Only allow necessary ports
   - Restrict SSH access to specific IPs
   
3. **Enable SELinux** (if not already)
   ```bash
   sudo setenforce 1
   ```

4. **Regular Updates**
   ```bash
   sudo yum update -y
   ```

5. **Monitor Logs**
   - Set up alerts for errors
   - Monitor failed login attempts
   
6. **Backup Strategy**
   - Daily database backups
   - Weekly full system backups
   - Test restore procedures

---

## Scaling Options

### Vertical Scaling
- Upgrade to larger compute instance (more CPU/RAM)
- Increase Gunicorn workers

### Horizontal Scaling
- Deploy multiple instances behind a load balancer
- Use Oracle Cloud Load Balancer
- Shared database or database replication

### Database Migration
For larger deployments, consider migrating from SQLite to PostgreSQL:
1. Export data from SQLite
2. Set up PostgreSQL instance
3. Import data
4. Update connection strings in application

---

## Support & Resources

- **Application Logs:** `/home/opc/upstox-trading-platform/logs/`
- **System Logs:** `sudo journalctl -xe`
- **Nginx Logs:** `/var/log/nginx/`
- **Documentation:** See project README and docs/

For issues:
1. Check troubleshooting section
2. Review application logs
3. Check system resource usage
4. Verify OCI security list configuration

---

## Rollback Procedure

If deployment fails or causes issues:

```bash
# Stop services
sudo systemctl stop upstox-api upstox-frontend

# Restore previous version
cd /home/opc/upstox-trading-platform
git checkout <previous-commit>

# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restore database (if needed)
cp /home/opc/backups/market_data_<date>.db market_data.db

# Restart services
sudo systemctl start upstox-api upstox-frontend
```

---

## Next Steps After Deployment

1. ✅ Verify all services are running
2. ✅ Configure SSL/HTTPS
3. ✅ Set up automated backups
4. ✅ Configure monitoring and alerts
5. ✅ Complete Upstox OAuth authentication
6. ✅ Test trading functionality
7. ✅ Set up log monitoring
8. ✅ Document custom configurations

---

**Deployment Status:** Ready for Production ✅  
**Last Updated:** February 2, 2026  
**Tested On:** Oracle Linux 8
