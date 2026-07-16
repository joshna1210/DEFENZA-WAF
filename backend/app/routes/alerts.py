from fastapi import APIRouter, Depends
from app.services import alert_service
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    limit: int = 50,
    unacknowledged_only: bool = True,
    user: dict = Depends(require_role("admin", "soc_analyst")),
):
    return await alert_service.list_alerts(limit, unacknowledged_only)
