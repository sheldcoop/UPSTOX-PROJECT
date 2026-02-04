#!/usr/bin/env python3
"""Webhook Blueprint"""

from flask import Blueprint, jsonify, g, request
import logging

from scripts.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

webhook_bp = Blueprint("webhook", __name__, url_prefix="")


@webhook_bp.route("/webhook/upstox", methods=["POST"])
@webhook_bp.route("/api/webhook/upstox", methods=["POST"])
def upstox_webhook():
    try:
        raw_body = request.get_data()
        service = WebhookService()
        result = service.receive(raw_body, request.headers)
        return jsonify(result)
    except ValueError as e:
        logger.error(f"[TraceID: {g.trace_id}] Webhook signature failed: {e}")
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 401
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Webhook failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
