"""News Service - Fetch and manage news data"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import BaseFetcher
from services.database_service import db


class NewsService(BaseFetcher):
    """
    Handles news fetching and storage.
    Replaces part of news_alerts_manager.py
    """
    
    def __init__(self):
        super().__init__(base_url="https://api.upstox.com/v2")
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate API response"""
        return "status" in response and response["status"] == "success"
    
    def fetch_latest_news(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch latest market news.
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Max news items
            
        Returns:
            List of news items
        """
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        
        response = self.fetch("/news/latest", params=params)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch news")
        
        return response.get("data", [])
    
    def save_news(self, news_items: List[Dict[str, Any]]) -> int:
        """Save news items to database"""
        if not news_items:
            return 0
        
        data_list = []
        for item in news_items:
            data_list.append((
                item.get("id"),
                item.get("title"),
                item.get("description"),
                item.get("url"),
                item.get("source"),
                item.get("published_at"),
                item.get("symbol"),
            ))
        
        query = """
            INSERT OR IGNORE INTO news
            (news_id, title, description, url, source, published_at, symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        return db.execute_many(query, data_list)
    
    def get_news_by_symbol(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get news for symbol from last N days"""
        sql = """
            SELECT news_id, title, description, url, source, published_at
            FROM news
            WHERE symbol = ? AND published_at >= datetime('now', '-' || ? || ' days')
            ORDER BY published_at DESC
        """
        
        rows = db.execute(sql, (symbol, days))
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "url": row[3],
                "source": row[4],
                "published_at": row[5]
            }
            for row in rows
        ]
