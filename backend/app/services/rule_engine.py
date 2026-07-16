"""
Fast-layer signature detection. Pure regex, no ML — this is what the proxy
(or backend, in ad-hoc /analyze calls) runs synchronously in <5ms per request.

Extend RULES with more patterns as you find real attack traffic in your logs.
Keep this list curated; overly broad patterns cause false positives.
"""
import re

RULES: dict[str, list[re.Pattern]] = {
    "sqli": [
        re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.I),
        re.compile(r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))", re.I),
        re.compile(r"\b(union\s+select|select\s+.+\s+from|insert\s+into|drop\s+table|or\s+1=1|xp_cmdshell)\b", re.I),
    ],
    "xss": [
        re.compile(r"<script[^>]*>", re.I),
        re.compile(r"javascript\s*:", re.I),
        re.compile(r"on(error|load|click|mouseover)\s*=", re.I),
        re.compile(r"<img[^>]+src[^>]*=", re.I),
    ],
    "path_traversal": [
        re.compile(r"\.\./"),
        re.compile(r"\.\.\\"),
        re.compile(r"/etc/passwd"),
        re.compile(r"boot\.ini", re.I),
    ],
    "command_injection": [
        re.compile(r"[;&|`]\s*(ls|cat|whoami|wget|curl|nc|bash|sh)\b", re.I),
        re.compile(r"\$\(.*\)"),
    ],
    "nosql_injection": [
        re.compile(r"\$where\s*[:=]", re.I),
        re.compile(r"[\[{:]\s*[\"']?\$(ne|gt|gte|lt|lte|regex|in|nin|or|and|exists)[\"']?\s*[\]:=]", re.I),
    ],
    "ssti": [
        re.compile(r"\{\{.*(__class__|__globals__|__mro__|__subclasses__|request\.|config\.|self\.).*\}\}", re.I),
        re.compile(r"\{\{\s*\d+\s*[\*\+\-]\s*\d+\s*\}\}"),
        re.compile(r"\$\{.*(java\.lang|Runtime|ProcessBuilder).*\}", re.I),
    ],
    "brute_force_indicator": [
        # Matches known default/admin usernames submitted specifically as a
        # username/login credential value, not just anywhere in the payload
        # (e.g. the word "test" alone is far too common to anchor on).
        re.compile(r"(?:user(?:name)?|login)=(admin|root|test|administrator)\b", re.I),
    ],
}

RULE_WEIGHT = {
    "sqli": 0.9,
    "xss": 0.8,
    "path_traversal": 0.85,
    "command_injection": 0.95,
    "nosql_injection": 0.85,
    "ssti": 0.9,
    "brute_force_indicator": 0.3,
}


def scan(payload: str) -> tuple[list[str], float, str]:
    """Returns (matched_rule_categories, risk_score, top_category)."""
    matched = []
    max_score = 0.0
    top_category = "benign"

    for category, patterns in RULES.items():
        for pattern in patterns:
            if pattern.search(payload):
                matched.append(category)
                weight = RULE_WEIGHT[category]
                if weight > max_score:
                    max_score = weight
                    top_category = category
                break

    return matched, max_score, top_category
