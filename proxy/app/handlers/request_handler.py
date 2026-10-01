"""
Inline fast-layer signature scan.
"""

import re
from urllib.parse import unquote

RULES = {
    "sqli": [
        re.compile(r"(%27)|(')|(--)|(%23)|(#)", re.I),
        re.compile(
            r"\b(union\s+select|select\s+.+\s+from|drop\s+table|or\s+1=1)\b",
            re.I,
        ),
    ],

    "xss": [
        re.compile(r"<script[^>]*>", re.I),
        re.compile(r"</script>", re.I),
        re.compile(r"javascript\s*:", re.I),
        re.compile(r"on(error|load|click|mouseover|focus)\s*=", re.I),
        re.compile(r"alert\s*\(", re.I),
    ],

    "path_traversal": [
        re.compile(r"\.\./"),
        re.compile(r"/etc/passwd"),
    ],

    "command_injection": [
        re.compile(r"[;&|`]\s*(ls|cat|whoami|wget|curl|bash|sh)\b", re.I),
    ],
}


def fast_scan(payload: str) -> tuple[bool, str |None]:
    """
    Returns:
        (True, category)  -> malicious
        (False, None)     -> clean
    """

    try:
        if payload is None:
            payload = ""

        payload = str(payload)
        payload = unquote(payload)

        print(f"[SCAN] {payload}")

        for category, patterns in RULES.items():
            for pattern in patterns:
                if pattern.search(payload):
                    print(f"[BLOCKED] {category}")
                    return True, category

        print("[ALLOW]")
        return False, None

    except Exception as e:
        print(f"[SCAN ERROR] {e}")
        return False, None