"""
Optional transformer-based (DistilBERT) content classifier.

This module is intentionally lazy-loaded and fully gated behind
`settings.ML_ENABLED`. With ML_ENABLED=false (the default), `classify()`
returns a stub result immediately so the rest of the pipeline (and the
whole docker-compose stack) works with zero ML dependencies installed.

To go live:
1. pip install torch transformers
2. Fine-tune / point ML_MODEL_NAME at a model trained on HTTP payload
   classification (benign vs sqli/xss/etc) — DistilBERT is a good base.
3. Set ML_ENABLED=true in .env
"""
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("ml_engine")

_model = None
_tokenizer = None


def _lazy_load():
    global _model, _tokenizer
    if _model is not None:
        return
    try:
        import torch  # noqa: F401
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        _tokenizer = AutoTokenizer.from_pretrained(settings.ML_MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(
            settings.ML_MODEL_NAME
        )
        _model.eval()
        logger.info(f"Loaded ML model {settings.ML_MODEL_NAME}")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Could not load ML model, falling back to stub: {exc}")
        _model = "unavailable"


def classify(payload: str) -> dict:
    """
    Returns:
        {
          "ml_confidence": float,   # 0-1 malicious probability
          "token_analysis": {...} | None,
          "engine": "bert" | "stub"
        }
    """
    if not settings.ML_ENABLED:
        return {"ml_confidence": None, "token_analysis": None, "engine": "stub"}

    _lazy_load()
    if _model == "unavailable":
        return {"ml_confidence": None, "token_analysis": None, "engine": "stub"}

    import torch

    try:
        with torch.no_grad():
            inputs = _tokenizer(
                payload, return_tensors="pt", truncation=True, max_length=256
            )
            outputs = _model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
            malicious_confidence = float(probs[-1])  # assumes last class = malicious

        return {
            "ml_confidence": malicious_confidence,
            "token_analysis": {
                "num_tokens": int(inputs["input_ids"].shape[1]),
            },
            "engine": "bert",
        }
    except Exception as exc:  # noqa: BLE001
        # A single malformed/edge-case payload must never take down the
        # whole analysis pipeline — fall back to the stub result for this
        # request and let rule/keyword engines carry the score instead.
        logger.warning(f"ML inference failed, falling back to stub for this payload: {exc}")
        return {"ml_confidence": None, "token_analysis": None, "engine": "stub"}
