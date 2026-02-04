#!/usr/bin/env python3
"""
WebSocket Feed Blueprint
Handles WebSocket feed authorization
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

websocket_bp = Blueprint("websocket", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@websocket_bp.route("/feed/portfolio-stream-feed/authorize", methods=["GET"])
def authorize_portfolio_stream():
    """
    Get WebSocket authorization for portfolio stream feed

    This endpoint returns:
    - Authorized WebSocket URL
    - Access token for WebSocket connection
    - Connection configuration

    The WebSocket connection allows real-time updates for:
    - Portfolio positions
    - Order updates
    - Trade executions
    """
    try:
        from scripts.services.feed_service import FeedService

        logger.info(f"[TraceID: {g.trace_id}] WebSocket feed authorization request")

        service = FeedService()
        update_types = request.args.get("update_types")
        auth_data = service.authorize_portfolio_stream(update_types=update_types)
        access_token = service.auth_manager.get_valid_token()

        logger.debug(
            f"[TraceID: {g.trace_id}] Portfolio stream auth: update_types={update_types}, "
            f"keys={list(auth_data.keys()) if isinstance(auth_data, dict) else type(auth_data)}"
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "authorized_redirect_uri": auth_data.get("authorized_redirect_uri"),
                    "websocket_url": auth_data.get(
                        "authorized_redirect_uri"
                    ),  # Alias for clarity
                    "access_token": access_token,
                    "instructions": {
                        "1": "Use the websocket_url to establish WebSocket connection",
                        "2": "Send access_token in connection parameters",
                        "3": "Subscribe to portfolio stream for real-time updates",
                        "4": "See /docs/WEBSOCKET_IMPLEMENTATION_PLAN.md for details",
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] WebSocket authorization failed: {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@websocket_bp.route("/feed/market-data-feed/authorize", methods=["GET"])
def authorize_market_data_feed():
    """
    Get WebSocket authorization for market data feed

    This endpoint returns authorization for WebSocket connection to stream:
    - Live market quotes
    - Order book updates
    - Option chain updates
    """
    try:
        from scripts.services.feed_service import FeedService

        logger.info(
            f"[TraceID: {g.trace_id}] Market data WebSocket authorization request"
        )

        service = FeedService()
        auth_data = service.authorize_market_data_feed()
        access_token = service.auth_manager.get_valid_token()

        logger.debug(
            f"[TraceID: {g.trace_id}] Market data auth: "
            f"keys={list(auth_data.keys()) if isinstance(auth_data, dict) else type(auth_data)}"
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "authorized_redirect_uri": auth_data.get("authorized_redirect_uri"),
                    "websocket_url": auth_data.get("authorized_redirect_uri"),
                    "access_token": access_token,
                    "instructions": {
                        "1": "Use the websocket_url for market data WebSocket connection",
                        "2": "Subscribe to specific instruments for real-time quotes",
                        "3": "See WebSocket documentation for subscription format",
                    },
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Market data WebSocket authorization failed: {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
