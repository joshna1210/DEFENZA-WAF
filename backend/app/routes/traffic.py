from fastapi import APIRouter, Depends, HTTPException
from app.schemas.traffic_schema import TrafficIngest, TrafficListResponse
from app.services import traffic_service
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.post("/ingest")
async def ingest_traffic(event: TrafficIngest):
    """Called by the proxy for every request it forwards. Not user-facing —
    in production, protect this with a shared secret or internal network
    boundary rather than user JWTs."""
    traffic_id = await traffic_service.ingest(event)
    return {"traffic_id": traffic_id}


@router.get("", response_model=TrafficListResponse)
async def list_traffic(
    limit: int = 50,
    skip: int = 0,
    blocked_only: bool = False,
    user: dict = Depends(require_role("admin", "soc_analyst")),
):
    total, items = await traffic_service.list_traffic(limit, skip, blocked_only)
    return {"total": total, "items": items}


@router.get("/{traffic_id}")
async def get_traffic(traffic_id: str, user: dict = Depends(require_role("admin", "soc_analyst"))):
    doc = await traffic_service.get_traffic(traffic_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc
