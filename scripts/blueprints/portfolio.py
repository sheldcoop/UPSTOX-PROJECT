#!/usr/bin/env python3
"""
Portfolio Blueprint
Handles portfolio and user profile endpoints
"""

from flask import Blueprint, jsonify, g, request
import sqlite3
import logging
import requests

portfolio_bp = Blueprint("portfolio", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@portfolio_bp.route("/portfolio", methods=["GET"])
def get_portfolio():
    """Get portfolio summary - fetches real data from Upstox if authenticated"""
    try:
        # Check if authenticated using AuthManager
        from auth_manager import AuthManager

        auth = AuthManager()
        access_token = auth.get_valid_token()

        # If authenticated, fetch real portfolio from Upstox
        if access_token:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            try:
                # Fetch user profile (available 24/7)
                profile_response = requests.get(
                    "https://api.upstox.com/v2/user/profile",
                    headers=headers,
                    timeout=10,
                )

                # Fetch holdings (available during market hours)
                holdings_response = requests.get(
                    "https://api.upstox.com/v2/portfolio/short-term-positions",
                    headers=headers,
                    timeout=10,
                )

                # Fetch funds (available 5:30 AM - 12:00 AM IST)
                funds_response = requests.get(
                    "https://api.upstox.com/v2/user/get-funds-and-margin",
                    headers=headers,
                    timeout=10,
                )

                # Check if we got valid responses
                if profile_response.status_code == 200:
                    # We're authenticated - build portfolio data
                    portfolio = {"authenticated": True, "mode": "live"}

                    # Try to get funds if API is available
                    if funds_response.status_code == 200:
                        funds_data = funds_response.json().get("data", {})
                        equity = funds_data.get("equity", {})

                        portfolio.update(
                            {
                                "total_value": float(equity.get("available_margin", 0)),
                                "cash_available": float(
                                    equity.get("available_margin", 0)
                                ),
                                "invested_value": float(equity.get("used_margin", 0)),
                                "unrealized_pnl": 0,
                                "realized_pnl": 0,
                                "day_pnl": 0,
                                "day_pnl_percent": 0,
                            }
                        )
                    else:
                        # Funds API not available (outside service hours)
                        portfolio.update(
                            {
                                "total_value": 0,
                                "cash_available": 0,
                                "invested_value": 0,
                                "unrealized_pnl": 0,
                                "realized_pnl": 0,
                                "day_pnl": 0,
                                "day_pnl_percent": 0,
                                "service_message": "Funds data available 5:30 AM - 12:00 AM IST",
                            }
                        )

                    # Get positions count
                    positions_count = 0
                    if holdings_response.status_code == 200:
                        positions_data = holdings_response.json().get("data", [])
                        positions_count = len(positions_data)

                    portfolio["positions_count"] = positions_count

                    return jsonify(portfolio)

            except Exception as e:
                logger.error(
                    f"[TraceID: {g.trace_id}] Failed to fetch from Upstox: {e}"
                )
                # Fall through to paper trading

        # Fall back to paper trading if not authenticated or error
        from paper_trading import PaperTradingSystem

        paper_system = PaperTradingSystem(db_path=DB_PATH)
        summary = paper_system.get_portfolio_summary()

        portfolio = {
            "authenticated": False,
            "total_value": summary.get("total_value", 100000),
            "cash_available": summary.get("cash_available", 100000),
            "invested_value": summary.get("invested_value", 0),
            "unrealized_pnl": summary.get("total_pnl", 0),
            "realized_pnl": summary.get("realized_pnl", 0),
            "day_pnl": 0,
            "day_pnl_percent": 0,
            "positions_count": len(summary.get("positions", [])),
            "mode": "paper",
        }

        return jsonify(portfolio)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Portfolio endpoint error: {e}")
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/user/profile", methods=["GET"])
def get_user_profile():
    """Get user profile from Upstox"""
    try:
        # Check if we have a valid token using AuthManager
        from auth_manager import AuthManager

        auth = AuthManager()
        access_token = auth.get_valid_token()

        if not access_token:
            return jsonify({"error": "Not authenticated", "authenticated": False}), 401

        # Fetch user profile from Upstox
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        response = requests.get(
            "https://api.upstox.com/v2/user/profile", headers=headers, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            user_data = data.get("data", {})

            return jsonify(
                {
                    "authenticated": True,
                    "name": user_data.get("user_name", "User"),
                    "email": user_data.get("email", ""),
                    "user_id": user_data.get("user_id", ""),
                    "user_type": user_data.get("user_type", "individual"),
                    "broker": "Upstox",
                    "exchanges": user_data.get("exchanges", []),
                }
            )
        else:
            return (
                jsonify({"error": "Failed to fetch profile", "authenticated": False}),
                response.status_code,
            )

    except Exception as e:
        return jsonify({"error": str(e), "authenticated": False}), 500


@portfolio_bp.route("/positions", methods=["GET"])
def get_positions():
    """Get all open positions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get positions with current prices (mock current price as entry + small change)
        query = """
            SELECT 
                id,
                symbol,
                quantity,
                average_price as entry_price,
                average_price * 1.02 as current_price,
                updated_at as entry_date,
                CASE WHEN quantity > 0 THEN 'long' ELSE 'short' END as side
            FROM paper_positions
            WHERE quantity != 0
            ORDER BY updated_at DESC
        """

        rows = cursor.execute(query).fetchall()
        conn.close()

        positions = []
        for row in rows:
            entry_price = row["entry_price"]
            current_price = row["current_price"]
            quantity = abs(row["quantity"])

            pnl = (current_price - entry_price) * quantity
            pnl_percent = (
                ((current_price - entry_price) / entry_price) * 100
                if entry_price > 0
                else 0
            )

            positions.append(
                {
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "quantity": quantity,
                    "entry_price": round(entry_price, 2),
                    "current_price": round(current_price, 2),
                    "entry_date": row["entry_date"],
                    "pnl": round(pnl, 2),
                    "pnl_percent": round(pnl_percent, 2),
                    "side": row["side"],
                }
            )

        return jsonify(positions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@portfolio_bp.route("/positions/<symbol>", methods=["GET"])
def get_position_by_symbol(symbol):
    """Get position for specific symbol"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                id, symbol, quantity, average_price as entry_price,
                average_price * 1.02 as current_price,
                updated_at as entry_date,
                CASE WHEN quantity > 0 THEN 'long' ELSE 'short' END as side
            FROM paper_positions
            WHERE symbol = ? AND quantity != 0
        """

        row = cursor.execute(query, (symbol,)).fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Position not found"}), 404

        entry_price = row["entry_price"]
        current_price = row["current_price"]
        quantity = abs(row["quantity"])

        pnl = (current_price - entry_price) * quantity
        pnl_percent = (
            ((current_price - entry_price) / entry_price) * 100
            if entry_price > 0
            else 0
        )

        position = {
            "id": row["id"],
            "symbol": row["symbol"],
            "quantity": quantity,
            "entry_price": round(entry_price, 2),
            "current_price": round(current_price, 2),
            "entry_date": row["entry_date"],
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "side": row["side"],
        }

        return jsonify(position)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
