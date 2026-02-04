"""
Base Fetcher Class - Foundation for all API data fetchers
Eliminates code duplication and provides consistent error handling
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from abc import ABC, abstractmethod

from scripts.auth_helper import auth

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """
    Abstract base class for all data fetchers.
    Provides common functionality: auth, retries, rate limiting, error handling.
    """
    
    def __init__(self, base_url: str = "https://api.upstox.com/v2"):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.session = requests.Session()
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return self.auth.get_headers()
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def fetch(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Generic fetch method with retry logic and error handling.
        
        Args:
            endpoint: API endpoint (e.g., "/user/profile")
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body (for POST/PUT)
            retries: Number of retry attempts
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dict
            
        Raises:
            Exception: If all retries fail
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=data,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    # Token expired, try refresh
                    logger.warning("Token expired, refreshing...")
                    self.auth._auth_manager.get_valid_token(force_refresh=True)
                    continue
                elif response.status_code == 429:
                    # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    if attempt == retries - 1:
                        raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{retries}")
                if attempt == retries - 1:
                    raise
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}/{retries}")
                if attempt == retries - 1:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == retries - 1:
                    raise
        
        raise Exception(f"Failed after {retries} attempts")
    
    def fetch_paginated(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page_param: str = "page",
        limit_param: str = "limit",
        max_pages: int = 100
    ) -> List[Dict]:
        """
        Fetch paginated data automatically.
        
        Args:
            endpoint: API endpoint
            params: Base query parameters
            page_param: Name of page parameter
            limit_param: Name of limit parameter
            max_pages: Maximum pages to fetch
            
        Returns:
            List of all results combined
        """
        all_results = []
        params = params or {}
        
        for page in range(1, max_pages + 1):
            params[page_param] = page
            response = self.fetch(endpoint, params=params)
            
            # Extract data (adjust based on API response structure)
            data = response.get("data", [])
            if not data:
                break
            
            all_results.extend(data)
            
            # Check if more pages exist
            if len(data) < params.get(limit_param, 100):
                break
        
        return all_results
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate API response structure.
        Must be implemented by subclasses.
        """
        pass
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on exit"""
        self.session.close()


class UpstoxFetcher(BaseFetcher):
    """Upstox-specific fetcher with validation"""
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate Upstox API response"""
        return "status" in response and response["status"] == "success"


class DatabaseFetcher(ABC):
    """Base class for database operations with context manager"""
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        """Open database connection"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection and commit/rollback"""
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query safely"""
        return self.cursor.execute(query, params)
    
    def fetchall(self):
        """Fetch all results"""
        return self.cursor.fetchall()
    
    def fetchone(self):
        """Fetch one result"""
        return self.cursor.fetchone()
