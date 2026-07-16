import sys
import types

from app.services import ml_engine


class _NoGradContext:
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_classify_returns_stub_when_ml_disabled(monkeypatch):
    monkeypatch.setattr(ml_engine.settings, "ML_ENABLED", False)
    result = ml_engine.classify("anything")
    assert result == {"ml_confidence": None, "token_analysis": None, "engine": "stub"}


def test_classify_falls_back_to_stub_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(ml_engine.settings, "ML_ENABLED", True)
    # Simulate _lazy_load() having already failed to import torch/transformers.
    monkeypatch.setattr(ml_engine, "_model", "unavailable")
    result = ml_engine.classify("anything")
    assert result == {"ml_confidence": None, "token_analysis": None, "engine": "stub"}


def test_classify_falls_back_to_stub_when_inference_raises(monkeypatch):
    """Even with a model 'loaded', if the forward pass throws for some
    malformed payload, classify() must not propagate the exception — it
    should degrade to the stub result so the rest of the pipeline still
    returns a response instead of 500ing."""
    monkeypatch.setattr(ml_engine.settings, "ML_ENABLED", True)
    monkeypatch.setattr(ml_engine, "_lazy_load", lambda: None)
    monkeypatch.setattr(ml_engine, "_model", object())

    class BoomTokenizer:
        def __call__(self, *args, **kwargs):
            raise RuntimeError("tokenizer exploded")

    monkeypatch.setattr(ml_engine, "_tokenizer", BoomTokenizer())

    fake_torch = types.ModuleType("torch")
    fake_torch.no_grad = _NoGradContext
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    result = ml_engine.classify("malformed payload")
    assert result == {"ml_confidence": None, "token_analysis": None, "engine": "stub"}
