"""Instrument Service - Manage instrument data and lookups"""

from typing import List, Dict, Any, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher
from services.database_service import db


class InstrumentService(UpstoxFetcher):
    """
    Handles instrument data fetching and database operations.
    Replaces etl/upstox_instruments_fetcher.py
    """
    
    def fetch_all_instruments(self) -> List[Dict[str, Any]]:
        """Fetch complete instrument list from Upstox API"""
        response = self.fetch("/instruments/all")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch instruments")
        return response.get("data", [])
    
    def fetch_instruments_by_exchange(self, exchange: str) -> List[Dict[str, Any]]:
        """Fetch instruments for specific exchange (NSE, BSE, MCX)"""
        response = self.fetch(f"/instruments/{exchange}")
        if not self.validate_response(response):
            raise ValueError(f"Failed to fetch {exchange} instruments")
        return response.get("data", [])
    
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
    
    def search_instruments(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search instruments by symbol or name.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching instruments
        """
        sql = """
            SELECT instrument_key, exchange, trading_symbol, name, instrument_type
            FROM instruments
            WHERE trading_symbol LIKE ? OR name LIKE ?
            ORDER BY trading_symbol
            LIMIT ?
        """
        
        pattern = f"%{query.upper()}%"
        rows = db.execute(sql, (pattern, pattern, limit))
        
        return [
            {
                "instrument_key": row[0],
                "exchange": row[1],
                "trading_symbol": row[2],
                "name": row[3],
                "instrument_type": row[4]
            }
            for row in rows
        ]
    
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
    
    def sync_instruments(self) -> Dict[str, int]:
        """
        Sync all instruments from API to database.
        
        Returns:
            Dict with counts per exchange
        """
        exchanges = ["NSE", "BSE", "MCX"]
        counts = {}
        
        for exchange in exchanges:
            try:
                instruments = self.fetch_instruments_by_exchange(exchange)
                count = self.save_to_database(instruments)
                counts[exchange] = count
            except Exception as e:
                counts[exchange] = 0
                print(f"Error syncing {exchange}: {e}")
        
        return counts
