import torch
import pandas as pd

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

# ============================================================
# PATHS
# ============================================================

MODEL_DIR = r"..\trained\distilbert-defenza"
TOKENIZER_DIR = r"..\tokenizer\distilbert-defenza"

# ============================================================
# LOAD MODEL
# ============================================================

print("\n========================================")
print("   DEFENZA UNSEEN DATA EVALUATION")
print("========================================\n")

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    TOKENIZER_DIR
)

print("Loading model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)

model.eval()

print("Model loaded successfully!\n")


# ============================================================
# UNSEEN TEST DATA
# ============================================================

data = [

    # ---------------- BENIGN ----------------

    {
        "method": "GET",
        "url": "/home",
        "body": "",
        "expected": "benign",
    },

    {
        "method": "GET",
        "url": "/products?category=electronics&page=2",
        "body": "",
        "expected": "benign",
    },

    {
        "method": "GET",
        "url": "/search?q=wireless+headphones",
        "body": "",
        "expected": "benign",
    },

    {
        "method": "POST",
        "url": "/login",
        "body": "username=john&password=hello123",
        "expected": "benign",
    },

    {
        "method": "GET",
        "url": "/api/users?page=3&limit=10",
        "body": "",
        "expected": "benign",
    },


    # ---------------- SQL INJECTION ----------------

    {
        "method": "GET",
        "url": "/products?id=10%20OR%201=1",
        "body": "",
        "expected": "sqli",
    },

    {
        "method": "GET",
        "url": "/user?id=5' AND 'x'='x",
        "body": "",
        "expected": "sqli",
    },

    {
        "method": "POST",
        "url": "/login",
        "body": "username=admin'--&password=test",
        "expected": "sqli",
    },

    {
        "method": "GET",
        "url": "/search?q=' UNION SELECT NULL,NULL--",
        "body": "",
        "expected": "sqli",
    },

    {
        "method": "GET",
        "url": "/item?id=1%27%20OR%20%271%27=%271",
        "body": "",
        "expected": "sqli",
    },


    # ---------------- XSS ----------------

    {
        "method": "GET",
        "url": "/search?q=<img src=x onerror=alert(1)>",
        "body": "",
        "expected": "xss",
    },

    {
        "method": "GET",
        "url": "/comment?text=<svg onload=alert(1)>",
        "body": "",
        "expected": "xss",
    },

    {
        "method": "POST",
        "url": "/profile",
        "body": "name=<script>alert(document.domain)</script>",
        "expected": "xss",
    },

    {
        "method": "GET",
        "url": "/page?name=javascript:alert(1)",
        "body": "",
        "expected": "xss",
    },

    {
        "method": "GET",
        "url": "/search?q=%3Ciframe%20src=javascript:alert(1)%3E",
        "body": "",
        "expected": "xss",
    },


    # ---------------- PATH TRAVERSAL ----------------

    {
        "method": "GET",
        "url": "/files?name=../../config.ini",
        "body": "",
        "expected": "path_traversal",
    },

    {
        "method": "GET",
        "url": "/download?file=../../../private/data.txt",
        "body": "",
        "expected": "path_traversal",
    },

    {
        "method": "GET",
        "url": "/image?path=..%2F..%2Fsecret.txt",
        "body": "",
        "expected": "path_traversal",
    },

    {
        "method": "GET",
        "url": "/static/../../../../etc/hosts",
        "body": "",
        "expected": "path_traversal",
    },

    {
        "method": "GET",
        "url": "/read?file=%2e%2e%2f%2e%2e%2fconfig.json",
        "body": "",
        "expected": "path_traversal",
    },


    # ---------------- COMMAND INJECTION ----------------

    {
        "method": "GET",
        "url": "/ping?host=127.0.0.1|whoami",
        "body": "",
        "expected": "cmdi",
    },

    {
        "method": "GET",
        "url": "/lookup?host=example.com;id",
        "body": "",
        "expected": "cmdi",
    },

    {
        "method": "POST",
        "url": "/diagnostics",
        "body": "host=127.0.0.1 && uname -a",
        "expected": "cmdi",
    },

    {
        "method": "GET",
        "url": "/exec?cmd=cat%20/etc/passwd",
        "body": "",
        "expected": "cmdi",
    },

    {
        "method": "GET",
        "url": "/ping?host=$(whoami)",
        "body": "",
        "expected": "cmdi",
    },
]


# ============================================================
# PREDICTION
# ============================================================

def predict(method, url, body):

    text = (
        f"METHOD: {method} "
        f"URL: {url} "
        f"BODY: {body} "
        f"REQUEST: {method} {url} {body}"
    )

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
    )

    with torch.no_grad():

        outputs = model(**inputs)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1
        )

        predicted_id = torch.argmax(
            probabilities,
            dim=1
        ).item()

    predicted_label = model.config.id2label[predicted_id]

    confidence = probabilities[0][predicted_id].item()

    return predicted_label, confidence


# ============================================================
# RUN EVALUATION
# ============================================================

y_true = []
y_pred = []

results = []

print("Running unseen tests...\n")

for index, item in enumerate(data, 1):

    predicted, confidence = predict(
        item["method"],
        item["url"],
        item["body"],
    )

    y_true.append(item["expected"])
    y_pred.append(predicted)

    results.append({
        "test": index,
        "expected": item["expected"],
        "predicted": predicted,
        "confidence": confidence,
        "correct": predicted == item["expected"],
    })

    status = "PASS" if predicted == item["expected"] else "FAIL"

    print(
        f"[{status}] "
        f"{index:02d} | "
        f"Expected: {item['expected']:16} | "
        f"Predicted: {predicted:16} | "
        f"Confidence: {confidence:.4f}"
    )


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_true,
    y_pred
)

print("\n========================================")
print("OVERALL ACCURACY")
print("========================================")

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Correct : {sum(y_t == y_p for y_t, y_p in zip(y_true, y_pred))}")
print(f"Total   : {len(y_true)}")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

labels = [
    "benign",
    "sqli",
    "xss",
    "cmdi",
    "path_traversal",
]

print("\n========================================")
print("CLASSIFICATION REPORT")
print("========================================\n")

print(
    classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("========================================")
print("CONFUSION MATRIX")
print("========================================\n")

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=labels,
)

print("Labels:")
print(labels)

print("\nMatrix:")
print(cm)


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    "unseen_results.csv",
    index=False,
)

print("\nResults saved to:")
print("unseen_results.csv")

print("\n========================================")
print("UNSEEN EVALUATION COMPLETE")
print("========================================")