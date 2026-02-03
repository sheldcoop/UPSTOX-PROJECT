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
        from scripts.auth_manager import AuthManager
        import requests

        logger.info(f"[TraceID: {g.trace_id}] Logout request")

        # Get current token
        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()

        if not token:
            logger.warning(f"[TraceID: {g.trace_id}] No active token to logout")
            return jsonify(
                {
                    "success": True,
                    "message": "No active session to logout",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Call Upstox logout endpoint to revoke token
        url = "https://api.upstox.com/v2/logout"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code in [200, 204]:
                logger.info(
                    f"[TraceID: {g.trace_id}] Token revoked successfully with Upstox"
                )
            else:
                logger.warning(
                    f"[TraceID: {g.trace_id}] Upstox logout returned {response.status_code}"
                )
        except Exception as api_error:
            logger.warning(
                f"[TraceID: {g.trace_id}] Failed to revoke token with Upstox: {api_error}"
            )
            # Continue with local cleanup even if API call fails

        # Mark token as inactive in local database
        import sqlite3

        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE auth_tokens 
            SET is_active = 0, updated_at = strftime('%s', 'now')
            WHERE is_active = 1
        """
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(
            f"[TraceID: {g.trace_id}] Logout complete - {rows_affected} tokens deactivated"
        )

        return jsonify(
            {
                "success": True,
                "message": "Logged out successfully",
                "tokens_revoked": rows_affected,
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
        from scripts.auth_manager import AuthManager

        logger.debug(f"[TraceID: {g.trace_id}] Auth status check")

        auth_manager = AuthManager()
        token = auth_manager.get_valid_token()

        if token:
            # Get token details from database
            import sqlite3

            conn = sqlite3.connect(auth_manager.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT user_id, expires_at 
                FROM auth_tokens 
                WHERE is_active = 1 
                LIMIT 1
            """
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return jsonify(
                    {
                        "is_authenticated": True,
                        "user_id": row[0],
                        "token_expires_at": datetime.fromtimestamp(row[1]).isoformat(),
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
