"""
DEFENZA AI Utilities
Shared helper functions.
"""

import os
import json
import random
import urllib.parse
import numpy as np

try:
    import torch
except ImportError:
    torch = None


def set_seed(seed=42):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


def clean_request(text):
    """Normalize HTTP request."""
    if not isinstance(text, str):
        return ""

    text = urllib.parse.unquote(text)
    text = text.lower()
    text = " ".join(text.split())

    return text


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)