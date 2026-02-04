"""Shared utilities for building authorization headers."""

from typing import Dict


def build_bearer_headers(token: str, include_json: bool = True) -> Dict[str, str]:
    """Build standard headers for Bearer token auth."""
    headers: Dict[str, str] = {"Authorization": f"Bearer {token}"}
    if include_json:
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
    return headers
