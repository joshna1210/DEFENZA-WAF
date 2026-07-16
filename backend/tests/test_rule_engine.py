from app.services import rule_engine


def test_benign_payload_matches_nothing():
    matched, score, category = rule_engine.scan("GET /products?id=42")
    assert matched == []
    assert score == 0.0
    assert category == "benign"


def test_sqli_union_select_detected():
    matched, score, category = rule_engine.scan("id=1 UNION SELECT username, password FROM users")
    assert "sqli" in matched
    assert category == "sqli"
    assert score == rule_engine.RULE_WEIGHT["sqli"]


def test_xss_script_tag_detected():
    matched, score, category = rule_engine.scan('comment=<script>alert(1)</script>')
    assert "xss" in matched
    assert category == "xss"


def test_path_traversal_detected():
    matched, score, category = rule_engine.scan("file=../../etc/passwd")
    assert "path_traversal" in matched
    assert category == "path_traversal"


def test_command_injection_detected():
    matched, score, category = rule_engine.scan("host=127.0.0.1; cat /etc/passwd")
    assert "command_injection" in matched
    assert category == "command_injection"


def test_nosql_injection_operator_detected():
    matched, score, category = rule_engine.scan('{"username": {"$ne": null}, "password": {"$ne": null}}')
    assert "nosql_injection" in matched


def test_nosql_injection_bracket_notation_detected():
    matched, _, _ = rule_engine.scan("username[$ne]=admin&password[$ne]=admin")
    assert "nosql_injection" in matched


def test_ssti_dangerous_object_detected():
    matched, _, category = rule_engine.scan("name={{ self.__class__.__mro__ }}")
    assert "ssti" in matched
    assert category == "ssti"


def test_ssti_arithmetic_probe_detected():
    matched, _, _ = rule_engine.scan("name={{7*7}}")
    assert "ssti" in matched


def test_brute_force_indicator_requires_credential_context():
    # A bare word like "test" appearing anywhere must NOT fire — that was
    # the old (broken) behavior of the anchored `^(admin|root|test)$` regex,
    # which could never match a full normalized payload string anyway.
    matched, score, _ = rule_engine.scan("GET /test/page HTTP report")
    assert "brute_force_indicator" not in matched


def test_brute_force_indicator_fires_on_default_username_value():
    matched, score, category = rule_engine.scan("POST /login username=admin&password=admin123")
    assert "brute_force_indicator" in matched
    assert category == "brute_force_indicator"
    assert score == rule_engine.RULE_WEIGHT["brute_force_indicator"]


def test_highest_weight_category_wins_as_top_category():
    # command_injection (0.95) should outrank xss (0.8) when both match.
    payload = "<script>alert(1)</script>; cat /etc/passwd"
    matched, score, category = rule_engine.scan(payload)
    assert "xss" in matched and "command_injection" in matched
    assert category == "command_injection"
    assert score == rule_engine.RULE_WEIGHT["command_injection"]
