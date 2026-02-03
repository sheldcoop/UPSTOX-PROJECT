#!/usr/bin/env python3
"""
Signals Blueprint
Handles trading signals and instruments endpoints
"""

from flask import Blueprint, jsonify, g, request
import sqlite3
import logging

signals_bp = Blueprint("signals", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@signals_bp.route("/signals", methods=["GET"])
def get_signals():
    """Get trading signals"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                id, symbol, strategy, action, confidence,
                entry_price, target_price, stop_loss, generated_at
            FROM trading_signals
            ORDER BY generated_at DESC
            LIMIT 20
        """

        rows = cursor.execute(query).fetchall()
        conn.close()

        signals = []
        for row in rows:
            signals.append(
                {
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "strategy": row["strategy"],
                    "action": row["action"],
                    "confidence": row["confidence"],
                    "entry_price": row["entry_price"],
                    "target_price": row["target_price"],
                    "stop_loss": row["stop_loss"],
                    "generated_at": row["generated_at"],
                }
            )

        return jsonify(signals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@signals_bp.route("/signals/<strategy>", methods=["GET"])
def get_signals_by_strategy(strategy):
    """Get signals for specific strategy"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                id, symbol, strategy, action, confidence,
                entry_price, target_price, stop_loss, generated_at
            FROM trading_signals
            WHERE strategy = ?
            ORDER BY generated_at DESC
            LIMIT 20
        """

        rows = cursor.execute(query, (strategy,)).fetchall()
        conn.close()

        signals = []
        for row in rows:
            signals.append(
                {
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "strategy": row["strategy"],
                    "action": row["action"],
                    "confidence": row["confidence"],
                    "entry_price": row["entry_price"],
                    "target_price": row["target_price"],
                    "stop_loss": row["stop_loss"],
                    "generated_at": row["generated_at"],
                }
            )

        return jsonify(signals)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@signals_bp.route("/instruments/nse-eq", methods=["GET"])
def get_nse_equity_instruments():
    """Get all NSE equity instruments for autocomplete

    Query params:
        search: Optional search term for filtering
        limit: Max results (default 100, max 500)

    Returns list of {symbol, name, instrument_key}
    """
    logger.info(f"[TraceID: {g.trace_id}] Fetching NSE equity instruments")

    search_term = request.args.get("search", "").strip().upper()
    limit = min(int(request.args.get("limit", 100)), 500)

    try:
        conn = get_db_connection()

        # Query with JOIN to get company names
        if search_term:
            query = """
                SELECT DISTINCT 
                    e.trading_symbol as symbol,
                    COALESCE(m.company_name, e.trading_symbol) as name,
                    e.instrument_key
                FROM exchange_listings e
                LEFT JOIN master_stocks m ON e.symbol = m.symbol
                WHERE e.segment = 'NSE_EQ'
                  AND (e.trading_symbol LIKE ? OR m.company_name LIKE ?)
                ORDER BY e.trading_symbol
                LIMIT ?
            """
            results = conn.execute(
                query, (f"{search_term}%", f"%{search_term}%", limit)
            ).fetchall()
        else:
            # Return popular/top stocks when no search term
            query = """
                SELECT DISTINCT 
                    e.trading_symbol as symbol,
                    COALESCE(m.company_name, e.trading_symbol) as name,
                    e.instrument_key
                FROM exchange_listings e
                LEFT JOIN master_stocks m ON e.symbol = m.symbol
                WHERE e.segment = 'NSE_EQ'
                  AND e.trading_symbol IN ('RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 
                                          'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
                                          'LT', 'AXISBANK', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI')
                ORDER BY e.trading_symbol
            """
            results = conn.execute(query).fetchall()

        conn.close()

        instruments = [
            {"symbol": row[0], "name": row[1], "instrument_key": row[2]}
            for row in results
        ]

        logger.info(f"[TraceID: {g.trace_id}] Returning {len(instruments)} instruments")

        return jsonify(
            {
                "instruments": instruments,
                "count": len(instruments),
                "search_term": search_term or None,
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Error fetching instruments: {str(e)}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500
