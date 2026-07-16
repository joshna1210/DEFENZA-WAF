from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.settings import settings
from app.config.database import ensure_indexes
from app.middlewares.logging_middleware import log_requests
from app.services import blockchain_service
from app.routes import auth, traffic, analysis, reports, vulnerability, blockchain, alerts

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    scheduler.add_job(
        blockchain_service.run_batch_job,
        "interval",
        seconds=settings.BATCH_LOG_INTERVAL_SECONDS,
        id="blockchain_batch_job",
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="AI-WAF Blockchain Backend",
    description="Reverse-proxy-fed traffic analysis, ML risk scoring, IP monitoring, "
                 "vulnerability reporting, and blockchain-batched audit logging.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(log_requests)

app.include_router(auth.router)
app.include_router(traffic.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(vulnerability.router)
app.include_router(blockchain.router)
app.include_router(alerts.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "ai-waf-backend"}


@app.get("/health")
async def health():
    return {"status": "healthy", "ml_enabled": settings.ML_ENABLED, "blockchain_enabled": settings.BLOCKCHAIN_ENABLED}
