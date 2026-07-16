from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnalysisOut(BaseModel):
    id: str
    traffic_id: str
    timestamp: datetime
    engine: str
    matched_rules: list[str]
    matched_keywords: list[str]
    ml_confidence: Optional[float]
    risk_score: float
    risk_level: str
    category: str


class AnalyzeRequest(BaseModel):
    """Ad-hoc analysis of a raw payload, useful for testing the pipeline
    from the dashboard without a live request."""
    method: str = "GET"
    path: str = "/"
    query_string: str = ""
    body: str = ""
    headers: dict = {}
