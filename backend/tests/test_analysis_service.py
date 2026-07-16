import pytest

from app.services import analysis_service


# ---- combine_scores -------------------------------------------------------

def test_combine_scores_without_ml_blends_rule_and_keyword():
    # weighted blend (0.65*0.4 + 0.35*0.6 = 0.47) exceeds the rule_score
    # floor (0.4) here, so the blend is what's returned.
    score = analysis_service.combine_scores(rule_score=0.4, keyword_score=0.6, ml_confidence=None)
    assert score == round(0.65 * 0.4 + 0.35 * 0.6, 4)


def test_combine_scores_with_ml_blends_all_three():
    score = analysis_service.combine_scores(rule_score=0.2, keyword_score=0.2, ml_confidence=0.6)
    assert score == round(0.35 * 0.2 + 0.15 * 0.2 + 0.5 * 0.6, 4)


def test_combine_scores_never_dilutes_a_confirmed_rule_match():
    # A command_injection signature match (0.95) with the other layers
    # reporting nothing must not get averaged down to "medium" risk.
    score = analysis_service.combine_scores(rule_score=0.95, keyword_score=0.0, ml_confidence=None)
    assert score >= 0.95


def test_combine_scores_ml_can_still_push_above_rule_score():
    score = analysis_service.combine_scores(rule_score=0.3, keyword_score=0.3, ml_confidence=0.99)
    assert score > 0.3


def test_combine_scores_caps_at_one():
    score = analysis_service.combine_scores(rule_score=1.0, keyword_score=1.0, ml_confidence=1.0)
    assert score == 1.0


def test_combine_scores_zero_everywhere_is_zero():
    assert analysis_service.combine_scores(0.0, 0.0, None) == 0.0


# ---- analyze_payload (integration of real sync engines + stub ML) --------

async def test_analyze_payload_benign_request():
    result = await analysis_service.analyze_payload("GET", "/products", "id=42", "")
    assert result["risk_level"] == "low"
    assert result["category"] == "benign"
    assert result["matched_rules"] == []
    assert result["engine"] == "stub"  # ML_ENABLED=False by default


async def test_analyze_payload_sqli_request_is_high_risk():
    result = await analysis_service.analyze_payload(
        "GET", "/search", "q=1' UNION SELECT username,password FROM users--", ""
    )
    assert result["category"] == "sqli"
    assert result["risk_level"] in ("high", "critical")
    assert "sqli" in result["matched_rules"]


async def test_analyze_payload_keyword_only_anomaly_category():
    # No regex rule fires, but suspicious keywords do -> "anomaly", not "benign".
    result = await analysis_service.analyze_payload("GET", "/", "q=select+union+drop", "")
    assert result["matched_keywords"]
    assert result["category"] == "anomaly"


# ---- analyze_and_store (persistence) --------------------------------------

async def test_analyze_and_store_persists_result_and_updates_traffic_log(fake_collections):
    traffic_id = "507f1f77bcf86cd799439011"
    result = await analysis_service.analyze_and_store(
        traffic_id, "POST", "/login", "", "username=admin&password=admin"
    )

    assert len(fake_collections["analysis_results"].inserted) == 1
    stored_doc = fake_collections["analysis_results"].inserted[0]
    assert stored_doc["risk_score"] == result["risk_score"]
    assert str(stored_doc["traffic_id"]) == traffic_id

    assert len(fake_collections["traffic_logs"].updated) == 1
    filter_, update = fake_collections["traffic_logs"].updated[0]
    assert str(filter_["_id"]) == traffic_id
    assert update["$set"]["risk_score"] == result["risk_score"]
    assert update["$set"]["analyzed"] is True
