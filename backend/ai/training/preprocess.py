import pandas as pd

from config import TRAIN_FILE, VALIDATION_FILE, TEST_FILE


def build_text(row):
    """
    Combine HTTP request components into one model input.
    """

    method = str(row.get("method", ""))
    url = str(row.get("url", ""))
    body = str(row.get("body", ""))
    request = str(row.get("request", ""))

    text = (
        f"METHOD: {method} "
        f"URL: {url} "
        f"BODY: {body} "
        f"REQUEST: {request}"
    )

    return text.strip()


def load_dataset(filepath):
    """
    Load CSV and prepare model text + labels.
    """

    df = pd.read_csv(filepath)

    # Remove rows with missing labels
    df = df.dropna(subset=["label"])

    # Normalize labels
    df["label"] = df["label"].astype(str).str.lower().str.strip()

    # Build Transformer input
    df["text"] = df.apply(build_text, axis=1)

    return df


def load_all_datasets():

    train_df = load_dataset(TRAIN_FILE)
    validation_df = load_dataset(VALIDATION_FILE)
    test_df = load_dataset(TEST_FILE)

    return train_df, validation_df, test_df


if __name__ == "__main__":

    train, validation, test = load_all_datasets()

    print("\n===== DEFENZA DATASET =====")

    print(f"Training samples   : {len(train)}")
    print(f"Validation samples : {len(validation)}")
    print(f"Test samples       : {len(test)}")

    print("\n===== LABEL DISTRIBUTION =====")

    print("\nTRAIN:")
    print(train["label"].value_counts())

    print("\nVALIDATION:")
    print(validation["label"].value_counts())

    print("\nTEST:")
    print(test["label"].value_counts())

    print("\n===== SAMPLE INPUT =====")

    print(train["text"].iloc[0])