#!/usr/bin/env python3
"""
Historical Data v3 Blueprint
Handles v3 historical candle endpoints including intraday
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime, timedelta
import logging

historical_v3_bp = Blueprint("historical_v3", __name__, url_prefix="/api/v3")

logger = logging.getLogger(__name__)


@historical_v3_bp.route(
    "/historical-candle/<path:instrument_key>/<interval>/<count>/<to_date>/<from_date>",
    methods=["GET"],
)
@historical_v3_bp.route(
    "/historical-candle/<path:instrument_key>/<interval>/<count>/<to_date>",
    methods=["GET"],
)
def get_historical_candle_v3(instrument_key, interval, count, to_date, from_date=None):
    """
    Get historical candle data using v3 API with count parameter

    Args:
        instrument_key: Instrument key (e.g., NSE_EQ|INE669E01016)
        interval: minutes/1, minutes/30, hours/1, days/1, etc.
        count: Number of candles to fetch
        to_date: End date (YYYY-MM-DD)
        from_date: Start date (optional, YYYY-MM-DD)

    Example:
        /api/v3/historical-candle/NSE_EQ|INE669E01016/days/1/100/2024-01-31/2024-01-01
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests

        logger.info(
            f"[TraceID: {g.trace_id}] Historical v3 request - {instrument_key}, {interval}, count: {count}"
        )

        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()

        if not token:
            return jsonify({"error": "Not authenticated"}), 401

        # Build URL path (URL encode instrument_key)
        from urllib.parse import quote

        encoded_key = quote(instrument_key, safe="")

        if from_date:
            url = f"https://api.upstox.com/v3/historical-candle/{encoded_key}/{interval}/{count}/{to_date}/{from_date}"
        else:
            url = f"https://api.upstox.com/v3/historical-candle/{encoded_key}/{interval}/{count}/{to_date}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            candles = data.get("data", {}).get("candles", [])

            return jsonify(
                {
                    "success": True,
                    "instrument_key": instrument_key,
                    "interval": interval,
                    "count": len(candles),
                    "data": data.get("data", {}),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            logger.warning(
                f"[TraceID: {g.trace_id}] Historical v3 API returned {response.status_code}"
            )
            return (
                jsonify({"error": f"API error: {response.status_code}"}),
                response.status_code,
            )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Historical v3 failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@historical_v3_bp.route(
    "/historical-candle/intraday/<path:instrument_key>/<interval>/<count>",
    methods=["GET"],
)
def get_intraday_candle_v3(instrument_key, interval, count):
    """
    Get intraday candle data using v3 API

    Args:
        instrument_key: Instrument key
        interval: minutes/1, minutes/5, minutes/15, minutes/30, hours/1
        count: Number of candles to fetch

    Example:
        /api/v3/historical-candle/intraday/NSE_EQ|INE669E01016/minutes/15/100
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests

        logger.info(
            f"[TraceID: {g.trace_id}] Intraday v3 request - {instrument_key}, {interval}, count: {count}"
        )

        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()

        if not token:
            return jsonify({"error": "Not authenticated"}), 401

        # Build URL path
        from urllib.parse import quote

        encoded_key = quote(instrument_key, safe="")

        url = f"https://api.upstox.com/v3/historical-candle/intraday/{encoded_key}/{interval}/{count}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            candles = data.get("data", {}).get("candles", [])

            return jsonify(
                {
                    "success": True,
                    "instrument_key": instrument_key,
                    "interval": interval,
                    "count": len(candles),
                    "data": data.get("data", {}),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            logger.warning(
                f"[TraceID: {g.trace_id}] Intraday v3 API returned {response.status_code}"
            )
            return (
                jsonify({"error": f"API error: {response.status_code}"}),
                response.status_code,
            )

    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Intraday v3 failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
