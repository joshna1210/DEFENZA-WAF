from app.config.database import alerts
from app.utils.helpers import now_utc


async def raise_alert(traffic_id: str, ip: str, category: str, risk_score: float):
    await alerts().insert_one(
        {
            "timestamp": now_utc(),
            "traffic_id": traffic_id,
            "ip": ip,
            "category": category,
            "risk_score": risk_score,
            "acknowledged": False,
        }
    )


async def list_alerts(limit: int = 50, unacknowledged_only: bool = True):
    query = {"acknowledged": False} if unacknowledged_only else {}
    cursor = alerts().find(query).sort("timestamp", -1).limit(limit)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results
