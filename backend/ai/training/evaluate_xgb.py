from pathlib import Path

import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TEST_FILE = BASE_DIR / "datasets" / "xgb" / "test_features.csv"
MODEL_FILE = BASE_DIR / "trained" / "xgboost-defenza" / "xgboost_model.json"


# ============================================================
# LABEL MAPPING
# ============================================================

LABELS = [
    "benign",
    "sqli",
    "xss",
    "cmdi",
    "path_traversal",
]

LABEL2ID = {
    "benign": 0,
    "sqli": 1,
    "xss": 2,
    "cmdi": 3,
    "path_traversal": 4,
}


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("DEFENZA - XGBoost Test Evaluation")
print("=" * 70)


# ============================================================
# LOAD TEST DATA
# ============================================================

print("\nLoading test dataset...")

df = pd.read_csv(TEST_FILE)

print(f"Test samples: {len(df)}")
print(f"Test file: {TEST_FILE}")


# ============================================================
# CHECK LABELS
# ============================================================

if "label" not in df.columns:
    raise ValueError("The test dataset does not contain a 'label' column.")

print("\nTest label distribution:")
print(df["label"].value_counts())


# ============================================================
# CONVERT STRING LABELS TO NUMERIC LABELS
# ============================================================

y_true = df["label"].map(LABEL2ID)

if y_true.isna().any():
    unknown = df.loc[y_true.isna(), "label"].unique()
    raise ValueError(
        f"Unknown labels found in test dataset: {unknown}"
    )

y_true = y_true.astype(int).values


# ============================================================
# PREPARE FEATURES
# ============================================================

X = df.drop(columns=["label"])


# Remove accidental index columns if present
for column in ["Unnamed: 0", "index"]:
    if column in X.columns:
        X = X.drop(columns=[column])


print(f"\nFeatures used: {X.shape[1]}")
print(f"Feature columns: {list(X.columns)}")


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading trained XGBoost model...")

model = xgb.XGBClassifier()

model.load_model(MODEL_FILE)

print("Model loaded successfully.")
print(f"Model file: {MODEL_FILE}")


# ============================================================
# PREDICTION
# ============================================================

print("\nRunning inference...")

y_pred = model.predict(X)

y_pred = y_pred.astype(int)

print("Inference complete.")


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_true,
    y_pred
)

print("\n" + "=" * 70)
print("FINAL TEST RESULTS")
print("=" * 70)

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Accuracy: {accuracy * 100:.2f}%")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:\n")

print(
    classification_report(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=LABELS,
        digits=4,
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("Confusion Matrix:\n")

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=list(range(len(LABELS))),
)

print(cm)


# ============================================================
# PER-CLASS CORRECT / INCORRECT
# ============================================================

print("\nPer-class results:")

for class_id, class_name in enumerate(LABELS):

    actual = (y_true == class_id).sum()
    correct = ((y_true == class_id) & (y_pred == class_id)).sum()
    incorrect = actual - correct

    print(
        f"{class_name:16s} "
        f"Actual={actual:4d} "
        f"Correct={correct:4d} "
        f"Incorrect={incorrect:4d}"
    )


# ============================================================
# SAVE PREDICTIONS
# ============================================================

result = df.copy()

result["true_label"] = [
    LABELS[i]
    for i in y_true
]

result["predicted_label"] = [
    LABELS[i]
    for i in y_pred
]

output_file = (
    BASE_DIR
    / "datasets"
    / "xgb"
    / "xgboost_test_predictions.csv"
)

result.to_csv(
    output_file,
    index=False
)

print("\nPredictions saved to:")
print(output_file)

print("\n" + "=" * 70)
print("XGBoost evaluation complete.")
print("=" * 70)