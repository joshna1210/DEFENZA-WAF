"""
Orchestrates the three-layer analysis pipeline:
  1. rule_engine
  2. keyword_engine
  3. ml_engine

Adds Context-Aware Risk Scoring:
  • Sensitive endpoint bonus
  • HTTP method bonus
"""

from bson import ObjectId

from app.config.database import analysis_results, traffic_logs
from app.config.settings import settings
from app.services import rule_engine, keyword_engine, ml_engine
from app.utils.tokenizer import normalize_payload
from app.utils.helpers import now_utc, risk_level_from_score
from app.utils.logger import get_logger

logger = get_logger("analysis_service")


def combine_scores(
    rule_score: float,
    keyword_score: float,
    ml_confidence: float | None,
) -> float:
    """
    Original weighted scoring.
    """

    if ml_confidence is not None:
        weighted = (
            0.35 * rule_score
            + 0.15 * keyword_score
            + 0.50 * ml_confidence
        )
    else:
        weighted = (
            0.65 * rule_score
            + 0.35 * keyword_score
        )

    return round(min(1.0, max(weighted, rule_score)), 4)


def apply_context_risk(
    score: float,
    method: str,
    path: str,
) -> tuple[float, list[str]]:
    """
    Adds contextual bonuses to the score.
    """

    reasons = []

    path = path.lower()

    # Sensitive endpoint
    if any(endpoint in path for endpoint in settings.SENSITIVE_ENDPOINTS):
        score += settings.SENSITIVE_ENDPOINT_BONUS
        reasons.append("Sensitive Endpoint")

    # POST request
    if method.upper() == "POST":
        score += settings.POST_REQUEST_BONUS
        reasons.append("POST Request")

    # High-risk methods
    if method.upper() in ["DELETE", "PATCH"]:
        score += settings.HIGH_RISK_METHOD_BONUS
        reasons.append("High Risk HTTP Method")

    score = min(score, 1.0)

    return round(score, 4), reasons


async def analyze_payload(
    method: str,
    path: str,
    query_string: str,
    body: str,
) -> dict:

    payload = normalize_payload(
        method,
        path,
        query_string,
        body,
    )

    matched_rules, rule_score, top_category = rule_engine.scan(payload)

    matched_keywords, keyword_score = keyword_engine.scan(payload)

    ml_result = ml_engine.classify(payload)

    base_score = combine_scores(
        rule_score,
        keyword_score,
        ml_result["ml_confidence"],
    )

    final_score, context_reasons = apply_context_risk(
        base_score,
        method,
        path,
    )

    risk_level = risk_level_from_score(final_score)

    category = top_category

    if category == "benign" and matched_keywords:
        category = "anomaly"

    return {
        "matched_rules": matched_rules,
        "matched_keywords": matched_keywords,
        "ml_confidence": ml_result["ml_confidence"],
        "token_analysis": ml_result["token_analysis"],
        "engine": ml_result["engine"],
        "risk_score": final_score,
        "risk_level": risk_level,
        "category": category,
        "context_reasons": context_reasons,
    }


async def analyze_and_store(
    traffic_id: str,
    method: str,
    path: str,
    query_string: str,
    body: str,
) -> dict:

    result = await analyze_payload(
        method,
        path,
        query_string,
        body,
    )

    doc = {
        "traffic_id": ObjectId(traffic_id),
        "timestamp": now_utc(),
        **result,
    }

    await analysis_results().insert_one(doc)

    await traffic_logs().update_one(
        {"_id": ObjectId(traffic_id)},
        {
            "$set": {
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "analyzed": True,
            }
        },
    )

    return result