#!/usr/bin/env python3
"""
Portfolio Services v3 for Upstox
Implements missing v3 portfolio endpoints:
- P&L Reports (GET /portfolio/trades/p-and-l)
- Position Conversion (POST /portfolio/positions/convert)
- Charge Breakdown (GET /portfolio/trades/charges)

Features:
  - Detailed P&L analysis by trade
  - Position conversion (MIS→CNC, etc.)
  - Brokerage and tax breakdown
  - Integration with existing portfolio analytics

Usage:
  from scripts.portfolio_services_v3 import PortfolioServicesV3

  ps = PortfolioServicesV3()

  # Get P&L report
  pnl = ps.get_pnl_report()

  # Convert position
  ps.convert_position("INFY", 10, "MIS", "CNC")

  # Get charge breakdown
  charges = ps.get_charges("trade_id")
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auth_manager import AuthManager
from scripts.error_handler import with_retry, UpstoxAPIError
from scripts.database_pool import get_db_pool
import requests

logger = logging.getLogger(__name__)


class PortfolioServicesV3:
    """
    Portfolio services using v3 API endpoints.
    Provides P&L reports, position conversion, and charge breakdown.
    """

    BASE_URL = "https://api.upstox.com/v2"

    # v3 Portfolio endpoints
    PNL_REPORT = "/portfolio/trades/p-and-l"
    POSITION_CONVERT = "/portfolio/positions/convert"
    CHARGES_BREAKDOWN = "/portfolio/trades/charges"

    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize Portfolio Services V3.

        Args:
            db_path: Path to SQLite database
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.session = requests.Session()

        self._init_database()
        logger.info("✅ PortfolioServicesV3 initialized")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with valid token"""
        token = self.auth_manager.get_valid_token()
        if not token:
            raise UpstoxAPIError("Failed to get valid access token")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _init_database(self):
        """Initialize database tables for P&L tracking"""
        with self.db_pool.get_connection() as conn:
            # P&L reports table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pnl_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT,
                    symbol TEXT,
                    buy_date DATE,
                    sell_date DATE,
                    buy_price REAL,
                    sell_price REAL,
                    quantity INTEGER,
                    realized_pnl REAL,
                    unrealized_pnl REAL,
                    total_charges REAL,
                    net_pnl REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Position conversions table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS position_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    from_product TEXT NOT NULL,
                    to_product TEXT NOT NULL,
                    conversion_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'SUCCESS',
                    error_message TEXT
                )
            """
            )

            # Charges breakdown table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_charges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL,
                    symbol TEXT,
                    brokerage REAL DEFAULT 0,
                    stt REAL DEFAULT 0,
                    exchange_txn_charge REAL DEFAULT 0,
                    gst REAL DEFAULT 0,
                    sebi_charges REAL DEFAULT 0,
                    stamp_duty REAL DEFAULT 0,
                    total_charges REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_pnl_symbol 
                ON pnl_reports(symbol, sell_date)
            """
            )

    @with_retry(max_attempts=3, use_cache=True)
    def get_pnl_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        segment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get P&L report for trades.

        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            segment: Trading segment (EQ, FO, etc.)

        Returns:
            P&L report dictionary with realized/unrealized P&L
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL}{self.PNL_REPORT}"

            params = {}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            if segment:
                params["segment"] = segment

            response = self.session.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                pnl_data = result.get("data", {})

                # Save to database
                self._save_pnl_data(pnl_data)

                logger.info("✅ P&L report retrieved successfully")
                return pnl_data

            else:
                logger.warning(f"P&L report API returned {response.status_code}")
                # Return cached data if available
                return self._get_cached_pnl()

        except Exception as e:
            logger.error(f"❌ Failed to get P&L report: {e}", exc_info=True)
            return self._get_cached_pnl()

    def calculate_pnl_summary(self) -> Dict[str, Any]:
        """
        Calculate P&L summary from database records.

        Returns:
            Summary with total realized/unrealized P&L, win rate, etc.
        """
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                # Total realized P&L
                cursor.execute(
                    """
                    SELECT 
                        SUM(realized_pnl) as total_realized,
                        SUM(unrealized_pnl) as total_unrealized,
                        SUM(total_charges) as total_charges,
                        SUM(net_pnl) as total_net_pnl,
                        COUNT(*) as total_trades,
                        COUNT(CASE WHEN net_pnl > 0 THEN 1 END) as winning_trades,
                        COUNT(CASE WHEN net_pnl < 0 THEN 1 END) as losing_trades
                    FROM pnl_reports
                    WHERE sell_date IS NOT NULL
                """
                )

                row = cursor.fetchone()

                total_realized = row[0] or 0
                total_unrealized = row[1] or 0
                total_charges = row[2] or 0
                total_net_pnl = row[3] or 0
                total_trades = row[4] or 0
                winning_trades = row[5] or 0
                losing_trades = row[6] or 0

                win_rate = (
                    (winning_trades / total_trades * 100) if total_trades > 0 else 0
                )

                return {
                    "total_realized_pnl": total_realized,
                    "total_unrealized_pnl": total_unrealized,
                    "total_charges": total_charges,
                    "net_pnl": total_net_pnl,
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": round(win_rate, 2),
                }

        except Exception as e:
            logger.error(f"Failed to calculate P&L summary: {e}")
            return {}

    @with_retry(max_attempts=3)
    def convert_position(
        self,
        symbol: str,
        quantity: int,
        from_product: str,
        to_product: str,
        transaction_type: str = "BUY",
    ) -> bool:
        """
        Convert position from one product type to another.
        Example: MIS (Intraday) → CNC (Delivery)

        Args:
            symbol: Trading symbol
            quantity: Quantity to convert
            from_product: Current product type (MIS, CNC, NRML)
            to_product: Target product type
            transaction_type: BUY or SELL

        Returns:
            True if successful, False otherwise
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL}{self.POSITION_CONVERT}"

            conversion_data = {
                "symbol": symbol,
                "quantity": quantity,
                "old_product": from_product,
                "new_product": to_product,
                "transaction_type": transaction_type,
            }

            response = self.session.post(
                url, json=conversion_data, headers=headers, timeout=15
            )

            if response.status_code == 200:
                # Save conversion record
                self._save_conversion(
                    symbol, quantity, from_product, to_product, "SUCCESS"
                )

                logger.info(
                    f"✅ Position converted: {symbol} {quantity} "
                    f"{from_product}→{to_product}"
                )
                return True

            else:
                error_msg = response.text
                logger.error(f"Position conversion failed: {error_msg}")
                self._save_conversion(
                    symbol, quantity, from_product, to_product, "FAILED", error_msg
                )
                return False

        except Exception as e:
            logger.error(f"❌ Position conversion error: {e}", exc_info=True)
            self._save_conversion(
                symbol, quantity, from_product, to_product, "ERROR", str(e)
            )
            return False

    @with_retry(max_attempts=3, use_cache=True)
    def get_charges(self, trade_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get charge breakdown for trades.

        Args:
            trade_id: Specific trade ID (optional)

        Returns:
            Charges breakdown with brokerage, STT, taxes, etc.
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL}{self.CHARGES_BREAKDOWN}"

            params = {}
            if trade_id:
                params["trade_id"] = trade_id

            response = self.session.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                result = response.json()
                charges_data = result.get("data", {})

                # Save to database
                if trade_id:
                    self._save_charges(trade_id, charges_data)

                logger.info("✅ Charges breakdown retrieved")
                return charges_data

            else:
                logger.warning(f"Charges API returned {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Failed to get charges: {e}", exc_info=True)
            return {}

    def _save_pnl_data(self, pnl_data: Dict[str, Any]):
        """Save P&L data to database"""
        try:
            if not pnl_data:
                return

            trades = pnl_data.get("trades", [])

            with self.db_pool.get_connection() as conn:
                for trade in trades:
                    conn.execute(
                        """
                        INSERT INTO pnl_reports 
                        (trade_id, symbol, buy_date, sell_date, buy_price, 
                         sell_price, quantity, realized_pnl, unrealized_pnl, 
                         total_charges, net_pnl)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            trade.get("trade_id"),
                            trade.get("symbol"),
                            trade.get("buy_date"),
                            trade.get("sell_date"),
                            trade.get("buy_price"),
                            trade.get("sell_price"),
                            trade.get("quantity"),
                            trade.get("realized_pnl", 0),
                            trade.get("unrealized_pnl", 0),
                            trade.get("total_charges", 0),
                            trade.get("net_pnl", 0),
                        ),
                    )

        except Exception as e:
            logger.error(f"Failed to save P&L data: {e}")

    def _get_cached_pnl(self) -> Dict[str, Any]:
        """Get cached P&L data from database"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM pnl_reports
                    ORDER BY created_at DESC
                    LIMIT 100
                """
                )

                rows = cursor.fetchall()

                trades = []
                for row in rows:
                    trades.append(
                        {
                            "trade_id": row["trade_id"],
                            "symbol": row["symbol"],
                            "buy_date": row["buy_date"],
                            "sell_date": row["sell_date"],
                            "buy_price": row["buy_price"],
                            "sell_price": row["sell_price"],
                            "quantity": row["quantity"],
                            "realized_pnl": row["realized_pnl"],
                            "unrealized_pnl": row["unrealized_pnl"],
                            "total_charges": row["total_charges"],
                            "net_pnl": row["net_pnl"],
                        }
                    )

                return {"trades": trades}

        except Exception as e:
            logger.error(f"Failed to get cached P&L: {e}")
            return {}

    def _save_conversion(
        self,
        symbol: str,
        quantity: int,
        from_product: str,
        to_product: str,
        status: str,
        error_message: Optional[str] = None,
    ):
        """Save position conversion record"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO position_conversions 
                    (symbol, quantity, from_product, to_product, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (symbol, quantity, from_product, to_product, status, error_message),
                )

        except Exception as e:
            logger.error(f"Failed to save conversion record: {e}")

    def _save_charges(self, trade_id: str, charges: Dict[str, Any]):
        """Save charge breakdown to database"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO trade_charges 
                    (trade_id, symbol, brokerage, stt, exchange_txn_charge, 
                     gst, sebi_charges, stamp_duty, total_charges)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trade_id,
                        charges.get("symbol"),
                        charges.get("brokerage", 0),
                        charges.get("stt", 0),
                        charges.get("exchange_transaction_charge", 0),
                        charges.get("gst", 0),
                        charges.get("sebi_charges", 0),
                        charges.get("stamp_duty", 0),
                        charges.get("total_charges", 0),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save charges: {e}")


if __name__ == "__main__":
    """Test portfolio services v3"""
    logging.basicConfig(level=logging.INFO)

    ps = PortfolioServicesV3()

    # Test P&L report
    print("\n📊 Getting P&L report...")
    pnl = ps.get_pnl_report()
    print(f"P&L data: {pnl}")

    # Test P&L summary
    print("\n📈 Calculating P&L summary...")
    summary = ps.calculate_pnl_summary()
    print(f"Summary: {summary}")

    print("\n✅ PortfolioServicesV3 test complete")
