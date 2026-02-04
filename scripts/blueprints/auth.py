#!/usr/bin/env python3
"""
Authentication Blueprint
Handles authentication-related endpoints including logout
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@auth_bp.route("/logout", methods=["DELETE"])
def logout():
    """
    Logout user and revoke access token

    This endpoint:
    1. Revokes the access token with Upstox
    2. Marks the token as inactive in database
    3. Clears any session data
    """
    try:
        from scripts.services.identity_service import IdentityService

        logger.info(f"[TraceID: {g.trace_id}] Logout request")

        identity_service = IdentityService()
        result = identity_service.logout(trace_id=g.trace_id)

        if result.get("message") == "No active session to logout":
            logger.warning(f"[TraceID: {g.trace_id}] No active token to logout")
            return jsonify(
                {
                    "success": True,
                    "message": "No active session to logout",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        logger.info(
            f"[TraceID: {g.trace_id}] Logout complete - {result.get('tokens_revoked', 0)} tokens deactivated"
        )

        return jsonify(
            {
                "success": True,
                "message": "Logged out successfully",
                "tokens_revoked": result.get("tokens_revoked", 0),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Logout failed: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500


@auth_bp.route("/auth/status", methods=["GET"])
def auth_status():
    """
    Check authentication status

    Returns:
        - is_authenticated: Boolean
        - user_id: User ID if authenticated
        - token_expires_at: Token expiry timestamp
    """
    try:
        from scripts.services.identity_service import IdentityService

        logger.debug(f"[TraceID: {g.trace_id}] Auth status check")

        identity_service = IdentityService()
        status = identity_service.auth_status()

        if status.get("is_authenticated"):
            return jsonify(
                {
                    "is_authenticated": True,
                    "user_id": status.get("user_id"),
                    "token_expires_at": datetime.fromtimestamp(
                        status.get("token_expires_at")
                    ).isoformat(),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return jsonify(
            {
                "is_authenticated": False,
                "message": "No active authentication",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(
            f"[TraceID: {g.trace_id}] Auth status check failed: {e}", exc_info=True
        )
        return jsonify({"error": str(e), "trace_id": g.trace_id}), 500
