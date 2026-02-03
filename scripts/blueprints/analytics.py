#!/usr/bin/env python3
"""
Analytics Blueprint
Handles performance, alerts, and analytics endpoints
"""

from flask import Blueprint, jsonify, g, request
import logging

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


@analytics_bp.route("/performance", methods=["GET"])
def get_performance():
    """Get performance metrics"""
    try:
        from performance_analytics import PerformanceAnalytics

        analytics = PerformanceAnalytics(db_path=DB_PATH)

        # Get comprehensive report
        report = analytics.get_comprehensive_report(days=30)

        metrics = {
            "total_trades": report.get("total_trades", 0),
            "winning_trades": report.get("winning_trades", 0),
            "losing_trades": report.get("losing_trades", 0),
            "win_rate": report.get("win_rate", 0),
            "profit_factor": report.get("profit_factor", 0),
            "sharpe_ratio": report.get("sharpe_ratio", 0),
            "sortino_ratio": report.get("sortino_ratio", 0),
            "max_drawdown": report.get("max_drawdown", 0),
            "max_drawdown_percent": report.get("max_drawdown_percent", 0),
            "total_pnl": report.get("total_pnl", 0),
        }

        return jsonify(metrics)
    except Exception as e:
        # Return default metrics if error
        logger.error(f"[TraceID: {g.trace_id}] Performance error: {e}")
        return jsonify(
            {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "sortino_ratio": 0,
                "max_drawdown": 0,
                "max_drawdown_percent": 0,
                "total_pnl": 0,
            }
        )


@analytics_bp.route("/analytics/performance", methods=["GET"])
def get_performance_analytics():
    """Get comprehensive performance analytics"""
    try:
        from portfolio_analytics import PortfolioAnalytics

        analytics = PortfolioAnalytics()
        summary = analytics.get_performance_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Analytics error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/analytics/equity-curve", methods=["GET"])
def get_equity_curve():
    """Get equity curve data"""
    try:
        from portfolio_analytics import PortfolioAnalytics

        days = int(request.args.get("days", 30))
        analytics = PortfolioAnalytics()
        curve = analytics.get_equity_curve(days=days)
        return jsonify({"equity_curve": curve})
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Equity curve error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
