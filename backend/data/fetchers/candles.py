#!/usr/bin/env python3
"""
Candle Fetcher v3 for Upstox
Migrated to v3 candle endpoints with performance improvements

New v3 Endpoint:
- GET /market-quote/candles/v3/{instrument_key} - Enhanced candle data

Features:
  - v3 API with better performance
  - Backward compatibility with v2
  - Quote caching layer
  - Batch processing optimization

Usage:
  from backend.data.fetchers.candles import CandleFetcherV3

  cf = CandleFetcherV3()

  # Fetch candles (v3)
  candles = cf.fetch_candles("NSE_EQ|INE009A01021", "day", "2024-01-01", "2024-12-31")
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.auth.manager import AuthManager
from backend.utils.logging.error_handler import with_retry, RateLimitError
from backend.data.database.database_pool import get_db_pool
from backend.utils.auth.mixins import OptionalAuthHeadersMixin
import requests

logger = logging.getLogger(__name__)


class CandleFetcherV3(OptionalAuthHeadersMixin):
    """
    Candle fetcher using v3 API with caching and performance optimizations.
    """

    BASE_URL = "https://api.upstox.com/v2"

    # v3 endpoint
    CANDLES_V3 = "/market-quote/candles/v3"

    # v2 fallback
    CANDLES_V2 = "/historical-candle"

    # Cache settings
    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(self, db_path: str = "market_data.db", use_v3: bool = True):
        """
        Initialize Candle Fetcher V3.

        Args:
            db_path: Path to SQLite database
            use_v3: Use v3 endpoints (default: True)
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.session = requests.Session()
        self.use_v3 = use_v3

        # In-memory cache
        self._cache: Dict[str, Any] = {}

        self._init_database()
        logger.info(f"✅ CandleFetcherV3 initialized (v3_enabled: {use_v3})")

    def _init_database(self):
        """Initialize database for candle caching"""
        with self.db_pool.get_connection() as conn:
            # Candle cache table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candle_cache_v3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_key TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    oi INTEGER,
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(instrument_key, interval, timestamp)
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_candle_cache_v3 
                ON candle_cache_v3(instrument_key, interval, timestamp)
            """
            )

    @with_retry(max_attempts=3, use_cache=True)
    def fetch_candles(
        self,
        instrument_key: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candles using v3 API.

        Args:
            instrument_key: Instrument key (e.g., 'NSE_EQ|INE009A01021')
            interval: Candle interval ('1minute', '30minute', 'day', 'week', 'month')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)

        Returns:
            List of candle dictionaries
        """
        try:
            # Check cache first
            cache_key = f"{instrument_key}:{interval}:{from_date}:{to_date}"
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info(f"✅ Candles retrieved from cache: {instrument_key}")
                return cached

            headers = self._get_headers()

            # Try v3 endpoint
            if self.use_v3:
                try:
                    url = f"{self.BASE_URL}{self.CANDLES_V3}/{instrument_key}"
                    params = {
                        "interval": interval,
                        "from_date": from_date,
                        "to_date": to_date,
                    }

                    response = self.session.get(
                        url, headers=headers, params=params, timeout=30
                    )

                    if response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded")

                    if response.status_code == 200:
                        result = response.json()
                        candles = result.get("data", {}).get("candles", [])

                        # Process and cache
                        processed = self._process_candles(candles)
                        self._save_to_cache(
                            cache_key, processed, instrument_key, interval
                        )

                        logger.info(
                            f"✅ Fetched {len(processed)} candles (v3): {instrument_key}"
                        )
                        return processed

                    else:
                        logger.warning(f"v3 API returned {response.status_code}")

                except Exception as v3_error:
                    logger.warning(f"v3 fetch failed, trying v2: {v3_error}")

            # v2 fallback
            logger.info("Using v2 API fallback")
            # v2 format: /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
            url_v2 = f"{self.BASE_URL}{self.CANDLES_V2}/{instrument_key}/{interval}/{to_date}/{from_date}"

            response = self.session.get(url_v2, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                candles = result.get("data", {}).get("candles", [])

                processed = self._process_candles(candles)
                self._save_to_cache(cache_key, processed, instrument_key, interval)

                logger.info(
                    f"✅ Fetched {len(processed)} candles (v2): {instrument_key}"
                )
                return processed

            else:
                logger.error(f"v2 API failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Candle fetch failed: {e}", exc_info=True)
            # Try to get from database cache
            return self._get_from_db_cache(instrument_key, interval, from_date, to_date)

    def fetch_latest_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest N candles.

        Args:
            instrument_key: Instrument key
            interval: Candle interval
            count: Number of candles to fetch

        Returns:
            List of candle dictionaries
        """
        # Calculate date range
        to_date = datetime.now().strftime("%Y-%m-%d")

        # Calculate from_date based on interval
        if interval in ["1minute", "5minute", "30minute"]:
            days_back = max(5, count // 375)  # ~375 minutes per day
        elif interval == "day":
            days_back = count + 10  # Extra buffer for holidays
        elif interval == "week":
            days_back = count * 7 + 14
        else:  # month
            days_back = count * 30 + 30

        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        candles = self.fetch_candles(instrument_key, interval, from_date, to_date)

        # Return latest N candles
        return candles[-count:] if len(candles) > count else candles

    def _process_candles(self, candles: List[Any]) -> List[Dict[str, Any]]:
        """Process raw candle data into standardized format"""
        processed = []

        for candle in candles:
            if isinstance(candle, list):
                # Array format: [timestamp, open, high, low, close, volume, oi]
                if len(candle) >= 5:
                    processed.append(
                        {
                            "timestamp": candle[0],
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": int(candle[5]) if len(candle) > 5 else 0,
                            "oi": int(candle[6]) if len(candle) > 6 else 0,
                        }
                    )

            elif isinstance(candle, dict):
                # Dictionary format
                processed.append(candle)

        return processed

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get candles from in-memory cache"""
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]

            # Check if cache is still valid
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.CACHE_TTL_SECONDS:
                logger.debug(f"Cache hit: {cache_key} (age: {age:.1f}s)")
                return cached_data
            else:
                # Expired
                del self._cache[cache_key]

        return None

    def _save_to_cache(
        self,
        cache_key: str,
        candles: List[Dict[str, Any]],
        instrument_key: str,
        interval: str,
    ):
        """Save candles to both in-memory and database cache"""
        # In-memory cache
        self._cache[cache_key] = (candles, datetime.now())

        # Database cache
        try:
            with self.db_pool.get_connection() as conn:
                for candle in candles:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO candle_cache_v3 
                        (instrument_key, interval, timestamp, open, high, low, close, volume, oi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            instrument_key,
                            interval,
                            candle.get("timestamp"),
                            candle.get("open"),
                            candle.get("high"),
                            candle.get("low"),
                            candle.get("close"),
                            candle.get("volume"),
                            candle.get("oi"),
                        ),
                    )

        except Exception as e:
            logger.error(f"Failed to cache candles to database: {e}")

    def _get_from_db_cache(
        self,
        instrument_key: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> List[Dict[str, Any]]:
        """Get candles from database cache"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT timestamp, open, high, low, close, volume, oi
                    FROM candle_cache_v3
                    WHERE instrument_key = ? 
                      AND interval = ?
                      AND timestamp BETWEEN ? AND ?
                      AND cached_at >= datetime('now', '-24 hours')
                    ORDER BY timestamp
                """,
                    (instrument_key, interval, from_date, to_date),
                )

                rows = cursor.fetchall()

                candles = []
                for row in rows:
                    candles.append(
                        {
                            "timestamp": row[0],
                            "open": row[1],
                            "high": row[2],
                            "low": row[3],
                            "close": row[4],
                            "volume": row[5],
                            "oi": row[6],
                        }
                    )

                if candles:
                    logger.info(f"✅ Retrieved {len(candles)} candles from DB cache")

                return candles

        except Exception as e:
            logger.error(f"Failed to get candles from DB cache: {e}")
            return []

    def clear_cache(self):
        """Clear in-memory cache"""
        self._cache.clear()
        logger.info("✅ Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        total_candles = sum(len(data[0]) for data in self._cache.values())

        return {
            "cache_entries": total_entries,
            "total_candles_cached": total_candles,
            "cache_ttl_seconds": self.CACHE_TTL_SECONDS,
        }


if __name__ == "__main__":
    """Test candle fetcher v3"""
    logging.basicConfig(level=logging.INFO)

    cf = CandleFetcherV3()

    # Test fetching candles
    print("\n📊 Fetching candles...")
    candles = cf.fetch_latest_candles("NSE_EQ|INE009A01021", "day", 10)

    if candles:
        print(f"✅ Fetched {len(candles)} candles")
        print(f"Latest: {candles[-1]}")
    else:
        print("❌ No candles fetched")

    # Cache stats
    print(f"\n📈 Cache stats: {cf.get_cache_stats()}")

    print("\n✅ CandleFetcherV3 test complete")
