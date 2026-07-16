"""
Inline fast-layer signature scan. Deliberately a copy of the regex rules
in backend/app/services/rule_engine.py rather than an import, because the
proxy is meant to be deployable standalone (its own process/container) with
zero dependency on the backend package tree. Keep the two in sync manually,
or later extract into a shared `waf_rules` pip package if you want a single
source of truth.
"""
import re

RULES = {
    "sqli": [
        re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.I),
        re.compile(r"\b(union\s+select|select\s+.+\s+from|drop\s+table|or\s+1=1)\b", re.I),
    ],
    "xss": [
        re.compile(r"<script[^>]*>", re.I),
        re.compile(r"javascript\s*:", re.I),
        re.compile(r"on(error|load|click)\s*=", re.I),
    ],
    "path_traversal": [
        re.compile(r"\.\./"),
        re.compile(r"/etc/passwd"),
    ],
    "command_injection": [
        re.compile(r"[;&|`]\s*(ls|cat|whoami|wget|curl|bash|sh)\b", re.I),
    ],
}

BLOCK_CATEGORIES = {"sqli", "xss", "path_traversal", "command_injection"}


def fast_scan(payload: str) -> tuple[bool, str | None]:
    """Returns (should_block, reason). This is the ONLY check that can
    block a request inline — everything else (ML, keyword scoring) happens
    asynchronously after the request has already been forwarded, so a slow
    model never adds latency to real traffic."""
    for category, patterns in RULES.items():
        for pattern in patterns:
            if pattern.search(payload):
                return True, category
    return False, None
