#!/usr/bin/env python3
"""
Market Information Blueprint
Handles market status, holidays, timings endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime, date
import logging

market_info_bp = Blueprint("market_info", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@market_info_bp.route("/market/status/<exchange>", methods=["GET"])
@market_info_bp.route("/market/status", methods=["GET"])
def get_market_status(exchange=None):
    """
    Get market status (open/closed)

    Args:
        exchange: Exchange code (NSE, BSE, etc.) - optional

    Query params:
        segment: Market segment (EQ, FO, etc.)
    """
    try:
        from scripts.market_info_service import MarketInfoService

        segment = request.args.get("segment")

        logger.info(
            f"[TraceID: {g.trace_id}] Market status request - exchange: {exchange}, segment: {segment}"
        )

        service = MarketInfoService()
        status = service.get_market_status(exchange=exchange, segment=segment)

        return jsonify(
            {"success": True, "data": status, "timestamp": datetime.now().isoformat()}
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Market status failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@market_info_bp.route("/market/holidays", methods=["GET"])
def get_market_holidays():
    """
    Get market holiday calendar

    Query params:
        year: Year (default: current year)
        exchange: Exchange code (NSE, BSE, etc.)
    """
    try:
        from scripts.market_info_service import MarketInfoService

        year = request.args.get("year", type=int)
        exchange = request.args.get("exchange")

        logger.info(
            f"[TraceID: {g.trace_id}] Holidays request - year: {year}, exchange: {exchange}"
        )

        service = MarketInfoService()
        holidays = service.get_market_holidays(year=year, exchange=exchange)

        return jsonify(
            {
                "success": True,
                "data": holidays,
                "count": len(holidays),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Holidays request failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@market_info_bp.route("/market/holidays/<date_str>", methods=["GET"])
def get_holiday_for_date(date_str):
    """
    Check if a specific date is a market holiday

    Args:
        date_str: Date in YYYY-MM-DD format
    """
    try:
        from scripts.market_info_service import MarketInfoService

        logger.info(f"[TraceID: {g.trace_id}] Holiday check for date: {date_str}")

        # Parse date
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        service = MarketInfoService()
        is_holiday = service.is_holiday(check_date=check_date)

        # Get holiday details if it is a holiday
        holiday_info = None
        if is_holiday:
            holidays = service.get_market_holidays(year=check_date.year)
            for h in holidays:
                if "date" in h and h["date"] == date_str:
                    holiday_info = h
                    break

        return jsonify(
            {
                "success": True,
                "date": date_str,
                "is_holiday": is_holiday,
                "holiday_info": holiday_info,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except ValueError as e:
        logger.error(f"[TraceID: {g.trace_id}] Invalid date format: {e}")
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Holiday check failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@market_info_bp.route("/market/timings/<date_str>", methods=["GET"])
@market_info_bp.route("/market/timings", methods=["GET"])
def get_market_timings(date_str=None):
    """
    Get market timings for a specific date or current date

    Args:
        date_str: Date in YYYY-MM-DD format (optional)

    Query params:
        exchange: Exchange code (NSE, BSE, etc.)
        segment: Market segment (EQ, FO, etc.)
    """
    try:
        from scripts.market_info_service import MarketInfoService

        exchange = request.args.get("exchange")
        segment = request.args.get("segment")

        logger.info(
            f"[TraceID: {g.trace_id}] Market timings request - date: {date_str}, exchange: {exchange}, segment: {segment}"
        )

        service = MarketInfoService()
        timings = service.get_market_timings(exchange=exchange, segment=segment)

        return jsonify(
            {
                "success": True,
                "date": date_str or datetime.now().strftime("%Y-%m-%d"),
                "data": timings,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Timings request failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
