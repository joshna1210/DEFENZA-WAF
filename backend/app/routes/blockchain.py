from fastapi import APIRouter, Depends
from app.services import blockchain_service
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])


@router.get("/batches")
async def list_batches(limit: int = 50, user: dict = Depends(require_role("admin", "soc_analyst"))):
    return await blockchain_service.list_batches(limit)


@router.post("/run-batch-now")
async def run_batch_now(user: dict = Depends(require_role("admin"))):
    await blockchain_service.run_batch_job()
    return {"status": "batch job triggered"}
