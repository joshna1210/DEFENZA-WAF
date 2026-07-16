from app.utils.tokenizer import (
    MAX_NORMALIZED_PAYLOAD_LENGTH,
    normalize_payload,
    tokenize,
)


def test_tokenize_empty_string_returns_empty_list():
    assert tokenize("") == []


def test_tokenize_lowercases_and_splits_words():
    assert tokenize("SELECT * FROM users") == ["select", "*", "from", "users"]


def test_tokenize_splits_punctuation_into_single_char_tokens():
    # Compound signatures like "cmd.exe" are NOT single tokens — this is why
    # keyword_engine checks them as substrings instead of token membership.
    assert tokenize("cmd.exe") == ["cmd", ".", "exe"]


def test_normalize_payload_joins_method_path_query_and_body():
    result = normalize_payload("get", "/login", "user=admin", "password=hunter2")
    assert result == "GET /login user=admin password=hunter2"


def test_normalize_payload_omits_empty_query_and_body():
    result = normalize_payload("GET", "/health", "", "")
    assert result == "GET /health"


def test_normalize_payload_caps_body_length():
    huge_body = "a" * 5000
    result = normalize_payload("POST", "/submit", "", huge_body)
    # body alone is capped at 2000 chars before joining
    assert len(result) <= len("POST /submit ") + 2000


def test_normalize_payload_caps_total_length_even_when_path_is_huge():
    huge_path = "/" + ("x" * 10000)
    result = normalize_payload("GET", huge_path, "", "")
    assert len(result) == MAX_NORMALIZED_PAYLOAD_LENGTH
