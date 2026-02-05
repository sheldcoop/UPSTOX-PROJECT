"""Alert Service - Manage price alerts and notifications"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db


class AlertService:
    """
    Handles price alerts and notifications.
    Replaces part of news_alerts_manager.py
    """
    
    def create_alert(
        self,
        symbol: str,
        alert_type: str,
        target_price: float,
        condition: str = "above",
        user_id: str = "default"
    ) -> int:
        """
        Create price alert.
        
        Args:
            symbol: Instrument symbol
            alert_type: Type (price, volume, etc.)
            target_price: Target price
            condition: 'above' or 'below'
            user_id: User identifier
            
        Returns:
            Alert ID
        """
        data = {
            "symbol": symbol,
            "alert_type": alert_type,
            "target_price": target_price,
            "condition": condition,
            "user_id": user_id,
            "is_active": 1,
            "created_at": datetime.now().isoformat()
        }
        
        return db.insert("alerts", data)
    
    def get_active_alerts(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all active alerts for user"""
        sql = """
            SELECT alert_id, symbol, alert_type, target_price, condition, created_at
            FROM alerts
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """
        
        rows = db.execute(sql, (user_id,))
        return [
            {
                "id": row[0],
                "symbol": row[1],
                "type": row[2],
                "target_price": row[3],
                "condition": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def check_alerts(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """
        Check if any alerts are triggered.
        
        Args:
            symbol: Symbol to check
            current_price: Current market price
            
        Returns:
            List of triggered alerts
        """
        sql = """
            SELECT alert_id, symbol, target_price, condition
            FROM alerts
            WHERE symbol = ? AND is_active = 1
        """
        
        rows = db.execute(sql, (symbol,))
        triggered = []
        
        for row in rows:
            alert_id, symbol, target_price, condition = row
            
            if condition == "above" and current_price >= target_price:
                triggered.append({"id": alert_id, "symbol": symbol, "price": current_price})
            elif condition == "below" and current_price <= target_price:
                triggered.append({"id": alert_id, "symbol": symbol, "price": current_price})
        
        return triggered
    
    def deactivate_alert(self, alert_id: int) -> bool:
        """Deactivate alert"""
        count = db.update("alerts", {"is_active": 0}, "alert_id = ?", (alert_id,))
        return count > 0
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete alert"""
        count = db.delete("alerts", "alert_id = ?", (alert_id,))
        return count > 0
