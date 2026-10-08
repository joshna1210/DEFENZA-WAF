import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ============================================================
# MODEL PATHS
# ============================================================

MODEL_DIR = r"..\trained\distilbert-defenza"
TOKENIZER_DIR = r"..\tokenizer\distilbert-defenza"


# ============================================================
# LOAD MODEL
# ============================================================

print("\n========================================")
print("      DEFENZA DISTILBERT TEST")
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
# PREDICTION FUNCTION
# ============================================================

def predict_request(method, url, body=""):

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

    label = model.config.id2label[predicted_id]

    confidence = probabilities[0][predicted_id].item()

    return label, confidence, probabilities[0]


# ============================================================
# UNSEEN TEST REQUESTS
# ============================================================

tests = [

    {
        "name": "Normal product request",
        "method": "GET",
        "url": "/products?id=25",
        "body": "",
    },

    {
        "name": "SQL Injection",
        "method": "GET",
        "url": "/products?id=1' OR '1'='1",
        "body": "",
    },

    {
        "name": "XSS",
        "method": "GET",
        "url": "/search?q=<script>alert(1)</script>",
        "body": "",
    },

    {
        "name": "Path Traversal",
        "method": "GET",
        "url": "/download?file=../../../../etc/passwd",
        "body": "",
    },

    {
        "name": "Command Injection",
        "method": "GET",
        "url": "/ping?host=127.0.0.1;whoami",
        "body": "",
    },

    {
        "name": "Normal API request",
        "method": "GET",
        "url": "/api/users?page=2&limit=20",
        "body": "",
    },

]


# ============================================================
# RUN TESTS
# ============================================================

for i, test in enumerate(tests, 1):

    label, confidence, probabilities = predict_request(
        test["method"],
        test["url"],
        test["body"]
    )

    print("=" * 70)

    print(f"TEST {i}: {test['name']}")

    print(f"Method     : {test['method']}")
    print(f"URL        : {test['url']}")

    print(f"\nPrediction : {label}")
    print(f"Confidence : {confidence:.4f}")

    print("\nClass probabilities:")

    for class_id, probability in enumerate(probabilities):

        class_name = model.config.id2label[class_id]

        print(
            f"  {class_name:18} "
            f"{probability.item():.4f}"
        )


print("\n" + "=" * 70)
print("DEFENZA TESTING COMPLETE")
print("=" * 70)