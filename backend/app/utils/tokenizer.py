"""
Lightweight tokenizer used by the keyword engine (always on) and as the
pre-processing step feeding the optional BERT engine (only active when
ML_ENABLED=true and the model is loaded — see analysis_service.py).
"""
import re

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]")

# Upper bound on the string handed to the regex/keyword/ML layers. Only
# capping `body` (as before) still left `path`/`query_string` unbounded, so a
# pathologically long URL could blow up per-request regex-scan cost; this
# caps the final combined string regardless of which part is oversized.
MAX_NORMALIZED_PAYLOAD_LENGTH = 4000


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


def normalize_payload(method: str, path: str, query_string: str, body: str) -> str:
    """Combine the parts of a request that matter for content analysis into
    a single normalized string."""
    parts = [method.upper(), path]
    if query_string:
        parts.append(query_string)
    if body:
        parts.append(body[:2000])  # cap body size fed to analysis
    combined = " ".join(parts)
    return combined[:MAX_NORMALIZED_PAYLOAD_LENGTH]
