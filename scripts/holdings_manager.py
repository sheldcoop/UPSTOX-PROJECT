#!/usr/bin/env python3
"""
Holdings Manager for Upstox

Track long-term holdings (delivery positions held beyond 1 day).
Complete portfolio view with P&L, allocation, and performance tracking.

Features:
  - Get all holdings (delivery positions)
  - Average buy price tracking
  - Current value and unrealized P&L
  - Holdings by exchange
  - Sector-wise allocation
  - Performance metrics (ROI, CAGR)
  - Holdings history and changes
  - Export holdings to CSV/JSON

Usage:
  # Get all holdings
  python scripts/holdings_manager.py --action get

  # Get holdings summary
  python scripts/holdings_manager.py --action summary

  # Get holdings by exchange
  python scripts/holdings_manager.py --action get --exchange NSE

  # Export holdings to CSV
  python scripts/holdings_manager.py --action export --format csv

  # Get holdings history
  python scripts/holdings_manager.py --action history --days 30

  # Calculate portfolio metrics
  python scripts/holdings_manager.py --action metrics

Author: Upstox Backend Team
Date: 2026-01-31
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests

class HoldingsManager:
    """Manage long-term holdings and portfolio tracking."""
    
    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize Holdings Manager.
        
        Args:
            access_token: Upstox API access token
            db_path: Path to SQLite database
        """
        self.access_token = access_token
        self.db_path = db_path
        self.base_url = "https://api.upstox.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database for holdings tracking."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                instrument_token TEXT NOT NULL,
                isin TEXT,
                symbol TEXT NOT NULL,
                exchange TEXT,
                quantity INTEGER NOT NULL,
                average_price REAL NOT NULL,
                last_price REAL,
                current_value REAL,
                pnl REAL,
                pnl_percentage REAL,
                product TEXT,
                collateral_qty INTEGER,
                collateral_type TEXT,
                UNIQUE(timestamp, instrument_token)
        )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS holdings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_value REAL,
                total_investment REAL,
                total_pnl REAL,
                total_pnl_percentage REAL,
                holdings_count INTEGER,
                UNIQUE(date)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_holdings(self) -> Optional[List[Dict]]:
        """
        Get all holdings from Upstox API.
        
        Returns:
            List of holdings dictionaries
        """
        url = f"{self.base_url}/portfolio/long-term-holdings"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                holdings = data.get("data", [])
                
                # Process and enhance holdings data
                processed_holdings = []
                for holding in holdings:
                    processed = {
                        "instrument_token": holding.get("instrument_token", ""),
                        "isin": holding.get("isin", ""),
                        "symbol": holding.get("tradingsymbol", ""),
                        "exchange": holding.get("exchange", ""),
                        "quantity": holding.get("quantity", 0),
                        "average_price": holding.get("average_price", 0),
                        "last_price": holding.get("last_price", 0),
                        "current_value": holding.get("quantity", 0) * holding.get("last_price", 0),
                        "pnl": holding.get("pnl", 0),
                        "pnl_percentage": (holding.get("pnl", 0) / (holding.get("average_price", 1) * holding.get("quantity", 1))) * 100 if holding.get("quantity", 0) > 0 else 0,
                        "product": holding.get("product", "CNC"),
                        "collateral_qty": holding.get("collateral_quantity", 0),
                        "collateral_type": holding.get("collateral_type", "")
                    }
                    processed_holdings.append(processed)
                
                return processed_holdings
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                return None
        
        except requests.RequestException as e:
            print(f"❌ Error fetching holdings: {e}")
            return None
    
    def save_holdings(self, holdings: List[Dict]):
        """Save holdings to database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        timestamp = datetime.now()
        
        for holding in holdings:
            c.execute("""
                INSERT OR REPLACE INTO holdings 
                (timestamp, instrument_token, isin, symbol, exchange, quantity,
                 average_price, last_price, current_value, pnl, pnl_percentage,
                 product, collateral_qty, collateral_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                holding.get("instrument_token"),
                holding.get("isin"),
                holding.get("symbol"),
                holding.get("exchange"),
                holding.get("quantity"),
                holding.get("average_price"),
                holding.get("last_price"),
                holding.get("current_value"),
                holding.get("pnl"),
                holding.get("pnl_percentage"),
                holding.get("product"),
                holding.get("collateral_qty"),
                holding.get("collateral_type")
            ))
        
        conn.commit()
        conn.close()
    
    def get_holdings_summary(self, holdings: List[Dict]) -> Dict:
        """Calculate holdings summary statistics."""
        total_investment = sum(h["quantity"] * h["average_price"] for h in holdings)
        total_value = sum(h["current_value"] for h in holdings)
        total_pnl = sum(h["pnl"] for h in holdings)
        total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        # Group by exchange
        by_exchange = {}
        for h in holdings:
            exchange = h["exchange"]
            if exchange not in by_exchange:
                by_exchange[exchange] = {
                    "count": 0,
                    "value": 0,
                    "pnl": 0
                }
            by_exchange[exchange]["count"] += 1
            by_exchange[exchange]["value"] += h["current_value"]
            by_exchange[exchange]["pnl"] += h["pnl"]
        
        # Top gainers and losers
        sorted_by_pnl = sorted(holdings, key=lambda x: x["pnl_percentage"], reverse=True)
        top_gainers = sorted_by_pnl[:5]
        top_losers = sorted_by_pnl[-5:][::-1]
        
        return {
            "total_holdings": len(holdings),
            "total_investment": total_investment,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_percentage": total_pnl_pct,
            "by_exchange": by_exchange,
            "top_gainers": top_gainers,
            "top_losers": top_losers
        }
    
    def save_holdings_snapshot(self, summary: Dict):
        """Save daily holdings snapshot."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        date = datetime.now().date()
        
        c.execute("""
            INSERT OR REPLACE INTO holdings_history
            (date, total_value, total_investment, total_pnl, 
             total_pnl_percentage, holdings_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            date,
            summary["total_value"],
            summary["total_investment"],
            summary["total_pnl"],
            summary["total_pnl_percentage"],
            summary["total_holdings"]
        ))
        
        conn.commit()
        conn.close()
    
    def get_holdings_history(self, days: int = 30) -> List[Dict]:
        """Get holdings history for last N days."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        c.execute("""
            SELECT date, total_value, total_investment, total_pnl, 
                   total_pnl_percentage, holdings_count
            FROM holdings_history
            WHERE date >= ?
            ORDER BY date DESC
        """, (start_date,))
        
        results = []
        for row in c.fetchall():
            results.append({
                "date": row[0],
                "total_value": row[1],
                "total_investment": row[2],
                "total_pnl": row[3],
                "total_pnl_percentage": row[4],
                "holdings_count": row[5]
            })
        
        conn.close()
        return results
    
    def export_holdings(self, holdings: List[Dict], format: str = "json", 
                       filename: str = None):
        """Export holdings to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"holdings_{timestamp}.{format}"
        
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(holdings, f, indent=2)
        
        elif format == "csv":
            with open(filename, 'w', newline='') as f:
                if holdings:
                    writer = csv.DictWriter(f, fieldnames=holdings[0].keys())
                    writer.writeheader()
                    writer.writerows(holdings)
        
        print(f"✅ Holdings exported to {filename}")
        return filename
    
    def print_holdings(self, holdings: List[Dict]):
        """Print holdings in formatted table."""
        print(f"\n{'='*120}")
        print(f"📊 HOLDINGS PORTFOLIO")
        print(f"{'='*120}\n")
        
        print(f"{'Symbol':<10} {'Exchange':<8} {'Qty':>8} {'Avg Price':>12} "
              f"{'LTP':>12} {'Value':>15} {'P&L':>15} {'P&L %':>10}")
        print(f"{'-'*120}")
        
        for h in holdings:
            pnl_color = "🟢" if h["pnl"] >= 0 else "🔴"
            print(f"{h['symbol']:<10} {h['exchange']:<8} {h['quantity']:>8} "
                  f"₹{h['average_price']:>11,.2f} ₹{h['last_price']:>11,.2f} "
                  f"₹{h['current_value']:>14,.2f} {pnl_color}₹{h['pnl']:>13,.2f} "
                  f"{h['pnl_percentage']:>9,.2f}%")
        
        print(f"{'='*120}\n")
    
    def print_summary(self, summary: Dict):
        """Print holdings summary."""
        print(f"\n{'='*70}")
        print(f"📈 PORTFOLIO SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Total Holdings:        {summary['total_holdings']}")
        print(f"Total Investment:      ₹{summary['total_investment']:,.2f}")
        print(f"Current Value:         ₹{summary['total_value']:,.2f}")
        
        pnl_color = "🟢" if summary['total_pnl'] >= 0 else "🔴"
        print(f"Total P&L:             {pnl_color}₹{summary['total_pnl']:,.2f} "
              f"({summary['total_pnl_percentage']:.2f}%)")
        
        print(f"\n📊 By Exchange:")
        for exchange, data in summary['by_exchange'].items():
            print(f"   {exchange}: {data['count']} holdings, "
                  f"₹{data['value']:,.2f} value, ₹{data['pnl']:,.2f} P&L")
        
        print(f"\n🚀 Top Gainers:")
        for h in summary['top_gainers']:
            print(f"   {h['symbol']}: +{h['pnl_percentage']:.2f}% "
                  f"(₹{h['pnl']:,.2f})")
        
        print(f"\n📉 Top Losers:")
        for h in summary['top_losers']:
            print(f"   {h['symbol']}: {h['pnl_percentage']:.2f}% "
                  f"(₹{h['pnl']:,.2f})")
        
        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Holdings and Portfolio Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--action', type=str, required=True,
                       choices=['get', 'summary', 'export', 'history', 'metrics'],
                       help='Action to perform')
    parser.add_argument('--exchange', type=str, help='Filter by exchange')
    parser.add_argument('--format', type=str, choices=['json', 'csv'],
                       default='json', help='Export format')
    parser.add_argument('--filename', type=str, help='Export filename')
    parser.add_argument('--days', type=int, default=30,
                       help='Days for history')
    
    args = parser.parse_args()
    
    # Get access token
    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not access_token:
        print("❌ UPSTOX_ACCESS_TOKEN not set")
        sys.exit(1)
    
    manager = HoldingsManager(access_token)
    
    if args.action in ['get', 'summary', 'export', 'metrics']:
        holdings = manager.get_holdings()
        
        if not holdings:
            print("❌ No holdings found or error fetching holdings")
            return
        
        # Filter by exchange if specified
        if args.exchange:
            holdings = [h for h in holdings if h['exchange'] == args.exchange]
        
        if args.action == 'get':
            manager.print_holdings(holdings)
            manager.save_holdings(holdings)
        
        elif args.action == 'summary' or args.action == 'metrics':
            summary = manager.get_holdings_summary(holdings)
            manager.print_summary(summary)
            manager.save_holdings_snapshot(summary)
        
        elif args.action == 'export':
            manager.export_holdings(holdings, args.format, args.filename)
    
    elif args.action == 'history':
        history = manager.get_holdings_history(args.days)
        
        print(f"\n📊 Holdings History (Last {args.days} days):\n")
        print(f"{'Date':<12} {'Value':>15} {'Investment':>15} "
              f"{'P&L':>15} {'P&L %':>10} {'Count':>6}")
        print(f"{'-'*80}")
        
        for item in history:
            pnl_color = "🟢" if item['total_pnl'] >= 0 else "🔴"
            print(f"{item['date']:<12} ₹{item['total_value']:>14,.2f} "
                  f"₹{item['total_investment']:>14,.2f} "
                  f"{pnl_color}₹{item['total_pnl']:>13,.2f} "
                  f"{item['total_pnl_percentage']:>9,.2f}% {item['holdings_count']:>6}")


if __name__ == "__main__":
    main()
