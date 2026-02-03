#!/usr/bin/env python3
"""
Upstox Integration Blueprint
Handles live Upstox API endpoints
"""

from flask import Blueprint, jsonify, g, request
import logging

upstox_bp = Blueprint("upstox", __name__, url_prefix="/api/upstox")

logger = logging.getLogger(__name__)


@upstox_bp.route("/profile", methods=["GET"])
def get_upstox_profile():
    """Get user profile from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        api = UpstoxLiveAPI()
        profile = api.get_profile()
        return jsonify(profile)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Profile error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@upstox_bp.route("/holdings", methods=["GET"])
def get_upstox_holdings():
    """Get long-term holdings from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        api = UpstoxLiveAPI()
        holdings = api.get_holdings()
        return jsonify(holdings)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Holdings error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@upstox_bp.route("/positions", methods=["GET"])
def get_upstox_positions():
    """Get day/net positions from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        api = UpstoxLiveAPI()
        positions = api.get_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Positions error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@upstox_bp.route("/option-chain", methods=["GET"])
def get_upstox_option_chain():
    """Get live option chain from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        symbol = request.args.get("symbol", "NIFTY")
        expiry_date = request.args.get("expiry_date")

        api = UpstoxLiveAPI()
        chain = api.get_option_chain(symbol, expiry_date)
        return jsonify(chain)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Option chain error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@upstox_bp.route("/market-quote", methods=["GET"])
def get_upstox_market_quote():
    """Get real-time market quote from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        symbol = request.args.get("symbol")
        if not symbol:
            return jsonify({"error": "Symbol required"}), 400

        api = UpstoxLiveAPI()
        quote = api.get_market_quote(symbol)
        return jsonify(quote)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Market quote error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@upstox_bp.route("/funds", methods=["GET"])
def get_upstox_funds():
    """Get account funds/margin from Upstox"""
    try:
        from upstox_live_api import UpstoxLiveAPI

        api = UpstoxLiveAPI()
        funds = api.get_funds()
        return jsonify(funds)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Funds error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
