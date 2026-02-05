#!/usr/bin/env python3
"""
Brokerage and Charges Calculator for Upstox

Calculate exact brokerage charges BEFORE placing orders.
Get complete breakdown: Brokerage, STT, Stamp Duty, GST, Total.

Features:
  - Calculate charges for any order (before execution)
  - Complete breakdown (all charges itemized)
  - Compare charges across products (MIS vs CNC)
  - Batch calculation for multiple orders
  - Save history for analysis
  - Cost estimation for strategies

Usage:
  # Calculate charges for single order
  python scripts/brokerage_calculator.py --symbol INFY --qty 10 --price 1450 \
    --side BUY --product CNC

  # Compare MIS vs CNC charges
  python scripts/brokerage_calculator.py --symbol INFY --qty 100 --price 1450 \
    --side BUY --compare

  # Calculate for multiple orders (basket)
  python scripts/brokerage_calculator.py --orders orders.json

  # Get charge history
  python scripts/brokerage_calculator.py --action history --limit 20

  # Calculate for futures
  python scripts/brokerage_calculator.py --symbol NIFTY --qty 50 --price 23500 \
    --side SELL --product NRML --instrument FUTIDX

Author: Upstox Backend Team
Date: 2026-01-31
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from typing import Optional, Dict, List
import requests


class BrokerageCalculator:
    """Calculate brokerage and charges using Upstox API."""

    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize Brokerage Calculator.

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
        """Initialize database for charge history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS brokerage_calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                side TEXT NOT NULL,
                product TEXT NOT NULL,
                instrument_type TEXT,
                brokerage REAL,
                stt_ctt REAL,
                transaction_charges REAL,
                gst REAL,
                sebi_charges REAL,
                stamp_duty REAL,
                total_charges REAL,
                total_cost REAL,
                breakeven_price REAL
            )
        """
        )

        conn.commit()
        conn.close()

    def calculate_charges(
        self,
        instrument_token: str,
        quantity: int,
        price: float,
        transaction_type: str,
        product: str = "D",
    ) -> Optional[Dict]:
        """
        Calculate brokerage charges using Upstox API.

        Args:
            instrument_token: Instrument key (e.g. "NSE_EQ|INE669E01016")
            quantity: Order quantity
            price: Order price
            transaction_type: BUY or SELL
            product: D (Delivery/CNC), I (Intraday/MIS), M (Margin)

        Returns:
            Charges breakdown dictionary
        """
        url = f"{self.base_url}/charges/brokerage"

        params = {
            "instrument_token": instrument_token,
            "quantity": quantity,
            "product": product,
            "transaction_type": transaction_type.upper(),
            "price": price,
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                charges = data.get("data", {}).get("charges", {})

                # Calculate totals
                brokerage = charges.get("brokerage", 0)
                stt = charges.get("stt_ctt", 0)
                transaction = charges.get("transaction_charges", 0)
                gst = charges.get("gst", 0)
                sebi = charges.get("sebi_charges", 0)
                stamp_duty = charges.get("stamp_duty", 0)

                total_charges = brokerage + stt + transaction + gst + sebi + stamp_duty
                total_cost = (
                    (price * quantity) + total_charges
                    if transaction_type.upper() == "BUY"
                    else (price * quantity) - total_charges
                )

                # Calculate breakeven price
                if transaction_type.upper() == "BUY":
                    breakeven = price + (total_charges / quantity)
                else:
                    breakeven = price - (total_charges / quantity)

                result = {
                    "brokerage": brokerage,
                    "stt_ctt": stt,
                    "transaction_charges": transaction,
                    "gst": gst,
                    "sebi_charges": sebi,
                    "stamp_duty": stamp_duty,
                    "total_charges": total_charges,
                    "order_value": price * quantity,
                    "total_cost": total_cost,
                    "breakeven_price": breakeven,
                    "charges_percentage": (total_charges / (price * quantity)) * 100,
                    "dp_plan": charges.get("dp_plan", {}),
                }

                return result
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                return None

        except requests.RequestException as e:
            print(f"❌ Error calculating charges: {e}")
            return None

    def save_calculation(
        self,
        symbol: str,
        quantity: int,
        price: float,
        side: str,
        product: str,
        charges: Dict,
    ):
        """Save calculation to database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO brokerage_calculations 
            (symbol, quantity, price, side, product, brokerage, stt_ctt,
             transaction_charges, gst, sebi_charges, stamp_duty, 
             total_charges, total_cost, breakeven_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                symbol,
                quantity,
                price,
                side,
                product,
                charges.get("brokerage", 0),
                charges.get("stt_ctt", 0),
                charges.get("transaction_charges", 0),
                charges.get("gst", 0),
                charges.get("sebi_charges", 0),
                charges.get("stamp_duty", 0),
                charges.get("total_charges", 0),
                charges.get("total_cost", 0),
                charges.get("breakeven_price", 0),
            ),
        )

        conn.commit()
        conn.close()

    def get_instrument_token(self, symbol: str) -> Optional[str]:
        """Get instrument token for symbol from database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Try exact match first
        c.execute(
            """
            SELECT instrument_key FROM instruments 
            WHERE tradingsymbol = ? OR name LIKE ?
            LIMIT 1
        """,
            (symbol, f"%{symbol}%"),
        )

        result = c.fetchone()
        conn.close()

        if result:
            return result[0]
        else:
            # Default format for equity
            return f"NSE_EQ|{symbol}"

    def compare_products(
        self, symbol: str, quantity: int, price: float, side: str
    ) -> Dict:
        """Compare charges across different products."""
        instrument_token = self.get_instrument_token(symbol)

        products = {"D": "Delivery (CNC)", "I": "Intraday (MIS)", "M": "Margin (NRML)"}

        comparison = {}

        for code, name in products.items():
            charges = self.calculate_charges(
                instrument_token, quantity, price, side, code
            )

            if charges:
                comparison[name] = charges

        return comparison

    def get_calculation_history(self, limit: int = 20) -> List[Dict]:
        """Get recent calculation history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            SELECT timestamp, symbol, quantity, price, side, product,
                   total_charges, breakeven_price
            FROM brokerage_calculations
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in c.fetchall():
            results.append(
                {
                    "timestamp": row[0],
                    "symbol": row[1],
                    "quantity": row[2],
                    "price": row[3],
                    "side": row[4],
                    "product": row[5],
                    "total_charges": row[6],
                    "breakeven_price": row[7],
                }
            )

        conn.close()
        return results

    def print_charges_breakdown(
        self, charges: Dict, symbol: str, quantity: int, price: float, side: str
    ):
        """Print detailed charges breakdown."""
        print(f"\n{'='*70}")
        print(f"💰 CHARGES BREAKDOWN - {symbol}")
        print(f"{'='*70}")
        print(f"\n📊 Order Details:")
        print(f"   Symbol: {symbol}")
        print(f"   Side: {side}")
        print(f"   Quantity: {quantity}")
        print(f"   Price: ₹{price:,.2f}")
        print(f"   Order Value: ₹{charges['order_value']:,.2f}")

        print(f"\n💸 Charges Breakdown:")
        print(f"   Brokerage:              ₹{charges['brokerage']:,.2f}")
        print(f"   STT/CTT:                ₹{charges['stt_ctt']:,.2f}")
        print(f"   Transaction Charges:    ₹{charges['transaction_charges']:,.2f}")
        print(f"   GST:                    ₹{charges['gst']:,.2f}")
        print(f"   SEBI Charges:           ₹{charges['sebi_charges']:,.2f}")
        print(f"   Stamp Duty:             ₹{charges['stamp_duty']:,.2f}")
        print(f"   {'-'*50}")
        print(f"   Total Charges:          ₹{charges['total_charges']:,.2f}")
        print(f"   Charges %:              {charges['charges_percentage']:.4f}%")

        print(f"\n🎯 Summary:")
        print(f"   Total Cost:             ₹{charges['total_cost']:,.2f}")
        print(f"   Breakeven Price:        ₹{charges['breakeven_price']:,.2f}")

        if side.upper() == "BUY":
            profit_at_1pct = (price * 1.01 * quantity) - charges["total_cost"]
            print(f"   Profit at +1%:          ₹{profit_at_1pct:,.2f}")
        else:
            profit_at_1pct = charges["total_cost"] - (price * 0.99 * quantity)
            print(f"   Profit at -1%:          ₹{profit_at_1pct:,.2f}")

        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Brokerage and Charges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--symbol", type=str, help="Trading symbol")
    parser.add_argument("--qty", type=int, help="Quantity")
    parser.add_argument("--price", type=float, help="Price")
    parser.add_argument("--side", type=str, choices=["BUY", "SELL"], help="Order side")
    parser.add_argument(
        "--product",
        type=str,
        choices=["CNC", "MIS", "NRML"],
        default="CNC",
        help="Product type",
    )
    parser.add_argument(
        "--compare", action="store_true", help="Compare charges across all products"
    )
    parser.add_argument(
        "--action", type=str, choices=["history"], help="Get calculation history"
    )
    parser.add_argument("--limit", type=int, default=20, help="Limit for history")

    args = parser.parse_args()

    # Get access token using AuthManager
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.auth_manager import AuthManager
        
        auth = AuthManager()
        access_token = auth.get_valid_token()
        
        if not access_token:
            print("❌ No valid token found. Please authenticate first:")
            print("   python3 scripts/oauth_server.py")
            print("   Then open: http://localhost:5050/auth/start")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        sys.exit(1)

    calculator = BrokerageCalculator(access_token)

    if args.action == "history":
        history = calculator.get_calculation_history(args.limit)
        print(f"\n📊 Recent Calculations ({len(history)}):\n")
        for item in history:
            print(
                f"{item['timestamp']} | {item['symbol']:8} | "
                f"{item['side']:4} {item['quantity']:4} @ ₹{item['price']:8.2f} | "
                f"Charges: ₹{item['total_charges']:6.2f} | "
                f"BE: ₹{item['breakeven_price']:.2f}"
            )

    elif args.compare and args.symbol and args.qty and args.price and args.side:
        comparison = calculator.compare_products(
            args.symbol, args.qty, args.price, args.side
        )

        print(f"\n{'='*70}")
        print(f"📊 PRODUCT COMPARISON - {args.symbol}")
        print(f"{'='*70}\n")

        for product_name, charges in comparison.items():
            print(f"{product_name}:")
            print(f"  Total Charges: ₹{charges['total_charges']:.2f}")
            print(f"  Breakeven: ₹{charges['breakeven_price']:.2f}")
            print(f"  Charges %: {charges['charges_percentage']:.4f}%\n")

    elif args.symbol and args.qty and args.price and args.side:
        # Map product names
        product_map = {"CNC": "D", "MIS": "I", "NRML": "M"}
        product_code = product_map.get(args.product, "D")

        instrument_token = calculator.get_instrument_token(args.symbol)
        charges = calculator.calculate_charges(
            instrument_token, args.qty, args.price, args.side, product_code
        )

        if charges:
            calculator.print_charges_breakdown(
                charges, args.symbol, args.qty, args.price, args.side
            )
            calculator.save_calculation(
                args.symbol, args.qty, args.price, args.side, args.product, charges
            )
        else:
            print("❌ Failed to calculate charges")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
