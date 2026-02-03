# 🔍 News, Sentiment & Announcements - TRUTH REVEALED

**IMPORTANT: Current Status of Data Sources**

---

## ⚠️ REALITY CHECK - What's Actually Happening

### **1. NEWS & SENTIMENT ANALYSIS**

#### **Current Implementation:**
```python
# Location: scripts/news_alerts_manager.py

def fetch_latest_news(self, symbol, limit=10):
    # In production, this would fetch from news API
    # For now, generate mock news data  ← THIS IS WHAT'S HAPPENING NOW
    
    mock_news = self._generate_mock_news(symbol, limit)
    
    # Store in database
    for news in mock_news:
        self._store_news(news)
```

**What You're Getting:**
- ❌ **NOT REAL NEWS** - It's mock/dummy data
- ✅ Sentiment analysis works (but on fake news)
- ✅ Database storage works
- ✅ Keyword matching works (POSITIVE/NEGATIVE/NEUTRAL)

**Mock News Templates (5 templates rotate):**
```python
1. "{symbol} reports strong Q3 earnings, beats estimates" → POSITIVE
2. "Analysts upgrade {symbol} to BUY, raise target price" → POSITIVE
3. "{symbol} faces regulatory scrutiny over compliance issues" → NEGATIVE
4. "{symbol} announces ₹15 per share dividend" → POSITIVE
5. "{symbol} Q3 revenue misses expectations, stock falls" → NEGATIVE
```

**Sentiment Analysis (REAL algorithm):**
```python
# These work on ANY text (real or mock):
positive_keywords = [
    'profit', 'growth', 'gain', 'rise', 'surge', 'boost', 'upgrade',
    'expand', 'acquisition', 'merger', 'dividend', 'bonus', 'buy',
    'outperform', 'strong', 'record', 'high', 'beat', 'exceed'
]

negative_keywords = [
    'loss', 'decline', 'fall', 'drop', 'plunge', 'downgrade', 'cut',
    'weak', 'miss', 'below', 'concern', 'risk', 'delay', 'cancel',
    'sell', 'underperform', 'regulatory', 'fine', 'lawsuit', 'fraud'
]

# Scoring: (positive_count - negative_count) / total_words
# BULLISH: score > 0.2
# BEARISH: score < -0.2
# NEUTRAL: -0.2 to 0.2
```

---

### **2. CORPORATE ANNOUNCEMENTS**

#### **Current Implementation:**
```python
# Location: scripts/corporate_announcements_fetcher.py

def get_corporate_actions(self, symbol):
    try:
        # Upstox API endpoint for corporate actions
        url = f"https://api.upstox.com/v2/corporate-actions/{symbol}"
        response = requests.get(url, headers=self.headers)
        
        # If API fails or no token → falls back to mock data
        if not self.access_token:
            return self._generate_mock_earnings(symbol)
    
    except RequestException:
        # Network error → falls back to mock data
        return self._generate_mock_earnings(symbol)
```

**What You're Getting:**

| Scenario | Data Source | Update Frequency |
|----------|-------------|------------------|
| **With Upstox Token** | ✅ REAL from Upstox API | On-demand (when you run script) |
| **No Token** | ❌ MOCK data | Static (pre-generated) |
| **API Down** | ❌ MOCK data | Static (pre-generated) |

**Upstox API Coverage:**
- ✅ Dividend announcements
- ✅ Stock splits
- ✅ Bonus shares
- ✅ Rights issues
- ✅ Buybacks
- ⚠️ Earnings dates (may not be available, falls back to mock)

**Mock Earnings Templates:**
```python
# Generated for demo purposes
{
    'symbol': 'INFY',
    'earnings_date': '2026-04-15',
    'quarter': 'Q4 FY26',
    'expected_eps': 18.50,
    'consensus_rating': 'BUY',
    'surprise_pct': None,  # Unknown until actual release
    'impact_level': 'HIGH'
}
```

---

### **3. ECONOMIC CALENDAR**

#### **Current Implementation:**
```python
# Location: scripts/economic_calendar_fetcher.py

def _load_static_events(self):
    """Load known recurring economic events for 2026."""
    
    # ✅ REAL DATES - Pre-loaded from official sources
    rbi_meetings_2026 = [
        {'date': '2026-02-07'},  # RBI publishes these dates in advance
        {'date': '2026-04-10'},
        {'date': '2026-06-08'},
        {'date': '2026-08-09'},
        {'date': '2026-10-09'},
        {'date': '2026-12-06'}
    ]
    
    fed_meetings_2026 = [
        {'date': '2026-01-29'},  # Fed publishes yearly calendar
        {'date': '2026-03-18'},
        # ... 8 meetings total
    ]
```

**What You're Getting:**
- ✅ **REAL DATES** - Pre-loaded from official calendars
- ✅ **STATIC** - Won't change (RBI/Fed publish dates months in advance)
- ✅ **51 Events for 2026:**
  * 6 RBI MPC meetings
  * 8 Fed FOMC meetings
  * 4 GDP releases
  * 11 CPI inflation releases
  * 22 PMI releases (manufacturing + services)

**Update Frequency:**
- ❌ **NOT UPDATED** - Static data loaded at startup
- ✅ Accurate (sourced from official calendars)
- ⚠️ Actual data (CPI numbers, GDP %, rate decisions) NOT available

---

## 🎯 Summary Table - What's REAL vs MOCK

| Feature | Data Source | Real/Mock | Update Method | Frequency |
|---------|-------------|-----------|---------------|-----------|
| **News Headlines** | Mock generator | ❌ MOCK | Auto-generated | On demand |
| **Sentiment Analysis** | Keyword algorithm | ✅ REAL | Calculated live | Real-time |
| **Corporate Actions** | Upstox API* | ✅ REAL* | API call | On demand |
| **Earnings Dates** | Mock/API* | ⚠️ MIXED | API or mock | On demand |
| **Economic Events** | Pre-loaded static | ✅ REAL DATES | Static file | Never updates |
| **CPI/GDP Numbers** | Not available | ❌ MOCK | N/A | N/A |
| **RBI/Fed Decisions** | Event dates only | ✅ REAL DATES | N/A | N/A |

*Requires UPSTOX_ACCESS_TOKEN

---

## 🔧 How to Get REAL Data

### **Option 1: Use Upstox API (Partial)**

```bash
# Set access token
export UPSTOX_ACCESS_TOKEN='your_token_here'

# Now corporate actions will be REAL
/Users/prince/Desktop/UPSTOX-project/.venv/bin/python scripts/corporate_announcements_fetcher.py \
    --action dividends \
    --symbol NSE_EQ|INE009A01021
```

**What Upstox Provides:**
- ✅ Dividend announcements (real)
- ✅ Stock splits (real)
- ✅ Bonus shares (real)
- ⚠️ Earnings dates (limited)
- ❌ News headlines (not available)
- ❌ Sentiment analysis (not available)

---

### **Option 2: Add Real News API (RECOMMENDED)**

**Need to integrate with news providers:**

#### **A. NewsAPI.org (Free tier: 100 requests/day)**

```python
# Add to news_alerts_manager.py

NEWS_API_KEY = os.getenv('NEWS_API_KEY')

def fetch_latest_news(self, symbol, limit=10):
    url = f"https://newsapi.org/v2/everything"
    params = {
        'q': f'{symbol} OR Infosys',  # Search query
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': limit,
        'apiKey': NEWS_API_KEY
    }
    
    response = requests.get(url, params=params)
    articles = response.json().get('articles', [])
    
    # Now sentiment analysis works on REAL news
    for article in articles:
        sentiment = self._analyze_sentiment(article['title'] + ' ' + article['description'])
        article['sentiment'] = sentiment
```

**Cost:** FREE (100 requests/day) or $449/month (unlimited)

---

#### **B. Alpha Vantage (Free tier: 500 requests/day)**

```python
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

def fetch_latest_news(self, symbol, limit=10):
    url = f"https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS_SENTIMENT',
        'tickers': symbol,
        'apikey': ALPHA_VANTAGE_KEY,
        'limit': limit
    }
    
    response = requests.get(url, params=params)
    news = response.json().get('feed', [])
    
    # Alpha Vantage includes sentiment score!
    for article in news:
        article['sentiment'] = article.get('overall_sentiment_label')
```

**Cost:** FREE (500 requests/day) or $49.99/month (premium)

---

#### **C. Moneycontrol/Economic Times (Web Scraping)**

```python
import requests
from bs4 import BeautifulSoup

def scrape_moneycontrol_news(symbol):
    url = f"https://www.moneycontrol.com/news/tags/{symbol.lower()}.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    articles = []
    for item in soup.find_all('h2'):
        headline = item.get_text()
        link = item.find('a')['href']
        articles.append({
            'headline': headline,
            'url': link,
            'source': 'Moneycontrol',
            'published_at': datetime.now()
        })
    
    return articles
```

**Cost:** FREE (but may break if site structure changes)

---

#### **D. RapidAPI - Indian Stock News (Paid)**

```python
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

def fetch_indian_stock_news(symbol):
    url = "https://indian-stock-exchange-api.p.rapidapi.com/news"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "indian-stock-exchange-api.p.rapidapi.com"
    }
    params = {'symbol': symbol}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

**Cost:** $10-50/month depending on plan

---

### **Option 3: Add Economic Data API**

**For ACTUAL CPI, GDP numbers:**

#### **Trading Economics API**

```python
def fetch_india_gdp():
    url = "https://api.tradingeconomics.com/country/india/indicator/gdp"
    params = {'c': TRADING_ECONOMICS_KEY}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return {
        'date': data[0]['DateTime'],
        'actual': data[0]['Value'],
        'previous': data[0]['Previous'],
        'forecast': data[0].get('Forecast')
    }
```

**Cost:** $50-500/month

---

## 💡 My Recommendation

### **For NOW (Free Solution):**

1. **Keep Economic Calendar** - ✅ Real dates, good enough
2. **Use Upstox API** - ✅ Real corporate actions (dividends, splits)
3. **Add NewsAPI.org FREE tier** - ✅ 100 real news/day
4. **Keep Sentiment Engine** - ✅ Works perfectly on real news

### **Cost Breakdown:**

| Service | Tier | Cost | What You Get |
|---------|------|------|--------------|
| **Upstox API** | Free with account | ₹0 | Corporate actions |
| **NewsAPI.org** | Free tier | ₹0 | 100 news/day |
| **Economic Calendar** | Static pre-load | ₹0 | 51 event dates |
| **Sentiment Analysis** | Your algorithm | ₹0 | Unlimited |
| **TOTAL** | - | **₹0/month** | Good for retail trader |

### **For SERIOUS Trading (Paid):**

| Service | Tier | Cost | What You Get |
|---------|------|------|--------------|
| **NewsAPI.org** | Developer | $449/month | Unlimited news |
| **Alpha Vantage** | Premium | $49.99/month | News + sentiment |
| **Trading Economics** | Basic | $50/month | Real economic data |
| **TOTAL** | - | **~$550/month** | Institutional-grade |

---

## 🚀 Quick Fix - Add Real News NOW (5 minutes)

**Step 1: Get FREE NewsAPI.org key**
```bash
# Sign up: https://newsapi.org/register
# Get API key (instant, no credit card)
export NEWS_API_KEY='your_key_here'
```

**Step 2: I'll update news_alerts_manager.py**

Want me to add NewsAPI.org integration right now? It's FREE and takes 5 minutes!

---

## 📊 Current Testing Results (With Mock Data)

When you ran these commands:
```bash
# 3. Test news sentiment
/Users/prince/Desktop/UPSTOX-project/.venv/bin/python scripts/news_alerts_manager.py \
    --action sentiment \
    --symbol INFY \
    --days 30
```

**You Got:**
- 5 mock news articles
- INFY sentiment: 60% positive, 40% negative → NEUTRAL rating
- Stored in database: `news_articles` table

**This is DEMO DATA** - The sentiment algorithm is real, but news is fake.

---

## ✅ Action Plan

**Tell me what you want:**

1. ✅ **Keep mock data** - Good for testing, ₹0 cost
2. ✅ **Add FREE NewsAPI.org** - 100 real news/day, ₹0 cost (I can do this NOW)
3. ✅ **Add PAID Alpha Vantage** - 500 news/day + sentiment, $49.99/month
4. ✅ **Build web scraper** - FREE but may break, maintenance needed
5. ✅ **Keep current setup** - Mock data is fine for backtesting

**Which option do you prefer?** 🤔
