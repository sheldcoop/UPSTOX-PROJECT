# Background Jobs & Scheduler Documentation

**Last Updated:** February 3, 2026  
**Current Status:** ⚠️ Partially Implemented  
**Scheduler:** `schedule` library (basic) → **APScheduler** (recommended)

---

## 🎯 Overview

The UPSTOX Trading Platform requires automated background jobs for:
- Market data synchronization
- NSE corporate actions scraping
- Alert monitoring and notifications  
- Database maintenance
- Performance analytics calculation
- Data gap detection and backfill

**Current Implementation:**
- ✅ Basic scheduling via `schedule` library in `data_sync_manager.py`
- ⚠️ Manual execution required (no daemon process)
- ❌ No production-ready scheduler service

**Recommended Implementation:**
- ✅ **APScheduler** for production
- ✅ Persistent job storage
- ✅ Retry logic and failure handling
- ✅ Job monitoring and management UI

---

## 📋 Required Background Jobs

### 1. NSE Data Scraping

**Job Name:** `nse_index_update`  
**Script:** `scripts/update_nse_indices.py`  
**Frequency:** Daily at 11:30 PM IST (after market close)  
**Duration:** ~5-10 minutes  
**Purpose:** Download NSE index constituents (NIFTY50, NIFTY500, etc.)

**What it does:**
- Downloads CSV files from NSE website
- Updates `nse_index_membership` table
- Updates `nse_sector_info` table
- Handles rate limiting and retries

**Data Sources:**
```python
NSE_INDICES = {
    "NIFTY50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "NIFTYNEXT50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "NIFTY100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    # ... 9 indices total
}
```

**Current Status:** ✅ Code exists, ⚠️ Not scheduled

---

### 2. Corporate Announcements Scraping

**Job Name:** `corporate_announcements_fetch`  
**Script:** `scripts/corporate_announcements_fetcher.py`  
**Frequency:** Daily at 11:00 PM IST  
**Duration:** ~10-15 minutes  
**Purpose:** Scrape dividends, splits, bonuses, earnings from NSE/BSE

**What it does:**
- Scrapes NSE corporate actions page
- Scrapes BSE announcements
- Parses earnings calendar
- Updates `corporate_announcements` table
- Updates `earnings_calendar` table
- Triggers alerts for watched symbols

**Current Status:** ✅ Code exists, ⚠️ Not scheduled

---

### 3. Market Data Sync

**Job Name:** `market_data_sync`  
**Script:** Uses `data_sync_manager.py`  
**Frequency:** Every hour during market hours (9:15 AM - 3:30 PM)  
**Duration:** ~2-5 minutes  
**Purpose:** Sync latest candles, quotes, option chain data

**What it syncs:**
- OHLCV candles (1min, 5min, 15min, daily)
- Option chain data
- Market quotes
- Index values

**Gap Detection:**
- Automatically detects missing data
- Schedules backfill jobs
- Logs gaps in `data_gaps` table

**Current Status:** ✅ Code exists, ⚠️ Manual execution only

---

### 4. Alert Monitoring

**Job Name:** `alert_scanner`  
**Script:** Uses `alert_system.py`  
**Frequency:** Every 1 minute during market hours  
**Duration:** <10 seconds  
**Purpose:** Check alert rules and trigger notifications

**Alert Types:**
- Price above/below threshold
- RSI overbought/oversold
- Volume spikes
- MACD crossovers
- Support/resistance breaks

**Notification Channels:**
- Email (SMTP)
- Telegram (if configured)
- Database log (always)

**Current Status:** ✅ Code exists, ⚠️ Not automated

---

### 5. News & Sentiment Analysis

**Job Name:** `news_sentiment_update`  
**Script:** `scripts/news_alerts_manager.py`  
**Frequency:** Every 30 minutes  
**Duration:** ~1-2 minutes  
**Purpose:** Fetch news and calculate sentiment scores

**Data Sources:**
- NewsAPI.org (paid tier recommended)
- FinBERT AI model for sentiment analysis

**What it does:**
- Fetches latest financial news
- Runs FinBERT sentiment analysis
- Updates `news_articles` table
- Updates `sentiment_history` table
- Triggers news-based alerts

**Current Status:** ✅ Code exists, ⚠️ Not scheduled

---

### 6. Database Maintenance

**Job Name:** `database_maintenance`  
**Frequency:** Weekly on Sunday at 2:00 AM  
**Duration:** ~5-30 minutes (depends on database size)  
**Purpose:** Optimize database performance

**Tasks:**
- `VACUUM` - Reclaim disk space
- `ANALYZE` - Update query statistics
- Integrity check
- Remove old data (>5 years)
- Compact WAL file

**Script:**
```bash
sqlite3 market_data.db "VACUUM;"
sqlite3 market_data.db "ANALYZE;"
sqlite3 market_data.db "PRAGMA integrity_check;"
```

**Current Status:** ⚠️ Manual only

---

### 7. Performance Analytics

**Job Name:** `calculate_performance_metrics`  
**Script:** Uses `performance_analytics.py`  
**Frequency:** Daily at 4:00 PM (after market close)  
**Duration:** ~2-5 minutes  
**Purpose:** Calculate daily performance metrics

**Metrics Calculated:**
- Daily P&L
- Win rate, profit factor
- Sharpe ratio, Sortino ratio
- Max drawdown
- Alpha, beta vs NIFTY50

**Tables Updated:**
- `daily_performance`
- `monthly_performance`
- `risk_metrics`
- `strategy_performance`

**Current Status:** ✅ Code exists, ⚠️ Manual execution

---

### 8. Database Backup

**Job Name:** `daily_backup`  
**Script:** `scripts/backup_db.sh`  
**Frequency:** Daily at 2:00 AM  
**Duration:** <1 minute  
**Purpose:** Create timestamped database backups

**What it backs up:**
- `market_data.db`
- `upstox.db` (if exists)
- `cache/yahoo_cache.sqlite`

**Retention Policy:**
- Last 7 daily backups
- Last 4 weekly backups
- Last 12 monthly backups

**Current Status:** ⚠️ Cron job needed

---

## 🚀 Implementation Options

### Option 1: APScheduler (Recommended)

**Advantages:**
- ✅ Production-ready
- ✅ Persistent job storage (survives restarts)
- ✅ Retry logic built-in
- ✅ Job monitoring via API
- ✅ Multiple executors (thread, process)
- ✅ Cron and interval scheduling
- ✅ Timezone support

**Installation:**
```bash
pip install apscheduler
```

**Example Implementation:**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import logging

# Configure scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(10)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time': 300  # 5 minutes
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Kolkata'
)

# Add jobs
scheduler.add_job(
    func=update_nse_indices,
    trigger='cron',
    hour=23,
    minute=30,
    id='nse_index_update',
    name='Update NSE indices',
    replace_existing=True
)

scheduler.add_job(
    func=sync_market_data,
    trigger='interval',
    minutes=60,
    id='market_data_sync',
    name='Sync market data'
)

scheduler.add_job(
    func=check_alerts,
    trigger='interval',
    minutes=1,
    id='alert_scanner',
    name='Scan alerts'
)

# Start scheduler
scheduler.start()
logging.info("Scheduler started")
```

**Management UI:**
```python
# List jobs
for job in scheduler.get_jobs():
    print(f"{job.id}: {job.next_run_time}")

# Pause job
scheduler.pause_job('alert_scanner')

# Resume job
scheduler.resume_job('alert_scanner')

# Remove job
scheduler.remove_job('alert_scanner')
```

**Integration with Flask:**
```python
# In scripts/api_server.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Add jobs
scheduler.add_job(...)

# Start when Flask app starts
@app.before_first_request
def init_scheduler():
    if not scheduler.running:
        scheduler.start()
        app.logger.info("Background scheduler started")

# Shutdown when Flask stops
import atexit
atexit.register(lambda: scheduler.shutdown())
```

---

### Option 2: Systemd Timers (Linux Only)

**Advantages:**
- ✅ Native to Linux
- ✅ Reliable and battle-tested
- ✅ Logs via journalctl
- ✅ No Python process needed

**Example Timer:**
```ini
# /etc/systemd/system/nse-update.timer
[Unit]
Description=NSE Index Update Timer
Requires=nse-update.service

[Timer]
OnCalendar=*-*-* 23:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/nse-update.service
[Unit]
Description=NSE Index Update Service

[Service]
Type=oneshot
User=upstox
WorkingDirectory=/opt/UPSTOX-PROJECT
ExecStart=/opt/UPSTOX-PROJECT/.venv/bin/python scripts/update_nse_indices.py
StandardOutput=journal
StandardError=journal
```

**Enable:**
```bash
sudo systemctl enable nse-update.timer
sudo systemctl start nse-update.timer
```

**Check status:**
```bash
systemctl list-timers
journalctl -u nse-update.service
```

---

### Option 3: Cron Jobs (Traditional)

**Advantages:**
- ✅ Simple and universal
- ✅ Works on all Unix systems

**Disadvantages:**
- ❌ No retry logic
- ❌ No job dependencies
- ❌ Limited logging

**Example Crontab:**
```bash
crontab -e
```

```cron
# NSE index update - Daily at 11:30 PM
30 23 * * * cd /path/to/UPSTOX-PROJECT && .venv/bin/python scripts/update_nse_indices.py >> logs/nse_update.log 2>&1

# Market data sync - Every hour during market hours
0 9-15 * * 1-5 cd /path/to/UPSTOX-PROJECT && .venv/bin/python -c "from scripts.data_sync_manager import DataSyncManager; DataSyncManager().sync_all()" >> logs/data_sync.log 2>&1

# Alert scanner - Every minute during market hours
*/1 9-15 * * 1-5 cd /path/to/UPSTOX-PROJECT && .venv/bin/python -c "from scripts.alert_system import AlertSystem; AlertSystem().check_all_alerts()" >> logs/alerts.log 2>&1

# Database backup - Daily at 2 AM
0 2 * * * /path/to/UPSTOX-PROJECT/scripts/backup_db.sh >> logs/backup.log 2>&1

# Database maintenance - Sunday at 2 AM
0 2 * * 0 sqlite3 /path/to/UPSTOX-PROJECT/market_data.db "VACUUM; ANALYZE;" >> logs/maintenance.log 2>&1
```

---

## 📊 Recommended Job Schedule

| Job | Frequency | Time (IST) | Duration | Priority |
|-----|-----------|------------|----------|----------|
| Alert Scanner | 1 minute | 9:15 AM - 3:30 PM | <10s | High |
| Market Data Sync | 1 hour | 9:15 AM - 3:30 PM | 2-5 min | High |
| News & Sentiment | 30 minutes | All day | 1-2 min | Medium |
| NSE Index Update | Daily | 11:30 PM | 5-10 min | High |
| Corporate Actions | Daily | 11:00 PM | 10-15 min | Medium |
| Performance Analytics | Daily | 4:00 PM | 2-5 min | Medium |
| Database Backup | Daily | 2:00 AM | <1 min | High |
| Database Maintenance | Weekly (Sun) | 2:00 AM | 5-30 min | Low |

---

## 🔧 Implementation Guide

### Step 1: Install APScheduler

```bash
pip install apscheduler==3.10.4
echo "apscheduler==3.10.4" >> requirements.txt
```

### Step 2: Create Scheduler Service

**File:** `scripts/scheduler_service.py`

```python
#!/usr/bin/env python3
"""
Background Job Scheduler Service
Runs all automated jobs for the trading platform
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime

# Import job functions
from scripts.update_nse_indices import NSEIndexUpdater
from scripts.data_sync_manager import DataSyncManager
from scripts.alert_system import AlertSystem
from scripts.performance_analytics import PerformanceAnalytics
from scripts.corporate_announcements_fetcher import CorporateAnnouncementsFetcher
from scripts.news_alerts_manager import NewsAlertsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///scheduler_jobs.db')
}
executors = {
    'default': ThreadPoolExecutor(10)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time': 300
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Kolkata'
)

# Job functions
def update_nse_indices():
    logger.info("Starting NSE index update...")
    updater = NSEIndexUpdater()
    updater.update_all_indices()
    logger.info("NSE index update completed")

def sync_market_data():
    logger.info("Starting market data sync...")
    sync_manager = DataSyncManager()
    sync_manager.sync_all()
    logger.info("Market data sync completed")

def check_alerts():
    logger.info("Checking alerts...")
    alert_system = AlertSystem()
    alert_system.check_all_alerts()

def calculate_performance():
    logger.info("Calculating performance metrics...")
    analytics = PerformanceAnalytics()
    analytics.calculate_daily_metrics()
    logger.info("Performance calculation completed")

def fetch_corporate_announcements():
    logger.info("Fetching corporate announcements...")
    fetcher = CorporateAnnouncementsFetcher()
    fetcher.fetch_all()
    logger.info("Corporate announcements fetch completed")

def fetch_news_and_sentiment():
    logger.info("Fetching news and sentiment...")
    manager = NewsAlertsManager()
    manager.fetch_and_analyze()
    logger.info("News fetch completed")

# Add jobs
scheduler.add_job(
    update_nse_indices,
    'cron',
    hour=23,
    minute=30,
    id='nse_index_update',
    name='Update NSE indices',
    replace_existing=True
)

scheduler.add_job(
    sync_market_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute=0,
    id='market_data_sync',
    name='Sync market data (hourly)'
)

scheduler.add_job(
    check_alerts,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*/1',
    id='alert_scanner',
    name='Alert scanner (every minute)'
)

scheduler.add_job(
    calculate_performance,
    'cron',
    day_of_week='mon-fri',
    hour=16,
    minute=0,
    id='performance_analytics',
    name='Calculate performance metrics'
)

scheduler.add_job(
    fetch_corporate_announcements,
    'cron',
    hour=23,
    minute=0,
    id='corporate_announcements',
    name='Fetch corporate announcements'
)

scheduler.add_job(
    fetch_news_and_sentiment,
    'interval',
    minutes=30,
    id='news_sentiment',
    name='Fetch news and sentiment'
)

def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
        logger.info(f"Next job runs:")
        for job in scheduler.get_jobs():
            logger.info(f"  {job.name}: {job.next_run_time}")

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    start_scheduler()
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
```

### Step 3: Create Systemd Service (Production)

**File:** `/etc/systemd/system/upstox-scheduler.service`

```ini
[Unit]
Description=UPSTOX Trading Platform Scheduler
After=network.target

[Service]
Type=simple
User=upstox
WorkingDirectory=/opt/UPSTOX-PROJECT
Environment="PATH=/opt/UPSTOX-PROJECT/.venv/bin"
ExecStart=/opt/UPSTOX-PROJECT/.venv/bin/python scripts/scheduler_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable upstox-scheduler
sudo systemctl start upstox-scheduler
sudo systemctl status upstox-scheduler
```

### Step 4: Monitor Jobs

**View logs:**
```bash
sudo journalctl -u upstox-scheduler -f
```

**Check job status (Python):**
```python
from scripts.scheduler_service import scheduler

# List all jobs
for job in scheduler.get_jobs():
    print(f"{job.id}: Next run = {job.next_run_time}")

# Get job details
job = scheduler.get_job('nse_index_update')
print(job)
```

---

## 📧 Email Notification Setup

### SMTP Configuration

**In `.env`:**
```bash
# Email settings
EMAIL_ENABLED=true
EMAIL_FROM=trading@example.com
EMAIL_TO=user@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

### Email Templates

**Job Failure Email:**
```python
def send_job_failure_email(job_name, error_message):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    
    if os.getenv('EMAIL_ENABLED') != 'true':
        return
    
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_FROM')
    msg['To'] = os.getenv('EMAIL_TO')
    msg['Subject'] = f'[ALERT] Job Failed: {job_name}'
    
    body = f"""
    Job: {job_name}
    Status: FAILED
    Time: {datetime.now()}
    Error: {error_message}
    
    Please check the logs for details.
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
```

---

## 🐛 Troubleshooting

### Jobs Not Running

**Check scheduler status:**
```python
from scripts.scheduler_service import scheduler
print(scheduler.running)  # Should be True
print(scheduler.get_jobs())  # List all jobs
```

**Check systemd service:**
```bash
sudo systemctl status upstox-scheduler
sudo journalctl -u upstox-scheduler -n 50
```

### Job Failures

**Check error logs:**
```bash
tail -f logs/scheduler.log
```

**Check database:**
```sql
SELECT * FROM sync_history WHERE status = 'FAILED' ORDER BY started_at DESC LIMIT 10;
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

---

## 📚 Related Documentation

- **[DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)** - Database tables for jobs
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[SHELL_SCRIPTS.md](SHELL_SCRIPTS.md)** - Shell script automation

---

**Current Status:** ⚠️ Implementation Needed  
**Recommended:** APScheduler + Systemd  
**Timeline:** 2-3 days to implement
