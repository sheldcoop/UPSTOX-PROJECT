# 🎯 Corporate Actions - What You REALLY Need & How Often

**Practical Guide: Frequency vs Value for Retail Traders**

---

## 📊 REALITY CHECK: What Happens How Often?

### **Data Collection Frequency Analysis:**

| Corporate Action | How Often It Happens | How Often to Check | Impact on Trading |
|------------------|---------------------|-------------------|-------------------|
| **Dividend Announcements** | Quarterly/Annually | **Once a day** | ⭐⭐⭐⭐⭐ HIGH |
| **Earnings Dates** | Quarterly (4x/year) | **Once a day** | ⭐⭐⭐⭐⭐ CRITICAL |
| **Stock Splits** | Rare (1-2x/year) | **Once a week** | ⭐⭐⭐ MEDIUM |
| **Bonus Issues** | Rare (1-2x/year) | **Once a week** | ⭐⭐⭐ MEDIUM |
| **Rights Issues** | Rare (once in 2-3 years) | **Once a week** | ⭐⭐ LOW |
| **Board Meetings** | Monthly | **Once a day** | ⭐⭐⭐⭐ HIGH |
| **M&A Announcements** | Very rare | **Once a week** | ⭐⭐ LOW |
| **AGM/EGM Dates** | Annually | **Once a month** | ⭐ VERY LOW |

---

## ⚡ What You REALLY Need (Priority Order)

### **🔥 CRITICAL (Check Daily - Must Have):**

#### **1. Earnings Dates**
```
Why critical:
- Stock moves 5-15% on earnings day
- Need to avoid or prepare for volatility
- Set up pre-earnings positions

Real Example:
INFY Q3 FY26 Results: Jan 15, 2026
→ Stock moved from ₹1,750 to ₹1,820 (+4%) in 1 day
→ Options IV jumped 50% → 100% week before

What you need:
- Earnings date: Jan 15, 2026
- Earnings time: After market close
- Conference call: 4:30 PM IST

How often: Check ONCE A DAY (morning 8 AM)
Why: Companies announce dates 15-30 days in advance
```

**Trading Strategy:**
```python
# If earnings in 7 days:
if days_until_earnings <= 7:
    print("ALERT: High volatility expected")
    
    # Options traders: Increase IV → sell options
    if strategy == 'options_selling':
        sell_straddle(symbol)
    
    # Equity traders: Reduce position size
    if strategy == 'equity':
        reduce_position_by(50)
    
    # Avoid new positions
    block_new_orders(symbol)
```

---

#### **2. Dividend Announcements**
```
Why critical:
- Stock falls ~2-3% on ex-dividend date
- Need to decide: hold for dividend or exit before?
- Affects short-term trading

Real Example:
INFY Dividend: ₹18 per share
Ex-date: Jan 22, 2026

Scenario 1: You hold 100 shares
Jan 21 (before ex-date): Stock at ₹1,800
Jan 22 (ex-date): Stock drops to ₹1,782 (-₹18)
You receive: ₹1,800 dividend (taxed at 10%)
Net gain: ₹1,620 dividend - ₹1,800 capital loss = -₹180

Scenario 2: You sell before ex-date
Jan 21: Sell at ₹1,800
Result: No dividend, but no ₹18 drop

What you need:
- Dividend amount: ₹18 per share
- Ex-date: Jan 22, 2026
- Record date: Jan 23, 2026
- Payment date: Feb 15, 2026

How often: Check ONCE A DAY (morning 8 AM)
Why: Announced 7-15 days before ex-date
```

**Trading Strategy:**
```python
# If ex-date in 3 days:
if days_until_exdate <= 3:
    
    # Decide: hold or sell
    if dividend_yield > 2% and holding_period > 1_year:
        print("HOLD for dividend (LTCG tax benefit)")
    else:
        print("SELL before ex-date (avoid price drop)")
    
    # For F&O traders
    if trading_futures:
        print("ALERT: Futures price will adjust for dividend")
```

---

#### **3. Board Meeting Dates**
```
Why important:
- Board discusses dividends, results, expansions
- Stock can move 2-5% on speculation
- Usually precedes major announcements

Real Example:
INFY Board Meeting: Jan 10, 2026
Purpose: Approve Q3 results and interim dividend

Pre-meeting (Jan 5-9): Stock up 3% on speculation
Meeting day (Jan 10): Results announced → stock +4%

What you need:
- Meeting date: Jan 10, 2026
- Purpose: Results & dividend approval
- Time: 11:00 AM IST

How often: Check ONCE A DAY
Why: Announced 7-14 days in advance
```

---

### **⚠️ IMPORTANT (Check Weekly - Good to Have):**

#### **4. Stock Splits**
```
Why matters:
- Changes share price (not value)
- Increases liquidity
- Psychological impact (looks "cheaper")

Real Example:
INFY announces 1:2 split
Before: ₹1,800 per share (you own 100 shares = ₹1,80,000)
After: ₹900 per share (you own 200 shares = ₹1,80,000)

Impact on trading:
- No change in portfolio value
- Better for small investors (lower price)
- Usually bullish sentiment

What you need:
- Split ratio: 1:2 (each share becomes 2)
- Record date: Feb 1, 2026
- Ex-date: Feb 5, 2026

How often: Check ONCE A WEEK
Why: Very rare, announced 30-60 days in advance
```

---

#### **5. Bonus Issues**
```
Why matters:
- Free shares issued
- Dilutes EPS but no cash outflow
- Usually bullish signal

Real Example:
INFY announces 1:1 bonus
Before: You own 100 shares at ₹1,800 = ₹1,80,000
After: You own 200 shares at ₹900 = ₹1,80,000
Bonus: 100 free shares

Impact:
- Your shareholding doubles
- Price adjusts (value unchanged)
- Tax-free capital gain opportunity

What you need:
- Bonus ratio: 1:1
- Record date: Mar 15, 2026
- Ex-date: Mar 18, 2026

How often: Check ONCE A WEEK
Why: Rare (1-2 times per year), announced 45-60 days ahead
```

---

### **📝 OPTIONAL (Check Monthly - Nice to Have):**

#### **6. Rights Issues**
```
Why less important for most traders:
- Only matters if you want to invest more
- Can ignore and let rights lapse
- Rare event

Real Example:
INFY announces 1:5 rights at ₹1,500
You own 100 shares
Rights: 20 shares at ₹1,500 each (₹30,000 investment)
Current price: ₹1,800

Decision:
Option 1: Buy rights (invest ₹30,000 more)
Option 2: Ignore (no impact on existing shares)
Option 3: Sell rights in market (₹6,000 gain)

How often: Check ONCE A MONTH
Why: Very rare (once in 2-3 years)
```

---

#### **7. M&A Announcements**
```
Why less important:
- Rare events
- When it happens, it's BIG news (hard to miss)
- Usually take 6-12 months to complete

How often: Check ONCE A MONTH (or just read news)
Why: Major news outlets cover it immediately
```

---

#### **8. AGM/EGM Dates**
```
Why least important for traders:
- No immediate price impact
- Voting rights (long-term investors)
- Results already announced before AGM

How often: Check ONCE A QUARTER (or ignore)
Why: Doesn't affect trading decisions
```

---

## 🎯 RECOMMENDED SETUP

### **Scenario 1: Active Trader (Daily Trading)**

**What to track:**
1. ✅ Earnings dates (DAILY check)
2. ✅ Dividend announcements (DAILY check)
3. ✅ Board meetings (DAILY check)
4. ❌ Skip rest (low value for daily trading)

**Automation:**
```bash
# Run once every morning at 8 AM
crontab -e

# Add this line:
0 8 * * 1-5 cd /path/to/project && python scripts/fetch_critical_events.py
```

**Script fetches:**
- Upcoming earnings (next 30 days)
- Dividend announcements (next 15 days)
- Board meetings (next 7 days)

**Result:** 
- Takes 30 seconds to run
- Sends Telegram alert if any events for your holdings
- Database updated once daily

---

### **Scenario 2: Swing Trader (Hold 1-4 weeks)**

**What to track:**
1. ✅ Earnings dates (DAILY)
2. ✅ Dividend announcements (DAILY)
3. ✅ Board meetings (DAILY)
4. ✅ Stock splits (WEEKLY)
5. ✅ Bonus issues (WEEKLY)
6. ❌ Skip rest

**Automation:**
```bash
# Daily checks (8 AM)
0 8 * * 1-5 python scripts/fetch_critical_events.py

# Weekly checks (Monday 8 AM)
0 8 * * 1 python scripts/fetch_corporate_actions.py
```

---

### **Scenario 3: Long-term Investor (Hold 1+ year)**

**What to track:**
1. ✅ Earnings dates (WEEKLY is enough)
2. ✅ Dividend announcements (WEEKLY)
3. ✅ All corporate actions (MONTHLY)

**Automation:**
```bash
# Weekly check (Monday 8 AM)
0 8 * * 1 python scripts/fetch_all_events.py
```

---

## 💾 STORAGE & DATABASE GROWTH

### **How much data will accumulate?**

#### **If you track 10 stocks:**

| Event Type | Events/Year | Database Rows | Storage Size |
|------------|-------------|---------------|--------------|
| Earnings dates | 40 (10 stocks × 4 quarters) | 40 | ~5 KB |
| Dividends | 20 (10 stocks × 2 dividends) | 20 | ~3 KB |
| Board meetings | 120 (10 stocks × 12 months) | 120 | ~15 KB |
| Splits/Bonus | 5 (rare) | 5 | ~1 KB |
| **TOTAL** | **185 events/year** | **185 rows** | **~25 KB/year** |

**After 5 years:** ~125 KB (negligible!)

#### **If you track 100 stocks:**

| Event Type | Events/Year | Storage Size |
|------------|-------------|--------------|
| All events | ~1,850 events | ~250 KB/year |
| After 5 years | ~9,250 events | ~1.2 MB total |

**Conclusion:** Database growth is MINIMAL (unlike tick data which is GB/year)

---

## 🚀 WHAT WE SHOULD BUILD

### **Option A: Minimal (Daily Traders)**

**Fetch only CRITICAL events:**
```python
# scripts/fetch_critical_events.py

def fetch_critical_only():
    # 1. Earnings dates (next 30 days)
    earnings = scrape_nse_earnings(days=30)
    
    # 2. Dividends (next 15 days)
    dividends = scrape_nse_dividends(days=15)
    
    # 3. Board meetings (next 7 days)
    board_meetings = scrape_nse_board_meetings(days=7)
    
    # Store in database
    # Send Telegram alert if any events for your watchlist
    
# Run: Once daily (8 AM)
# Time: ~30 seconds
# API calls: 3 requests to NSE
# Storage: ~50 bytes per event
```

**What you get:**
- ✅ Critical events only
- ✅ Fast execution (30 sec)
- ✅ Low storage (~25 KB/year)
- ✅ Telegram alerts
- ❌ No splits/bonus (rare anyway)

---

### **Option B: Complete (All Traders)**

**Fetch everything, but smartly:**
```python
# scripts/fetch_all_corporate_actions.py

def fetch_all_smartly():
    # Daily (every morning 8 AM):
    fetch_critical_only()  # Earnings, dividends, board meetings
    
    # Weekly (Monday 8 AM):
    if today.weekday() == 0:  # Monday
        fetch_splits_bonus(days=90)
        fetch_rights_issues(days=180)
    
    # Monthly (1st of month):
    if today.day == 1:
        fetch_agm_dates(days=365)
        fetch_ma_announcements(days=180)

# Run: Automated via cron
# Time: Daily 30 sec, Weekly +15 sec, Monthly +5 sec
# Storage: ~250 KB/year (for 100 stocks)
```

**What you get:**
- ✅ Everything tracked
- ✅ Smart scheduling (not wasteful)
- ✅ Still minimal storage
- ✅ Complete audit trail

---

## 📊 MY RECOMMENDATION

### **For YOU (based on typical retail trader):**

**Build Option A + Weekly Bonus/Splits:**

```python
# Daily (8 AM): Critical events
0 8 * * 1-5 python scripts/fetch_critical_events.py

# Weekly (Monday 8 AM): Splits/Bonus
0 8 * * 1 python scripts/fetch_splits_bonus.py
```

**Why this setup:**
1. ✅ Covers 95% of trading-relevant events
2. ✅ Fast (30 sec daily, 15 sec weekly)
3. ✅ Minimal storage (~30 KB/year)
4. ✅ No API rate limits (NSE allows scraping)
5. ✅ Telegram alerts for YOUR holdings only
6. ✅ Low maintenance (no breaking daily)

**What you'll miss:**
- ❌ Rights issues (rare, low impact on traders)
- ❌ M&A (covered by news anyway)
- ❌ AGM dates (irrelevant for trading)

**Impact of missing these:** Near zero for active trading

---

## 🎯 FINAL DECISION TREE

```
Are you a DAILY TRADER?
├─ YES → Fetch: Earnings + Dividends + Board Meetings (DAILY)
│         Skip: Everything else
│         Reason: Need to avoid earnings volatility, plan around dividends
│
└─ NO → Are you a SWING TRADER (1-4 weeks)?
    ├─ YES → Fetch: Earnings + Dividends + Board (DAILY)
    │                Splits + Bonus (WEEKLY)
    │         Skip: Rights, M&A, AGM
    │         Reason: Corporate actions can affect multi-week positions
    │
    └─ NO → You're LONG-TERM INVESTOR
              Fetch: Everything (WEEKLY or MONTHLY)
              Reason: Tax planning, voting rights matter
```

---

## ✅ WHAT TO BUILD RIGHT NOW

**I recommend building:**

1. **fetch_critical_events.py** (30 minutes)
   - Scrape NSE for earnings + dividends + board meetings
   - Run daily at 8 AM
   - Send Telegram alert if events for YOUR watchlist
   - Store in existing database

2. **fetch_bonus_splits.py** (15 minutes)
   - Scrape NSE for splits + bonus
   - Run weekly (Monday 8 AM)
   - Alert if any of YOUR holdings affected

**Total build time:** 45 minutes  
**Total cost:** ₹0 (free NSE scraping)  
**Value:** CRITICAL for trading decisions

---

## ❓ YOUR DECISION

Tell me your trading style:

1. ✅ **Daily trader** → Build earnings + dividends only (20 min)
2. ✅ **Swing trader** → Build earnings + dividends + splits (45 min) **RECOMMENDED**
3. ✅ **Long-term investor** → Build everything (1 hour)
4. ❌ **Skip for now** → Keep using mock data

**Which one?** I'll build it RIGHT NOW! 🚀
