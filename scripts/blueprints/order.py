#!/usr/bin/env python3
"""
Order Placement Blueprint
Handles order placement and modification endpoints
"""

from flask import Blueprint, jsonify, g, request
import logging

order_bp = Blueprint("order", __name__, url_prefix="/api/order")

logger = logging.getLogger(__name__)


@order_bp.route("/place", methods=["POST"])
def place_upstox_order():
    """Place order via Upstox"""
    try:
        from services import OrderService

        data = request.json
        required = ["symbol", "quantity", "order_type", "transaction_type"]
        if not all(k in data for k in required):
            return jsonify({"error": f"Missing required fields: {required}"}), 400

        manager = OrderService()
        result = manager.place_order(
            symbol=data["symbol"],
            quantity=data["quantity"],
            order_type=data["order_type"],
            transaction_type=data["transaction_type"],
            price=data.get("price"),
            trigger_price=data.get("trigger_price"),
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Place order error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@order_bp.route("/cancel/<order_id>", methods=["DELETE"])
def cancel_upstox_order(order_id):
    """Cancel order via Upstox"""
    try:
        from services import OrderService

        manager = OrderService()
        result = manager.cancel_order(order_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Cancel order error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@order_bp.route("/modify/<order_id>", methods=["PUT"])
def modify_order(order_id):
    """Modify order via Upstox"""
    try:
        from services import OrderService

        data = request.json
        manager = OrderService()
        result = manager.modify_order(
            order_id=order_id,
            quantity=data.get("quantity"),
            price=data.get("price"),
            trigger_price=data.get("trigger_price"),
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Modify order error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@order_bp.route("/status/<order_id>", methods=["GET"])
def get_order_status(order_id):
    """Get order status from Upstox"""
    try:
        from services import OrderService

        manager = OrderService()
        status = manager.get_order_status(order_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Order status error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
