#!/usr/bin/env python3
"""GTT Orders Blueprint"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

from scripts.services.gtt_service import GTTService

logger = logging.getLogger(__name__)

gtt_bp = Blueprint("gtt", __name__, url_prefix="/api")


@gtt_bp.route("/gtt", methods=["GET"])
def get_gtt_orders():
    try:
        service = GTTService()
        orders = service.retrieve_all()
        return jsonify(orders)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] GTT retrieve failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@gtt_bp.route("/gtt", methods=["POST"])
def create_gtt_order():
    try:
        data = request.json or {}
        service = GTTService()
        result = service.create_gtt(data)
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] GTT create failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@gtt_bp.route("/gtt/<gtt_id>", methods=["PUT"])
def modify_gtt_order(gtt_id):
    try:
        data = request.json or {}
        data["gtt_id"] = gtt_id
        service = GTTService()
        result = service.modify_gtt(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] GTT modify failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@gtt_bp.route("/gtt/<gtt_id>", methods=["DELETE"])
def cancel_gtt_order(gtt_id):
    try:
        service = GTTService()
        result = service.cancel_gtt({"gtt_id": gtt_id})
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] GTT cancel failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
