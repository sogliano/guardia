"""Inference utilities for Guard-IA DistilBERT classifier.

Provides standalone prediction functions for use outside the
backend pipeline (e.g., CLI testing, notebook experiments).
"""

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import MAX_SEQ_LENGTH, MODEL_OUTPUT_DIR
from src.preprocess import preprocess_text


def load_model(
    model_path: str = MODEL_OUTPUT_DIR,
) -> tuple[AutoTokenizer, AutoModelForSequenceClassification]:
    """Load fine-tuned model and tokenizer for inference."""
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    return tokenizer, model


def predict(
    text: str,
    model: AutoModelForSequenceClassification | None = None,
    tokenizer: AutoTokenizer | None = None,
) -> dict:
    """Run inference on a single email text.

    Returns:
        dict with keys:
          - score (float 0-1): phishing probability
          - confidence (float 0-1): max class probability
          - label (str): "phishing" or "legitimate"
    """
    if model is None or tokenizer is None:
        tokenizer, model = load_model()

    cleaned = preprocess_text(text)
    inputs = tokenizer(
        cleaned,
        max_length=MAX_SEQ_LENGTH,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)

    phishing_score = probs[0][1].item()
    confidence = max(probs[0][0].item(), probs[0][1].item())
    label = "phishing" if phishing_score >= 0.5 else "legitimate"

    return {
        "score": round(phishing_score, 4),
        "confidence": round(confidence, 4),
        "label": label,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Urgent: Your account has been compromised. Click here to verify your identity."

    print(f"Input: {text[:100]}...")
    result = predict(text)
    print(f"Result: {result}")
