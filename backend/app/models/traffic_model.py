"""
Mongo document shape reference for `traffic_logs` collection.
Not an ORM model (we use Motor directly) — this documents the schema.

{
  "_id": ObjectId,
  "timestamp": datetime,
  "ip": str,
  "method": str,
  "path": str,
  "query_string": str,
  "headers": dict,
  "body_preview": str,        # truncated, sanitized
  "user_agent": str,
  "status_code": int | None,  # response status once forwarded
  "response_time_ms": float | None,
  "blocked": bool,
  "block_reason": str | None,
  "risk_score": float,        # 0-1, updated by analysis pipeline
  "risk_level": str,          # low | medium | high | critical
  "analyzed": bool,           # whether async ML pass has completed
  "blockchain_batch_id": str | None,
}
"""
