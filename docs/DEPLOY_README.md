# 🚀 Quick Start: Deploy to Oracle Cloud

Your UPSTOX Trading Platform is **production-ready**! Follow these steps to deploy.

---

## ⚡ Fast Track (15 minutes)

### Step 1: Get Oracle Cloud Instance
1. Create an Oracle Cloud account (if you don't have one)
2. Launch a Compute instance:
   - **Image:** Oracle Linux 8
   - **Shape:** VM.Standard.E4.Flex (2 OCPUs, 16GB RAM)
   - **Network:** Allow public IP
3. Note your instance's **public IP address**

### Step 2: Configure Security
In OCI Console → Networking → Your VCN → Security Lists:
- Add Ingress Rule: Port 80 (HTTP) - Source: 0.0.0.0/0
- Add Ingress Rule: Port 443 (HTTPS) - Source: 0.0.0.0/0

### Step 3: Deploy Application
```bash
# SSH to your instance
ssh opc@YOUR_INSTANCE_IP

# Clone repository
git clone https://github.com/YOUR_USERNAME/UPSTOX-PROJECT-Oracle.git upstox-trading-platform
cd upstox-trading-platform

# Run automated deployment
sudo bash deploy/oracle_cloud_deploy.sh
```

The script will automatically:
- Install Python, Nginx, SQLite
- Create virtual environment
- Install dependencies
- Configure services
- Set up firewall
- Start everything

### Step 4: Configure Credentials
```bash
# Create .env file
cp .env.example .env
nano .env
```

Add your Upstox credentials:
```env
UPSTOX_CLIENT_ID=your_client_id_here
UPSTOX_CLIENT_SECRET=your_secret_here
UPSTOX_REDIRECT_URI=http://YOUR_INSTANCE_IP/auth/callback
ENCRYPTION_KEY=your_generated_key
```

Generate encryption key:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 5: Restart Services
```bash
sudo systemctl restart upstox-api upstox-frontend
```

### Step 6: Verify
```bash
# Check health
./scripts/health_check.sh

# Test API
curl http://localhost/api/health
```

### Step 7: Access Your App
Open browser: `http://YOUR_INSTANCE_IP`

**Done!** ✅

---

## 📱 What You'll See

After deployment:
- **Frontend:** Your trading dashboard at `http://your-ip/`
- **API:** Backend API at `http://your-ip/api/`
- **Health:** Status check at `http://your-ip/api/health`

---

## 🔒 Enable HTTPS (Recommended)

### Option A: Let's Encrypt (Free)
```bash
# Install certbot
sudo yum install -y certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is set up automatically
```

### Option B: Use Oracle Cloud Load Balancer
- Create Load Balancer in OCI Console
- Add SSL certificate
- Point to your backend instances
- More scalable for production

---

## 📊 Service Management

### Check Status
```bash
sudo systemctl status upstox-api
sudo systemctl status upstox-frontend
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u upstox-api -f

# Last 50 lines
sudo journalctl -u upstox-api -n 50

# Application logs
tail -f logs/gunicorn_error.log
```

### Restart Services
```bash
sudo systemctl restart upstox-api upstox-frontend
```

### Stop Services
```bash
sudo systemctl stop upstox-api upstox-frontend
```

---

## 🛠️ Troubleshooting

### Can't access from internet?
1. **Check OCI Security List** (most common issue)
   - Go to OCI Console → Networking
   - Add Ingress Rules for ports 80 and 443
   
2. **Check firewall**
   ```bash
   sudo firewall-cmd --list-all
   ```

3. **Check services are running**
   ```bash
   sudo systemctl status upstox-api upstox-frontend nginx
   ```

### Services won't start?
```bash
# Check logs
sudo journalctl -u upstox-api -n 50

# Check Python dependencies
source .venv/bin/activate
pip list

# Check permissions
ls -la /home/opc/upstox-trading-platform
```

### Port already in use?
```bash
# Find process
sudo lsof -i :8000

# Stop properly
sudo systemctl stop upstox-api
```

---

## 📚 Full Documentation

For detailed information, see:

| Document | Purpose |
|----------|---------|
| **FILE_STRUCTURE.md** | Project structure overview |
| **PRODUCTION_QUICKSTART.md** | Command reference guide |
| **ORACLE_CLOUD_DEPLOYMENT.md** | Complete deployment guide |
| **IMPROVEMENTS_SUGGESTIONS.md** | Future enhancements |

---

## 🎯 Next Steps After Deployment

1. **Configure SSL** - Let's Encrypt (free)
2. **Set up backups** - Already automated, test with `./scripts/backup_db.sh`
3. **Monitor services** - Run `./scripts/health_check.sh`
4. **Authenticate with Upstox** - Complete OAuth flow
5. **Start trading** - Your platform is live!

---

## 💰 Oracle Cloud Costs

**Free Tier:** Includes 2 VMs and 200GB storage (sufficient for testing)

**Estimated Monthly Cost:**
- Small (2 OCPU, 12GB RAM): $15-25/month
- Medium (4 OCPU, 24GB RAM): $40-60/month
- Large (8 OCPU, 48GB RAM): $80-120/month

---

## 🆘 Need Help?

1. **Check documentation** - See guides above
2. **Check logs** - `sudo journalctl -u upstox-api -f`
3. **Run health check** - `./scripts/health_check.sh`
4. **Review error dumps** - Check `debug_dumps/` directory

---

## 🎉 Success!

Your UPSTOX Trading Platform is now running in production on Oracle Cloud!

**What's Working:**
- ✅ Multi-worker production server
- ✅ Automatic restarts on failure
- ✅ Health monitoring
- ✅ Database backups
- ✅ Security hardening
- ✅ Professional-grade infrastructure

**Enjoy your trading platform!** 📈

---

**Quick Commands:**
```bash
# Health check
./scripts/health_check.sh

# View logs
sudo journalctl -u upstox-api -f

# Restart
sudo systemctl restart upstox-api upstox-frontend

# Backup
./scripts/backup_db.sh
```
