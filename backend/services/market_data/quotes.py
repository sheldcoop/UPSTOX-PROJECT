#!/usr/bin/env python3
"""
Market Quote Fetcher v3 for Upstox
Enhanced quote fetching with v3 API and intelligent caching

New v3 Endpoint:
- POST /market-quote/quotes/v3/ - Batch quote fetching with better performance

Features:
  - v3 API with improved performance
  - Multi-level caching (memory + database)
  - Batch optimization
  - Rate limit handling
  - Quote staleness detection

Usage:
  from scripts.market_quote_v3 import MarketQuoteV3

  mq = MarketQuoteV3()

  # Single quote
  quote = mq.get_quote("NSE_EQ|INE009A01021")

  # Batch quotes
  quotes = mq.get_batch_quotes(["NSE_EQ|INE009A01021", "NSE_EQ|INE467B01029"])
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


class MarketQuoteV3(OptionalAuthHeadersMixin):
    """
    Market quote fetcher using v3 API with intelligent caching.
    """

    BASE_URL = "https://api.upstox.com/v2"

    # v3 endpoint
    QUOTES_V3 = "/market-quote/quotes/v3/"

    # v2 fallback
    QUOTES_V2 = "/market-quote/quotes"

    # Cache settings
    QUOTE_CACHE_TTL_SECONDS = 5  # 5 seconds for real-time quotes
    BATCH_SIZE = 500  # Maximum instruments per request

    def __init__(self, db_path: str = "market_data.db", use_v3: bool = True):
        """
        Initialize Market Quote V3.

        Args:
            db_path: Path to SQLite database
            use_v3: Use v3 endpoints (default: True)
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.session = requests.Session()
        self.use_v3 = use_v3

        # Multi-level cache
        self._memory_cache: Dict[str, tuple] = {}  # (quote, timestamp)

        self._init_database()
        logger.info(f"✅ MarketQuoteV3 initialized (v3_enabled: {use_v3})")

    def _init_database(self):
        """Initialize database for quote caching"""
        with self.db_pool.get_connection() as conn:
            # Quote cache table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quote_cache_v3 (
                    instrument_key TEXT PRIMARY KEY,
                    ltp REAL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    oi INTEGER,
                    bid_price REAL,
                    ask_price REAL,
                    bid_qty INTEGER,
                    ask_qty INTEGER,
                    upper_circuit REAL,
                    lower_circuit REAL,
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Quote request metrics
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quote_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_type TEXT,
                    instruments_count INTEGER,
                    cache_hit_count INTEGER,
                    api_call_count INTEGER,
                    total_time_ms INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    @with_retry(max_attempts=3, use_cache=False)
    def get_quote(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """
        Get quote for a single instrument.

        Args:
            instrument_key: Instrument key (e.g., 'NSE_EQ|INE009A01021')

        Returns:
            Quote dictionary or None
        """
        # Check memory cache
        cached = self._get_from_memory_cache(instrument_key)
        if cached:
            return cached

        # Fetch from API
        quotes = self.get_batch_quotes([instrument_key])
        return quotes.get(instrument_key)

    @with_retry(max_attempts=3, use_cache=False)
    def get_batch_quotes(
        self,
        instrument_keys: List[str],
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple instruments efficiently.

        Args:
            instrument_keys: List of instrument keys
            use_cache: Whether to use cache (default: True)

        Returns:
            Dictionary mapping instrument_key -> quote
        """
        start_time = time.time()

        # Remove duplicates
        unique_keys = list(set(instrument_keys))

        results = {}
        cache_hits = 0
        api_calls = 0

        # Check cache first
        if use_cache:
            uncached_keys = []

            for key in unique_keys:
                cached = self._get_from_memory_cache(key)
                if cached:
                    results[key] = cached
                    cache_hits += 1
                else:
                    uncached_keys.append(key)

            # If all cached, return
            if not uncached_keys:
                logger.info(f"✅ All {len(unique_keys)} quotes from cache")
                return results

            logger.info(f"📊 Cache: {cache_hits} hits, {len(uncached_keys)} misses")
        else:
            uncached_keys = unique_keys

        # Fetch uncached keys in batches
        for i in range(0, len(uncached_keys), self.BATCH_SIZE):
            batch = uncached_keys[i : i + self.BATCH_SIZE]
            batch_results = self._fetch_batch(batch)
            results.update(batch_results)
            api_calls += 1

        # Save metrics
        elapsed_ms = int((time.time() - start_time) * 1000)
        self._save_metrics("batch", len(unique_keys), cache_hits, api_calls, elapsed_ms)

        logger.info(
            f"✅ Fetched {len(results)}/{len(unique_keys)} quotes in {elapsed_ms}ms"
        )

        return results

    def _fetch_batch(self, instrument_keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch a batch of quotes from API"""
        try:
            headers = self._get_headers()

            # Try v3 endpoint
            if self.use_v3:
                try:
                    url = f"{self.BASE_URL}{self.QUOTES_V3}"

                    # v3 uses POST with JSON body
                    payload = {"instrument_keys": instrument_keys}

                    response = self.session.post(
                        url, json=payload, headers=headers, timeout=30
                    )

                    if response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded")

                    if response.status_code == 200:
                        result = response.json()
                        quotes_data = result.get("data", {})

                        # Cache the results
                        for key, quote in quotes_data.items():
                            self._save_to_cache(key, quote)

                        logger.info(f"✅ Fetched {len(quotes_data)} quotes (v3)")
                        return quotes_data

                    else:
                        logger.warning(f"v3 API returned {response.status_code}")

                except Exception as v3_error:
                    logger.warning(f"v3 fetch failed, trying v2: {v3_error}")

            # v2 fallback
            logger.info("Using v2 API fallback")
            url_v2 = f"{self.BASE_URL}{self.QUOTES_V2}"

            # v2 uses GET with comma-separated keys
            params = {"instrument_key": ",".join(instrument_keys)}

            response = self.session.get(
                url_v2, headers=headers, params=params, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                quotes_data = result.get("data", {})

                # Cache the results
                for key, quote in quotes_data.items():
                    self._save_to_cache(key, quote)

                logger.info(f"✅ Fetched {len(quotes_data)} quotes (v2)")
                return quotes_data

            else:
                logger.error(f"v2 API failed: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Batch fetch failed: {e}", exc_info=True)
            return {}

    def _get_from_memory_cache(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Get quote from memory cache"""
        if instrument_key in self._memory_cache:
            quote, cached_time = self._memory_cache[instrument_key]

            # Check staleness
            age = (datetime.now() - cached_time).total_seconds()
            if age < self.QUOTE_CACHE_TTL_SECONDS:
                logger.debug(f"Memory cache hit: {instrument_key} (age: {age:.1f}s)")
                return quote
            else:
                # Stale, remove
                del self._memory_cache[instrument_key]

        # Try database cache (longer TTL)
        return self._get_from_db_cache(instrument_key)

    def _get_from_db_cache(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Get quote from database cache"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT *
                    FROM quote_cache_v3
                    WHERE instrument_key = ?
                      AND cached_at >= datetime('now', '-60 seconds')
                    LIMIT 1
                """,
                    (instrument_key,),
                )

                row = cursor.fetchone()

                if row:
                    quote = {
                        "instrument_key": row["instrument_key"],
                        "ltp": row["ltp"],
                        "open": row["open"],
                        "high": row["high"],
                        "low": row["low"],
                        "close": row["close"],
                        "volume": row["volume"],
                        "oi": row["oi"],
                        "bid_price": row["bid_price"],
                        "ask_price": row["ask_price"],
                        "bid_qty": row["bid_qty"],
                        "ask_qty": row["ask_qty"],
                        "upper_circuit": row["upper_circuit"],
                        "lower_circuit": row["lower_circuit"],
                    }

                    logger.debug(f"DB cache hit: {instrument_key}")
                    return quote

                return None

        except Exception as e:
            logger.error(f"DB cache error: {e}")
            return None

    def _save_to_cache(self, instrument_key: str, quote: Dict[str, Any]):
        """Save quote to both memory and database cache"""
        # Memory cache
        self._memory_cache[instrument_key] = (quote, datetime.now())

        # Database cache
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO quote_cache_v3
                    (instrument_key, ltp, open, high, low, close, volume, oi,
                     bid_price, ask_price, bid_qty, ask_qty, upper_circuit, lower_circuit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        instrument_key,
                        quote.get("ltp"),
                        quote.get("ohlc", {}).get("open"),
                        quote.get("ohlc", {}).get("high"),
                        quote.get("ohlc", {}).get("low"),
                        quote.get("ohlc", {}).get("close"),
                        quote.get("volume"),
                        quote.get("oi"),
                        quote.get("depth", {}).get("buy", [{}])[0].get("price"),
                        quote.get("depth", {}).get("sell", [{}])[0].get("price"),
                        quote.get("depth", {}).get("buy", [{}])[0].get("quantity"),
                        quote.get("depth", {}).get("sell", [{}])[0].get("quantity"),
                        quote.get("upper_circuit_limit"),
                        quote.get("lower_circuit_limit"),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to cache quote: {e}")

    def _save_metrics(
        self,
        request_type: str,
        instruments_count: int,
        cache_hits: int,
        api_calls: int,
        total_time_ms: int,
    ):
        """Save quote request metrics"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO quote_metrics 
                    (request_type, instruments_count, cache_hit_count, 
                     api_call_count, total_time_ms)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        request_type,
                        instruments_count,
                        cache_hits,
                        api_calls,
                        total_time_ms,
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_entries = len(self._memory_cache)

        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                # DB cache count
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM quote_cache_v3
                    WHERE cached_at >= datetime('now', '-1 hour')
                """
                )
                db_entries = cursor.fetchone()[0]

                # Recent metrics
                cursor.execute(
                    """
                    SELECT 
                        AVG(cache_hit_count * 100.0 / instruments_count) as avg_hit_rate,
                        AVG(total_time_ms) as avg_time_ms,
                        SUM(api_call_count) as total_api_calls
                    FROM quote_metrics
                    WHERE timestamp >= datetime('now', '-1 hour')
                """
                )

                row = cursor.fetchone()

                return {
                    "memory_cache_entries": memory_entries,
                    "db_cache_entries": db_entries,
                    "avg_cache_hit_rate_pct": round(row[0] or 0, 2),
                    "avg_fetch_time_ms": round(row[1] or 0, 2),
                    "total_api_calls_1h": row[2] or 0,
                }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"memory_cache_entries": memory_entries}

    def clear_cache(self):
        """Clear all caches"""
        self._memory_cache.clear()

        try:
            with self.db_pool.get_connection() as conn:
                conn.execute("DELETE FROM quote_cache_v3")

        except Exception as e:
            logger.error(f"Failed to clear DB cache: {e}")

        logger.info("✅ Cache cleared")


if __name__ == "__main__":
    """Test market quote v3"""
    logging.basicConfig(level=logging.INFO)

    mq = MarketQuoteV3()

    # Test single quote
    print("\n📊 Getting single quote...")
    quote = mq.get_quote("NSE_EQ|INE009A01021")
    if quote:
        print(f"✅ Quote: LTP={quote.get('ltp')}")

    # Test batch quotes
    print("\n📊 Getting batch quotes...")
    quotes = mq.get_batch_quotes(["NSE_EQ|INE009A01021", "NSE_EQ|INE467B01029"])
    print(f"✅ Fetched {len(quotes)} quotes")

    # Cache stats
    print(f"\n📈 Cache stats: {mq.get_cache_stats()}")

    print("\n✅ MarketQuoteV3 test complete")
