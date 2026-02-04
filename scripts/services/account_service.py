"""Account Service - User profile, funds, margins"""

from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class AccountService(UpstoxFetcher):
    """Handles all account-related operations"""
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        response = self.fetch("/user/profile")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch profile")
        return response.get("data", {})
    
    def get_funds(self) -> Dict[str, Any]:
        """Get funds and margin information"""
        response = self.fetch("/user/get-funds-and-margin")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch funds")
        return response.get("data", {})
    
    def get_balance(self) -> float:
        """Get available balance"""
        funds = self.get_funds()
        equity = funds.get("equity", {})
        return equity.get("available_margin", 0.0)
    
    def get_margins(self, segment: str = "equity") -> Dict[str, Any]:
        """Get margin details for segment"""
        funds = self.get_funds()
        return funds.get(segment, {})
