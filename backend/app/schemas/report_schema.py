from pydantic import BaseModel
from datetime import datetime


class TrafficSummary(BaseModel):
    total_requests: int
    blocked_requests: int
    high_risk_requests: int
    unique_ips: int
    top_categories: dict[str, int]
    requests_over_time: list[dict]   # [{"bucket": "2026-07-11T10:00", "count": 12}]


class IpSummary(BaseModel):
    ip: str
    request_count: int
    blocked_count: int
    avg_risk_score: float
    last_seen: datetime
    country: str | None = None
    flagged: bool = False
