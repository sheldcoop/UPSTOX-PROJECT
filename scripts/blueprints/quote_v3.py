#!/usr/bin/env python3
"""
Market Quote v3 Blueprint
Handles v3 market quote endpoints (LTP, OHLC, Option Greeks)
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

quote_v3_bp = Blueprint("quote_v3", __name__, url_prefix="/api/v3")

logger = logging.getLogger(__name__)


@quote_v3_bp.route("/market-quote/ltp", methods=["GET"])
def get_ltp_v3():
    """
    Get Last Traded Price (LTP) using v3 API
    
    Query params:
        symbol: Instrument key (e.g., "NSE_EQ|INE669E01016") - can be comma-separated for multiple
        
    Example:
        /api/v3/market-quote/ltp?symbol=NSE_EQ|INE669E01016
        /api/v3/market-quote/ltp?symbol=NSE_EQ|INE669E01016,NSE_EQ|INE009A01021
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests
        
        symbol = request.args.get("symbol")
        
        if not symbol:
            return jsonify({"error": "Symbol parameter required"}), 400
        
        logger.info(f"[TraceID: {g.trace_id}] LTP v3 request - symbol: {symbol}")
        
        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()
        
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Call Upstox v3 LTP API
        url = "https://api.upstox.com/v3/market-quote/ltp"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        params = {"symbol": symbol}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"[TraceID: {g.trace_id}] LTP v3 API returned {response.status_code}")
            return jsonify({"error": f"API error: {response.status_code}"}), response.status_code
            
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] LTP v3 failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@quote_v3_bp.route("/market-quote/ohlc", methods=["GET"])
def get_ohlc_v3():
    """
    Get OHLC data using v3 API
    
    Query params:
        symbol: Instrument key - can be comma-separated for multiple
        interval: Optional interval (1minute, 30minute, day, etc.)
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests
        
        symbol = request.args.get("symbol")
        interval = request.args.get("interval")
        
        if not symbol:
            return jsonify({"error": "Symbol parameter required"}), 400
        
        logger.info(f"[TraceID: {g.trace_id}] OHLC v3 request - symbol: {symbol}, interval: {interval}")
        
        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()
        
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Call Upstox v3 OHLC API
        url = "https://api.upstox.com/v3/market-quote/ohlc"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        params = {"symbol": symbol}
        if interval:
            params["interval"] = interval
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"[TraceID: {g.trace_id}] OHLC v3 API returned {response.status_code}")
            return jsonify({"error": f"API error: {response.status_code}"}), response.status_code
            
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] OHLC v3 failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@quote_v3_bp.route("/market-quote/option-greek", methods=["GET"])
def get_option_greeks_v3():
    """
    Get Option Greeks using v3 API
    
    Query params:
        symbol: Option instrument key - can be comma-separated for multiple options
        
    Returns Greeks: Delta, Gamma, Theta, Vega, Rho, IV
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests
        
        symbol = request.args.get("symbol")
        
        if not symbol:
            return jsonify({"error": "Symbol parameter required"}), 400
        
        logger.info(f"[TraceID: {g.trace_id}] Option Greeks v3 request - symbol: {symbol}")
        
        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()
        
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Call Upstox v3 Option Greeks API
        url = "https://api.upstox.com/v3/market-quote/option-greek"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        params = {"symbol": symbol}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"[TraceID: {g.trace_id}] Option Greeks v3 API returned {response.status_code}")
            return jsonify({"error": f"API error: {response.status_code}"}), response.status_code
            
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Option Greeks v3 failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
