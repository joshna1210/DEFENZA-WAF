"""
DEFENZA AI ML Engine

Combines:

    DistilBERT
        +
    XGBoost
        ↓
    Probability Fusion
        ↓
    Attack Classification
        ↓
    Risk Score
        ↓
    Policy Decision

This module is lazy-loaded so the FastAPI application can start
without loading the models until the first ML request.
"""

from pathlib import Path

import numpy as np

from app.config.settings import settings
from app.utils.logger import get_logger


logger = get_logger("ml_engine")


# ============================================================
# PATHS
# ============================================================

# backend/app/services/ml_engine.py
#
# parents:
# services -> app -> backend
#
# Therefore:
# Path(__file__).resolve().parents[2] == backend

BACKEND_DIR = Path(__file__).resolve().parents[2]

AI_DIR = BACKEND_DIR / "ai"

DISTILBERT_MODEL_DIR = (
    AI_DIR
    / "trained"
    / "distilbert-defenza"
)

DISTILBERT_TOKENIZER_DIR = (
    AI_DIR
    / "tokenizer"
    / "distilbert-defenza"
)

XGB_MODEL_PATH = (
    AI_DIR
    / "trained"
    / "xgboost-defenza"
    / "xgboost_model.json"
)


# ============================================================
# LABELS
# ============================================================

LABELS = [
    "benign",
    "sqli",
    "xss",
    "cmdi",
    "path_traversal",
]

LABEL2ID = {
    label: index
    for index, label in enumerate(LABELS)
}

ID2LABEL = {
    index: label
    for index, label in enumerate(LABELS)
}


# ============================================================
# MODEL WEIGHTS
# ============================================================

DISTILBERT_WEIGHT = 0.60
XGBOOST_WEIGHT = 0.40


# ============================================================
# RISK THRESHOLDS
# ============================================================

LOW_RISK_THRESHOLD = 30
MEDIUM_RISK_THRESHOLD = 60
HIGH_RISK_THRESHOLD = 80


# ============================================================
# XGBOOST FEATURE ORDER
# ============================================================

# MUST match the order used during XGBoost training.

XGB_FEATURES = [
    "url_length",
    "body_length",
    "total_length",
    "parameter_count",
    "path_depth",
    "quote_count",
    "semicolon_count",
    "pipe_count",
    "ampersand_count",
    "equals_count",
    "angle_bracket_count",
    "parentheses_count",
    "brace_count",
    "bracket_count",
    "backslash_count",
    "percent_encoded_count",
    "double_encoded_count",
    "traversal_count",
    "decoded_traversal_count",
    "double_decoded_traversal_count",
    "sql_keyword_count",
    "sql_comment_count",
    "xss_keyword_count",
    "command_keyword_count",
    "shell_operator_count",
    "digit_count",
    "alpha_count",
    "special_count",
    "digit_ratio",
    "alpha_ratio",
    "special_ratio",
    "method_get",
    "method_post",
    "method_put",
    "method_delete",
    "method_patch",
]


# ============================================================
# LAZY LOADED MODELS
# ============================================================

_tokenizer = None
_distilbert_model = None
_xgb_model = None
_extract_features = None

_models_loaded = False
_model_load_error = None


# ============================================================
# LOAD MODELS
# ============================================================

def _lazy_load():
    """
    Load DistilBERT and XGBoost only once.
    """

    global _tokenizer
    global _distilbert_model
    global _xgb_model
    global _extract_features
    global _models_loaded
    global _model_load_error

    if _models_loaded:
        return True

    if _model_load_error is not None:
        return False

    if not settings.ML_ENABLED:

        logger.info(
            "DEFENZA ML is disabled by settings.ML_ENABLED."
        )

        return False

    try:

        logger.info(
            "Loading DEFENZA DistilBERT + XGBoost models..."
        )

        # ----------------------------------------------------
        # Imports
        # ----------------------------------------------------

        import torch

        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
        )

        from xgboost import XGBClassifier

        # Import structural feature extractor.

        import sys

        training_dir = (
            AI_DIR
            / "training"
        )

        if str(training_dir) not in sys.path:

            sys.path.insert(
                0,
                str(training_dir),
            )

        from http_features import (
            extract_features,
        )

        _extract_features = extract_features

        # ----------------------------------------------------
        # Check model files
        # ----------------------------------------------------

        if not DISTILBERT_MODEL_DIR.exists():

            raise FileNotFoundError(
                "DistilBERT model directory not found: "
                f"{DISTILBERT_MODEL_DIR}"
            )

        if not DISTILBERT_TOKENIZER_DIR.exists():

            raise FileNotFoundError(
                "DistilBERT tokenizer directory not found: "
                f"{DISTILBERT_TOKENIZER_DIR}"
            )

        if not XGB_MODEL_PATH.exists():

            raise FileNotFoundError(
                "XGBoost model not found: "
                f"{XGB_MODEL_PATH}"
            )

        # ----------------------------------------------------
        # Load DistilBERT
        # ----------------------------------------------------

        _tokenizer = (
            AutoTokenizer.from_pretrained(
                str(
                    DISTILBERT_TOKENIZER_DIR
                )
            )
        )

        _distilbert_model = (
            AutoModelForSequenceClassification.from_pretrained(
                str(
                    DISTILBERT_MODEL_DIR
                )
            )
        )

        _distilbert_model.eval()

        # ----------------------------------------------------
        # Load XGBoost
        # ----------------------------------------------------

        _xgb_model = XGBClassifier()

        _xgb_model.load_model(
            str(XGB_MODEL_PATH)
        )

        # ----------------------------------------------------
        # Verify XGBoost feature names
        # ----------------------------------------------------

        if hasattr(
            _xgb_model,
            "feature_names",
        ):

            model_features = (
                _xgb_model.feature_names
            )

            if model_features is not None:

                if list(model_features) != XGB_FEATURES:

                    raise ValueError(
                        "XGBoost feature-name mismatch."
                    )

        _models_loaded = True

        logger.info(
            "DEFENZA DistilBERT + XGBoost "
            "models loaded successfully."
        )

        return True

    except Exception as exc:

        _model_load_error = str(exc)

        logger.exception(
            "Failed to load DEFENZA AI models: %s",
            exc,
        )

        return False


# ============================================================
# DISTILBERT
# ============================================================

def _predict_distilbert(
    method: str,
    path: str,
    query_string: str,
    body: str,
):
    """
    Semantic HTTP classification using DistilBERT.
    """

    import torch

    method = str(
        method or ""
    ).upper()

    path = str(
        path or ""
    )

    query_string = str(
        query_string or ""
    )

    body = str(
        body or ""
    )

    # Reconstruct URL.

    if query_string:

        url = (
            f"{path}?{query_string}"
        )

    else:

        url = path

    # Same representation used by the
    # DEFENZA training pipeline.

    request_text = (
        f"METHOD: {method} "
        f"URL: {url} "
        f"BODY: {body} "
        f"REQUEST: {method} {url} {body}"
    )

    inputs = _tokenizer(
        request_text,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )

    with torch.no_grad():

        outputs = (
            _distilbert_model(
                **inputs
            )
        )

        probabilities = (
            torch.softmax(
                outputs.logits,
                dim=-1,
            )[0]
            .cpu()
            .numpy()
        )

    predicted_id = int(
        np.argmax(
            probabilities
        )
    )

    predicted_label = (
        ID2LABEL[
            predicted_id
        ]
    )

    confidence = float(
        probabilities[
            predicted_id
        ]
    )

    return {
        "probabilities":
            probabilities,

        "prediction":
            predicted_label,

        "confidence":
            confidence,

        "num_tokens":
            int(
                inputs[
                    "input_ids"
                ].shape[1]
            ),
    }


# ============================================================
# XGBOOST
# ============================================================

def _predict_xgboost(
    method: str,
    path: str,
    query_string: str,
    body: str,
):
    """
    Structural HTTP analysis using XGBoost.
    """

    if query_string:

        url = (
            f"{path}?{query_string}"
        )

    else:

        url = path

    feature_dict = (
        _extract_features(
            method,
            url,
            body,
        )
    )

    feature_row = [
        feature_dict.get(
            feature_name,
            0,
        )
        for feature_name in XGB_FEATURES
    ]

    # Import pandas only when needed.

    import pandas as pd

    feature_df = pd.DataFrame(
        [feature_row],
        columns=XGB_FEATURES,
    )

    probabilities = (
        _xgb_model.predict_proba(
            feature_df
        )[0]
    )

    predicted_id = int(
        np.argmax(
            probabilities
        )
    )

    predicted_label = (
        ID2LABEL[
            predicted_id
        ]
    )

    confidence = float(
        probabilities[
            predicted_id
        ]
    )

    return {
        "probabilities":
            probabilities,

        "prediction":
            predicted_label,

        "confidence":
            confidence,

        "features":
            feature_dict,
    }


# ============================================================
# RISK LEVEL
# ============================================================

def _risk_level(
    risk_score: float,
):

    if risk_score < LOW_RISK_THRESHOLD:

        return "low"

    if risk_score < MEDIUM_RISK_THRESHOLD:

        return "medium"

    if risk_score < HIGH_RISK_THRESHOLD:

        return "high"

    return "critical"


# ============================================================
# POLICY
# ============================================================

def _policy(
    label: str,
    risk_score: float,
):

    if (
        label == "benign"
        and risk_score
        < LOW_RISK_THRESHOLD
    ):

        return "ALLOW"

    if risk_score < MEDIUM_RISK_THRESHOLD:

        return "MONITOR"

    if risk_score < HIGH_RISK_THRESHOLD:

        return "CAPTCHA"

    if risk_score < 90:

        return "RATE_LIMIT"

    return "BLOCK"


# ============================================================
# EXPLAINABILITY
# ============================================================

def _generate_reasons(
    final_label,
    distilbert_result,
    xgb_result,
):

    reasons = []

    db_label = (
        distilbert_result[
            "prediction"
        ]
    )

    xgb_label = (
        xgb_result[
            "prediction"
        ]
    )

    if db_label == xgb_label:

        reasons.append(
            "DistilBERT and XGBoost "
            f"agree on {final_label}."
        )

    else:

        reasons.append(
            "Model disagreement: "
            f"DistilBERT={db_label}, "
            f"XGBoost={xgb_label}."
        )

    reasons.append(
        "DistilBERT confidence: "
        f"{distilbert_result['confidence']:.2%}."
    )

    reasons.append(
        "XGBoost confidence: "
        f"{xgb_result['confidence']:.2%}."
    )

    features = (
        xgb_result[
            "features"
        ]
    )

    if features[
        "double_decoded_traversal_count"
    ] > 0:

        reasons.append(
            "Double-decoded path traversal "
            "pattern detected."
        )

    elif features[
        "decoded_traversal_count"
    ] > 0:

        reasons.append(
            "Decoded path traversal "
            "pattern detected."
        )

    elif features[
        "traversal_count"
    ] > 0:

        reasons.append(
            "Path traversal pattern detected."
        )

    if features[
        "xss_keyword_count"
    ] > 0:

        reasons.append(
            "Potential XSS-related "
            "pattern detected."
        )

    if features[
        "sql_keyword_count"
    ] > 0:

        reasons.append(
            "SQL-related keywords detected."
        )

    if features[
        "sql_comment_count"
    ] > 0:

        reasons.append(
            "SQL comment syntax detected."
        )

    if features[
        "command_keyword_count"
    ] > 0:

        reasons.append(
            "Command execution keyword detected."
        )

    if features[
        "shell_operator_count"
    ] > 0:

        reasons.append(
            "Shell command operator detected."
        )

    if features[
        "quote_count"
    ] > 0:

        reasons.append(
            "Quote characters associated "
            "with injection patterns detected."
        )

    if final_label == "benign":

        reasons.append(
            "No strong malicious intent "
            "was identified."
        )

    return reasons


# ============================================================
# PUBLIC CLASSIFY FUNCTION
# ============================================================

def classify_request(
    method: str,
    path: str,
    query_string: str = "",
    body: str = "",
) -> dict:
    """
    Main DEFENZA classification function.

    Returns the complete AI analysis.
    """

    if not settings.ML_ENABLED:

        return {
            "engine": "stub",

            "ml_confidence": None,

            "prediction": "unknown",

            "category": "unknown",

            "risk_score": None,

            "risk_level": None,

            "policy": "MONITOR",

            "token_analysis": None,

            "reasons": [
                "ML_ENABLED is false."
            ],
        }

    if not _lazy_load():

        return {
            "engine": "stub",

            "ml_confidence": None,

            "prediction": "unknown",

            "category": "unknown",

            "risk_score": None,

            "risk_level": None,

            "policy": "MONITOR",

            "token_analysis": None,

            "reasons": [
                "DEFENZA AI models could "
                "not be loaded."
            ],
        }

    try:

        # ====================================================
        # DISTILBERT
        # ====================================================

        distilbert_result = (
            _predict_distilbert(
                method,
                path,
                query_string,
                body,
            )
        )

        # ====================================================
        # XGBOOST
        # ====================================================

        xgb_result = (
            _predict_xgboost(
                method,
                path,
                query_string,
                body,
            )
        )

        # ====================================================
        # FUSION
        # ====================================================

        db_probs = np.asarray(
            distilbert_result[
                "probabilities"
            ],
            dtype=float,
        )

        xgb_probs = np.asarray(
            xgb_result[
                "probabilities"
            ],
            dtype=float,
        )

        fused_probs = (
            DISTILBERT_WEIGHT
            * db_probs
            +
            XGBOOST_WEIGHT
            * xgb_probs
        )

        total = (
            fused_probs.sum()
        )

        if total > 0:

            fused_probs = (
                fused_probs / total
            )

        # ====================================================
        # FINAL CLASS
        # ====================================================

        final_id = int(
            np.argmax(
                fused_probs
            )
        )

        final_label = (
            ID2LABEL[
                final_id
            ]
        )

        final_confidence = float(
            fused_probs[
                final_id
            ]
        )

        # ====================================================
        # RISK
        # ====================================================

        benign_probability = float(
            fused_probs[
                LABEL2ID[
                    "benign"
                ]
            ]
        )

        attack_probability = (
            1.0
            - benign_probability
        )

        risk_score = (
            attack_probability
            * 100.0
        )

        risk_score = max(
            0.0,
            min(
                100.0,
                risk_score,
            ),
        )

        risk_level = (
            _risk_level(
                risk_score
            )
        )

        policy = (
            _policy(
                final_label,
                risk_score,
            )
        )

        # ====================================================
        # REASONS
        # ====================================================

        reasons = (
            _generate_reasons(
                final_label,
                distilbert_result,
                xgb_result,
            )
        )

        # ====================================================
        # PROBABILITY MAP
        # ====================================================

        fused_probability_map = {

            LABELS[index]:
                round(
                    float(
                        probability
                    ),
                    6,
                )

            for index, probability
            in enumerate(
                fused_probs
            )
        }

        # ====================================================
        # RESULT
        # ====================================================

        return {

            "engine":
                "defenza_fusion",

            "ml_confidence":
                final_confidence,

            "prediction":
                final_label,

            "category":
                final_label,

            "risk_score":
                round(
                    risk_score,
                    2,
                ),

            "risk_level":
                risk_level,

            "policy":
                policy,

            "token_analysis": {

                "num_tokens":
                    distilbert_result[
                        "num_tokens"
                    ],

            },

            "distilbert": {

                "prediction":
                    distilbert_result[
                        "prediction"
                    ],

                "confidence":
                    round(
                        distilbert_result[
                            "confidence"
                        ],
                        6,
                    ),

            },

            "xgboost": {

                "prediction":
                    xgb_result[
                        "prediction"
                    ],

                "confidence":
                    round(
                        xgb_result[
                            "confidence"
                        ],
                        6,
                    ),

            },

            "probabilities":
                fused_probability_map,

            "attack_probability":
                round(
                    attack_probability,
                    6,
                ),

            "reasons":
                reasons,
        }

    except Exception as exc:

        logger.exception(
            "DEFENZA AI inference failed: %s",
            exc,
        )

        return {

            "engine":
                "stub",

            "ml_confidence":
                None,

            "prediction":
                "unknown",

            "category":
                "unknown",

            "risk_score":
                None,

            "risk_level":
                None,

            "policy":
                "MONITOR",

            "token_analysis":
                None,

            "reasons": [
                "AI inference failed; "
                "request was not blocked "
                "by the ML engine."
            ],

        }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def classify(
    payload: str,
) -> dict:
    """
    Compatibility wrapper.

    Existing code may still call:

        ml_engine.classify(payload)

    The new application integration should use:

        classify_request(
            method,
            path,
            query_string,
            body
        )
    """

    # Since the old function only receives a single payload,
    # treat it as the URL/request text.

    result = classify_request(
        method="GET",
        path=payload,
        query_string="",
        body="",
    )

    return result