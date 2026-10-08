from pathlib import Path
import pandas as pd

from http_features import extract_features


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = BASE_DIR / "datasets" / "processed"
OUTPUT_DIR = BASE_DIR / "datasets" / "xgb"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


TRAIN_FILE = DATASET_DIR / "train.csv"
VALIDATION_FILE = DATASET_DIR / "validation.csv"
TEST_FILE = DATASET_DIR / "test.csv"


# ============================================================
# DATASET PROCESSING
# ============================================================

def build_features(input_file, output_file):

    print("\n" + "=" * 70)
    print(f"Processing: {input_file.name}")
    print("=" * 70)

    df = pd.read_csv(input_file)

    print(f"Rows: {len(df)}")

    required_columns = [
        "method",
        "url",
        "body",
        "label",
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Missing required column: {column}"
            )

    feature_rows = []

    for index, row in df.iterrows():

        method = row["method"]
        url = row["url"]
        body = row["body"]

        features = extract_features(
            method,
            url,
            body
        )

        # Keep the original label
        features["label"] = row["label"]

        feature_rows.append(features)

        if (index + 1) % 1000 == 0:
            print(
                f"Processed "
                f"{index + 1}/{len(df)}"
            )

    feature_df = pd.DataFrame(feature_rows)

    feature_df.to_csv(
        output_file,
        index=False
    )

    print("\nSaved:")
    print(output_file)

    print("\nFeature shape:")
    print(feature_df.shape)

    print("\nLabel distribution:")
    print(feature_df["label"].value_counts())

    print("\nFeature columns:")
    print(
        [
            column
            for column in feature_df.columns
            if column != "label"
        ]
    )

    return feature_df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("DEFENZA XGBOOST DATASET BUILDER")
    print("=" * 70)

    train_output = OUTPUT_DIR / "train_features.csv"
    validation_output = OUTPUT_DIR / "validation_features.csv"
    test_output = OUTPUT_DIR / "test_features.csv"

    build_features(
        TRAIN_FILE,
        train_output
    )

    build_features(
        VALIDATION_FILE,
        validation_output
    )

    build_features(
        TEST_FILE,
        test_output
    )

    print("\n")
    print("=" * 70)
    print("DATASET BUILD COMPLETE")
    print("=" * 70)

    print("\nGenerated files:")

    print(train_output)
    print(validation_output)
    print(test_output)