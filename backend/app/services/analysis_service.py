"""
DEFENZA Analysis Service

Analysis pipeline:

    HTTP Request
        ↓
    Request Normalization
        ↓
    Rule Engine
        ↓
    Keyword Engine
        ↓
    DistilBERT + XGBoost Fusion
        ↓
    Context-Aware Risk
        ↓
    Final Risk
        ↓
    MongoDB + Dashboard

AI engine:
    DistilBERT 60%
    XGBoost    40%
"""

from bson import ObjectId

from app.config.database import analysis_results, traffic_logs
from app.config.settings import settings
from app.services import (
    rule_engine,
    keyword_engine,
    ml_engine,
)
from app.utils.tokenizer import normalize_payload
from app.utils.helpers import now_utc, risk_level_from_score
from app.utils.logger import get_logger


logger = get_logger("analysis_service")


# ============================================================
# LEGACY SCORE COMBINATION
# ============================================================

def combine_scores(
    rule_score: float,
    keyword_score: float,
    ml_confidence: float | None,
) -> float:
    """
    Legacy scoring method.

    Kept for backward compatibility with the existing
    rule/keyword pipeline.

    The new DEFENZA fusion risk score is preferred when
    the new ML engine returns a valid risk_score.
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

    return round(
        min(
            1.0,
            max(
                weighted,
                rule_score,
            ),
        ),
        4,
    )


# ============================================================
# CONTEXT-AWARE RISK
# ============================================================

def apply_context_risk(
    score: float,
    method: str,
    path: str,
) -> tuple[float, list[str]]:
    """
    Adds contextual bonuses to the normalized risk score.

    score:
        0.0 - 1.0

    Returns:
        final normalized score
        context reasons
    """

    reasons = []

    path = str(path or "").lower()

    # --------------------------------------------------------
    # Sensitive endpoint
    # --------------------------------------------------------

    if any(
        endpoint.lower() in path
        for endpoint in settings.SENSITIVE_ENDPOINTS
    ):

        score += settings.SENSITIVE_ENDPOINT_BONUS

        reasons.append(
            "Sensitive Endpoint"
        )

    # --------------------------------------------------------
    # POST request
    # --------------------------------------------------------

    if method.upper() == "POST":

        score += settings.POST_REQUEST_BONUS

        reasons.append(
            "POST Request"
        )

    # --------------------------------------------------------
    # High-risk HTTP methods
    # --------------------------------------------------------

    if method.upper() in [
        "DELETE",
        "PATCH",
    ]:

        score += settings.HIGH_RISK_METHOD_BONUS

        reasons.append(
            "High Risk HTTP Method"
        )

    score = min(
        score,
        1.0,
    )

    return (
        round(
            score,
            4,
        ),
        reasons,
    )


# ============================================================
# CONVERT AI RISK TO NORMALIZED SCORE
# ============================================================

def _normalize_ml_risk(
    ml_risk_score: float | None,
) -> float | None:
    """
    Convert DEFENZA ML risk score:

        0 - 100

    into:

        0.0 - 1.0
    """

    if ml_risk_score is None:
        return None

    try:

        score = float(
            ml_risk_score
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    return round(
        score / 100.0,
        4,
    )


# ============================================================
# FINAL CATEGORY
# ============================================================

def _resolve_category(
    ml_result: dict,
    top_category: str,
    matched_keywords: list[str],
) -> str:
    """
    Resolve the final attack category.

    Priority:

        1. DEFENZA fusion prediction
        2. Rule engine category
        3. Keyword anomaly
        4. benign
    """

    ml_category = (
        ml_result.get(
            "category"
        )
    )

    if (
        ml_category
        and ml_category != "unknown"
    ):

        return ml_category

    if top_category:
        category = top_category

    else:
        category = "benign"

    if (
        category == "benign"
        and matched_keywords
    ):

        return "anomaly"

    return category


# ============================================================
# ANALYZE PAYLOAD
# ============================================================

async def analyze_payload(
    method: str,
    path: str,
    query_string: str,
    body: str,
) -> dict:
    """
    Perform complete DEFENZA analysis.
    """

    # --------------------------------------------------------
    # 1. Normalize request
    # --------------------------------------------------------

    payload = normalize_payload(
        method,
        path,
        query_string,
        body,
    )

    # --------------------------------------------------------
    # 2. Rule engine
    # --------------------------------------------------------

    matched_rules, rule_score, top_category = (
        rule_engine.scan(
            payload
        )
    )

    # --------------------------------------------------------
    # 3. Keyword engine
    # --------------------------------------------------------

    matched_keywords, keyword_score = (
        keyword_engine.scan(
            payload
        )
    )

    # --------------------------------------------------------
    # 4. DEFENZA AI fusion
    #
    # DistilBERT + XGBoost
    # --------------------------------------------------------

    ml_result = (
        ml_engine.classify_request(
            method=method,
            path=path,
            query_string=query_string,
            body=body,
        )
    )

    # --------------------------------------------------------
    # 5. Extract ML values
    # --------------------------------------------------------

    ml_confidence = (
        ml_result.get(
            "ml_confidence"
        )
    )

    ml_risk_score = (
        ml_result.get(
            "risk_score"
        )
    )

    ml_risk_level = (
        ml_result.get(
            "risk_level"
        )
    )

    ml_policy = (
        ml_result.get(
            "policy"
        )
    )

    # --------------------------------------------------------
    # 6. Determine whether the new fusion engine produced
    #    a valid AI risk score.
    # --------------------------------------------------------

    normalized_ml_risk = (
        _normalize_ml_risk(
            ml_risk_score
        )
    )

    # --------------------------------------------------------
    # 7. Final risk calculation
    #
    # NEW DEFENZA ENGINE:
    #
    #     ML fusion risk is the primary score.
    #
    # Rule/keyword/context signals are supporting signals.
    # --------------------------------------------------------

    if normalized_ml_risk is not None:

        final_score = (
            normalized_ml_risk
        )

        # ----------------------------------------------------
        # Context bonuses
        # ----------------------------------------------------

        final_score, context_reasons = (
            apply_context_risk(
                final_score,
                method,
                path,
            )
        )

        # ----------------------------------------------------
        # Additional rule/keyword evidence
        #
        # Only add a small supporting contribution so that
        # the trained fusion model remains the primary
        # intelligence layer.
        # ----------------------------------------------------

        if rule_score > 0:

            rule_support = min(
                0.10,
                rule_score * 0.10,
            )

            final_score = min(
                1.0,
                final_score + rule_support,
            )

            context_reasons.append(
                "Rule Engine Evidence"
            )

        if keyword_score > 0:

            keyword_support = min(
                0.05,
                keyword_score * 0.05,
            )

            final_score = min(
                1.0,
                final_score + keyword_support,
            )

            context_reasons.append(
                "Keyword Engine Evidence"
            )

        final_score = round(
            final_score,
            4,
        )

    else:

        # ----------------------------------------------------
        # FALLBACK
        #
        # If the ML engine is disabled or unavailable,
        # preserve the original rule + keyword pipeline.
        # ----------------------------------------------------

        logger.warning(
            "DEFENZA ML risk unavailable. "
            "Using legacy rule/keyword scoring."
        )

        base_score = combine_scores(
            rule_score,
            keyword_score,
            ml_confidence,
        )

        final_score, context_reasons = (
            apply_context_risk(
                base_score,
                method,
                path,
            )
        )

    # --------------------------------------------------------
    # 8. Risk level
    # --------------------------------------------------------

    risk_level = risk_level_from_score(
        final_score
    )

    # --------------------------------------------------------
    # 9. Final category
    # --------------------------------------------------------

    category = _resolve_category(
        ml_result,
        top_category,
        matched_keywords,
    )

    # --------------------------------------------------------
    # 10. Convert final normalized score to percentage
    #
    # Existing backend historically stores risk_score as
    # 0.0 - 1.0.
    #
    # Keep that format for compatibility.
    # --------------------------------------------------------

    final_risk_percentage = round(
        final_score * 100.0,
        2,
    )

    # --------------------------------------------------------
    # 11. Return complete analysis
    # --------------------------------------------------------

    return {

        # ----------------------------------------------
        # Existing rule/keyword information
        # ----------------------------------------------

        "matched_rules":
            matched_rules,

        "matched_keywords":
            matched_keywords,

        # ----------------------------------------------
        # AI information
        # ----------------------------------------------

        "ml_confidence":
            ml_confidence,

        "token_analysis":
            ml_result.get(
                "token_analysis"
            ),

        "engine":
            ml_result.get(
                "engine",
                "unknown",
            ),

        "prediction":
            ml_result.get(
                "prediction"
            ),

        # ----------------------------------------------
        # Classification
        # ----------------------------------------------

        "category":
            category,

        # ----------------------------------------------
        # Risk
        # ----------------------------------------------

        "risk_score":
            final_score,

        "risk_score_percentage":
            final_risk_percentage,

        "risk_level":
            risk_level,

        # ----------------------------------------------
        # AI policy
        # ----------------------------------------------

        "policy":
            ml_policy,

        # ----------------------------------------------
        # Model details
        # ----------------------------------------------

        "distilbert":
            ml_result.get(
                "distilbert"
            ),

        "xgboost":
            ml_result.get(
                "xgboost"
            ),

        "probabilities":
            ml_result.get(
                "probabilities"
            ),

        "attack_probability":
            ml_result.get(
                "attack_probability"
            ),

        # ----------------------------------------------
        # Explainability
        # ----------------------------------------------

        "reasons":
            ml_result.get(
                "reasons",
                [],
            ),

        "context_reasons":
            context_reasons,
    }


# ============================================================
# ANALYZE + STORE
# ============================================================

async def analyze_and_store(
    traffic_id: str,
    method: str,
    path: str,
    query_string: str,
    body: str,
) -> dict:
    """
    Analyze traffic and store the result in MongoDB.
    """

    result = await analyze_payload(
        method,
        path,
        query_string,
        body,
    )

    # --------------------------------------------------------
    # MongoDB analysis document
    # --------------------------------------------------------

    doc = {
        "traffic_id": ObjectId(
            traffic_id
        ),

        "timestamp":
            now_utc(),

        **result,
    }

    await analysis_results().insert_one(
        doc
    )

    # --------------------------------------------------------
    # Update traffic log
    # --------------------------------------------------------

    await traffic_logs().update_one(
        {
            "_id":
                ObjectId(
                    traffic_id
                )
        },
        {
            "$set": {

                "risk_score":
                    result[
                        "risk_score"
                    ],

                "risk_level":
                    result[
                        "risk_level"
                    ],

                "analyzed":
                    True,

                "ml_prediction":
                    result.get(
                        "prediction"
                    ),

                "ml_policy":
                    result.get(
                        "policy"
                    ),

                "attack_probability":
                    result.get(
                        "attack_probability"
                    ),

                "category":
                    result.get(
                        "category"
                    ),
            }
        },
    )

    return result