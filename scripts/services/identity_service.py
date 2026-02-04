"""Identity Service - Auth, profile, balance, logout"""

from typing import Dict, Any, Optional
import sqlite3
import requests

from base_fetcher import UpstoxFetcher
from scripts.auth_helper import auth
from scripts.config_loader import get_api_base_url
from scripts.logger_config import get_logger

logger = get_logger(__name__)


class IdentityService(UpstoxFetcher):
    """Handles authentication/session and user identity operations"""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        db_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(base_url=base_url or get_api_base_url())
        self.session = session or self.session
        self.auth = auth
        self.db_path = db_path

    def get_authorization_url(self) -> str:
        return self.auth.get_auth_url()

    def exchange_code_for_token(self, auth_code: str) -> Dict[str, Any]:
        return self.auth.exchange_code_for_token(auth_code)

    def save_token(self, user_id: str, token_data: Dict[str, Any]):
        return self.auth.save_token(user_id, token_data)

    def get_access_token(self, user_id: str = "default") -> Optional[str]:
        return self.auth.get_token(user_id)

    def _get_headers(self, user_id: str = "default") -> Dict[str, str]:
        return self.auth.get_headers(user_id)

    def get_profile(self, user_id: str = "default") -> Dict[str, Any]:
        response = self.fetch("/user/profile")
        return response.get("data", {})

    def get_funds(self, user_id: str = "default") -> Dict[str, Any]:
        response = self.fetch("/user/get-funds-and-margin")
        return response.get("data", {})

    def get_balance(self, user_id: str = "default") -> float:
        funds = self.get_funds(user_id)
        equity = funds.get("equity", {})
        return float(equity.get("available_margin", 0.0))

    def auth_status(self) -> Dict[str, Any]:
        token = self.get_access_token()
        if not token:
            return {
                "is_authenticated": False,
                "message": "No active authentication",
            }

        conn = sqlite3.connect(self.db_path or "market_data.db")
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

        if not row:
            return {
                "is_authenticated": False,
                "message": "No active authentication",
            }

        return {
            "is_authenticated": True,
            "user_id": row[0],
            "token_expires_at": row[1],
        }

    def logout(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        token = self.get_access_token()

        if not token:
            return {
                "success": True,
                "message": "No active session to logout",
            }

        try:
            response = self.fetch("/logout", method="DELETE")
            if response:
                logger.info(
                    f"[TraceID: {trace_id}] Token revoked successfully with Upstox"
                )
        except Exception as api_error:
            logger.warning(
                f"[TraceID: {trace_id}] Failed to revoke token with Upstox: {api_error}"
            )

        conn = sqlite3.connect(self.db_path or "market_data.db")
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

        return {
            "success": True,
            "message": "Logged out successfully",
            "tokens_revoked": rows_affected,
        }
