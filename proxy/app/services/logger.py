"""
DEFENZA Backend Communication Service.

This module handles communication between the
reverse proxy and the DEFENZA backend.

The proxy does NOT load the ML models directly.

Instead:

    PROXY
       |
       | HTTP
       v
    BACKEND
       |
       +--> DistilBERT
       |
       +--> XGBoost
       |
       +--> Fusion Engine
       |
       +--> Risk Score
       |
       +--> Policy
"""


import os

import httpx


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)

INTERNAL_API_KEY = os.getenv(
    "DEFENZA_INTERNAL_API_KEY",
    "defenza-internal-change-this-key",
)


# ============================================================
# HTTP CLIENT
# ============================================================

_client = httpx.AsyncClient(
    timeout=10.0,
)


# ============================================================
# TRAFFIC LOGGING
# ============================================================

async def log_to_backend(event: dict):
    """
    Send traffic information to the DEFENZA backend.

    This function is intentionally fail-safe.

    If the backend is unavailable, the proxy should
    continue operating instead of crashing.
    """

    try:

        response = await _client.post(
            f"{BACKEND_URL}/api/traffic/ingest",
            json=event,
            headers={
                "X-DEFENZA-INTERNAL-KEY": INTERNAL_API_KEY,
            },
        )

        response.raise_for_status()

    except Exception as exc:

        print(
            "DEFENZA traffic logging unavailable:",
            exc,
        )


# ============================================================
# AI ANALYSIS
# ============================================================

async def analyze_with_backend(
    method: str,
    path: str,
    query_string: str,
    body: str,
):
    """
    Send a request to the DEFENZA backend AI analysis endpoint.

    Backend performs:

        DistilBERT
            +
        XGBoost
            |
        Fusion Engine
            |
        Risk Score
            |
        Policy

    Returns:
        dict -> AI analysis result

    Returns:
        None -> backend unavailable
    """

    payload = {
        "method": method,
        "path": path,
        "query_string": query_string,
        "body": body,
        "headers": {},
    }

    try:

        response = await _client.post(
            f"{BACKEND_URL}/api/analysis/proxy",
            json=payload,
            headers={
                "X-DEFENZA-INTERNAL-KEY": INTERNAL_API_KEY,
            },
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:

        print(
            "DEFENZA backend analysis unavailable:",
            exc,
        )

        return None