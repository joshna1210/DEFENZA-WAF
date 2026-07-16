import httpx
import os

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:3000")

_client = httpx.AsyncClient(timeout=15.0)


async def forward(method: str, path: str, headers: dict, body: bytes, params: dict):
    url = f"{TARGET_URL.rstrip('/')}{path}"
    # Drop hop-by-hop headers that shouldn't be forwarded as-is
    clean_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in ("host", "content-length", "connection")
    }
    response = await _client.request(
        method, url, headers=clean_headers, content=body, params=params
    )
    return response
