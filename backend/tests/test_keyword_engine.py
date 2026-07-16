from app.services import keyword_engine


def test_benign_payload_matches_nothing():
    matched, score = keyword_engine.scan("GET /products?category=shoes")
    assert matched == []
    assert score == 0.0


def test_word_keyword_matched_via_tokenizer():
    matched, score = keyword_engine.scan("id=1 UNION SELECT 1")
    assert "union" in matched
    assert "select" in matched
    assert score == round(
        keyword_engine.WORD_KEYWORD_WEIGHTS["union"] + keyword_engine.WORD_KEYWORD_WEIGHTS["select"], 4
    )


def test_compound_signature_matched_as_substring_not_token():
    # Regression test: tokenize() splits "cmd.exe" into "cmd" / "." / "exe",
    # so this can only ever be detected via substring search.
    matched, score = keyword_engine.scan("run.php?cmd=cmd.exe /c whoami")
    assert "cmd.exe" in matched
    assert score >= keyword_engine.SUBSTRING_KEYWORD_WEIGHTS["cmd.exe"]


def test_path_traversal_substring_signature_matched():
    matched, score = keyword_engine.scan("file=../../../etc/shadow")
    assert "../" in matched
    assert "shadow" in matched


def test_dropped_false_positive_keywords_no_longer_match():
    # "etc", "cmd", and "0x" were removed for being too broad; make sure
    # they don't sneak back in via either the word or substring path.
    matched, score = keyword_engine.scan("color=0x1A2B3F description=etc cmd=run")
    assert "0x" not in matched
    assert "etc" not in matched
    assert "cmd" not in matched


def test_score_capped_at_max_keyword_score():
    payload = " ".join(keyword_engine.WORD_KEYWORD_WEIGHTS.keys()) + " " + " ".join(
        keyword_engine.SUBSTRING_KEYWORD_WEIGHTS.keys()
    )
    _, score = keyword_engine.scan(payload)
    assert score == keyword_engine.MAX_KEYWORD_SCORE


def test_low_severity_single_common_word_stays_low_risk():
    # A single occurrence of a common word like "update" (weight 0.05)
    # should not, by itself, push the keyword score anywhere near "high".
    matched, score = keyword_engine.scan("update=profile")
    assert matched == ["update"]
    assert score == keyword_engine.WORD_KEYWORD_WEIGHTS["update"]
