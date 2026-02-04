#!/usr/bin/env python3
"""
Order Management System for Upstox v3 API
Migrated to use v3 order endpoints with backward compatibility to v2

New v3 Endpoints:
- POST /orders/v3/regular/create - Create new order
- PUT /orders/v3/regular/modify - Modify existing order
- DELETE /orders/v3/regular/cancel/{order_id} - Cancel order
- GET /orders - Get order book
- GET /trades - Get trade history

Features:
  - v3 API endpoints with improved performance
  - Backward compatibility fallback to v2
  - Enhanced error handling
  - All v2 features preserved

Usage:
  from scripts.order_manager_v3 import OrderManagerV3

  # Initialize
  om = OrderManagerV3(access_token)

  # Place order
  order_id = om.place_order("INFY", "BUY", 1, order_type="MARKET")
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auth_manager import AuthManager
from scripts.error_handler import with_retry, UpstoxAPIError, RateLimitError
from scripts.database_pool import get_db_pool
from scripts.auth_headers_mixin import AuthHeadersMixin
import requests

logger = logging.getLogger(__name__)


class OrderManagerV3(AuthHeadersMixin):
    """
    Order Manager using Upstox v3 API endpoints.
    Provides v2 fallback for compatibility.
    """

    # API endpoints
    BASE_URL_V3 = "https://api.upstox.com/v2"  # v3 is under v2 base

    # v3 endpoints
    PLACE_ORDER_V3 = "/orders/v3/regular/create"
    MODIFY_ORDER_V3 = "/orders/v3/regular/modify"
    CANCEL_ORDER_V3 = "/orders/v3/regular/cancel"
    ORDER_BOOK = "/orders"
    TRADE_HISTORY = "/trades"

    # v2 fallback endpoints
    PLACE_ORDER_V2 = "/order/place"
    MODIFY_ORDER_V2 = "/order/modify"
    CANCEL_ORDER_V2 = "/order/cancel"

    def __init__(self, db_path: str = "market_data.db", use_v3: bool = True):
        """
        Initialize Order Manager V3.

        Args:
            db_path: Path to SQLite database
            use_v3: Use v3 endpoints (fallback to v2 on error)
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.use_v3 = use_v3
        self.session = requests.Session()

        self._init_database()
        logger.info(f"✅ OrderManagerV3 initialized (v3_enabled: {use_v3})")

    def _init_database(self):
        """Initialize database tables for order tracking"""
        with self.db_pool.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders_v3 (
                    order_id TEXT PRIMARY KEY,
                    exchange TEXT,
                    symbol TEXT NOT NULL,
                    instrument_key TEXT,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    filled_quantity INTEGER DEFAULT 0,
                    pending_quantity INTEGER,
                    order_type TEXT NOT NULL,
                    price REAL,
                    trigger_price REAL,
                    order_status TEXT DEFAULT 'PENDING',
                    status_message TEXT,
                    product_type TEXT,
                    validity TEXT DEFAULT 'DAY',
                    disclosed_quantity INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    api_version TEXT DEFAULT 'v3',
                    trade_id TEXT,
                    average_price REAL,
                    rejection_reason TEXT
                )
            """
            )

            # Create index for faster queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_v3_symbol_status 
                ON orders_v3(symbol, order_status)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_v3_created_at 
                ON orders_v3(created_at)
            """
            )

    @with_retry(max_attempts=3, use_cache=False)
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        product_type: str = "D",  # D=Delivery, I=Intraday
        validity: str = "DAY",
        disclosed_quantity: Optional[int] = None,
        instrument_key: Optional[str] = None,
    ) -> Optional[str]:
        """
        Place an order using v3 API (with v2 fallback).

        Args:
            symbol: Trading symbol (e.g., 'INFY', 'NIFTY')
            side: 'BUY' or 'SELL'
            quantity: Number of shares/contracts
            order_type: 'MARKET' or 'LIMIT' or 'SL' or 'SL-M'
            price: Limit price (required for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            product_type: 'D' (Delivery/CNC) or 'I' (Intraday/MIS)
            validity: 'DAY' or 'IOC'
            disclosed_quantity: Disclosed quantity
            instrument_key: Instrument key (format: NSE_EQ|INE009A01021)

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Validate inputs
            if side not in ["BUY", "SELL"]:
                raise ValueError("Side must be BUY or SELL")

            if order_type not in ["MARKET", "LIMIT", "SL", "SL-M"]:
                raise ValueError("Invalid order type")

            if order_type == "LIMIT" and price is None:
                raise ValueError("Price required for LIMIT orders")

            if order_type in ["SL", "SL-M"] and trigger_price is None:
                raise ValueError("Trigger price required for SL orders")

            headers = self._get_headers()

            # Try v3 endpoint first
            if self.use_v3:
                order_data = {
                    "quantity": quantity,
                    "order_type": order_type,
                    "product": product_type,
                    "side": side,
                    "symbol": symbol,
                    "validity": validity,
                }

                if instrument_key:
                    order_data["instrument_key"] = instrument_key

                if price:
                    order_data["price"] = price

                if trigger_price:
                    order_data["trigger_price"] = trigger_price

                if disclosed_quantity:
                    order_data["disclosed_quantity"] = disclosed_quantity

                try:
                    url = f"{self.BASE_URL_V3}{self.PLACE_ORDER_V3}"
                    response = self.session.post(
                        url, json=order_data, headers=headers, timeout=15
                    )

                    if response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded")

                    response.raise_for_status()

                    result = response.json()
                    order_id = result.get("data", {}).get("order_id")

                    if order_id:
                        self._save_order(
                            order_id,
                            symbol,
                            side,
                            quantity,
                            order_type,
                            price,
                            product_type,
                            api_version="v3",
                        )
                        logger.info(f"✅ Order placed (v3): {order_id}")
                        return order_id

                except Exception as v3_error:
                    logger.warning(f"v3 API failed, falling back to v2: {v3_error}")

            # Fallback to v2
            logger.info("Using v2 API fallback")
            order_data_v2 = {
                "quantity": quantity,
                "order_type": order_type,
                "product_type": "MIS" if product_type == "I" else "CNC",
                "side": side,
                "symbol": symbol,
            }

            if price:
                order_data_v2["price"] = price
            if trigger_price:
                order_data_v2["trigger_price"] = trigger_price
            if disclosed_quantity:
                order_data_v2["disclosed_qty"] = disclosed_quantity

            url_v2 = f"{self.BASE_URL_V3}{self.PLACE_ORDER_V2}"
            response = self.session.post(
                url_v2, json=order_data_v2, headers=headers, timeout=15
            )

            response.raise_for_status()
            result = response.json()
            order_id = result.get("data", {}).get("order_id")

            if order_id:
                self._save_order(
                    order_id,
                    symbol,
                    side,
                    quantity,
                    order_type,
                    price,
                    product_type,
                    api_version="v2",
                )
                logger.info(f"✅ Order placed (v2 fallback): {order_id}")
                return order_id

            return None

        except Exception as e:
            logger.error(f"❌ Order placement failed: {e}", exc_info=True)
            raise

    @with_retry(max_attempts=3)
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None,
        validity: Optional[str] = None,
    ) -> bool:
        """
        Modify an existing order using v3 API.

        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New price
            trigger_price: New trigger price
            order_type: New order type
            validity: New validity

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = self._get_headers()

            # Build modification data (only include changed fields)
            modify_data = {}

            if quantity is not None:
                modify_data["quantity"] = quantity
            if price is not None:
                modify_data["price"] = price
            if trigger_price is not None:
                modify_data["trigger_price"] = trigger_price
            if order_type is not None:
                modify_data["order_type"] = order_type
            if validity is not None:
                modify_data["validity"] = validity

            if not modify_data:
                logger.warning("No modifications specified")
                return False

            # Try v3 endpoint
            if self.use_v3:
                try:
                    url = f"{self.BASE_URL_V3}{self.MODIFY_ORDER_V3}"
                    modify_data["order_id"] = order_id

                    response = self.session.put(
                        url, json=modify_data, headers=headers, timeout=15
                    )

                    response.raise_for_status()

                    self._update_order_status(order_id, "MODIFIED")
                    logger.info(f"✅ Order modified (v3): {order_id}")
                    return True

                except Exception as v3_error:
                    logger.warning(f"v3 modify failed, trying v2: {v3_error}")

            # v2 fallback
            url_v2 = f"{self.BASE_URL_V3}{self.MODIFY_ORDER_V2}/{order_id}"
            response = self.session.put(
                url_v2, json=modify_data, headers=headers, timeout=15
            )

            response.raise_for_status()

            self._update_order_status(order_id, "MODIFIED")
            logger.info(f"✅ Order modified (v2): {order_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Order modification failed: {e}", exc_info=True)
            return False

    @with_retry(max_attempts=3)
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order using v3 API.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = self._get_headers()

            # Try v3 endpoint
            if self.use_v3:
                try:
                    url = f"{self.BASE_URL_V3}{self.CANCEL_ORDER_V3}/{order_id}"
                    response = self.session.delete(url, headers=headers, timeout=15)

                    response.raise_for_status()

                    self._update_order_status(order_id, "CANCELLED")
                    logger.info(f"✅ Order cancelled (v3): {order_id}")
                    return True

                except Exception as v3_error:
                    logger.warning(f"v3 cancel failed, trying v2: {v3_error}")

            # v2 fallback
            url_v2 = f"{self.BASE_URL_V3}{self.CANCEL_ORDER_V2}/{order_id}"
            response = self.session.delete(url_v2, headers=headers, timeout=15)

            response.raise_for_status()

            self._update_order_status(order_id, "CANCELLED")
            logger.info(f"✅ Order cancelled (v2): {order_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Order cancellation failed: {e}", exc_info=True)
            return False

    @with_retry(max_attempts=3, use_cache=True)
    def get_order_book(self) -> List[Dict[str, Any]]:
        """
        Get order book (all orders).

        Returns:
            List of order dictionaries
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL_V3}{self.ORDER_BOOK}"

            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            result = response.json()
            orders = result.get("data", [])

            logger.info(f"✅ Retrieved {len(orders)} orders from order book")
            return orders

        except Exception as e:
            logger.error(f"❌ Failed to get order book: {e}", exc_info=True)
            return []

    @with_retry(max_attempts=3, use_cache=True)
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        Get trade history (executed trades).

        Returns:
            List of trade dictionaries
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL_V3}{self.TRADE_HISTORY}"

            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            result = response.json()
            trades = result.get("data", [])

            logger.info(f"✅ Retrieved {len(trades)} trades from history")
            return trades

        except Exception as e:
            logger.error(f"❌ Failed to get trade history: {e}", exc_info=True)
            return []

    def _save_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
        price: Optional[float],
        product_type: str,
        api_version: str = "v3",
    ):
        """Save order to database"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO orders_v3 
                    (order_id, symbol, side, quantity, order_type, price, 
                     product_type, order_status, api_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order_id,
                        symbol,
                        side,
                        quantity,
                        order_type,
                        price,
                        product_type,
                        "PENDING",
                        api_version,
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save order to database: {e}")

    def _update_order_status(self, order_id: str, status: str):
        """Update order status in database"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE orders_v3 
                    SET order_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """,
                    (status, order_id),
                )

        except Exception as e:
            logger.error(f"Failed to update order status: {e}")


if __name__ == "__main__":
    """Test order manager v3"""
    logging.basicConfig(level=logging.INFO)

    # Initialize
    om = OrderManagerV3()

    # Test order book retrieval
    print("\n📋 Getting order book...")
    orders = om.get_order_book()
    print(f"Found {len(orders)} orders")

    # Test trade history
    print("\n📜 Getting trade history...")
    trades = om.get_trade_history()
    print(f"Found {len(trades)} trades")

    print("\n✅ OrderManagerV3 test complete")
