from fastapi import APIRouter, Depends, Header, HTTPException

from app.config.settings import settings
from app.schemas.analysis_schema import AnalyzeRequest
from app.services import analysis_service
from app.middlewares.security_middleware import require_role


router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
)


# ============================================================
# ADMIN / SOC ANALYST ANALYSIS
# ============================================================

@router.post("/test")
async def analyze_ad_hoc(
    payload: AnalyzeRequest,
    user: dict = Depends(
        require_role(
            "admin",
            "soc_analyst",
        )
    ),
):
    """
    Manual analysis endpoint for authenticated
    administrators and SOC analysts.
    """

    return await analysis_service.analyze_payload(
        payload.method,
        payload.path,
        payload.query_string,
        payload.body,
    )


# ============================================================
# INTERNAL REVERSE-PROXY ANALYSIS
# ============================================================

@router.post("/proxy")
async def analyze_from_proxy(
    payload: AnalyzeRequest,
    x_defenza_internal_key: str | None = Header(
        default=None,
        alias="X-DEFENZA-INTERNAL-KEY",
    ),
):
    """
    Internal endpoint used by the DEFENZA reverse proxy.

    The proxy sends a request here before forwarding it
    to the target application.

    The endpoint runs:

        Rule Engine
             +
        Keyword Engine
             +
        DistilBERT
             +
        XGBoost
             ↓
        Fusion
             ↓
        Risk
             ↓
        Policy

    The endpoint is protected using an internal API key.
    """

    # --------------------------------------------------------
    # Verify internal proxy
    # --------------------------------------------------------

    if (
        not x_defenza_internal_key
        or x_defenza_internal_key
        != settings.INTERNAL_API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid internal proxy key",
        )

    # --------------------------------------------------------
    # Run complete DEFENZA analysis
    # --------------------------------------------------------

    result = await analysis_service.analyze_payload(
        payload.method,
        payload.path,
        payload.query_string,
        payload.body,
    )

    return result