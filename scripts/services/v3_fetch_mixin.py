"""Shared mixin for Upstox v3 HTTP fetch behavior."""

from typing import Dict, Any, Optional
import time

from scripts.config_loader import get_api_timeout


class V3FetcherMixin:
    """Mixin providing shared v3 fetch logic with retry and auth refresh."""

    def _fetch_v3(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retries: int = 2,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = f"{self._base_url_v3}/{endpoint.lstrip('/')}"
        timeout = timeout or get_api_timeout()

        for attempt in range(retries + 1):
            try:
                self._rate_limit()
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=data,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    return response.json()
                if response.status_code == 401 and attempt < retries:
                    self.auth._auth_manager.get_valid_token(force_refresh=True)
                    continue
                if response.status_code == 429 and attempt < retries:
                    time.sleep(2 ** attempt)
                    continue

                raise ValueError(f"HTTP {response.status_code}: {response.text}")
            except Exception:
                if attempt == retries:
                    raise

        raise ValueError("Failed to fetch v3 endpoint")
