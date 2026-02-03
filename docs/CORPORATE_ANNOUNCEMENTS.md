# Corporate Announcements Page Documentation

## Overview
The Corporate Announcements page provides real-time access to NSE corporate filings, financial results, events, and board meetings for listed companies.

## Location
- **File:** `/dashboard_ui/pages/corporate_announcements.py`
- **Route:** Accessible via "Corporate Announcements" in the Tools menu
- **Page ID:** `corporate_announcements`

## Features

### 1. Tab-Based Interface
Four main sections accessible via tabs:

#### a. Corporate Announcements (📢)
- Company announcements and filings
- Dividend declarations
- Acquisitions and mergers
- Press releases
- Material events

#### b. Financial Results (📊)
- Quarterly results (Q1, Q2, Q3, Q4)
- Annual results
- Audited/Unaudited financials
- Result type categorization

#### c. Event Calendar (📅)
- Annual General Meetings (AGM)
- Earnings calls
- Investor meets
- Dividend payment dates
- Record dates

#### d. Board Meetings (🏢)
- Upcoming board meetings
- Meeting purposes
- Result approval meetings
- Dividend declarations
- Fundraising approvals
- Buyback proposals

### 2. Filtering & Search

#### Search Box
- Search by company name
- Search by subject/purpose
- Real-time filtering

#### Date Filters
- **Quick Filters:** 7, 14, 30, 60, 90 days
- **Custom Range:** Start date to end date picker
- Auto-reset when switching filters

### 3. Data Display

#### Table Features
- **Sortable columns**
- **Responsive design** (mobile-friendly)
- **Hover effects** for better UX
- **Color-coded badges** for categories
- **Direct links** to NSE source documents

#### Columns
**Announcements:**
- Company Name
- Symbol
- Subject
- Date
- Category
- Actions (View link)

**Financial Results:**
- Company Name
- Symbol
- Period (Q1-Q4, Annual)
- Date
- Type (Audited/Unaudited)
- Actions

**Events:**
- Company Name
- Symbol
- Event Type
- Date
- Venue
- Actions

**Board Meetings:**
- Company Name
- Symbol
- Meeting Date
- Purpose
- Category
- Actions

### 4. Pagination
- **20 rows per page** (configurable)
- First/Previous/Next/Last controls
- Current page indicator
- Total results count

### 5. Auto-Refresh
- **Manual refresh** button with loading state
- **Auto-refresh toggle** (hourly when enabled)
- **Last updated timestamp** display
- Visual feedback on refresh

## Database Schema

### Tables Created

#### 1. `nse_announcements`
```sql
CREATE TABLE nse_announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    symbol TEXT,
    subject TEXT NOT NULL,
    announcement_date DATE NOT NULL,
    category TEXT,
    url TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, subject, announcement_date)
);
```

#### 2. `nse_financial_results`
```sql
CREATE TABLE nse_financial_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    symbol TEXT,
    period TEXT NOT NULL,
    result_date DATE NOT NULL,
    category TEXT,
    result_type TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, period, result_date)
);
```

#### 3. `nse_events`
```sql
CREATE TABLE nse_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    symbol TEXT,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    venue TEXT,
    purpose TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, event_type, event_date)
);
```

#### 4. `nse_board_meetings`
```sql
CREATE TABLE nse_board_meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    symbol TEXT,
    meeting_date DATE NOT NULL,
    purpose TEXT,
    category TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, meeting_date, purpose)
);
```

#### 5. `scraping_status`
```sql
CREATE TABLE scraping_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT UNIQUE NOT NULL,
    last_scraped TIMESTAMP,
    status TEXT,
    error_message TEXT,
    records_count INTEGER DEFAULT 0
);
```

### Indexes
- `idx_announcements_date` on `announcement_date`
- `idx_results_date` on `result_date`
- `idx_events_date` on `event_date`
- `idx_meetings_date` on `meeting_date`

## Mock Data

The page initializes with **mock data** for testing:

### Sample Companies Included
- Reliance Industries Ltd (RELIANCE)
- Tata Consultancy Services Ltd (TCS)
- HDFC Bank Ltd (HDFCBANK)
- Infosys Ltd (INFY)
- ITC Ltd (ITC)
- Tata Motors Ltd (TATAMOTORS)
- Wipro Ltd (WIPRO)
- Asian Paints Ltd (ASIANPAINT)
- State Bank of India (SBIN)
- And more...

### Mock Data Categories
- Board Meeting Outcomes
- Dividend Declarations
- Financial Results
- Acquisitions
- AGM Notices
- Earnings Calls
- Investor Meets

## Future Implementation: Web Scraping

### NSE Scraping Targets

The `NSEScraper` class is a **placeholder** for future implementation:

#### Target URLs
1. **Announcements:**  
   `https://www.nseindia.com/companies-listing/corporate-filings-announcements`

2. **Financial Results:**  
   `https://www.nseindia.com/companies-listing/corporate-filings-financial-results`

3. **Event Calendar:**  
   `https://www.nseindia.com/companies-listing/corporate-filings-event-calendar`

### Required Implementation Steps

#### 1. Dependencies
```python
import requests
from bs4 import BeautifulSoup
from selenium import webdriver  # For JavaScript-heavy pages
from selenium.webdriver.common.by import By
```

#### 2. Session Setup
```python
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
})
```

#### 3. Scraping Logic
```python
def scrape_announcements(self, days: int = 7):
    # 1. Make request to NSE
    response = self.session.get(self.BASE_URLS['announcements'])
    
    # 2. Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 3. Find table rows (inspect NSE page for actual selectors)
    table = soup.find('table', {'id': 'announcements-table'})
    rows = table.find_all('tr')
    
    # 4. Extract data
    announcements = []
    for row in rows[1:]:  # Skip header
        cols = row.find_all('td')
        announcements.append({
            'company_name': cols[0].text.strip(),
            'symbol': cols[1].text.strip(),
            'subject': cols[2].text.strip(),
            'date': cols[3].text.strip(),
            'category': cols[4].text.strip(),
            'url': cols[5].find('a')['href'] if cols[5].find('a') else None
        })
    
    # 5. Insert into database
    self._insert_announcements(announcements)
    
    return announcements
```

#### 4. Error Handling
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

#### 5. Rate Limiting
```python
import time

def scrape_with_rate_limit(self):
    time.sleep(2)  # Wait 2 seconds between requests
    # Make request...
```

### Selenium Alternative (for JavaScript pages)

NSE may use JavaScript to load data dynamically. In that case:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.get(url)

# Wait for table to load
driver.implicitly_wait(10)

# Extract data
table_html = driver.find_element(By.ID, 'announcements-table').get_attribute('outerHTML')
soup = BeautifulSoup(table_html, 'html.parser')
# Continue parsing...

driver.quit()
```

## Background Scheduler

### APScheduler Implementation

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def init_scheduler():
    scheduler = BackgroundScheduler()
    
    # Nightly update at 11 PM IST
    scheduler.add_job(
        scrape_all_nse_data,
        trigger=CronTrigger(hour=23, minute=0, timezone='Asia/Kolkata'),
        id='nightly_nse_scrape',
        name='Nightly NSE Data Scrape',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler

def scrape_all_nse_data():
    """Scrape all NSE data types"""
    scraper = NSEScraper()
    
    try:
        # Announcements
        scraper.scrape_announcements()
        update_scraping_status('announcements', 'success')
    except Exception as e:
        logger.error(f"Announcements scraping failed: {e}")
        update_scraping_status('announcements', 'failed', str(e))
    
    # Similarly for other data types...
```

### Hourly Auto-Refresh

```python
# In render_page function
if page_state['auto_refresh']:
    ui.timer(3600, lambda: manual_refresh())  # 3600 seconds = 1 hour
```

## UI Components Used

### NiceGUI Components
- `ui.tabs()` - Tab navigation
- `ui.tab()` - Individual tab
- `ui.tab_panels()` - Tab content containers
- `ui.tab_panel()` - Individual panel
- `ui.input()` - Search and date inputs
- `ui.select()` - Days filter dropdown
- `ui.button()` - Refresh button
- `ui.switch()` - Auto-refresh toggle
- `ui.element('table')` - Data tables
- `ui.badge()` - Category badges
- `ui.link()` - External links
- `ui.label()` - Text labels

### Styling Classes
- `bg-slate-900/50` - Semi-transparent dark background
- `border-slate-800` - Subtle borders
- `text-indigo-400` - Primary accent color
- `hover:bg-slate-700/50` - Hover effects
- `animate-fade-in` - Smooth transitions

## Usage Instructions

### Accessing the Page
1. Start the dashboard: `python nicegui_dashboard.py`
2. Navigate to **Tools → Corporate Announcements**

### Searching Data
1. Enter company name or keyword in search box
2. Press Enter or wait for auto-update
3. Results filter instantly

### Filtering by Date
**Quick Filter:**
- Select 7, 14, 30, 60, or 90 days from dropdown

**Custom Range:**
- Click "Start Date" picker
- Select start date
- Click "End Date" picker
- Select end date
- Results update automatically

### Manual Refresh
- Click the refresh button (🔄) in control panel
- Loading state shows during refresh
- Last updated timestamp updates

### Auto-Refresh
- Toggle "Auto-refresh" switch
- Notification confirms enable/disable
- Refreshes hourly when enabled

### Pagination
- Use arrow buttons to navigate pages
- Click "First Page" (⏮) to jump to start
- Click "Last Page" (⏭) to jump to end
- Page indicator shows current/total pages

## Performance Considerations

### Database Optimization
- **Indexes** on date columns for fast queries
- **UNIQUE constraints** prevent duplicates
- **Parameterized queries** prevent SQL injection

### UI Optimization
- **Pagination** limits DOM elements
- **Lazy loading** with refreshable components
- **Debouncing** on search input (implicit via on_change)

### Memory Management
- **Page size limit** (20 rows) reduces memory footprint
- **Database connection** closes after each query
- **No in-memory caching** of large datasets

## Error Handling

### Database Errors
```python
try:
    db_manager.insert_mock_data()
except Exception as e:
    logger.error(f"Error initializing mock data: {e}")
```

### Scraping Errors
```python
try:
    scraper.scrape_announcements()
except requests.RequestException as e:
    logger.error(f"Network error: {e}")
    update_scraping_status('announcements', 'failed', str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### UI Errors
- Empty data states show "No data available"
- Loading states prevent multiple simultaneous requests
- Notifications provide user feedback

## Testing

### Manual Testing Checklist
- [ ] Page loads without errors
- [ ] All 4 tabs render correctly
- [ ] Mock data displays in tables
- [ ] Search filters data
- [ ] Date filters work (quick + custom range)
- [ ] Pagination controls function
- [ ] Refresh button works
- [ ] Auto-refresh toggle works
- [ ] Links open in new tabs
- [ ] Responsive on mobile
- [ ] Dark mode compatible

### Unit Test Template
```python
def test_get_announcements():
    db = CorporateAnnouncementsDB(':memory:')
    db.insert_mock_data()
    
    results = db.get_announcements(days=7)
    assert len(results) > 0
    assert 'company_name' in results[0]
    assert 'date' in results[0]

def test_search_filter():
    db = CorporateAnnouncementsDB(':memory:')
    db.insert_mock_data()
    
    results = db.get_announcements(search_term='Reliance')
    assert all('Reliance' in r['company_name'] for r in results)
```

## Troubleshooting

### Issue: No data showing
**Solution:** Check if mock data was inserted
```python
db_manager.insert_mock_data()
```

### Issue: Search not working
**Solution:** Verify SQL LIKE syntax with wildcards
```python
query += f" AND (company_name LIKE '%{search_term}%')"
```

### Issue: Pagination broken
**Solution:** Check page_state['current_page'] bounds
```python
page_state['current_page'] = min(page, total_pages - 1)
```

### Issue: Date filter not clearing
**Solution:** Reset date inputs when changing quick filter
```python
start_date_input.value = ""
end_date_input.value = ""
```

## Future Enhancements

### Phase 1: Live Scraping
- [ ] Implement NSE scraper with BeautifulSoup
- [ ] Add Selenium for JavaScript-heavy pages
- [ ] Handle NSE anti-bot protection
- [ ] Store raw HTML for debugging

### Phase 2: Advanced Features
- [ ] Export to CSV/Excel
- [ ] Email notifications for specific companies
- [ ] Favorite companies watchlist
- [ ] Advanced filters (sector, market cap)

### Phase 3: Analytics
- [ ] Announcement frequency charts
- [ ] Company comparison view
- [ ] Sentiment analysis on subjects
- [ ] Timeline visualization

### Phase 4: Integration
- [ ] Link to holdings in portfolio
- [ ] Alert system integration
- [ ] Strategy builder integration
- [ ] Mobile app version

## Maintenance

### Database Cleanup
```sql
-- Remove old records (older than 1 year)
DELETE FROM nse_announcements 
WHERE announcement_date < date('now', '-1 year');

-- Vacuum to reclaim space
VACUUM;
```

### Log Monitoring
```python
# Check scraping status
SELECT * FROM scraping_status ORDER BY last_scraped DESC;

# Check record counts
SELECT COUNT(*) FROM nse_announcements;
SELECT COUNT(*) FROM nse_financial_results;
SELECT COUNT(*) FROM nse_events;
SELECT COUNT(*) FROM nse_board_meetings;
```

## License & Credits
- **NSE Data:** © National Stock Exchange of India Ltd.
- **Framework:** NiceGUI (https://nicegui.io)
- **Icons:** Material Icons

## Contact & Support
For issues or enhancements, refer to the main project documentation.
