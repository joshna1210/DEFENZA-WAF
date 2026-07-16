from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TrafficIngest(BaseModel):
    """Payload the proxy sends to the backend for every request it forwards."""
    ip: str
    method: str
    path: str
    query_string: str = ""
    headers: dict = Field(default_factory=dict)
    body_preview: str = ""
    user_agent: str = ""
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    blocked: bool = False
    block_reason: Optional[str] = None


class TrafficOut(BaseModel):
    id: str
    timestamp: datetime
    ip: str
    method: str
    path: str
    status_code: Optional[int]
    response_time_ms: Optional[float]
    blocked: bool
    block_reason: Optional[str]
    risk_score: float
    risk_level: str
    analyzed: bool


class TrafficListResponse(BaseModel):
    total: int
    items: list[TrafficOut]
