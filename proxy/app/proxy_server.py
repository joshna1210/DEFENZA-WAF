"""
DEFENZA AI Reverse Proxy.

Request flow:

    CLIENT
       |
    FAST SCAN
       |
    AI ANALYSIS
       |
    DISTILBERT + XGBOOST
       |
    FUSION ENGINE
       |
    POLICY
       |
    ALLOW / BLOCK / MONITOR / RATE_LIMIT / CAPTCHA
       |
    TARGET APPLICATION
"""

import asyncio
import time

from fastapi import FastAPI, Request, Response

from app.handlers.request_handler import fast_scan
from app.services.forwarder import forward
from app.services.logger import (
    analyze_with_backend,
    log_to_backend,
)
from app.utils.parser import client_ip


# ============================================================
# DEFENZA PROXY APPLICATION
# ============================================================

app = FastAPI(
    title="DEFENZA AI Reverse Proxy",
    description="Intent-aware AI-powered Web Application Firewall",
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/_proxy_health")
async def health():
    return {
        "status": "healthy",
        "service": "defenza-reverse-proxy",
    }


# ============================================================
# MAIN PROXY
# ============================================================

@app.api_route(
    "/{full_path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
    ],
)
async def proxy(
    full_path: str,
    request: Request,
):
    start = time.time()

    # --------------------------------------------------------
    # REQUEST INFORMATION
    # --------------------------------------------------------

    ip = client_ip(request)

    body_bytes = await request.body()

    body_preview = body_bytes[:4096].decode(
        "utf-8",
        errors="replace",
    )

    query_string = str(request.url.query)

    path = f"/{full_path}"

    scan_payload = (
        f"{request.method} "
        f"{path} "
        f"{query_string} "
        f"{body_preview}"
    )

    # --------------------------------------------------------
    # STEP 1
    # FAST SYNCHRONOUS SCAN
    # --------------------------------------------------------

    blocked, reason = fast_scan(scan_payload)

    if blocked:

        response_time_ms = round(
            (time.time() - start) * 1000,
            2,
        )

        # Log asynchronously so blocking remains fast
        asyncio.create_task(
            log_to_backend(
                {
                    "ip": ip,
                    "method": request.method,
                    "path": path,
                    "query_string": query_string,
                    "headers": dict(request.headers),
                    "body_preview": body_preview,
                    "user_agent": request.headers.get(
                        "user-agent",
                        "",
                    ),
                    "status_code": 403,
                    "response_time_ms": response_time_ms,
                    "blocked": True,
                    "block_reason": reason,
                }
            )
        )

        return Response(
            content=(
                '{"error":"Request blocked by WAF",'
                '"category":"%s"}'
                % reason
            ),
            status_code=403,
            media_type="application/json",
        )

    # --------------------------------------------------------
    # STEP 2
    # AI ANALYSIS
    #
    # Proxy sends the request to the backend.
    #
    # Backend:
    #   DistilBERT
    #       +
    #   XGBoost
    #       ↓
    #   Fusion Engine
    #       ↓
    #   Risk Score
    #       ↓
    #   Policy
    # --------------------------------------------------------

    analysis = await analyze_with_backend(
        method=request.method,
        path=path,
        query_string=query_string,
        body=body_preview,
    )

    # --------------------------------------------------------
    # STEP 3
    # AI POLICY ENFORCEMENT
    # --------------------------------------------------------

    if analysis is not None:

        policy = str(
            analysis.get(
                "policy",
                "ALLOW",
            )
        ).upper()

        risk_level = str(
            analysis.get(
                "risk_level",
                "unknown",
            )
        ).lower()

        prediction = analysis.get(
            "prediction",
            "unknown",
        )

        risk_score = analysis.get(
            "risk_score_percentage",
            analysis.get(
                "risk_score",
                0,
            ),
        )

        # ----------------------------------------------------
        # CONSOLE OUTPUT
        # ----------------------------------------------------

        print()
        print("========== DEFENZA AI ==========")
        print(f"METHOD     : {request.method}")
        print(f"PATH       : {path}")
        print(f"PREDICTION : {prediction}")
        print(f"RISK       : {risk_score}")
        print(f"LEVEL      : {risk_level}")
        print(f"POLICY     : {policy}")
        print("================================")
        print()

        # ----------------------------------------------------
        # BLOCK
        # ----------------------------------------------------

        if policy == "BLOCK":

            response_time_ms = round(
                (time.time() - start) * 1000,
                2,
            )

            asyncio.create_task(
                log_to_backend(
                    {
                        "ip": ip,
                        "method": request.method,
                        "path": path,
                        "query_string": query_string,
                        "headers": dict(request.headers),
                        "body_preview": body_preview,
                        "user_agent": request.headers.get(
                            "user-agent",
                            "",
                        ),
                        "status_code": 403,
                        "response_time_ms": response_time_ms,
                        "blocked": True,
                        "block_reason": prediction,
                    }
                )
            )

            return Response(
                content=(
                    '{"error":"Request blocked by DEFENZA AI",'
                    '"category":"%s",'
                    '"risk_level":"%s",'
                    '"risk_score":%s}'
                    % (
                        prediction,
                        risk_level,
                        risk_score,
                    )
                ),
                status_code=403,
                media_type="application/json",
            )

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if policy == "RATE_LIMIT":

            print(
                "DEFENZA: RATE_LIMIT policy selected "
                "(rate limiter not yet enabled)"
            )

        # ----------------------------------------------------
        # CAPTCHA
        # ----------------------------------------------------

        elif policy == "CAPTCHA":

            print(
                "DEFENZA: CAPTCHA policy selected "
                "(CAPTCHA enforcement not yet enabled)"
            )

        # ----------------------------------------------------
        # MONITOR
        # ----------------------------------------------------

        elif policy == "MONITOR":

            print(
                "DEFENZA: MONITOR policy selected"
            )

        # ----------------------------------------------------
        # ALLOW
        # ----------------------------------------------------

        elif policy == "ALLOW":

            print(
                "DEFENZA: ALLOW policy selected"
            )

    else:

        # ----------------------------------------------------
        # AI FAILURE
        #
        # Fast scan already passed.
        # Therefore forward the request.
        # ----------------------------------------------------

        print(
            "DEFENZA AI unavailable. "
            "Fast scan passed; forwarding request."
        )

    # --------------------------------------------------------
    # STEP 4
    # FORWARD TO TARGET APPLICATION
    # --------------------------------------------------------

    upstream = await forward(
        request.method,
        path,
        dict(request.headers),
        body_bytes,
        dict(request.query_params),
    )

    response_time_ms = round(
        (time.time() - start) * 1000,
        2,
    )

    # --------------------------------------------------------
    # STEP 5
    # LOG TRAFFIC
    # --------------------------------------------------------

    asyncio.create_task(
        log_to_backend(
            {
                "ip": ip,
                "method": request.method,
                "path": path,
                "query_string": query_string,
                "headers": dict(request.headers),
                "body_preview": body_preview,
                "user_agent": request.headers.get(
                    "user-agent",
                    "",
                ),
                "status_code": upstream.status_code,
                "response_time_ms": response_time_ms,
                "blocked": False,
                "block_reason": None,
            }
        )
    )

    # --------------------------------------------------------
    # STEP 6
    # RETURN TARGET RESPONSE
    # --------------------------------------------------------

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={
            key: value
            for key, value in upstream.headers.items()
            if key.lower()
            not in (
                "content-encoding",
                "transfer-encoding",
                "content-length",
            )
        },
        media_type=upstream.headers.get(
            "content-type"
        ),
    )