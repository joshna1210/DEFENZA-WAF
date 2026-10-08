from pathlib import Path

import numpy as np
import pandas as pd
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

from xgboost import XGBClassifier

from http_features import extract_features


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DISTILBERT_MODEL_DIR = (
    BASE_DIR / "trained" / "distilbert-defenza"
)

DISTILBERT_TOKENIZER_DIR = (
    BASE_DIR / "tokenizer" / "distilbert-defenza"
)

XGB_MODEL_DIR = (
    BASE_DIR / "trained" / "xgboost-defenza"
)

XGB_MODEL_PATH = (
    XGB_MODEL_DIR / "xgboost_model.json"
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
# FUSION CONFIGURATION
# ============================================================

# DistilBERT = semantic understanding
# XGBoost    = structural HTTP analysis

DISTILBERT_WEIGHT = 0.60
XGBOOST_WEIGHT = 0.40


# ============================================================
# RISK THRESHOLDS
# ============================================================

# These are initial configurable policy thresholds.
# They are NOT production-calibrated thresholds.

LOW_RISK_THRESHOLD = 30
MEDIUM_RISK_THRESHOLD = 60
HIGH_RISK_THRESHOLD = 80


# ============================================================
# XGBOOST FEATURE ORDER
# ============================================================
#
# IMPORTANT:
#
# This MUST match the exact order used while training XGBoost.
#
# DO NOT read feature_importance.csv for ordering.
# That file is sorted by feature importance, not training order.
# ============================================================

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
# LOAD DISTILBERT
# ============================================================

print("=" * 70)
print("Loading DEFENZA DistilBERT model...")
print("=" * 70)

tokenizer = AutoTokenizer.from_pretrained(
    str(DISTILBERT_TOKENIZER_DIR)
)

distilbert_model = (
    AutoModelForSequenceClassification.from_pretrained(
        str(DISTILBERT_MODEL_DIR)
    )
)

distilbert_model.eval()

print("DistilBERT loaded successfully.")


# ============================================================
# LOAD XGBOOST
# ============================================================

print()
print("=" * 70)
print("Loading DEFENZA XGBoost model...")
print("=" * 70)

xgb_model = XGBClassifier()

xgb_model.load_model(
    str(XGB_MODEL_PATH)
)

print("XGBoost loaded successfully.")


# ============================================================
# VERIFY XGBOOST FEATURES
# ============================================================

print()
print("=" * 70)
print("Checking XGBoost feature configuration...")
print("=" * 70)

print(
    f"Expected feature count: {len(XGB_FEATURES)}"
)

if hasattr(xgb_model, "feature_names"):

    model_features = xgb_model.feature_names

    if model_features is not None:

        if list(model_features) != XGB_FEATURES:

            print()
            print("WARNING:")
            print("XGBoost feature names differ from the configured order.")
            print()
            print("Model expects:")
            print(model_features)
            print()
            print("Configured:")
            print(XGB_FEATURES)
            print()

            raise ValueError(
                "XGBoost feature configuration mismatch."
            )

        print(
            "XGBoost feature names verified successfully."
        )

print(
    "XGBoost feature configuration is valid."
)


# ============================================================
# DISTILBERT PREDICTION
# ============================================================

def predict_distilbert(
    method: str,
    url: str,
    body: str = "",
):
    """
    Run an HTTP request through the trained DistilBERT model.

    Returns:
        probabilities
        predicted_label
        confidence
    """

    method = str(method or "").upper()
    url = str(url or "")
    body = str(body or "")

    # This follows the same request representation used
    # during DEFENZA DistilBERT preprocessing.

    request_text = (
        f"METHOD: {method} "
        f"URL: {url} "
        f"BODY: {body} "
        f"REQUEST: {method} {url} {body}"
    )

    inputs = tokenizer(
        request_text,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )

    with torch.no_grad():

        outputs = distilbert_model(
            **inputs
        )

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0].cpu().numpy()

    predicted_id = int(
        np.argmax(probabilities)
    )

    predicted_label = ID2LABEL[
        predicted_id
    ]

    confidence = float(
        probabilities[predicted_id]
    )

    return {
        "probabilities": probabilities,
        "predicted_label": predicted_label,
        "confidence": confidence,
    }


# ============================================================
# XGBOOST PREDICTION
# ============================================================

def predict_xgboost(
    method: str,
    url: str,
    body: str = "",
):
    """
    Extract structural HTTP features and run XGBoost.
    """

    feature_dict = extract_features(
        method,
        url,
        body,
    )

    # Build features in EXACT training order.

    feature_row = [
        feature_dict.get(
            feature_name,
            0,
        )
        for feature_name in XGB_FEATURES
    ]

    feature_df = pd.DataFrame(
        [feature_row],
        columns=XGB_FEATURES,
    )

    probabilities = (
        xgb_model.predict_proba(
            feature_df
        )[0]
    )

    predicted_id = int(
        np.argmax(probabilities)
    )

    predicted_label = ID2LABEL[
        predicted_id
    ]

    confidence = float(
        probabilities[predicted_id]
    )

    return {
        "probabilities": probabilities,
        "predicted_label": predicted_label,
        "confidence": confidence,
        "features": feature_dict,
    }


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(
    risk_score: float,
):

    if risk_score < LOW_RISK_THRESHOLD:

        return "LOW"

    elif risk_score < MEDIUM_RISK_THRESHOLD:

        return "MEDIUM"

    elif risk_score < HIGH_RISK_THRESHOLD:

        return "HIGH"

    return "CRITICAL"


# ============================================================
# POLICY ENGINE
# ============================================================

def get_policy(
    final_label: str,
    risk_score: float,
):
    """
    Convert risk into a DEFENZA policy decision.
    """

    # Very low-risk benign request.

    if (
        final_label == "benign"
        and risk_score < LOW_RISK_THRESHOLD
    ):

        return "ALLOW"

    # Suspicious but relatively low risk.

    if risk_score < MEDIUM_RISK_THRESHOLD:

        return "MONITOR"

    # Medium/high risk.

    if risk_score < HIGH_RISK_THRESHOLD:

        return "CAPTCHA"

    # Very high risk.

    if risk_score < 90:

        return "RATE_LIMIT"

    # Critical risk.

    return "BLOCK"


# ============================================================
# EXPLAINABILITY
# ============================================================

def generate_reasons(
    final_label,
    distilbert_result,
    xgb_result,
):

    reasons = []

    db_label = (
        distilbert_result[
            "predicted_label"
        ]
    )

    xgb_label = (
        xgb_result[
            "predicted_label"
        ]
    )

    db_conf = (
        distilbert_result[
            "confidence"
        ]
    )

    xgb_conf = (
        xgb_result[
            "confidence"
        ]
    )

    # --------------------------------------------------------
    # MODEL AGREEMENT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MODEL CONFIDENCE
    # --------------------------------------------------------

    reasons.append(
        "DistilBERT confidence: "
        f"{db_conf:.2%}."
    )

    reasons.append(
        "XGBoost confidence: "
        f"{xgb_conf:.2%}."
    )

    # --------------------------------------------------------
    # STRUCTURAL FEATURES
    # --------------------------------------------------------

    features = xgb_result[
        "features"
    ]

    if (
        features[
            "double_decoded_traversal_count"
        ] > 0
    ):

        reasons.append(
            "Double-decoded path traversal "
            "pattern detected."
        )

    if (
        features[
            "decoded_traversal_count"
        ] > 0
    ):

        reasons.append(
            "Decoded path traversal "
            "pattern detected."
        )

    if (
        features[
            "traversal_count"
        ] > 0
    ):

        reasons.append(
            "Path traversal pattern detected."
        )

    if (
        features[
            "xss_keyword_count"
        ] > 0
    ):

        reasons.append(
            "Potential XSS-related pattern detected."
        )

    if (
        features[
            "sql_keyword_count"
        ] > 0
    ):

        reasons.append(
            "SQL-related keywords detected."
        )

    if (
        features[
            "sql_comment_count"
        ] > 0
    ):

        reasons.append(
            "SQL comment syntax detected."
        )

    if (
        features[
            "command_keyword_count"
        ] > 0
    ):

        reasons.append(
            "Command execution keyword detected."
        )

    if (
        features[
            "shell_operator_count"
        ] > 0
    ):

        reasons.append(
            "Shell command operator detected."
        )

    if (
        features[
            "quote_count"
        ] > 0
    ):

        reasons.append(
            "Quote characters associated "
            "with injection patterns detected."
        )

    if (
        features[
            "percent_encoded_count"
        ] > 0
    ):

        reasons.append(
            "Percent-encoded characters detected."
        )

    # --------------------------------------------------------
    # BENIGN
    # --------------------------------------------------------

    if final_label == "benign":

        reasons.append(
            "No strong malicious intent "
            "was identified."
        )

    return reasons


# ============================================================
# MAIN FUSION ENGINE
# ============================================================

def analyze_request(
    method: str,
    url: str,
    body: str = "",
):
    """
    Complete DEFENZA AI analysis pipeline.

    HTTP Request
        ↓
    DistilBERT
        +
    XGBoost
        ↓
    Probability Fusion
        ↓
    Risk Score
        ↓
    Policy Decision
    """

    # ========================================================
    # MODEL 1
    # ========================================================

    distilbert_result = (
        predict_distilbert(
            method,
            url,
            body,
        )
    )

    # ========================================================
    # MODEL 2
    # ========================================================

    xgb_result = (
        predict_xgboost(
            method,
            url,
            body,
        )
    )

    # ========================================================
    # PROBABILITIES
    # ========================================================

    db_probabilities = np.asarray(
        distilbert_result[
            "probabilities"
        ],
        dtype=float,
    )

    xgb_probabilities = np.asarray(
        xgb_result[
            "probabilities"
        ],
        dtype=float,
    )

    # ========================================================
    # FUSION
    # ========================================================

    fused_probabilities = (
        DISTILBERT_WEIGHT
        * db_probabilities
        +
        XGBOOST_WEIGHT
        * xgb_probabilities
    )

    # Numerical normalization.

    probability_sum = (
        fused_probabilities.sum()
    )

    if probability_sum > 0:

        fused_probabilities = (
            fused_probabilities
            / probability_sum
        )

    # ========================================================
    # FINAL CLASS
    # ========================================================

    final_id = int(
        np.argmax(
            fused_probabilities
        )
    )

    final_label = ID2LABEL[
        final_id
    ]

    final_confidence = float(
        fused_probabilities[
            final_id
        ]
    )

    # ========================================================
    # RISK SCORE
    # ========================================================

    benign_probability = float(
        fused_probabilities[
            LABEL2ID["benign"]
        ]
    )

    attack_probability = (
        1.0 - benign_probability
    )

    risk_score = (
        attack_probability * 100.0
    )

    risk_score = max(
        0.0,
        min(
            100.0,
            risk_score,
        ),
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    risk_level = get_risk_level(
        risk_score
    )

    # ========================================================
    # POLICY
    # ========================================================

    policy = get_policy(
        final_label,
        risk_score,
    )

    # ========================================================
    # EXPLAINABILITY
    # ========================================================

    reasons = generate_reasons(
        final_label,
        distilbert_result,
        xgb_result,
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "request": {
            "method": method,
            "url": url,
            "body": body,
        },

        "distilbert": {

            "prediction":
                distilbert_result[
                    "predicted_label"
                ],

            "confidence":
                round(
                    distilbert_result[
                        "confidence"
                    ],
                    6,
                ),

            "probabilities": {

                LABELS[index]:
                    round(
                        float(
                            probability
                        ),
                        6,
                    )

                for index, probability
                in enumerate(
                    db_probabilities
                )
            },
        },

        "xgboost": {

            "prediction":
                xgb_result[
                    "predicted_label"
                ],

            "confidence":
                round(
                    xgb_result[
                        "confidence"
                    ],
                    6,
                ),

            "probabilities": {

                LABELS[index]:
                    round(
                        float(
                            probability
                        ),
                        6,
                    )

                for index, probability
                in enumerate(
                    xgb_probabilities
                )
            },
        },

        "fusion": {

            "prediction":
                final_label,

            "confidence":
                round(
                    final_confidence,
                    6,
                ),

            "probabilities": {

                LABELS[index]:
                    round(
                        float(
                            probability
                        ),
                        6,
                    )

                for index, probability
                in enumerate(
                    fused_probabilities
                )
            },
        },

        "risk": {

            "score":
                round(
                    risk_score,
                    2,
                ),

            "level":
                risk_level,

            "attack_probability":
                round(
                    attack_probability,
                    6,
                ),
        },

        "policy": policy,

        "explainability": {

            "reasons":
                reasons,
        },
    }


# ============================================================
# PRETTY PRINT
# ============================================================

def print_result(
    result,
):

    print()

    print(
        f"DistilBERT : "
        f"{result['distilbert']['prediction']} "
        f"("
        f"{result['distilbert']['confidence']:.2%}"
        f")"
    )

    print(
        f"XGBoost    : "
        f"{result['xgboost']['prediction']} "
        f"("
        f"{result['xgboost']['confidence']:.2%}"
        f")"
    )

    print(
        f"FUSED      : "
        f"{result['fusion']['prediction']} "
        f"("
        f"{result['fusion']['confidence']:.2%}"
        f")"
    )

    print()

    print(
        f"Risk Score : "
        f"{result['risk']['score']}/100"
    )

    print(
        f"Risk Level : "
        f"{result['risk']['level']}"
    )

    print(
        f"Policy     : "
        f"{result['policy']}"
    )

    print()

    print("Reasons:")

    for reason in (
        result[
            "explainability"
        ]["reasons"]
    ):

        print(
            f"  • {reason}"
        )


# ============================================================
# TEST CASES
# ============================================================

if __name__ == "__main__":

    test_requests = [

        # ----------------------------------------------------
        # BENIGN
        # ----------------------------------------------------

        (
            "GET",
            "/products?id=25",
            "",
        ),

        # ----------------------------------------------------
        # SQL INJECTION
        # ----------------------------------------------------

        (
            "GET",
            "/products?id=1' OR '1'='1",
            "",
        ),

        # ----------------------------------------------------
        # XSS
        # ----------------------------------------------------

        (
            "GET",
            "/search?q=<script>alert(1)</script>",
            "",
        ),

        # ----------------------------------------------------
        # PATH TRAVERSAL
        # ----------------------------------------------------

        (
            "GET",
            "/download?file=../../../../etc/passwd",
            "",
        ),

        # ----------------------------------------------------
        # COMMAND INJECTION
        # ----------------------------------------------------

        (
            "GET",
            "/ping?host=127.0.0.1;whoami",
            "",
        ),
    ]

    print()

    print(
        "=" * 80
    )

    print(
        "DEFENZA FUSION ENGINE"
    )

    print(
        "=" * 80
    )

    for index, (
        method,
        url,
        body,
    ) in enumerate(
        test_requests,
        start=1,
    ):

        print()

        print(
            "=" * 80
        )

        print(
            f"TEST REQUEST #{index}"
        )

        print(
            "=" * 80
        )

        print()

        print(
            f"{method} {url}"
        )

        try:

            result = analyze_request(
                method,
                url,
                body,
            )

            print_result(
                result
            )

        except Exception as error:

            print()

            print(
                "ERROR:"
            )

            print(
                str(error)
            )

            print()

            raise

    print()

    print(
        "=" * 80
    )

    print(
        "DEFENZA FUSION TEST COMPLETE"
    )

    print(
        "=" * 80
    )