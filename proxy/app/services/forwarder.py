import os
import httpx

TARGET_URL = os.getenv(
    "TARGET_URL",
    "http://host.docker.internal:5000"
)

_client = httpx.AsyncClient(timeout=15.0)


async def forward(method: str, path: str, headers: dict, body: bytes, params: dict):
    url = f"{TARGET_URL.rstrip('/')}{path}"

    clean_headers = {
        k: v
        for k, v in headers.items()
        if k.lower() not in ("host", "content-length", "connection")
    }

    response = await _client.request(
        method=method,
        url=url,
        headers=clean_headers,
        content=body,
        params=params,
        follow_redirects=True,
    )

    return response