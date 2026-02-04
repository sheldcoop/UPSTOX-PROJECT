#!/usr/bin/env python3
"""
Market Information Service
Implements market status, holidays, and timings endpoints

New Endpoints:
- GET /market-status - Market status (open/closed)
- GET /market-holidays - Holiday calendar
- GET /market-timings - Market timings by segment

Features:
  - Real-time market status
  - Holiday calendar
  - Segment-wise timings
  - Cached for performance

Usage:
  from scripts.market_info_service import MarketInfoService

  mis = MarketInfoService()

  # Check if market is open
  status = mis.get_market_status()

  # Get holidays
  holidays = mis.get_market_holidays()

  # Get market timings
  timings = mis.get_market_timings("NSE_EQ")
"""

import logging
import sys
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.auth.manager import AuthManager
from backend.utils.logging.error_handler import with_retry
from backend.data.database.database_pool import get_db_pool
import requests

logger = logging.getLogger(__name__)


class MarketInfoService:
    """
    Market information service for status, holidays, and timings.
    """

    BASE_URL = "https://api.upstox.com/v2"

    # Market info endpoints
    MARKET_STATUS = "/market/status"
    MARKET_HOLIDAYS = "/market/holidays"
    MARKET_TIMINGS = "/market/timings"

    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize Market Info Service.

        Args:
            db_path: Path to SQLite database
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.session = requests.Session()

        self._init_database()
        logger.info("✅ MarketInfoService initialized")

    def _get_headers(self, allow_unauth: bool = False) -> Dict[str, str]:
        """Get authorization headers with valid token"""
        if allow_unauth:
            return {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        token = self.auth_manager.get_valid_token()
        if not token:
            logger.warning("No valid token, using unauthenticated request")
            return {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _init_database(self):
        """Initialize database tables for market info"""
        with self.db_pool.get_connection() as conn:
            # Market status table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_open BOOLEAN,
                    next_open_time DATETIME,
                    next_close_time DATETIME
                )
            """
            )

            # Market holidays table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_holidays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    holiday_name TEXT NOT NULL,
                    exchange TEXT,
                    segment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, exchange, segment)
                )
            """
            )

            # Market timings table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_timings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    open_time TIME NOT NULL,
                    close_time TIME NOT NULL,
                    pre_open_start TIME,
                    pre_open_end TIME,
                    post_close_start TIME,
                    post_close_end TIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(exchange, segment)
                )
            """
            )

            # Create indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_holidays_date 
                ON market_holidays(date)
            """
            )

    @with_retry(max_attempts=3, use_cache=True)
    def get_market_status(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get current market status (open/closed).

        Args:
            exchange: Exchange code (NSE, BSE, etc.)
            segment: Segment (EQ, FO, etc.)

        Returns:
            Market status dictionary
        """
        try:
            headers = self._get_headers(allow_unauth=True)
            url = f"{self.BASE_URL}{self.MARKET_STATUS}"

            params = {}
            if exchange:
                params["exchange"] = exchange
            if segment:
                params["segment"] = segment

            response = self.session.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                status_data = result.get("data", {})

                # Save to database
                self._save_market_status(status_data)

                logger.info("✅ Market status retrieved")
                return status_data

            else:
                logger.warning(f"Market status API returned {response.status_code}")
                # Return cached status
                return self._get_cached_status(exchange, segment)

        except Exception as e:
            logger.error(f"❌ Failed to get market status: {e}", exc_info=True)
            return self._get_cached_status(exchange, segment)

    def is_market_open(
        self,
        exchange: str = "NSE",
        segment: str = "EQ",
    ) -> bool:
        """
        Check if market is currently open.

        Args:
            exchange: Exchange code
            segment: Segment

        Returns:
            True if market is open, False otherwise
        """
        status = self.get_market_status(exchange, segment)

        if not status:
            # Fallback to time-based check
            return self._is_trading_hours()

        return status.get("is_open", False)

    def _is_trading_hours(self) -> bool:
        """Fallback: Check if current time is within trading hours"""
        now = datetime.now().time()

        # NSE regular trading: 9:15 AM - 3:30 PM
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()

        # Check if today is weekend
        if datetime.now().weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        return market_open <= now <= market_close

    @with_retry(max_attempts=3, use_cache=True)
    def get_market_holidays(
        self,
        year: Optional[int] = None,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get market holiday calendar.

        Args:
            year: Year (default: current year)
            exchange: Exchange code (NSE, BSE, etc.)

        Returns:
            List of holiday dictionaries
        """
        try:
            headers = self._get_headers(allow_unauth=True)
            url = f"{self.BASE_URL}{self.MARKET_HOLIDAYS}"

            if year is None:
                year = datetime.now().year

            params = {"year": year}
            if exchange:
                params["exchange"] = exchange

            response = self.session.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                holidays = result.get("data", [])

                # Save to database
                self._save_holidays(holidays, exchange)

                logger.info(f"✅ Retrieved {len(holidays)} holidays")
                return holidays

            else:
                logger.warning(f"Holidays API returned {response.status_code}")
                return self._get_cached_holidays(year, exchange)

        except Exception as e:
            logger.error(f"❌ Failed to get holidays: {e}", exc_info=True)
            return self._get_cached_holidays(year, exchange)

    def is_holiday(self, check_date: Optional[date] = None) -> bool:
        """
        Check if a date is a market holiday.

        Args:
            check_date: Date to check (default: today)

        Returns:
            True if holiday, False otherwise
        """
        if check_date is None:
            check_date = date.today()

        holidays = self.get_market_holidays(year=check_date.year)

        holiday_dates = [
            datetime.strptime(h["date"], "%Y-%m-%d").date()
            for h in holidays
            if "date" in h
        ]

        return check_date in holiday_dates

    @with_retry(max_attempts=3, use_cache=True)
    def get_market_timings(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get market timings by segment.

        Args:
            exchange: Exchange code
            segment: Segment

        Returns:
            Market timings dictionary
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL}{self.MARKET_TIMINGS}"

            params = {}
            if exchange:
                params["exchange"] = exchange
            if segment:
                params["segment"] = segment

            response = self.session.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                timings = result.get("data", {})

                # Save to database
                self._save_timings(timings)

                logger.info("✅ Market timings retrieved")
                return timings

            else:
                logger.warning(f"Timings API returned {response.status_code}")
                return self._get_cached_timings(exchange, segment)

        except Exception as e:
            logger.error(f"❌ Failed to get timings: {e}", exc_info=True)
            return self._get_cached_timings(exchange, segment)

    def _save_market_status(self, status_data: Dict[str, Any]):
        """Save market status to database"""
        try:
            if not status_data:
                return

            with self.db_pool.get_connection() as conn:
                for market in status_data.get("markets", []):
                    conn.execute(
                        """
                        INSERT INTO market_status 
                        (exchange, segment, status, is_open, next_open_time, next_close_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            market.get("exchange"),
                            market.get("segment"),
                            market.get("status"),
                            market.get("is_open", False),
                            market.get("next_open_time"),
                            market.get("next_close_time"),
                        ),
                    )

        except Exception as e:
            logger.error(f"Failed to save market status: {e}")

    def _get_cached_status(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get cached market status"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM market_status 
                    WHERE 1=1
                """
                params = []

                if exchange:
                    query += " AND exchange = ?"
                    params.append(exchange)

                if segment:
                    query += " AND segment = ?"
                    params.append(segment)

                query += " ORDER BY timestamp DESC LIMIT 1"

                cursor.execute(query, params)
                row = cursor.fetchone()

                if row:
                    return {
                        "exchange": row["exchange"],
                        "segment": row["segment"],
                        "status": row["status"],
                        "is_open": bool(row["is_open"]),
                        "timestamp": row["timestamp"],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get cached status: {e}")
            return {}

    def _save_holidays(self, holidays: List[Dict], exchange: Optional[str]):
        """Save holidays to database"""
        try:
            with self.db_pool.get_connection() as conn:
                for holiday in holidays:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO market_holidays 
                        (date, holiday_name, exchange, segment)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            holiday.get("date"),
                            holiday.get("name"),
                            exchange or holiday.get("exchange"),
                            holiday.get("segment"),
                        ),
                    )

        except Exception as e:
            logger.error(f"Failed to save holidays: {e}")

    def _get_cached_holidays(
        self,
        year: int,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get cached holidays"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM market_holidays 
                    WHERE strftime('%Y', date) = ?
                """
                params = [str(year)]

                if exchange:
                    query += " AND exchange = ?"
                    params.append(exchange)

                query += " ORDER BY date"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                holidays = []
                for row in rows:
                    holidays.append(
                        {
                            "date": row["date"],
                            "name": row["holiday_name"],
                            "exchange": row["exchange"],
                            "segment": row["segment"],
                        }
                    )

                return holidays

        except Exception as e:
            logger.error(f"Failed to get cached holidays: {e}")
            return []

    def _save_timings(self, timings: Dict[str, Any]):
        """Save market timings to database"""
        try:
            if not timings:
                return

            with self.db_pool.get_connection() as conn:
                for market in timings.get("markets", []):
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO market_timings 
                        (exchange, segment, open_time, close_time, 
                         pre_open_start, pre_open_end)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            market.get("exchange"),
                            market.get("segment"),
                            market.get("open_time"),
                            market.get("close_time"),
                            market.get("pre_open_start"),
                            market.get("pre_open_end"),
                        ),
                    )

        except Exception as e:
            logger.error(f"Failed to save timings: {e}")

    def _get_cached_timings(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get cached market timings"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM market_timings WHERE 1=1"
                params = []

                if exchange:
                    query += " AND exchange = ?"
                    params.append(exchange)

                if segment:
                    query += " AND segment = ?"
                    params.append(segment)

                cursor.execute(query, params)
                row = cursor.fetchone()

                if row:
                    return {
                        "exchange": row["exchange"],
                        "segment": row["segment"],
                        "open_time": row["open_time"],
                        "close_time": row["close_time"],
                        "pre_open_start": row["pre_open_start"],
                        "pre_open_end": row["pre_open_end"],
                    }

                return {}

        except Exception as e:
            logger.error(f"Failed to get cached timings: {e}")
            return {}


if __name__ == "__main__":
    """Test market info service"""
    logging.basicConfig(level=logging.INFO)

    mis = MarketInfoService()

    # Test market status
    print("\n📊 Getting market status...")
    status = mis.get_market_status()
    print(f"Status: {status}")
    print(f"Is market open? {mis.is_market_open()}")

    # Test holidays
    print("\n📅 Getting market holidays...")
    holidays = mis.get_market_holidays()
    print(f"Found {len(holidays)} holidays")
    print(f"Is today a holiday? {mis.is_holiday()}")

    # Test timings
    print("\n⏰ Getting market timings...")
    timings = mis.get_market_timings()
    print(f"Timings: {timings}")

    print("\n✅ MarketInfoService test complete")
