from pathlib import Path

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TEST_FILE = BASE_DIR / "datasets" / "processed" / "test.csv"
MODEL_DIR = BASE_DIR / "trained" / "distilbert-defenza"


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


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 8
MAX_LENGTH = 128


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("DEFENZA - DistilBERT Test Evaluation")
print("=" * 70)

print("\nLoading test dataset...")

df = pd.read_csv(TEST_FILE)

print(f"Test samples: {len(df)}")
print(f"Test file: {TEST_FILE}")

# Convert labels to IDs
y_true = df["label"].map(LABEL2ID).values

texts = df["request"].fillna("").astype(str).tolist()


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_DIR
)

print("Loading trained DistilBERT model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)

model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model.to(device)

print(f"Device: {device}")


# ============================================================
# PREDICTION
# ============================================================

print("\nRunning inference...")
print(f"Batch size: {BATCH_SIZE}")
print(f"Max sequence length: {MAX_LENGTH}")

all_predictions = []

with torch.no_grad():

    for start in range(0, len(texts), BATCH_SIZE):

        batch_texts = texts[start:start + BATCH_SIZE]

        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(device)
            for key, value in encoded.items()
        }

        outputs = model(**encoded)

        predictions = torch.argmax(
            outputs.logits,
            dim=-1
        )

        all_predictions.extend(
            predictions.cpu().numpy()
        )

        processed = min(
            start + BATCH_SIZE,
            len(texts)
        )

        if processed % 100 == 0 or processed == len(texts):
            print(
                f"Processed {processed}/{len(texts)}"
            )


# ============================================================
# EVALUATION
# ============================================================

y_pred = all_predictions

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

print("\nClassification Report:")
print()

print(
    classification_report(
        y_true,
        y_pred,
        target_names=LABELS,
        digits=4,
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("Confusion Matrix:")
print()

cm = confusion_matrix(
    y_true,
    y_pred,
)

print(cm)


# ============================================================
# SAVE PREDICTIONS
# ============================================================

df["true_label"] = df["label"]

df["predicted_label"] = [
    LABELS[index]
    for index in y_pred
]

output_file = (
    BASE_DIR
    / "datasets"
    / "processed"
    / "distilbert_test_predictions.csv"
)

df.to_csv(
    output_file,
    index=False
)

print("\nPredictions saved to:")
print(output_file)

print("\n" + "=" * 70)
print("Evaluation complete.")
print("=" * 70)