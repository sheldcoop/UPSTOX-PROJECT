"""Portfolio Service - Holdings and positions"""

from typing import Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class PortfolioService(UpstoxFetcher):
    """Handles portfolio operations"""
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get all holdings"""
        response = self.fetch("/portfolio/long-term-holdings")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch holdings")
        return response.get("data", [])
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        response = self.fetch("/portfolio/short-term-positions")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch positions")
        return response.get("data", {})
    
    def get_pnl(self) -> Dict[str, float]:
        """Calculate total P&L from positions"""
        positions = self.get_positions()
        total_pnl = 0.0
        realized_pnl = 0.0
        unrealized_pnl = 0.0
        
        for pos in positions:
            pnl = pos.get("pnl", 0.0)
            total_pnl += pnl
            if pos.get("quantity", 0) == 0:
                realized_pnl += pnl
            else:
                unrealized_pnl += pnl
        
        return {
            "total": total_pnl,
            "realized": realized_pnl,
            "unrealized": unrealized_pnl
        }
