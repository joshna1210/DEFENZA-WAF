"""
Keyword-frequency / suspicious-token layer. Sits between the fast regex
rule engine and the (optional) BERT model — cheap, no GPU needed, catches
things pure regex misses (e.g. unusual token combinations) without the
latency cost of a transformer forward pass.
"""
from app.utils.tokenizer import tokenize

# Per-keyword severity weight, for single-word tokens only (tokenize() splits
# on any non-alnum/underscore character, so these are matched via token-set
# intersection). Common English/API words that happen to overlap with SQL
# verbs ("select", "update", ...) are weighted low since they show up
# constantly in benign traffic and should only nudge the score when several
# distinct signals combine; tool/protocol-specific tokens that rarely appear
# outside an attack are weighted high.
# NOTE: bare "etc", "cmd", and "0x" were deliberately dropped — they matched
# far too much benign traffic (hex color codes, "cmd" query params, the
# word "etc.") to be useful signals.
WORD_KEYWORD_WEIGHTS = {
    "select": 0.08, "insert": 0.08, "update": 0.05, "delete": 0.08,
    "union": 0.22, "drop": 0.22, "exec": 0.18, "waitfor": 0.2,
    "script": 0.18, "alert": 0.08, "onerror": 0.22, "onload": 0.22,
    "eval": 0.18, "base64_decode": 0.22, "powershell": 0.22,
    "wget": 0.15, "curl": 0.15, "nc": 0.15, "netcat": 0.15,
    "passwd": 0.2, "shadow": 0.2,
}

# Compound signatures containing punctuation (".", "(", "%", "/", "\\").
# tokenize() would split these apart (e.g. "cmd.exe" -> "cmd", ".", "exe"),
# so a token-set intersection against them can never match — they're
# checked as plain substrings of the (lowercased) payload instead.
SUBSTRING_KEYWORD_WEIGHTS = {
    "cmd.exe": 0.22, "boot.ini": 0.2,
    "system(": 0.18, "sleep(": 0.2, "benchmark(": 0.2,
    "../": 0.2, "..\\": 0.2, "%00": 0.2,
}

MAX_KEYWORD_SCORE = 0.75      # keyword engine alone never claims "critical"


def scan(payload: str) -> tuple[list[str], float]:
    tokens = set(tokenize(payload))
    matched = sorted(tokens & WORD_KEYWORD_WEIGHTS.keys())
    score = sum(WORD_KEYWORD_WEIGHTS[t] for t in matched)

    lowered = payload.lower()
    for signature, weight in SUBSTRING_KEYWORD_WEIGHTS.items():
        if signature in lowered:
            matched.append(signature)
            score += weight

    return sorted(matched), round(min(score, MAX_KEYWORD_SCORE), 4)
