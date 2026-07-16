from app.services import analysis_service


def test_analyze_ad_hoc_returns_pipeline_result(client, monkeypatch):
    canned_result = {
        "matched_rules": ["sqli"],
        "matched_keywords": ["union", "select"],
        "ml_confidence": None,
        "token_analysis": None,
        "engine": "stub",
        "risk_score": 0.9,
        "risk_level": "critical",
        "category": "sqli",
    }

    async def fake_analyze_payload(method, path, query_string, body):
        assert method == "GET"
        assert path == "/search"
        assert query_string == "q=' UNION SELECT 1--"
        return canned_result

    monkeypatch.setattr(analysis_service, "analyze_payload", fake_analyze_payload)

    response = client.post(
        "/api/analysis/test",
        json={"method": "GET", "path": "/search", "query_string": "q=' UNION SELECT 1--", "body": ""},
    )

    assert response.status_code == 200
    assert response.json() == canned_result


def test_analyze_ad_hoc_uses_request_body_defaults(client, monkeypatch):
    async def fake_analyze_payload(method, path, query_string, body):
        return {
            "matched_rules": [], "matched_keywords": [], "ml_confidence": None,
            "token_analysis": None, "engine": "stub", "risk_score": 0.0,
            "risk_level": "low", "category": "benign",
        }

    monkeypatch.setattr(analysis_service, "analyze_payload", fake_analyze_payload)

    response = client.post("/api/analysis/test", json={})
    assert response.status_code == 200
    assert response.json()["category"] == "benign"


def test_analyze_ad_hoc_requires_authentication(client):
    from app.main import app
    from app.middlewares.security_middleware import get_current_user

    app.dependency_overrides.pop(get_current_user, None)
    try:
        response = client.post("/api/analysis/test", json={})
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = lambda: {"sub": "tester", "role": "admin"}
