"""
Corporate Announcements Page
Real-time NSE corporate filings, financial results, events, and board meetings.
"""

from nicegui import ui, run, app
from ..common import Components
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"

# ============================================================================
# Database Manager
# ============================================================================


class CorporateAnnouncementsDB:
    """Database manager for corporate announcements"""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Corporate Announcements Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_announcements (
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
            )
        """
        )

        # Financial Results Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_financial_results (
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
            )
        """
        )

        # Event Calendar Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_events (
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
            )
        """
        )

        # Board Meetings Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nse_board_meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                symbol TEXT,
                meeting_date DATE NOT NULL,
                purpose TEXT,
                category TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_name, meeting_date, purpose)
            )
        """
        )

        # Scraping Status Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT UNIQUE NOT NULL,
                last_scraped TIMESTAMP,
                status TEXT,
                error_message TEXT,
                records_count INTEGER DEFAULT 0
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_announcements_date ON nse_announcements(announcement_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_date ON nse_financial_results(result_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_date ON nse_events(event_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_meetings_date ON nse_board_meetings(meeting_date)"
        )

        conn.commit()
        conn.close()

    def get_announcements(
        self,
        days: int = 7,
        search_term: str = "",
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Fetch corporate announcements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            date_filter = f"announcement_date BETWEEN '{start_date}' AND '{end_date}'"
        else:
            date_filter = f"announcement_date >= date('now', '-{days} days')"

        query = f"""
            SELECT company_name, symbol, subject, announcement_date, category, url
            FROM nse_announcements
            WHERE {date_filter}
        """

        if search_term:
            query += f" AND (company_name LIKE '%{search_term}%' OR subject LIKE '%{search_term}%')"

        query += " ORDER BY announcement_date DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "company_name": row[0],
                "symbol": row[1],
                "subject": row[2],
                "date": row[3],
                "category": row[4],
                "url": row[5],
            }
            for row in rows
        ]

    def get_financial_results(
        self,
        days: int = 7,
        search_term: str = "",
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Fetch financial results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            date_filter = f"result_date BETWEEN '{start_date}' AND '{end_date}'"
        else:
            date_filter = f"result_date >= date('now', '-{days} days')"

        query = f"""
            SELECT company_name, symbol, period, result_date, category, result_type, url
            FROM nse_financial_results
            WHERE {date_filter}
        """

        if search_term:
            query += f" AND (company_name LIKE '%{search_term}%' OR period LIKE '%{search_term}%')"

        query += " ORDER BY result_date DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "company_name": row[0],
                "symbol": row[1],
                "period": row[2],
                "date": row[3],
                "category": row[4],
                "result_type": row[5],
                "url": row[6],
            }
            for row in rows
        ]

    def get_events(
        self,
        days: int = 7,
        search_term: str = "",
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Fetch events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            date_filter = f"event_date BETWEEN '{start_date}' AND '{end_date}'"
        else:
            date_filter = f"event_date >= date('now', '-{days} days')"

        query = f"""
            SELECT company_name, symbol, event_type, event_date, venue, purpose, url
            FROM nse_events
            WHERE {date_filter}
        """

        if search_term:
            query += f" AND (company_name LIKE '%{search_term}%' OR event_type LIKE '%{search_term}%')"

        query += " ORDER BY event_date DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "company_name": row[0],
                "symbol": row[1],
                "event_type": row[2],
                "date": row[3],
                "venue": row[4],
                "purpose": row[5],
                "url": row[6],
            }
            for row in rows
        ]

    def get_board_meetings(
        self,
        days: int = 7,
        search_term: str = "",
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Fetch board meetings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            date_filter = f"meeting_date BETWEEN '{start_date}' AND '{end_date}'"
        else:
            date_filter = f"meeting_date >= date('now', '-{days} days')"

        query = f"""
            SELECT company_name, symbol, meeting_date, purpose, category, url
            FROM nse_board_meetings
            WHERE {date_filter}
        """

        if search_term:
            query += f" AND (company_name LIKE '%{search_term}%' OR purpose LIKE '%{search_term}%')"

        query += " ORDER BY meeting_date DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "company_name": row[0],
                "symbol": row[1],
                "date": row[2],
                "purpose": row[3],
                "category": row[4],
                "url": row[5],
            }
            for row in rows
        ]

    def insert_mock_data(self):
        """Insert mock data for testing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Mock Announcements
        mock_announcements = [
            (
                "Reliance Industries Ltd",
                "RELIANCE",
                "Outcome of Board Meeting - Dividend Declaration",
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "Board Meeting Outcome",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                "The Board has declared an interim dividend of ₹9 per share",
            ),
            (
                "Tata Consultancy Services Ltd",
                "TCS",
                "Press Release - Q3 FY24 Results",
                (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "Financial Results",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                "TCS announces Q3 results with revenue growth of 4.1%",
            ),
            (
                "HDFC Bank Ltd",
                "HDFCBANK",
                "Acquisition of Additional Stake in HDB Financial Services",
                (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "Acquisition",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                "HDFC Bank acquires additional 4.99% stake",
            ),
            (
                "Infosys Ltd",
                "INFY",
                "Intimation of Board Meeting",
                (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
                "Board Meeting",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                "Board meeting scheduled for Q3 results announcement",
            ),
            (
                "ITC Ltd",
                "ITC",
                "Signing of Share Purchase Agreement",
                (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "Agreement",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
                "ITC signs agreement for acquisition of Sproutlife Foods",
            ),
        ]

        for ann in mock_announcements:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO nse_announcements
                    (company_name, symbol, subject, announcement_date, category, url, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    ann,
                )
            except Exception as e:
                logger.error(f"Error inserting announcement: {e}")

        # Mock Financial Results
        mock_results = [
            (
                "Tata Motors Ltd",
                "TATAMOTORS",
                "Q3 FY2024",
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "Quarterly Results",
                "Unaudited",
                "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            ),
            (
                "Wipro Ltd",
                "WIPRO",
                "Q3 FY2024",
                (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "Quarterly Results",
                "Unaudited",
                "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            ),
            (
                "Asian Paints Ltd",
                "ASIANPAINT",
                "Q3 FY2024",
                (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "Quarterly Results",
                "Unaudited",
                "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            ),
            (
                "Maruti Suzuki India Ltd",
                "MARUTI",
                "Annual FY2023",
                (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d"),
                "Annual Results",
                "Audited",
                "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            ),
            (
                "Bharti Airtel Ltd",
                "BHARTIARTL",
                "Q2 FY2024",
                (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "Quarterly Results",
                "Unaudited",
                "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
            ),
        ]

        for result in mock_results:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO nse_financial_results
                    (company_name, symbol, period, result_date, category, result_type, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    result,
                )
            except Exception as e:
                logger.error(f"Error inserting result: {e}")

        # Mock Events
        mock_events = [
            (
                "Larsen & Toubro Ltd",
                "LT",
                "Annual General Meeting",
                (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "Mumbai, India",
                "AGM for FY 2023-24",
                "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            ),
            (
                "Sun Pharmaceutical Industries Ltd",
                "SUNPHARMA",
                "Earnings Call",
                (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                "Virtual",
                "Q3 FY24 Earnings Conference Call",
                "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            ),
            (
                "NTPC Ltd",
                "NTPC",
                "Investor Meet",
                (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
                "New Delhi",
                "Analyst and Investor Meeting",
                "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            ),
            (
                "Power Grid Corporation",
                "POWERGRID",
                "Dividend Payment",
                (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "N/A",
                "Interim Dividend Payment Date",
                "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            ),
            (
                "Adani Enterprises Ltd",
                "ADANIENT",
                "Record Date",
                (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
                "N/A",
                "Record Date for Dividend Eligibility",
                "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
            ),
        ]

        for event in mock_events:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO nse_events
                    (company_name, symbol, event_type, event_date, venue, purpose, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    event,
                )
            except Exception as e:
                logger.error(f"Error inserting event: {e}")

        # Mock Board Meetings
        mock_meetings = [
            (
                "State Bank of India",
                "SBIN",
                (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
                "To consider and approve Q3 FY24 Results",
                "Financial Results",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            ),
            (
                "Coal India Ltd",
                "COALINDIA",
                (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
                "To discuss dividend declaration",
                "Dividend",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            ),
            (
                "Bajaj Finance Ltd",
                "BAJFINANCE",
                (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
                "To approve fund raising plans",
                "Fundraising",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            ),
            (
                "HCL Technologies Ltd",
                "HCLTECH",
                (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "To consider buyback proposal",
                "Buyback",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            ),
            (
                "Axis Bank Ltd",
                "AXISBANK",
                (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d"),
                "To approve quarterly results",
                "Financial Results",
                "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            ),
        ]

        for meeting in mock_meetings:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO nse_board_meetings
                    (company_name, symbol, meeting_date, purpose, category, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    meeting,
                )
            except Exception as e:
                logger.error(f"Error inserting meeting: {e}")

        # Update scraping status
        cursor.execute(
            """
            INSERT OR REPLACE INTO scraping_status
            (data_type, last_scraped, status, records_count)
            VALUES (?, ?, ?, ?)
        """,
            ("announcements", datetime.now().isoformat(), "success", len(mock_announcements)),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO scraping_status
            (data_type, last_scraped, status, records_count)
            VALUES (?, ?, ?, ?)
        """,
            ("financial_results", datetime.now().isoformat(), "success", len(mock_results)),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO scraping_status
            (data_type, last_scraped, status, records_count)
            VALUES (?, ?, ?, ?)
        """,
            ("events", datetime.now().isoformat(), "success", len(mock_events)),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO scraping_status
            (data_type, last_scraped, status, records_count)
            VALUES (?, ?, ?, ?)
        """,
            ("board_meetings", datetime.now().isoformat(), "success", len(mock_meetings)),
        )

        conn.commit()
        conn.close()


# Initialize database
db_manager = CorporateAnnouncementsDB()

# ============================================================================
# NSE Web Scraper (Placeholder for future implementation)
# ============================================================================


class NSEScraper:
    """
    NSE website scraper for corporate announcements.
    
    NOTE: This is a placeholder. Real implementation requires:
    - BeautifulSoup4 for HTML parsing
    - Selenium for dynamic content (NSE uses JavaScript)
    - Proper headers and cookies to avoid blocking
    - Rate limiting and retry logic
    """

    BASE_URLS = {
        "announcements": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
        "financial_results": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
        "event_calendar": "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar",
    }

    def __init__(self):
        self.session = None
        # TODO: Initialize requests session with proper headers

    def scrape_announcements(self, days: int = 7) -> List[Dict]:
        """
        Scrape corporate announcements from NSE.
        
        TODO: Implement actual scraping logic:
        1. Use requests with proper headers (User-Agent, cookies)
        2. Parse HTML with BeautifulSoup
        3. Extract table data
        4. Handle pagination
        5. Store in database
        """
        logger.info(f"Scraping announcements for last {days} days")
        # Placeholder - return empty list for now
        return []

    def scrape_financial_results(self, days: int = 7) -> List[Dict]:
        """Scrape financial results from NSE"""
        logger.info(f"Scraping financial results for last {days} days")
        # Placeholder - return empty list for now
        return []

    def scrape_events(self, days: int = 7) -> List[Dict]:
        """Scrape event calendar from NSE"""
        logger.info(f"Scraping events for last {days} days")
        # Placeholder - return empty list for now
        return []


# ============================================================================
# Background Scheduler (Placeholder)
# ============================================================================


async def schedule_nightly_update():
    """
    Background task to scrape NSE data nightly.
    
    TODO: Implement using APScheduler:
    1. Install: apscheduler
    2. Create BackgroundScheduler instance
    3. Add job for nightly scraping (e.g., 11 PM IST)
    4. Handle errors and retries
    5. Update scraping_status table
    
    Example:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(scrape_all_data, 'cron', hour=23, minute=0)
        scheduler.start()
    """
    logger.info("Nightly update scheduled (placeholder)")
    pass


# ============================================================================
# Page Rendering
# ============================================================================


def render_page(state):
    """Main page renderer"""
    Components.section_header(
        "Corporate Announcements",
        "NSE corporate filings, financial results, events & board meetings",
        "📢",
    )

    # Initialize mock data if empty
    try:
        db_manager.insert_mock_data()
    except Exception as e:
        logger.error(f"Error initializing mock data: {e}")

    # State variables
    page_state = {
        "active_tab": "announcements",
        "search_term": "",
        "days_filter": 7,
        "start_date": None,
        "end_date": None,
        "auto_refresh": False,
        "current_page": 0,
        "page_size": 20,
        "last_updated": datetime.now(),
        "is_loading": False,
    }

    # Control Panel
    with Components.card():
        with ui.row().classes("w-full items-center gap-4 flex-wrap"):
            # Search box
            search_input = (
                ui.input(placeholder="Search companies, subjects...")
                .props("outlined dense")
                .classes("flex-1 min-w-[200px]")
                .on("change", lambda e: update_search(e.value))
            )

            # Days filter
            days_select = (
                ui.select(
                    options=[7, 14, 30, 60, 90],
                    value=7,
                    label="Days",
                )
                .props("outlined dense")
                .classes("w-24")
                .on("change", lambda e: update_days_filter(e.value))
            )

            # Date range
            with ui.row().classes("gap-2"):
                start_date_input = (
                    ui.input(label="Start Date", value="")
                    .props("outlined dense type=date")
                    .classes("w-40")
                )
                end_date_input = (
                    ui.input(label="End Date", value="")
                    .props("outlined dense type=date")
                    .classes("w-40")
                )

            # Refresh button
            refresh_btn = ui.button(icon="refresh", on_click=lambda: manual_refresh()).props(
                "flat dense round"
            )

            # Auto-refresh toggle
            auto_refresh_toggle = ui.switch("Auto-refresh", value=False).on(
                "change", lambda e: toggle_auto_refresh(e.value)
            )

            # Last updated
            last_updated_label = ui.label(
                f"Updated: {page_state['last_updated'].strftime('%I:%M %p')}"
            ).classes("text-slate-400 text-sm")

    # Tabs
    with Components.card().classes("mt-4"):
        with ui.tabs().classes("w-full text-slate-400") as tabs:
            tab_announcements = ui.tab("📢 Announcements", icon="campaign")
            tab_results = ui.tab("📊 Financial Results", icon="assessment")
            tab_events = ui.tab("📅 Event Calendar", icon="event")
            tab_meetings = ui.tab("🏢 Board Meetings", icon="groups")

        # Tab panels container
        with ui.tab_panels(tabs, value=tab_announcements).classes("w-full mt-4"):
            # Announcements Tab
            with ui.tab_panel(tab_announcements):
                announcements_container = ui.column().classes("w-full")

            # Financial Results Tab
            with ui.tab_panel(tab_results):
                results_container = ui.column().classes("w-full")

            # Events Tab
            with ui.tab_panel(tab_events):
                events_container = ui.column().classes("w-full")

            # Board Meetings Tab
            with ui.tab_panel(tab_meetings):
                meetings_container = ui.column().classes("w-full")

    # Event Handlers
    def update_search(value: str):
        page_state["search_term"] = value
        page_state["current_page"] = 0
        load_active_tab()

    def update_days_filter(value: int):
        page_state["days_filter"] = value
        page_state["current_page"] = 0
        start_date_input.value = ""
        end_date_input.value = ""
        page_state["start_date"] = None
        page_state["end_date"] = None
        load_active_tab()

    async def manual_refresh():
        """Manual refresh button handler"""
        refresh_btn.props("loading")
        await asyncio.sleep(0.5)  # Visual feedback
        
        # In real implementation, trigger scraping here
        # scraper = NSEScraper()
        # await run.io_bound(scraper.scrape_announcements)
        
        page_state["last_updated"] = datetime.now()
        last_updated_label.text = f"Updated: {page_state['last_updated'].strftime('%I:%M %p')}"
        load_active_tab()
        refresh_btn.props(remove="loading")

    def toggle_auto_refresh(enabled: bool):
        """Toggle auto-refresh"""
        page_state["auto_refresh"] = enabled
        if enabled:
            ui.notify("Auto-refresh enabled (hourly)", type="positive")
            # TODO: Implement hourly refresh timer
        else:
            ui.notify("Auto-refresh disabled", type="info")

    def load_active_tab():
        """Load data for active tab"""
        active_tab = tabs.value
        
        if active_tab == tab_announcements:
            render_announcements_table()
        elif active_tab == tab_results:
            render_results_table()
        elif active_tab == tab_events:
            render_events_table()
        elif active_tab == tab_meetings:
            render_meetings_table()

    def render_announcements_table():
        """Render announcements table with pagination"""
        announcements_container.clear()
        
        with announcements_container:
            # Get data
            start_date = start_date_input.value if start_date_input.value else None
            end_date = end_date_input.value if end_date_input.value else None
            
            data = db_manager.get_announcements(
                days=page_state["days_filter"],
                search_term=page_state["search_term"],
                start_date=start_date,
                end_date=end_date,
            )

            if not data:
                ui.label("No announcements found for the selected period.").classes(
                    "text-slate-400 italic p-4 text-center"
                )
                return

            # Calculate pagination
            total_items = len(data)
            total_pages = (total_items + page_state["page_size"] - 1) // page_state["page_size"]
            start_idx = page_state["current_page"] * page_state["page_size"]
            end_idx = min(start_idx + page_state["page_size"], total_items)
            page_data = data[start_idx:end_idx]

            # Table
            with ui.element("div").classes("overflow-x-auto"):
                with ui.element("table").classes("w-full text-sm"):
                    # Header
                    with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                        with ui.element("tr"):
                            with ui.element("th").classes("pb-3 text-left pl-4 pr-2 font-semibold"):
                                ui.label("Company")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Symbol")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Subject")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Date")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Category")
                            with ui.element("th").classes("pb-3 text-left pl-2 pr-4 font-semibold"):
                                ui.label("Actions")

                    # Body
                    with ui.element("tbody"):
                        for idx, row in enumerate(page_data):
                            bg_class = "bg-slate-800/30" if idx % 2 == 0 else ""
                            with ui.element("tr").classes(
                                f"{bg_class} hover:bg-slate-700/50 transition-colors"
                            ):
                                with ui.element("td").classes("py-3 pl-4 pr-2 text-white"):
                                    ui.label(row["company_name"]).classes("font-medium")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["symbol"] or "-")
                                with ui.element("td").classes("py-3 px-2 text-slate-300 max-w-md"):
                                    ui.label(row["subject"]).classes("truncate")
                                with ui.element("td").classes("py-3 px-2 text-slate-400"):
                                    ui.label(row["date"])
                                with ui.element("td").classes("py-3 px-2"):
                                    ui.badge(
                                        row["category"] or "General",
                                        color="indigo" if row["category"] else "slate",
                                    ).props("outline")
                                with ui.element("td").classes("py-3 pl-2 pr-4"):
                                    if row["url"]:
                                        ui.link("View", row["url"], new_tab=True).classes(
                                            "text-indigo-400 hover:text-indigo-300"
                                        )

            # Pagination
            render_pagination(total_items, total_pages, page_data)

    def render_results_table():
        """Render financial results table"""
        results_container.clear()
        
        with results_container:
            start_date = start_date_input.value if start_date_input.value else None
            end_date = end_date_input.value if end_date_input.value else None
            
            data = db_manager.get_financial_results(
                days=page_state["days_filter"],
                search_term=page_state["search_term"],
                start_date=start_date,
                end_date=end_date,
            )

            if not data:
                ui.label("No financial results found for the selected period.").classes(
                    "text-slate-400 italic p-4 text-center"
                )
                return

            total_items = len(data)
            total_pages = (total_items + page_state["page_size"] - 1) // page_state["page_size"]
            start_idx = page_state["current_page"] * page_state["page_size"]
            end_idx = min(start_idx + page_state["page_size"], total_items)
            page_data = data[start_idx:end_idx]

            with ui.element("div").classes("overflow-x-auto"):
                with ui.element("table").classes("w-full text-sm"):
                    with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                        with ui.element("tr"):
                            with ui.element("th").classes("pb-3 text-left pl-4 pr-2 font-semibold"):
                                ui.label("Company")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Symbol")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Period")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Date")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Type")
                            with ui.element("th").classes("pb-3 text-left pl-2 pr-4 font-semibold"):
                                ui.label("Actions")

                    with ui.element("tbody"):
                        for idx, row in enumerate(page_data):
                            bg_class = "bg-slate-800/30" if idx % 2 == 0 else ""
                            with ui.element("tr").classes(
                                f"{bg_class} hover:bg-slate-700/50 transition-colors"
                            ):
                                with ui.element("td").classes("py-3 pl-4 pr-2 text-white"):
                                    ui.label(row["company_name"]).classes("font-medium")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["symbol"] or "-")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["period"])
                                with ui.element("td").classes("py-3 px-2 text-slate-400"):
                                    ui.label(row["date"])
                                with ui.element("td").classes("py-3 px-2"):
                                    ui.badge(
                                        row["result_type"] or "N/A",
                                        color="emerald" if row["result_type"] == "Audited" else "amber",
                                    ).props("outline")
                                with ui.element("td").classes("py-3 pl-2 pr-4"):
                                    if row["url"]:
                                        ui.link("View", row["url"], new_tab=True).classes(
                                            "text-indigo-400 hover:text-indigo-300"
                                        )

            render_pagination(total_items, total_pages, page_data)

    def render_events_table():
        """Render events calendar table"""
        events_container.clear()
        
        with events_container:
            start_date = start_date_input.value if start_date_input.value else None
            end_date = end_date_input.value if end_date_input.value else None
            
            data = db_manager.get_events(
                days=page_state["days_filter"],
                search_term=page_state["search_term"],
                start_date=start_date,
                end_date=end_date,
            )

            if not data:
                ui.label("No events found for the selected period.").classes(
                    "text-slate-400 italic p-4 text-center"
                )
                return

            total_items = len(data)
            total_pages = (total_items + page_state["page_size"] - 1) // page_state["page_size"]
            start_idx = page_state["current_page"] * page_state["page_size"]
            end_idx = min(start_idx + page_state["page_size"], total_items)
            page_data = data[start_idx:end_idx]

            with ui.element("div").classes("overflow-x-auto"):
                with ui.element("table").classes("w-full text-sm"):
                    with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                        with ui.element("tr"):
                            with ui.element("th").classes("pb-3 text-left pl-4 pr-2 font-semibold"):
                                ui.label("Company")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Symbol")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Event Type")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Date")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Venue")
                            with ui.element("th").classes("pb-3 text-left pl-2 pr-4 font-semibold"):
                                ui.label("Actions")

                    with ui.element("tbody"):
                        for idx, row in enumerate(page_data):
                            bg_class = "bg-slate-800/30" if idx % 2 == 0 else ""
                            with ui.element("tr").classes(
                                f"{bg_class} hover:bg-slate-700/50 transition-colors"
                            ):
                                with ui.element("td").classes("py-3 pl-4 pr-2 text-white"):
                                    ui.label(row["company_name"]).classes("font-medium")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["symbol"] or "-")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["event_type"])
                                with ui.element("td").classes("py-3 px-2 text-slate-400"):
                                    ui.label(row["date"])
                                with ui.element("td").classes("py-3 px-2 text-slate-400"):
                                    ui.label(row["venue"] or "N/A")
                                with ui.element("td").classes("py-3 pl-2 pr-4"):
                                    if row["url"]:
                                        ui.link("View", row["url"], new_tab=True).classes(
                                            "text-indigo-400 hover:text-indigo-300"
                                        )

            render_pagination(total_items, total_pages, page_data)

    def render_meetings_table():
        """Render board meetings table"""
        meetings_container.clear()
        
        with meetings_container:
            start_date = start_date_input.value if start_date_input.value else None
            end_date = end_date_input.value if end_date_input.value else None
            
            data = db_manager.get_board_meetings(
                days=page_state["days_filter"],
                search_term=page_state["search_term"],
                start_date=start_date,
                end_date=end_date,
            )

            if not data:
                ui.label("No board meetings found for the selected period.").classes(
                    "text-slate-400 italic p-4 text-center"
                )
                return

            total_items = len(data)
            total_pages = (total_items + page_state["page_size"] - 1) // page_state["page_size"]
            start_idx = page_state["current_page"] * page_state["page_size"]
            end_idx = min(start_idx + page_state["page_size"], total_items)
            page_data = data[start_idx:end_idx]

            with ui.element("div").classes("overflow-x-auto"):
                with ui.element("table").classes("w-full text-sm"):
                    with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                        with ui.element("tr"):
                            with ui.element("th").classes("pb-3 text-left pl-4 pr-2 font-semibold"):
                                ui.label("Company")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Symbol")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Meeting Date")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Purpose")
                            with ui.element("th").classes("pb-3 text-left px-2 font-semibold"):
                                ui.label("Category")
                            with ui.element("th").classes("pb-3 text-left pl-2 pr-4 font-semibold"):
                                ui.label("Actions")

                    with ui.element("tbody"):
                        for idx, row in enumerate(page_data):
                            bg_class = "bg-slate-800/30" if idx % 2 == 0 else ""
                            with ui.element("tr").classes(
                                f"{bg_class} hover:bg-slate-700/50 transition-colors"
                            ):
                                with ui.element("td").classes("py-3 pl-4 pr-2 text-white"):
                                    ui.label(row["company_name"]).classes("font-medium")
                                with ui.element("td").classes("py-3 px-2 text-slate-300"):
                                    ui.label(row["symbol"] or "-")
                                with ui.element("td").classes("py-3 px-2 text-slate-400"):
                                    ui.label(row["date"])
                                with ui.element("td").classes("py-3 px-2 text-slate-300 max-w-md"):
                                    ui.label(row["purpose"] or "N/A").classes("truncate")
                                with ui.element("td").classes("py-3 px-2"):
                                    ui.badge(
                                        row["category"] or "General",
                                        color="violet" if row["category"] else "slate",
                                    ).props("outline")
                                with ui.element("td").classes("py-3 pl-2 pr-4"):
                                    if row["url"]:
                                        ui.link("View", row["url"], new_tab=True).classes(
                                            "text-indigo-400 hover:text-indigo-300"
                                        )

            render_pagination(total_items, total_pages, page_data)

    def render_pagination(total_items: int, total_pages: int, page_data: List):
        """Render pagination controls"""
        if total_pages <= 1:
            return

        with ui.row().classes("w-full justify-between items-center mt-4 pt-4 border-t border-slate-700"):
            # Info
            start_idx = page_state["current_page"] * page_state["page_size"] + 1
            end_idx = start_idx + len(page_data) - 1
            ui.label(f"Showing {start_idx}-{end_idx} of {total_items}").classes(
                "text-slate-400 text-sm"
            )

            # Page controls
            with ui.row().classes("gap-2"):
                ui.button(
                    icon="first_page",
                    on_click=lambda: go_to_page(0),
                ).props(
                    "flat dense round"
                ).set_enabled(page_state["current_page"] > 0)

                ui.button(
                    icon="chevron_left",
                    on_click=lambda: go_to_page(page_state["current_page"] - 1),
                ).props(
                    "flat dense round"
                ).set_enabled(page_state["current_page"] > 0)

                ui.label(f"Page {page_state['current_page'] + 1} of {total_pages}").classes(
                    "text-slate-300 px-2"
                )

                ui.button(
                    icon="chevron_right",
                    on_click=lambda: go_to_page(page_state["current_page"] + 1),
                ).props(
                    "flat dense round"
                ).set_enabled(page_state["current_page"] < total_pages - 1)

                ui.button(
                    icon="last_page",
                    on_click=lambda: go_to_page(total_pages - 1),
                ).props(
                    "flat dense round"
                ).set_enabled(page_state["current_page"] < total_pages - 1)

    def go_to_page(page: int):
        """Navigate to a specific page"""
        page_state["current_page"] = page
        load_active_tab()

    # Tab change handler
    tabs.on("update:model-value", lambda: on_tab_change())

    def on_tab_change():
        """Handle tab changes"""
        page_state["current_page"] = 0
        load_active_tab()

    # Initial load
    load_active_tab()
