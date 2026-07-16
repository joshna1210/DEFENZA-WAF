from fastapi import APIRouter, Depends
from app.services import report_service, ip_monitor
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
async def summary(hours: int = 24, user: dict = Depends(require_role("admin", "soc_analyst"))):
    return await report_service.traffic_summary(hours)


@router.get("/ips")
async def ip_list(
    limit: int = 100,
    flagged_only: bool = False,
    user: dict = Depends(require_role("admin", "soc_analyst")),
):
    return await ip_monitor.list_ips(limit, flagged_only)
