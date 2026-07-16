"""Sends traffic events to the backend's ingestion endpoint. Fire-and-forget
with a short timeout — if the backend is briefly down, the proxy still
forwards traffic (fail-open on logging, fail-closed only on the fast-layer
block decision)."""
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

_client = httpx.AsyncClient(timeout=3.0)


async def log_to_backend(event: dict):
    try:
        await _client.post(f"{BACKEND_URL}/api/traffic/ingest", json=event)
    except Exception:
        # Never let logging failures break the proxy's primary job.
        pass
