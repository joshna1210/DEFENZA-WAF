"""
Reverse proxy: sits in front of the real application (TARGET_URL). For every
request it:
  1. Runs a fast, inline regex scan (request_handler.fast_scan) — this is the
     ONLY thing allowed to block synchronously, so it stays well under 5ms.
  2. Forwards the request to the target app (unless blocked).
  3. Fires an async log event to the backend for the full analysis pipeline
     (rules + keywords + optional ML) without adding latency to the response.
"""
import time
import asyncio
from fastapi import FastAPI, Request, Response

from app.handlers.request_handler import fast_scan
from app.services.forwarder import forward
from app.services.logger import log_to_backend
from app.utils.parser import extract_body_preview, client_ip

app = FastAPI(title="AI-WAF Reverse Proxy")


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
async def proxy(full_path: str, request: Request):
    start = time.time()
    ip = client_ip(request)
    body_bytes = await request.body()
    body_preview = body_bytes[:4096].decode("utf-8", errors="replace")
    query_string = str(request.url.query)

    scan_payload = f"{request.method} /{full_path} {query_string} {body_preview}"
    blocked, reason = fast_scan(scan_payload)

    status_code = None
    response_time_ms = None

    if blocked:
        status_code = 403
        response_body = {"error": "Request blocked by WAF", "category": reason}
        response_time_ms = round((time.time() - start) * 1000, 2)
        asyncio.create_task(
            log_to_backend(
                {
                    "ip": ip,
                    "method": request.method,
                    "path": f"/{full_path}",
                    "query_string": query_string,
                    "headers": dict(request.headers),
                    "body_preview": body_preview,
                    "user_agent": request.headers.get("user-agent", ""),
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                    "blocked": True,
                    "block_reason": reason,
                }
            )
        )
        return Response(content=str(response_body), status_code=403, media_type="application/json")

    upstream = await forward(
        request.method, f"/{full_path}", dict(request.headers), body_bytes, dict(request.query_params)
    )
    response_time_ms = round((time.time() - start) * 1000, 2)

    asyncio.create_task(
        log_to_backend(
            {
                "ip": ip,
                "method": request.method,
                "path": f"/{full_path}",
                "query_string": query_string,
                "headers": dict(request.headers),
                "body_preview": body_preview,
                "user_agent": request.headers.get("user-agent", ""),
                "status_code": upstream.status_code,
                "response_time_ms": response_time_ms,
                "blocked": False,
                "block_reason": None,
            }
        )
    )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={k: v for k, v in upstream.headers.items() if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")},
    )


@app.get("/_proxy_health")
async def health():
    return {"status": "healthy"}