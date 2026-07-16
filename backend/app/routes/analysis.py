from fastapi import APIRouter, Depends
from app.schemas.analysis_schema import AnalyzeRequest
from app.services import analysis_service
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/test")
async def analyze_ad_hoc(
    payload: AnalyzeRequest,
    user: dict = Depends(require_role("admin", "soc_analyst")),
):
    """Run the analysis pipeline against an arbitrary payload without
    needing live proxy traffic — useful for testing rules from the
    dashboard."""
    return await analysis_service.analyze_payload(
        payload.method, payload.path, payload.query_string, payload.body
    )
