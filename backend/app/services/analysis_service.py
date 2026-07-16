"""
Orchestrates the three-layer analysis pipeline:
  1. rule_engine   (fast, regex, sync)
  2. keyword_engine (fast, sync)
  3. ml_engine      (optional, slow, called async by the worker in traffic_service)

Combines their outputs into a single risk_score / risk_level / category and
persists the result to `analysis_results`.
"""
from datetime import datetime
from bson import ObjectId

from app.config.database import analysis_results, traffic_logs
from app.services import rule_engine, keyword_engine, ml_engine
from app.utils.tokenizer import normalize_payload
from app.utils.helpers import now_utc, risk_level_from_score
from app.utils.logger import get_logger

logger = get_logger("analysis_service")


def combine_scores(rule_score: float, keyword_score: float, ml_confidence: float | None) -> float:
    """Weighted combination. ML (when available) gets the most trust since it
    generalizes beyond known signatures; rules get the most weight when ML is
    off since they're the most precise signal we have.

    The rule engine only fires on high-precision signature matches (a
    literal `<script>` tag, `union select`, etc.), so a match there is never
    allowed to be diluted below its own confidence just because the other,
    lower-precision layers saw nothing — the final score is at least
    `rule_score`, with the weighted blend only able to push it higher."""
    if ml_confidence is not None:
        weighted = 0.35 * rule_score + 0.15 * keyword_score + 0.5 * ml_confidence
    else:
        weighted = 0.65 * rule_score + 0.35 * keyword_score
    return round(min(1.0, max(weighted, rule_score)), 4)


async def analyze_payload(method: str, path: str, query_string: str, body: str) -> dict:
    """Runs all layers on a raw payload and returns the combined result
    WITHOUT persisting anything. Used for both the async traffic pipeline
    and the ad-hoc /analysis/test endpoint."""
    payload = normalize_payload(method, path, query_string, body)

    matched_rules, rule_score, top_category = rule_engine.scan(payload)
    matched_keywords, keyword_score = keyword_engine.scan(payload)
    ml_result = ml_engine.classify(payload)

    final_score = combine_scores(rule_score, keyword_score, ml_result["ml_confidence"])
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
    }


async def analyze_and_store(traffic_id: str, method: str, path: str, query_string: str, body: str) -> dict:
    result = await analyze_payload(method, path, query_string, body)

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
