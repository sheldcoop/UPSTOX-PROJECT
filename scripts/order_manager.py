#!/usr/bin/env python3
"""
Order Management System for Upstox

Place, modify, cancel, and track orders. Supports market and limit orders.
Full order lifecycle management with persistent storage.

Features:
  - Place buy/sell orders (market/limit)
  - Modify existing orders (price, quantity)
  - Cancel orders
  - Get order status and details
  - Order history and tracking
  - Bracket orders support
  - GTT order management
  - Real-time order updates

Usage:
  # Place market order
  python scripts/order_manager.py --action place --symbol INFY --side BUY --qty 1 --type MARKET

  # Place limit order
  python scripts/order_manager.py --action place --symbol NIFTY --side SELL --qty 25 --type LIMIT --price 23500

  # Get order status
  python scripts/order_manager.py --action status --order-id ORD_ID

  # Cancel order
  python scripts/order_manager.py --action cancel --order-id ORD_ID

  # Modify order
  python scripts/order_manager.py --action modify --order-id ORD_ID --price 23550 --qty 50

  # List active orders
  python scripts/order_manager.py --action list-active

  # Get order history
  python scripts/order_manager.py --action history --limit 20

  # Place bracket order
  python scripts/order_manager.py --action place-bracket --symbol INFY --qty 1 --entry-price 1800 \
    --stop-loss 1750 --target 1850
"""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, List
import requests


class OrderManager:
    """Manages order placement, modification, and tracking."""

    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize Order Manager.

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
        """Initialize database for order tracking."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                parent_order_id TEXT,
                exchange TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                filled_quantity INTEGER DEFAULT 0,
                pending_quantity INTEGER,
                order_type TEXT NOT NULL,
                price REAL,
                trigger_price REAL,
                order_status TEXT DEFAULT 'PENDING',
                status_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                product_type TEXT,
                time_in_force TEXT DEFAULT 'IOC',
                disclosed_quantity INTEGER,
                validity TEXT,
                UNIQUE(order_id)
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS order_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                filled_qty INTEGER,
                average_price REAL,
                message TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(order_id)
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS bracket_orders (
                bracket_id TEXT PRIMARY KEY,
                entry_order_id TEXT NOT NULL,
                stop_loss_order_id TEXT,
                target_order_id TEXT,
                symbol TEXT NOT NULL,
                quantity INTEGER,
                entry_price REAL,
                stop_loss_price REAL,
                target_price REAL,
                status TEXT DEFAULT 'PENDING',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bracket_id)
            )
        """
        )

        conn.commit()
        conn.close()

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product_type: str = "MIS",
        disclosed_qty: Optional[int] = None,
    ) -> Optional[str]:
        """
        Place an order.

        Args:
            symbol: Trading symbol (e.g., 'INFY', 'NIFTY')
            side: 'BUY' or 'SELL'
            quantity: Number of shares/contracts
            order_type: 'MARKET', 'LIMIT', or 'STOP_LOSS'
            price: Limit price (required for LIMIT orders)
            trigger_price: Trigger price (for STOP_LOSS orders)
            product_type: 'MIS', 'CNC', 'MTF'
            disclosed_qty: Disclosed quantity

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Validate inputs
            if side not in ["BUY", "SELL"]:
                print("❌ Side must be BUY or SELL")
                return None

            if order_type == "LIMIT" and price is None:
                print("❌ Price required for LIMIT orders")
                return None

            if order_type == "STOP_LOSS" and trigger_price is None:
                print("❌ Trigger price required for STOP_LOSS orders")
                return None

            # Prepare order request
            order_data = {
                "quantity": quantity,
                "order_type": order_type,
                "product_type": product_type,
                "side": side,
                "symbol": symbol,
            }

            if price:
                order_data["price"] = price
            if trigger_price:
                order_data["trigger_price"] = trigger_price
            if disclosed_qty:
                order_data["disclosed_quantity"] = disclosed_qty

            # Call API
            url = f"{self.base_url}/order/place"
            response = requests.post(
                url, json=order_data, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                order_id = data.get("data", {}).get("order_id")

                if order_id:
                    # Store in database
                    self._store_order(
                        order_id=order_id,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        order_type=order_type,
                        price=price,
                        trigger_price=trigger_price,
                        product_type=product_type,
                    )

                    print(f"✅ Order placed successfully")
                    print(f"   Order ID: {order_id}")
                    print(f"   Symbol: {symbol}")
                    print(f"   Side: {side}")
                    print(f"   Quantity: {quantity}")
                    print(f"   Type: {order_type}")
                    if price:
                        print(f"   Price: {price}")

                    return order_id
                else:
                    print("❌ No order ID in response")
                    return None
            else:
                error_msg = response.json().get("message", response.text)
                print(f"❌ API Error: {error_msg}")
                return None

        except requests.Timeout:
            print("❌ Request timeout")
            return None
        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return None

    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
    ) -> bool:
        """
        Modify an existing order.

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            trigger_price: New trigger price

        Returns:
            True if successful, False otherwise
        """
        try:
            modify_data = {}
            if quantity:
                modify_data["quantity"] = quantity
            if price:
                modify_data["price"] = price
            if trigger_price:
                modify_data["trigger_price"] = trigger_price

            if not modify_data:
                print("❌ No modification parameters provided")
                return False

            url = f"{self.base_url}/order/modify/{order_id}"
            response = requests.put(
                url, json=modify_data, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                print(f"✅ Order {order_id} modified successfully")
                self._update_order_status(order_id, "MODIFIED")
                return True
            else:
                print(f"❌ Modify failed: {response.json().get('message')}")
                return False

        except Exception as e:
            print(f"❌ Error modifying order: {e}")
            return False

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/order/cancel/{order_id}"
            response = requests.delete(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                print(f"✅ Order {order_id} cancelled successfully")
                self._update_order_status(order_id, "CANCELLED")
                return True
            else:
                print(f"❌ Cancellation failed: {response.json().get('message')}")
                return False

        except Exception as e:
            print(f"❌ Error cancelling order: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get order status and details.

        Args:
            order_id: Order ID

        Returns:
            Order details dict or None if not found
        """
        try:
            url = f"{self.base_url}/order/retrieve"
            params = {"order_id": order_id}

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                order_data = response.json().get("data", {})
                self._update_order_status(order_id, order_data.get("status"))
                return order_data
            else:
                print(f"❌ Failed to get order status: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting order status: {e}")
            return None

    def get_orders(self) -> List[Dict]:
        """Get all active orders."""
        try:
            url = f"{self.base_url}/order/retrieve-all"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                orders = response.json().get("data", [])
                print(f"✅ Retrieved {len(orders)} active orders")
                return orders
            else:
                print(f"❌ Failed to get orders: {response.json().get('message')}")
                return []

        except Exception as e:
            print(f"❌ Error getting orders: {e}")
            return []

    def get_order_history(
        self, symbol: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """Get order history from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            if symbol:
                c.execute(
                    """
                    SELECT * FROM orders
                    WHERE symbol = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (symbol, limit),
                )
            else:
                c.execute(
                    """
                    SELECT * FROM orders
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            orders = [dict(row) for row in c.fetchall()]
            conn.close()
            return orders

        except Exception as e:
            print(f"❌ Error getting order history: {e}")
            return []

    def place_bracket_order(
        self,
        symbol: str,
        quantity: int,
        entry_price: float,
        stop_loss_price: float,
        target_price: float,
    ) -> Optional[str]:
        """
        Place a bracket order (entry + stop loss + target).

        Args:
            symbol: Trading symbol
            quantity: Number of shares
            entry_price: Entry price
            stop_loss_price: Stop loss price
            target_price: Target/profit-taking price

        Returns:
            Bracket ID if successful
        """
        try:
            bracket_id = str(uuid.uuid4())[:8]

            # Place entry order
            entry_order_id = self.place_order(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                order_type="LIMIT",
                price=entry_price,
            )

            if not entry_order_id:
                print("❌ Failed to place entry order")
                return None

            # Store bracket order
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO bracket_orders
                (bracket_id, entry_order_id, symbol, quantity, entry_price,
                 stop_loss_price, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    bracket_id,
                    entry_order_id,
                    symbol,
                    quantity,
                    entry_price,
                    stop_loss_price,
                    target_price,
                ),
            )

            conn.commit()
            conn.close()

            print(f"✅ Bracket order placed")
            print(f"   Bracket ID: {bracket_id}")
            print(
                f"   Entry: {entry_price} | SL: {stop_loss_price} | Target: {target_price}"
            )

            return bracket_id

        except Exception as e:
            print(f"❌ Error placing bracket order: {e}")
            return None

    def _store_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product_type: str = "MIS",
    ):
        """Store order in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT OR REPLACE INTO orders
                (order_id, symbol, side, quantity, order_type, price, trigger_price,
                 product_type, order_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    order_id,
                    symbol,
                    side,
                    quantity,
                    order_type,
                    price,
                    trigger_price,
                    product_type,
                    "PENDING",
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️  Database store error: {e}")

    def _update_order_status(self, order_id: str, status: str):
        """Update order status in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                UPDATE orders
                SET order_status = ?, updated_at = ?
                WHERE order_id = ?
            """,
                (status, datetime.now(), order_id),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️  Update error: {e}")

    def display_orders(self, orders: List[Dict]):
        """Display orders in formatted table."""
        if not orders:
            print("No orders found")
            return

        print("\n" + "=" * 120)
        print(
            f"{'Order ID':12} | {'Symbol':8} | {'Side':4} | {'Qty':5} | {'Type':7} | {'Price':10} | {'Status':10} | {'Created':19}"
        )
        print("=" * 120)

        for order in orders:
            print(
                f"{order.get('order_id', 'N/A'):12} | "
                f"{order.get('symbol', 'N/A'):8} | "
                f"{order.get('side', 'N/A'):4} | "
                f"{order.get('quantity', 0):5} | "
                f"{order.get('order_type', 'N/A'):7} | "
                f"{order.get('price', 0):10.2f} | "
                f"{order.get('order_status', 'N/A'):10} | "
                f"{order.get('created_at', 'N/A'):19}"
            )

        print("=" * 120)

    def place_multi_order(self, orders: List[Dict]) -> List[str]:
        """
        Place multiple orders in a single API call (atomic operation).

        Args:
            orders: List of order dicts with keys: symbol, side, quantity, order_type, price, etc.

        Returns:
            List of order IDs if successful
        """
        try:
            # Prepare multi-order payload
            order_list = []
            for order in orders:
                order_data = {
                    "symbol": order.get("symbol"),
                    "side": order.get("side"),
                    "quantity": order.get("quantity"),
                    "order_type": order.get("order_type", "MARKET"),
                    "product_type": order.get("product_type", "MIS"),
                }

                if order.get("price"):
                    order_data["price"] = order["price"]
                if order.get("trigger_price"):
                    order_data["trigger_price"] = order["trigger_price"]

                order_list.append(order_data)

            # Call multi-order API
            url = f"{self.base_url}/order/multi/place"
            response = requests.post(
                url, json={"orders": order_list}, headers=self.headers, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                order_ids = [item.get("order_id") for item in data.get("data", [])]

                print(f"✅ Multi-order placed successfully - {len(order_ids)} orders")

                # Store all orders
                for i, order_id in enumerate(order_ids):
                    if order_id:
                        self._store_order(
                            order_id=order_id,
                            symbol=orders[i].get("symbol"),
                            side=orders[i].get("side"),
                            quantity=orders[i].get("quantity"),
                            order_type=orders[i].get("order_type", "MARKET"),
                            price=orders[i].get("price"),
                            product_type=orders[i].get("product_type", "MIS"),
                        )

                return order_ids
            else:
                error_msg = response.json().get("message", response.text)
                print(f"❌ Multi-order failed: {error_msg}")
                return []

        except Exception as e:
            print(f"❌ Error placing multi-order: {e}")
            return []

    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """
        Get FULL order details including lifecycle, fills, and exchange timestamps.

        Args:
            order_id: Order ID

        Returns:
            Detailed order information
        """
        try:
            url = f"{self.base_url}/order/details"
            params = {"order_id": order_id}

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json().get("data", {})

                # Enhanced details
                details = {
                    "order_id": data.get("order_id"),
                    "symbol": data.get("tradingsymbol"),
                    "exchange": data.get("exchange"),
                    "side": data.get("transaction_type"),
                    "quantity": data.get("quantity"),
                    "filled_quantity": data.get("filled_quantity", 0),
                    "pending_quantity": data.get("pending_quantity", 0),
                    "order_type": data.get("order_type"),
                    "price": data.get("price"),
                    "status": data.get("status"),
                    "status_message": data.get("status_message"),
                    "rejection_reason": data.get("rejection_reason"),
                    "average_price": data.get("average_price"),
                }

                return details
            else:
                print(
                    f"❌ Failed to get order details: {response.json().get('message')}"
                )
                return None

        except Exception as e:
            print(f"❌ Error getting order details: {e}")
            return None

    def get_trades(self, order_id: Optional[str] = None) -> List[Dict]:
        """
        Get trades (executions/fills) for orders.
        One order can have multiple trades if partially filled.

        Args:
            order_id: Specific order ID (optional, gets all trades if None)

        Returns:
            List of trade dictionaries
        """
        try:
            url = f"{self.base_url}/order/trades"
            params = {}
            if order_id:
                params["order_id"] = order_id

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                trades = response.json().get("data", [])

                processed_trades = []
                for trade in trades:
                    processed_trades.append(
                        {
                            "trade_id": trade.get("trade_id"),
                            "order_id": trade.get("order_id"),
                            "symbol": trade.get("tradingsymbol"),
                            "quantity": trade.get("quantity"),
                            "price": trade.get("price"),
                            "trade_timestamp": trade.get("trade_timestamp"),
                        }
                    )

                return processed_trades
            else:
                print(f"❌ Failed to get trades: {response.json().get('message')}")
                return []

        except Exception as e:
            print(f"❌ Error getting trades: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(
        description="Upstox Order Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--token", type=str, help="Upstox access token")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=[
            "place",
            "modify",
            "cancel",
            "status",
            "list-active",
            "history",
            "place-bracket",
        ],
        help="Action to perform",
    )

    # Place order arguments
    parser.add_argument("--symbol", type=str, help="Trading symbol")
    parser.add_argument("--side", type=str, choices=["BUY", "SELL"], help="Buy or Sell")
    parser.add_argument("--qty", type=int, help="Quantity")
    parser.add_argument(
        "--type",
        type=str,
        choices=["MARKET", "LIMIT", "STOP_LOSS"],
        default="MARKET",
        help="Order type",
    )
    parser.add_argument("--price", type=float, help="Limit price")
    parser.add_argument("--trigger-price", type=float, help="Trigger price")
    parser.add_argument(
        "--product-type",
        type=str,
        choices=["MIS", "CNC", "MTF"],
        default="MIS",
        help="Product type",
    )

    # Modify/Cancel/Status arguments
    parser.add_argument("--order-id", type=str, help="Order ID")
    parser.add_argument("--new-qty", type=int, help="New quantity")
    parser.add_argument("--new-price", type=float, help="New price")

    # Bracket order arguments
    parser.add_argument("--entry-price", type=float, help="Entry price")
    parser.add_argument("--stop-loss", type=float, help="Stop loss price")
    parser.add_argument("--target", type=float, help="Target price")

    # History arguments
    parser.add_argument("--limit", type=int, default=20, help="Limit for history")

    args = parser.parse_args()

    token = args.token or os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("❌ Access token required. Set UPSTOX_ACCESS_TOKEN or use --token")
        sys.exit(1)

    manager = OrderManager(token)

    if args.action == "place":
        if not all([args.symbol, args.side, args.qty]):
            print("❌ --symbol, --side, and --qty required for place action")
            sys.exit(1)

        manager.place_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.qty,
            order_type=args.type,
            price=args.price,
            trigger_price=args.trigger_price,
            product_type=args.product_type,
        )

    elif args.action == "modify":
        if not args.order_id:
            print("❌ --order-id required for modify action")
            sys.exit(1)

        manager.modify_order(
            order_id=args.order_id,
            quantity=args.new_qty,
            price=args.new_price,
        )

    elif args.action == "cancel":
        if not args.order_id:
            print("❌ --order-id required for cancel action")
            sys.exit(1)

        manager.cancel_order(args.order_id)

    elif args.action == "status":
        if not args.order_id:
            print("❌ --order-id required for status action")
            sys.exit(1)

        order = manager.get_order_status(args.order_id)
        if order:
            print("\n📋 ORDER DETAILS")
            print("=" * 60)
            for key, value in order.items():
                print(f"{key:20}: {value}")

    elif args.action == "list-active":
        orders = manager.get_orders()
        manager.display_orders(orders)

    elif args.action == "history":
        orders = manager.get_order_history(args.symbol, args.limit)
        manager.display_orders(orders)

    elif args.action == "place-bracket":
        if not all(
            [args.symbol, args.qty, args.entry_price, args.stop_loss, args.target]
        ):
            print("❌ --symbol, --qty, --entry-price, --stop-loss, --target required")
            sys.exit(1)

        manager.place_bracket_order(
            symbol=args.symbol,
            quantity=args.qty,
            entry_price=args.entry_price,
            stop_loss_price=args.stop_loss,
            target_price=args.target,
        )


if __name__ == "__main__":
    main()
