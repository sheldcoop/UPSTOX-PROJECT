"""Order Service - Place, modify, cancel orders"""

from typing import Dict, Any, List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class OrderService(UpstoxFetcher):
    """Handles order operations"""
    
    def place_order(
        self,
        instrument_key: str,
        quantity: int,
        transaction_type: str,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        product: str = "D"
    ) -> Dict[str, Any]:
        """Place a new order"""
        data = {
            "quantity": quantity,
            "product": product,
            "validity": "DAY",
            "price": price or 0,
            "tag": "string",
            "instrument_token": instrument_key,
            "order_type": order_type,
            "transaction_type": transaction_type,
            "disclosed_quantity": 0,
            "trigger_price": 0,
            "is_amo": False
        }
        
        response = self.fetch("/order/place", method="POST", data=data)
        if not self.validate_response(response):
            raise ValueError("Failed to place order")
        return response.get("data", {})
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        response = self.fetch(f"/order/cancel/{order_id}", method="DELETE")
        if not self.validate_response(response):
            raise ValueError("Failed to cancel order")
        return response.get("data", {})
    
    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify an existing order"""
        response = self.fetch(f"/order/modify/{order_id}", method="PUT", data=kwargs)
        if not self.validate_response(response):
            raise ValueError("Failed to modify order")
        return response.get("data", {})
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of specific order"""
        response = self.fetch(f"/order/status/{order_id}")
        if not self.validate_response(response):
            raise ValueError("Failed to get order status")
        return response.get("data", {})
    
    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        response = self.fetch("/order/retrieve-all")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch order history")
        return response.get("data", [])
