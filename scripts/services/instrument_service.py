"""Instrument Service - Manage instrument data and lookups"""

from typing import List, Dict, Any, Optional, Tuple
import csv
import io
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher
from scripts.config_loader import get_api_base_url
from services.database_service import db


class InstrumentService(UpstoxFetcher):
    """
    Handles instrument data fetching and database operations.
    Replaces etl/upstox_instruments_fetcher.py
    """

    def __init__(self, base_url: Optional[str] = None, cache_ttl: float = 86400):
        super().__init__(base_url=base_url or get_api_base_url())
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._option_chain_cache: Dict[str, Tuple[float, Any]] = {}
        self._option_chain_ttl = 300

    def _cache_get(self, key: str) -> Optional[Any]:
        cached = self._cache.get(key)
        if not cached:
            return None
        timestamp, value = cached
        if (time.time() - timestamp) > self._cache_ttl:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any):
        self._cache[key] = (time.time(), value)
    
    def fetch_instruments_csv(self, date: Optional[str] = None) -> str:
        """Fetch instruments CSV from Upstox API"""
        cache_key = f"instruments_csv:{date or 'latest'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        endpoint = "/market/instruments" if not date else f"/market/instruments/{date}"
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "text/csv",
            "Content-Type": "text/csv",
        }

        response = self.session.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch instruments CSV: {response.status_code}")

        csv_text = response.text
        self._cache_set(cache_key, csv_text)
        return csv_text

    def parse_instruments_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parse instruments CSV to list of dicts"""
        reader = csv.DictReader(io.StringIO(csv_text))
        return [row for row in reader]

    def fetch_instruments(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch and parse instruments list"""
        cache_key = f"instruments_parsed:{date or 'latest'}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        csv_text = self.fetch_instruments_csv(date=date)
        instruments = self.parse_instruments_csv(csv_text)
        self._cache_set(cache_key, instruments)
        return instruments

    def get_option_chain(self, instrument_key: str, expiry_date: str) -> Dict[str, Any]:
        """Get option chain for instrument and expiry"""
        cache_key = f"option_chain:{instrument_key}:{expiry_date}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        option_cached = self._option_chain_cache.get(cache_key)
        if option_cached:
            timestamp, value = option_cached
            if (time.time() - timestamp) <= self._option_chain_ttl:
                return value
            self._option_chain_cache.pop(cache_key, None)

        params = {"instrument_key": instrument_key, "expiry_date": expiry_date}
        response = self.fetch("/option/chain", params=params)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch option chain")
        data = response.get("data", {})
        self._option_chain_cache[cache_key] = (time.time(), data)
        return data
    
    def save_to_database(self, instruments: List[Dict[str, Any]]) -> int:
        """
        Save instruments to database.
        
        Returns:
            Number of instruments saved
        """
        if not instruments:
            return 0
        
        # Prepare data for batch insert
        data_list = []
        for inst in instruments:
            data_list.append((
                inst.get("instrument_key"),
                inst.get("exchange"),
                inst.get("trading_symbol"),
                inst.get("name"),
                inst.get("instrument_type"),
                inst.get("segment"),
                inst.get("lot_size", 1),
                inst.get("tick_size", 0.05),
            ))
        
        # Batch insert
        query = """
            INSERT OR REPLACE INTO instruments 
            (instrument_key, exchange, trading_symbol, name, instrument_type, segment, lot_size, tick_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        return db.execute_many(query, data_list)
    
    def search_instruments(
        self,
        query: str,
        limit: int = 50,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search instruments by symbol or name.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching instruments
        """
        sql = """
            SELECT instrument_key, exchange, trading_symbol, name, instrument_type, segment
            FROM instruments
            WHERE (trading_symbol LIKE ? OR name LIKE ?)
        """

        params: List[Any] = []
        pattern = f"%{query.upper()}%"
        params.extend([pattern, pattern])

        if exchange:
            sql += " AND exchange = ?"
            params.append(exchange)
        if segment:
            sql += " AND segment = ?"
            params.append(segment)

        sql += " ORDER BY trading_symbol LIMIT ?"
        params.append(limit)

        rows = db.execute(sql, tuple(params))
        
        return [
            {
                "instrument_key": row[0],
                "exchange": row[1],
                "trading_symbol": row[2],
                "name": row[3],
                "instrument_type": row[4],
                "segment": row[5],
            }
            for row in rows
        ]

    def search_instrument(
        self,
        query: str,
        limit: int = 50,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self.search_instruments(
            query=query,
            limit=limit,
            exchange=exchange,
            segment=segment,
        )
    
    def get_instrument_by_key(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Get instrument details by key"""
        sql = "SELECT * FROM instruments WHERE instrument_key = ?"
        row = db.execute_one(sql, (instrument_key,))
        
        if not row:
            return None
        
        return {
            "instrument_key": row[0],
            "exchange": row[1],
            "trading_symbol": row[2],
            "name": row[3],
            "instrument_type": row[4],
            "segment": row[5],
            "lot_size": row[6],
            "tick_size": row[7]
        }
    
    def sync_instruments(self, date: Optional[str] = None) -> Dict[str, int]:
        """
        Sync all instruments from API to database.

        Returns:
            Dict with total count
        """
        try:
            instruments = self.fetch_instruments(date=date)
            count = self.save_to_database(instruments)
            return {"total": count}
        except Exception as e:
            print(f"Error syncing instruments: {e}")
            return {"total": 0}
