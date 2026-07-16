"""Helpers for pulling a normalized payload out of an incoming request,
used by the fast-layer rule scan that runs inline in the proxy."""


async def extract_body_preview(request, max_bytes: int = 4096) -> str:
    try:
        body = await request.body()
        return body[:max_bytes].decode("utf-8", errors="replace")
    except Exception:
        return ""


def client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
