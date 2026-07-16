import hashlib
import json
from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_log_entry(entry: dict) -> str:
    """Deterministic hash of a traffic log entry for blockchain batching."""
    stable = json.dumps(entry, sort_keys=True, default=str)
    return sha256_hex(stable)


def risk_level_from_score(score: float) -> str:
    if score >= 0.9:
        return "critical"
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"
