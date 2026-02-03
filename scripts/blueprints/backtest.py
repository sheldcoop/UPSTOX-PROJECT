#!/usr/bin/env python3
"""
Backtesting Blueprint
Handles backtesting endpoints
"""

from flask import Blueprint, jsonify, g, request
import sqlite3
import pandas as pd
import logging

backtest_bp = Blueprint("backtest", __name__, url_prefix="/api/backtest")

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


@backtest_bp.route("/run", methods=["POST"])
def run_backtest():
    """Run strategy backtest"""
    try:
        from backtesting_engine import (
            Backtester,
            create_iron_condor,
            create_bull_call_spread,
        )

        data = request.json
        strategy_name = data.get("strategy")
        entry_date = data.get("entry_date")
        exit_date = data.get("exit_date")

        # Create backtester
        backtester = Backtester()

        # Get strategy (for now, use pre-built strategies)
        if strategy_name == "iron_condor":
            strategy = create_iron_condor(spot_price=data.get("spot_price", 18000))
        elif strategy_name == "bull_call_spread":
            strategy = create_bull_call_spread(spot_price=data.get("spot_price", 18000))
        else:
            return jsonify({"error": "Unknown strategy"}), 400

        # Mock historical data (in production, fetch from database)
        dates = pd.date_range(entry_date, exit_date, freq="H")
        historical_data = pd.DataFrame(
            {"timestamp": dates, "close": [18000 + i * 10 for i in range(len(dates))]}
        )

        result = backtester.run_backtest(
            strategy, historical_data, entry_date, exit_date
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Backtest error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@backtest_bp.route("/strategies", methods=["GET"])
def get_backtest_strategies():
    """Get available backtest strategies"""
    return jsonify(
        {
            "strategies": [
                {
                    "id": "iron_condor",
                    "name": "Iron Condor",
                    "description": "Sell OTM put/call spreads, profit from low volatility",
                    "max_profit": "Net premium",
                    "max_loss": "Spread width - premium",
                },
                {
                    "id": "bull_call_spread",
                    "name": "Bull Call Spread",
                    "description": "Buy lower strike call, sell higher strike call",
                    "max_profit": "Strike difference - premium",
                    "max_loss": "Net premium paid",
                },
            ]
        }
    )


@backtest_bp.route("/results", methods=["GET"])
def get_backtest_results():
    """Get past backtest results from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Query backtest results (if stored in DB)
        cursor.execute(
            """
            SELECT * FROM backtest_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "id": row[0],
                    "strategy": row[1],
                    "entry_date": row[2],
                    "exit_date": row[3],
                    "pnl": row[4],
                    "win_rate": row[5],
                    "created_at": row[6],
                }
            )

        conn.close()
        return jsonify({"results": results})
    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Backtest results error: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@backtest_bp.route("/multi-expiry", methods=["POST"])
def backtest_multi_expiry():
    """Backtest multi-expiry strategy with auto-rolling"""
    try:
        from multi_expiry_strategies import (
            create_calendar_spread,
            create_diagonal_spread,
            MultiExpiryBacktester,
        )
        import numpy as np

        data = request.json
        required = ["strategy_type", "start_date", "end_date", "underlying_price"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing required fields: {required}"}), 400

        # Create strategy based on type
        strategy_type = data["strategy_type"]

        if strategy_type == "calendar_spread":
            strategy = create_calendar_spread(
                underlying_price=data["underlying_price"],
                strike=data.get("strike", data["underlying_price"]),
                near_expiry=data.get("near_expiry", "2026-02-06"),
                far_expiry=data.get("far_expiry", "2026-02-27"),
                option_type=data.get("option_type", "CALL"),
            )
        elif strategy_type == "diagonal_spread":
            strategy = create_diagonal_spread(
                underlying_price=data["underlying_price"],
                near_strike=data.get("near_strike", data["underlying_price"]),
                far_strike=data.get("far_strike", data["underlying_price"] + 200),
                near_expiry=data.get("near_expiry", "2026-02-06"),
                far_expiry=data.get("far_expiry", "2026-02-27"),
                option_type=data.get("option_type", "CALL"),
            )
        else:
            return jsonify({"error": "Unknown strategy type"}), 400

        # Create mock historical data
        dates = pd.date_range(data["start_date"], data["end_date"], freq="D")
        prices = data["underlying_price"] + np.cumsum(np.random.randn(len(dates)) * 20)

        historical_data = pd.DataFrame(
            {"date": dates.strftime("%Y-%m-%d"), "close": prices}
        )

        # Run backtest
        backtester = MultiExpiryBacktester()
        result = backtester.backtest_with_rolling(
            strategy,
            historical_data,
            data["start_date"],
            data["end_date"],
            auto_roll=data.get("auto_roll", True),
            roll_days_before=data.get("roll_days_before", 3),
        )

        return jsonify(result)
    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Multi-expiry backtest error: {e}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500
