"""Market Information Service - status, holidays, timings"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import date
import time

from scripts.market_info_service import MarketInfoService


class MarketInformationService:
    """Facade over MarketInfoService for market status and calendar data"""

    def __init__(self, service: Optional[MarketInfoService] = None):
        self._service = service or MarketInfoService()
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl_status = 60
        self._ttl_holidays = 86400
        self._ttl_timings = 86400

    def _cache_get(self, key: str, ttl: int) -> Optional[Any]:
        cached = self._cache.get(key)
        if not cached:
            return None
        timestamp, value = cached
        if (time.time() - timestamp) > ttl:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any):
        self._cache[key] = (time.time(), value)

    def get_status(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        cache_key = f"status:{exchange}:{segment}"
        cached = self._cache_get(cache_key, self._ttl_status)
        if cached is not None:
            return cached
        data = self._service.get_market_status(exchange=exchange, segment=segment)
        self._cache_set(cache_key, data)
        return data

    def get_holidays(
        self,
        year: Optional[int] = None,
        exchange: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cache_key = f"holidays:{year}:{exchange}"
        cached = self._cache_get(cache_key, self._ttl_holidays)
        if cached is not None:
            return cached
        data = self._service.get_market_holidays(year=year, exchange=exchange)
        self._cache_set(cache_key, data)
        return data

    def is_holiday(self, check_date: Optional[date] = None) -> bool:
        return self._service.is_holiday(check_date=check_date)

    def get_timings(
        self,
        exchange: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        cache_key = f"timings:{exchange}:{segment}"
        cached = self._cache_get(cache_key, self._ttl_timings)
        if cached is not None:
            return cached
        data = self._service.get_market_timings(exchange=exchange, segment=segment)
        self._cache_set(cache_key, data)
        return data
