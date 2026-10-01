"""
Tracks per-IP request behavior: volume, blocked ratio, average risk, and
simple burst-based flagging (naive rate anomaly detection). GeoIP lookup is
stubbed behind GEOIP_ENABLED so the pipeline works offline by default.
"""
from datetime import timedelta, timezone
from app.config.database import ip_activity, traffic_logs
from app.utils.helpers import now_utc
from app.config.settings import settings

BURST_WINDOW_SECONDS = 60
BURST_REQUEST_THRESHOLD = 50   # requests from one IP within the window -> flagged


async def record_request(ip: str, blocked: bool, risk_score: float):
    now = now_utc()
    existing = await ip_activity().find_one({"ip": ip})

    if existing is None:
        await ip_activity().insert_one(
            {
                "ip": ip,
                "request_count": 1,
                "blocked_count": 1 if blocked else 0,
                "risk_score_sum": risk_score,
                "first_seen": now,
                "last_seen": now,
                "recent_timestamps": [now],
                "flagged": False,
                "country": await _geolocate(ip),
            }
        )
        return

    recent = [
        t for t in existing.get("recent_timestamps", [])
        if (now - (t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t)) < timedelta(seconds=BURST_WINDOW_SECONDS)
    ]
    recent.append(now)
    flagged = len(recent) >= BURST_REQUEST_THRESHOLD or existing.get("flagged", False)

    await ip_activity().update_one(
        {"ip": ip},
        {
            "$set": {
                "last_seen": now,
                "recent_timestamps": recent[-BURST_REQUEST_THRESHOLD:],
                "flagged": flagged,
            },
            "$inc": {
                "request_count": 1,
                "blocked_count": 1 if blocked else 0,
                "risk_score_sum": risk_score,
            },
        },
    )


async def _geolocate(ip: str) -> str | None:
    if not settings.GEOIP_ENABLED:
        return None
    # Plug in MaxMind GeoLite2 / ip-api.com here. Kept as a stub so the
    # pipeline has zero external dependency by default.
    return None


async def list_ips(limit: int = 100, flagged_only: bool = False):
    query = {"flagged": True} if flagged_only else {}
    cursor = ip_activity().find(query).sort("last_seen", -1).limit(limit)
    results = []
    async for doc in cursor:
        count = doc.get("request_count", 1)
        results.append(
            {
                "ip": doc["ip"],
                "request_count": count,
                "blocked_count": doc.get("blocked_count", 0),
                "avg_risk_score": round(doc.get("risk_score_sum", 0) / count, 4),
                "last_seen": doc["last_seen"],
                "country": doc.get("country"),
                "flagged": doc.get("flagged", False),
            }
        )
    return results

