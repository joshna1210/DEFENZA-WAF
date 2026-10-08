from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from xgboost import XGBClassifier


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "xgb"

TRAIN_FILE = DATASET_DIR / "train_features.csv"
VALIDATION_FILE = DATASET_DIR / "validation_features.csv"
TEST_FILE = DATASET_DIR / "test_features.csv"

MODEL_DIR = BASE_DIR / "trained" / "xgboost-defenza"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MODEL_FILE = MODEL_DIR / "xgboost_model.json"

LABEL_MAP_FILE = MODEL_DIR / "label_mapping.csv"


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
    for label, index in LABEL2ID.items()
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(file_path):

    print(f"\nLoading: {file_path.name}")

    df = pd.read_csv(file_path)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_data(df):

    if "label" not in df.columns:
        raise ValueError(
            "Dataset does not contain 'label' column."
        )

    # Everything except label is an input feature
    feature_columns = [
        column
        for column in df.columns
        if column != "label"
    ]

    X = df[feature_columns].copy()

    # Convert class names to numeric IDs
    y = df["label"].map(LABEL2ID)

    # Check for unknown labels
    if y.isna().any():

        unknown_labels = (
            df.loc[y.isna(), "label"]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"Unknown labels found: {unknown_labels}"
        )

    y = y.astype(int)

    return X, y, feature_columns


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("DEFENZA XGBOOST TRAINING")
    print("=" * 70)

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    train_df = load_dataset(TRAIN_FILE)

    validation_df = load_dataset(
        VALIDATION_FILE
    )

    test_df = load_dataset(
        TEST_FILE
    )

    # --------------------------------------------------------
    # Prepare datasets
    # --------------------------------------------------------

    X_train, y_train, feature_columns = (
        prepare_data(train_df)
    )

    X_validation, y_validation, _ = (
        prepare_data(validation_df)
    )

    X_test, y_test, _ = (
        prepare_data(test_df)
    )

    print()
    print("=" * 70)
    print("DATASET INFORMATION")
    print("=" * 70)

    print(f"Training samples   : {len(X_train)}")
    print(f"Validation samples : {len(X_validation)}")
    print(f"Test samples       : {len(X_test)}")
    print(f"Number of features : {len(feature_columns)}")
    print(f"Number of classes  : {len(LABELS)}")

    print()
    print("Features:")

    for index, feature in enumerate(
        feature_columns,
        start=1
    ):
        print(
            f"{index:2}. {feature}"
        )

    # --------------------------------------------------------
    # Label mapping
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("LABEL MAPPING")
    print("=" * 70)

    for class_id, label in ID2LABEL.items():

        print(
            f"{class_id} -> {label}"
        )

    # Save label mapping
    label_mapping_df = pd.DataFrame(
        {
            "id": list(ID2LABEL.keys()),
            "label": list(ID2LABEL.values()),
        }
    )

    label_mapping_df.to_csv(
        LABEL_MAP_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Create XGBoost model
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CREATING XGBOOST MODEL")
    print("=" * 70)

    model = XGBClassifier(

        # Number of boosting rounds
        n_estimators=300,

        # Tree depth
        max_depth=6,

        # Learning rate
        learning_rate=0.05,

        # Minimum loss reduction
        gamma=0,

        # Subsample rows
        subsample=0.9,

        # Subsample features
        colsample_bytree=0.9,

        # Minimum child weight
        min_child_weight=1,

        # Regularization
        reg_alpha=0.0,
        reg_lambda=1.0,

        # Multi-class classification
        objective="multi:softprob",

        num_class=len(LABELS),

        eval_metric="mlogloss",

        # CPU
        tree_method="hist",

        # Reproducibility
        random_state=42,

        # Prevent unnecessary output
        verbosity=1,
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)

    model.fit(
        X_train,
        y_train,

        eval_set=[
            (
                X_train,
                y_train
            ),
            (
                X_validation,
                y_validation
            ),
        ],

        verbose=True,
    )

    # --------------------------------------------------------
    # Validation evaluation
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    validation_predictions = (
        model.predict(X_validation)
    )

    validation_accuracy = accuracy_score(
        y_validation,
        validation_predictions
    )

    print(
        f"Validation Accuracy: "
        f"{validation_accuracy:.4f}"
    )

    print()
    print(
        classification_report(
            y_validation,
            validation_predictions,
            target_names=LABELS,
            digits=4,
        )
    )

    # --------------------------------------------------------
    # Test evaluation
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)

    test_predictions = (
        model.predict(X_test)
    )

    test_accuracy = accuracy_score(
        y_test,
        test_predictions
    )

    print(
        f"Test Accuracy: "
        f"{test_accuracy:.4f}"
    )

    print()
    print("Classification Report:")

    print(
        classification_report(
            y_test,
            test_predictions,
            target_names=LABELS,
            digits=4,
        )
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    print()
    print("Confusion Matrix:")

    cm = confusion_matrix(
        y_test,
        test_predictions
    )

    print()

    print(
        "Labels:",
        LABELS
    )

    print(cm)

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TOP FEATURE IMPORTANCE")
    print("=" * 70)

    importance = (
        model.feature_importances_
    )

    importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": importance,
        }
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False
        )
    )

    for _, row in importance_df.head(15).iterrows():

        print(
            f"{row['feature']:35} "
            f"{row['importance']:.6f}"
        )

    # Save feature importance
    importance_df.to_csv(
        MODEL_DIR / "feature_importance.csv",
        index=False
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SAVING MODEL")
    print("=" * 70)

    model.save_model(
        MODEL_FILE
    )

    print(
        f"Model saved to:\n"
        f"{MODEL_FILE}"
    )

    print(
        f"Label mapping saved to:\n"
        f"{LABEL_MAP_FILE}"
    )

    print()
    print("=" * 70)
    print("XGBOOST TRAINING COMPLETE")
    print("=" * 70)