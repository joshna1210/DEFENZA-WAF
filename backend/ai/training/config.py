from pathlib import Path

# =========================
# DEFENZA TRAINING CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# DATASET
# =========================

DATASET_DIR = BASE_DIR / "datasets" / "processed"

TRAIN_FILE = DATASET_DIR / "train.csv"
VALIDATION_FILE = DATASET_DIR / "validation.csv"
TEST_FILE = DATASET_DIR / "test.csv"


# =========================
# OUTPUT DIRECTORIES
# =========================

MODEL_DIR = BASE_DIR / "trained" / "distilbert-defenza"

TOKENIZER_DIR = BASE_DIR / "tokenizer" / "distilbert-defenza"


# =========================
# MODEL
# =========================

MODEL_NAME = "distilbert-base-uncased"


# =========================
# DEFENZA CLASSES
# =========================

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

NUM_LABELS = len(LABELS)


# =========================
# TRAINING
# =========================

# Shorter sequences = faster CPU training
MAX_LENGTH = 128

# 16 GB RAM system
BATCH_SIZE = 8
EVAL_BATCH_SIZE = 8

# Start with 2 epochs
EPOCHS = 2

LEARNING_RATE = 2e-5

WEIGHT_DECAY = 0.01

# Transformers 5.x recommends warmup_steps
WARMUP_STEPS = 100

SEED = 42


# =========================
# REPRODUCIBILITY
# =========================

import random
import numpy as np
import torch

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)