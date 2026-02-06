"""Shared mixin for building authenticated JSON headers."""

from typing import Dict

from backend.utils.logging.error_handler import UpstoxAPIError


class AuthHeadersMixin:
    """Mixin that provides a standard JSON auth header builder."""

    def _get_headers(self) -> Dict[str, str]:
        token = self.auth_manager.get_valid_token()
        if not token:
            raise UpstoxAPIError("Failed to get valid access token")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


class OptionalAuthHeadersMixin:
    """Mixin that provides auth headers if token is available, else empty dict."""

    def _get_headers(self) -> Dict[str, str]:
        if not hasattr(self, 'auth_manager'):
            return {}
            
        token = self.auth_manager.get_valid_token()
        if not token:
            return {}

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
