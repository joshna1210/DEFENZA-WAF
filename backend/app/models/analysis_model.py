"""
Schema reference for `analysis_results` collection.

{
  "_id": ObjectId,
  "traffic_id": ObjectId,     # FK -> traffic_logs._id
  "timestamp": datetime,
  "engine": str,               # "rule" | "keyword" | "bert"
  "matched_rules": list[str],
  "matched_keywords": list[str],
  "token_analysis": dict | None,   # ML token-level breakdown when ML_ENABLED
  "ml_confidence": float | None,
  "risk_score": float,
  "risk_level": str,
  "category": str,             # sqli | xss | path_traversal | brute_force | anomaly | benign
}
"""
