"""
Handles ingestion of a traffic event from the proxy: stores the log,
kicks off async analysis (fire-and-forget task, so the proxy is never
blocked waiting on it), and updates IP activity.
"""
import asyncio
from bson import ObjectId

from app.config.database import traffic_logs
from app.schemas.traffic_schema import TrafficIngest
from app.services import analysis_service, ip_monitor, alert_service
from app.utils.helpers import now_utc
from app.utils.logger import get_logger

logger = get_logger("traffic_service")


async def ingest(event: TrafficIngest) -> str:
    doc = {
        "timestamp": now_utc(),
        "ip": event.ip,
        "method": event.method,
        "path": event.path,
        "query_string": event.query_string,
        "headers": event.headers,
        "body_preview": event.body_preview[:2000],
        "user_agent": event.user_agent,
        "status_code": event.status_code,
        "response_time_ms": event.response_time_ms,
        "blocked": event.blocked,
        "block_reason": event.block_reason,
        "risk_score": 0.0,
        "risk_level": "low",
        "analyzed": False,
        "blockchain_batch_id": None,
    }
    result = await traffic_logs().insert_one(doc)
    traffic_id = str(result.inserted_id)

    # fire-and-forget async analysis so ingestion never blocks
    asyncio.create_task(_analyze_and_react(traffic_id, event))

    return traffic_id


async def _analyze_and_react(traffic_id: str, event: TrafficIngest):
    try:
        result = await analysis_service.analyze_and_store(
            traffic_id, event.method, event.path, event.query_string, event.body_preview
        )
        await ip_monitor.record_request(event.ip, event.blocked, result["risk_score"])

        if event.blocked or result["risk_level"] in ("high", "critical"):
            category = result["category"]
            if event.blocked and (category == "benign" or not category):
                category = event.block_reason or "security_violation"

            risk_score = result["risk_score"]
            if event.blocked and risk_score < 0.7:
                risk_score = 0.9

            await alert_service.raise_alert(
                traffic_id=traffic_id,
                ip=event.ip,
                category=category,
                risk_score=risk_score,
            )
    except Exception:
        logger.exception(f"Failed to analyze traffic_id={traffic_id}")


async def list_traffic(limit: int = 50, skip: int = 0, blocked_only: bool = False):
    query = {"blocked": True} if blocked_only else {}
    total = await traffic_logs().count_documents(query)
    cursor = traffic_logs().find(query).sort("timestamp", -1).skip(skip).limit(limit)
    items = []
    async for doc in cursor:
        items.append(_serialize(doc))
    return total, items


async def get_traffic(traffic_id: str):
    doc = await traffic_logs().find_one({"_id": ObjectId(traffic_id)})
    return _serialize(doc) if doc else None


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "timestamp": doc["timestamp"],
        "ip": doc["ip"],
        "method": doc["method"],
        "path": doc["path"],
        "status_code": doc.get("status_code"),
        "response_time_ms": doc.get("response_time_ms"),
        "blocked": doc.get("blocked", False),
        "block_reason": doc.get("block_reason"),
        "risk_score": doc.get("risk_score", 0.0),
        "risk_level": doc.get("risk_level", "low"),
        "analyzed": doc.get("analyzed", False),
    }
