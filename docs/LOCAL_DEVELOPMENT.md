# 🛠️ Local Development Guide

**UPSTOX Trading Platform**  
**Last Updated:** February 3, 2026

---

## 🚀 How to Start

**One command to run everything:**

```bash
python3 run_platform.py
```

**That's it!** This master script handles:
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Environment file setup (.env)
- ✅ System health checks
- ✅ Pre-flight safety validation
- ✅ Starting all services (API, OAuth, Frontend)
- ✅ Opening browser to http://localhost:5001

---

## 📋 What You Need First

- **Python 3.11+** installed on your system
- **Upstox API credentials** (get from [Upstox Developer Portal](https://upstox.com))

---

## 🎯 First-Time Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sheldcoop/UPSTOX-PROJECT.git
   cd UPSTOX-PROJECT
   ```

2. **Configure credentials:**
   The master script will create `.env` from `.env.example` automatically.
   Edit `.env` with your Upstox credentials:
   ```bash
   nano .env  # or use your preferred editor
   ```
   
   Required variables:
   ```env
   UPSTOX_CLIENT_ID=your_client_id_here
   UPSTOX_CLIENT_SECRET=your_client_secret_here
   UPSTOX_REDIRECT_URI=http://localhost:5050/auth/callback
   ```

3. **Run the platform:**
   ```bash
   python3 run_platform.py
   ```

---

## 🔧 Additional Commands

### Health Check Only
```bash
python3 run_platform.py --check
```

### Stop All Services
```bash
python3 run_platform.py --stop
```

### Setup Without Starting
```bash
python3 run_platform.py --setup
```

---

## 📍 Service URLs

After starting, access:
- **Frontend Dashboard:** http://localhost:5001
- **API Server:** http://localhost:8000
- **OAuth Service:** http://localhost:5050

---

## 🐛 Troubleshooting

### Import Errors
```bash
python3 run_platform.py --setup  # Reinstalls dependencies
```

### Port Already in Use
```bash
python3 run_platform.py --stop   # Stops all services
```

### Check System Health
```bash
python scripts/check_health.py   # Detailed health report
```

---

## 📚 Additional Resources

- **Full Testing Guide:** `TESTING.md`
- **Production Deployment:** `DEPLOYMENT.md`
- **API Documentation:** `docs/ENDPOINTS.md`
- **Debugging Protocol:** `.github/debugging-protocol.md`

---

**Need help?** Check the additional documentation or open an issue on GitHub.

**Happy Trading! 🚀**

