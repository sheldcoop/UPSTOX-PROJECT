#!/usr/bin/env python3
"""
Charges Blueprint
Handles brokerage and margin calculation endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

charges_bp = Blueprint("charges", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@charges_bp.route("/charges/brokerage", methods=["GET"])
def calculate_brokerage():
    """
    Calculate brokerage charges for an order
    
    Query params:
        instrument_token: Instrument key (e.g., "NSE_EQ|INE669E01016")
        quantity: Order quantity
        product: Product type (D=Delivery/CNC, I=Intraday/MIS, M=Margin/NRML)
        transaction_type: BUY or SELL
        price: Order price
    """
    try:
        from scripts.auth_manager import AuthManager
        
        # Get query parameters
        instrument_token = request.args.get("instrument_token")
        quantity = request.args.get("quantity", type=int)
        price = request.args.get("price", type=float)
        transaction_type = request.args.get("transaction_type", "BUY")
        product = request.args.get("product", "D")
        
        logger.info(f"[TraceID: {g.trace_id}] Brokerage calculation - instrument: {instrument_token}, qty: {quantity}, price: {price}")
        
        # Validate required params
        if not all([instrument_token, quantity, price]):
            return jsonify({"error": "Missing required parameters: instrument_token, quantity, price"}), 400
        
        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()
        
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Initialize brokerage calculator
        from scripts.brokerage_calculator import BrokerageCalculator
        
        calculator = BrokerageCalculator(token)
        charges = calculator.calculate_charges(
            instrument_token=instrument_token,
            quantity=quantity,
            price=price,
            transaction_type=transaction_type,
            product=product
        )
        
        if charges:
            return jsonify({
                "success": True,
                "data": {
                    "charges": charges
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to calculate charges"}), 500
            
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Brokerage calculation failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@charges_bp.route("/charges/margin", methods=["GET"])
def calculate_margin():
    """
    Calculate margin requirements for an order
    
    Query params:
        instrument_token: Instrument key
        quantity: Order quantity
        transaction_type: BUY or SELL
        price: Order price (optional, for limit orders)
    """
    try:
        from scripts.auth_manager import AuthManager
        import requests
        
        # Get query parameters
        instrument_token = request.args.get("instrument_token")
        quantity = request.args.get("quantity", type=int)
        transaction_type = request.args.get("transaction_type", "BUY")
        price = request.args.get("price", type=float)
        
        logger.info(f"[TraceID: {g.trace_id}] Margin calculation - instrument: {instrument_token}, qty: {quantity}")
        
        # Validate required params
        if not all([instrument_token, quantity]):
            return jsonify({"error": "Missing required parameters: instrument_token, quantity"}), 400
        
        # Get access token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()
        
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        # Call Upstox margin API
        url = "https://api.upstox.com/v2/charges/margin"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        params = {
            "instrument_token": instrument_token,
            "quantity": quantity,
            "transaction_type": transaction_type.upper()
        }
        
        if price:
            params["price"] = price
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "success": True,
                "data": data.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })
        else:
            logger.warning(f"[TraceID: {g.trace_id}] Margin API returned {response.status_code}")
            return jsonify({"error": f"API error: {response.status_code}"}), response.status_code
            
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Margin calculation failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
