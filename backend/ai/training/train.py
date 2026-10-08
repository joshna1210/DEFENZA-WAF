import os
import numpy as np
import torch

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

from config import (
    MODEL_NAME,
    MODEL_DIR,
    TOKENIZER_DIR,
    LABEL2ID,
    ID2LABEL,
    NUM_LABELS,
    MAX_LENGTH,
    BATCH_SIZE,
    EVAL_BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    WEIGHT_DECAY,
    WARMUP_STEPS,
    SEED,
)

from preprocess import load_all_datasets


# ============================================================
# 1. REPRODUCIBILITY
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\n========================================")
print("       DEFENZA TRANSFORMER TRAINING")
print("========================================\n")

print("Loading datasets...")

train_df, validation_df, test_df = load_all_datasets()

print(f"Training samples   : {len(train_df)}")
print(f"Validation samples : {len(validation_df)}")
print(f"Test samples       : {len(test_df)}")


# ============================================================
# 3. CONVERT LABELS
# ============================================================

def encode_labels(df):

    df = df.copy()

    df["labels"] = df["label"].map(LABEL2ID)

    if df["labels"].isna().any():

        unknown = df.loc[
            df["labels"].isna(),
            "label"
        ].unique()

        raise ValueError(
            f"Unknown labels found: {unknown}"
        )

    df["labels"] = df["labels"].astype(int)

    return df


train_df = encode_labels(train_df)
validation_df = encode_labels(validation_df)
test_df = encode_labels(test_df)


# ============================================================
# 4. CONVERT TO HUGGING FACE DATASETS
# ============================================================

train_dataset = Dataset.from_pandas(
    train_df[["text", "labels"]],
    preserve_index=False,
)

validation_dataset = Dataset.from_pandas(
    validation_df[["text", "labels"]],
    preserve_index=False,
)

test_dataset = Dataset.from_pandas(
    test_df[["text", "labels"]],
    preserve_index=False,
)


# ============================================================
# 5. LOAD TOKENIZER
# ============================================================

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


# ============================================================
# 6. TOKENIZATION
# ============================================================

def tokenize_function(batch):

    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=MAX_LENGTH,
    )


print("Tokenizing training data...")

train_dataset = train_dataset.map(
    tokenize_function,
    batched=True,
    desc="Tokenizing training data",
)

print("Tokenizing validation data...")

validation_dataset = validation_dataset.map(
    tokenize_function,
    batched=True,
    desc="Tokenizing validation data",
)

print("Tokenizing test data...")

test_dataset = test_dataset.map(
    tokenize_function,
    batched=True,
    desc="Tokenizing test data",
)


# ============================================================
# 7. DYNAMIC PADDING
# ============================================================

data_collator = DataCollatorWithPadding(
    tokenizer=tokenizer
)


# ============================================================
# 8. LOAD DISTILBERT
# ============================================================

print("\nLoading DistilBERT model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS,
    id2label=ID2LABEL,
    label2id=LABEL2ID,
)


# ============================================================
# 9. METRICS
# ============================================================

def compute_metrics(eval_prediction):

    predictions, labels = eval_prediction

    predictions = np.argmax(
        predictions,
        axis=1,
    )

    accuracy = (
        predictions == labels
    ).mean()

    return {
        "accuracy": float(accuracy)
    }


# ============================================================
# 10. CREATE OUTPUT DIRECTORIES
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True,
)

os.makedirs(
    TOKENIZER_DIR,
    exist_ok=True,
)


# ============================================================
# 11. TRAINING ARGUMENTS
# ============================================================

training_args = TrainingArguments(

    output_dir=str(MODEL_DIR),

    num_train_epochs=EPOCHS,

    per_device_train_batch_size=BATCH_SIZE,

    per_device_eval_batch_size=EVAL_BATCH_SIZE,

    learning_rate=LEARNING_RATE,

    weight_decay=WEIGHT_DECAY,

    warmup_steps=WARMUP_STEPS,

    eval_strategy="epoch",

    save_strategy="epoch",

    logging_strategy="steps",

    logging_steps=100,

    load_best_model_at_end=True,

    metric_for_best_model="accuracy",

    greater_is_better=True,

    report_to="none",

    save_total_limit=2,

    fp16=False,

    dataloader_pin_memory=False,

    dataloader_num_workers=0,
)


# ============================================================
# 12. TRAINER
# ============================================================

trainer = Trainer(

    model=model,

    args=training_args,

    train_dataset=train_dataset,

    eval_dataset=validation_dataset,

    processing_class=tokenizer,

    data_collator=data_collator,

    compute_metrics=compute_metrics,
)


# ============================================================
# 13. START TRAINING
# ============================================================

print("\n========================================")
print("Starting DEFENZA training...")
print("========================================\n")

trainer.train()


# ============================================================
# 14. SAVE MODEL
# ============================================================

print("\nSaving trained model...")

trainer.save_model(
    str(MODEL_DIR)
)

tokenizer.save_pretrained(
    str(TOKENIZER_DIR)
)


# ============================================================
# 15. FINAL TEST EVALUATION
# ============================================================

print("\n========================================")
print("FINAL TEST RESULTS")
print("========================================\n")

results = trainer.evaluate(
    test_dataset
)

for key, value in results.items():

    if isinstance(value, (int, float)):

        print(
            f"{key}: {value:.4f}"
        )


print("\n========================================")
print("DEFENZA TRAINING COMPLETE")
print("========================================")