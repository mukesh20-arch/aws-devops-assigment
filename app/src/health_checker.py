"""
Core health check logic for the API Health Monitoring System.

Given an ApiConfig, this module performs a simple HTTP request and
decides whether the API is UP or DOWN.
"""

import time
from typing import Optional, Tuple

import requests

from .models import ApiConfig


def check_api(config: ApiConfig) -> Tuple[str, Optional[int], Optional[int], Optional[str]]:
    """
    Execute a health check for a single API.

    Returns a tuple of:
    - state: "UP" or "DOWN"
    - status_code: HTTP status code if we got one
    - latency_ms: round-trip time in milliseconds
    - error: error message if something went wrong
    """
    if not config.enabled:
        # Treat disabled APIs as "UP" but skip any real work.
        return "UP", None, None, None

    timeout_seconds = config.timeout_ms / 1000.0

    method = config.method.upper()
    if method not in ("GET", "HEAD"):
        # To keep things simple we only support GET/HEAD in this project.
        method = "GET"

    start = time.time()
    try:
        response = requests.request(method, config.url, timeout=timeout_seconds)
        latency_ms = int((time.time() - start) * 1000)
        status_code = response.status_code

        if status_code in config.expected_status_codes:
            return "UP", status_code, latency_ms, None
        else:
            return "DOWN", status_code, latency_ms, f"Unexpected status code {status_code}"

    except requests.RequestException as exc:
        latency_ms = int((time.time() - start) * 1000)
        return "DOWN", None, latency_ms, str(exc)
