"""Centralized configuration loader for trading.yaml"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any, Dict

import yaml


_ENV_PATTERN = re.compile(r"\$\{([^:}]+)(:-([^}]*))?\}")


def _expand_env(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(3) or ""
        return os.getenv(var_name, default)

    return _ENV_PATTERN.sub(_replace, value)


def _expand_tree(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _expand_tree(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_expand_tree(v) for v in data]
    return _expand_env(data)


@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "trading.yaml",
    )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    return _expand_tree(config)


def get_api_base_url() -> str:
    config = get_config()
    return config.get("api", {}).get("base_url", "https://api.upstox.com/v2")


def get_api_base_url_v3() -> str:
    config = get_config()
    base_v3 = config.get("api", {}).get("base_url_v3")
    if base_v3:
        return base_v3
    return get_api_base_url().replace("/v2", "/v3")


def get_api_timeout() -> int:
    config = get_config()
    return int(config.get("api", {}).get("timeout", 30))


def get_min_request_interval() -> float:
    config = get_config()
    return float(config.get("api", {}).get("min_request_interval", 0.1))


def get_rate_limit_wait_seconds() -> int:
    config = get_config()
    return int(config.get("error_handling", {}).get("rate_limit_wait_seconds", 60))