from datetime import timedelta
from app.config.database import traffic_logs, analysis_results
from app.utils.helpers import now_utc


async def traffic_summary(hours: int = 24) -> dict:
    since = now_utc() - timedelta(hours=hours)
    match = {"timestamp": {"$gte": since}}

    total = await traffic_logs().count_documents(match)
    blocked = await traffic_logs().count_documents({**match, "blocked": True})
    high_risk = await traffic_logs().count_documents(
        {**match, "risk_level": {"$in": ["high", "critical"]}}
    )
    unique_ips = len(await traffic_logs().distinct("ip", match))

    category_cursor = analysis_results().aggregate(
        [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
    )
    top_categories = {}
    async for doc in category_cursor:
        top_categories[doc["_id"]] = doc["count"]

    timeseries_cursor = traffic_logs().aggregate(
        [
            {"$match": match},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%dT%H:00", "date": "$timestamp"}
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
    )
    requests_over_time = []
    async for doc in timeseries_cursor:
        requests_over_time.append({"bucket": doc["_id"], "count": doc["count"]})

    return {
        "total_requests": total,
        "blocked_requests": blocked,
        "high_risk_requests": high_risk,
        "unique_ips": unique_ips,
        "top_categories": top_categories,
        "requests_over_time": requests_over_time,
    }
