"""Historical Data Service - Candles and historical data"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class HistoricalDataService(UpstoxFetcher):
    """Handles historical data operations"""

    def _parse_candles(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        candles = response.get("data", {}).get("candles", [])
        return [
            {
                "timestamp": c[0],
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5],
            }
            for c in candles
        ]
    
    def get_candles(
        self,
        instrument_key: str,
        interval: str,
        from_date: str,
        to_date: str
    ) -> List[Dict[str, Any]]:
        """Get historical candles (date range)"""
        return self.get_historical_candles(
            instrument_key=instrument_key,
            interval=interval,
            to_date=to_date,
            from_date=from_date,
        )

    def get_historical_candles(
        self,
        instrument_key: str,
        interval: str,
        to_date: str,
        from_date: str,
    ) -> List[Dict[str, Any]]:
        """Get historical candles for a date range"""
        endpoint = f"/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        response = self.fetch(endpoint)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch candles")
        return self._parse_candles(response)
    
    def get_intraday_candles(
        self,
        instrument_key: str,
        interval: str = "1minute",
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get intraday candles"""
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")

        endpoint = f"/historical-candle/{instrument_key}/{interval}/{to_date}"
        response = self.fetch(endpoint)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch intraday candles")
        
        return self._parse_candles(response)
