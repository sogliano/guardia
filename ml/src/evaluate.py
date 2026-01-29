"""Evaluation script for Guard-IA DistilBERT classifier.

Runs comprehensive evaluation on the test set and logs metrics to MLflow.
"""

from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.config import (
    BATCH_SIZE,
    DATA_SPLITS_DIR,
    MAX_SEQ_LENGTH,
    MLFLOW_EXPERIMENT_NAME,
    MODEL_OUTPUT_DIR,
)
from src.preprocess import preprocess_text


def evaluate(model_path: str = MODEL_OUTPUT_DIR) -> dict:
    """Evaluate model on test set.

    Metrics targets (thesis goals):
    - Precision >= 98.66%
    - Recall >= 99.57%
    - F1-Score: derived
    - Confusion matrix
    - ROC-AUC
    """
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()

    # Device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    model.to(device)
    print(f"Using device: {device}")

    # Load test data
    test_path = Path(DATA_SPLITS_DIR) / "test.csv"
    test_df = pd.read_csv(test_path)
    test_df["text"] = test_df["text"].apply(preprocess_text)
    print(f"Test samples: {len(test_df)}")

    # Tokenize
    test_ds = Dataset.from_pandas(test_df[["text", "label"]])

    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            max_length=MAX_SEQ_LENGTH,
            truncation=True,
            padding="max_length",
        )

    test_ds = test_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    test_ds.set_format("torch")

    # Inference in batches
    all_preds: list[int] = []
    all_probs: list[float] = []
    all_labels: list[int] = []

    batch_size = BATCH_SIZE * 2
    for i in range(0, len(test_ds), batch_size):
        batch = test_ds[i : i + batch_size]
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"]

        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=-1)

        preds = torch.argmax(probs, dim=-1).cpu().numpy()
        phishing_probs = probs[:, 1].cpu().numpy()

        all_preds.extend(preds.tolist())
        all_probs.extend(phishing_probs.tolist())
        all_labels.extend(labels.numpy().tolist())

    # Calculate metrics
    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)
    y_prob = np.array(all_probs)

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_true, y_prob)
    cm = confusion_matrix(y_true, y_pred)

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "true_negatives": int(cm[0][0]),
        "false_positives": int(cm[0][1]),
        "false_negatives": int(cm[1][0]),
        "true_positives": int(cm[1][1]),
    }

    # Print results
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f} (target: >= 0.9866)")
    print(f"Recall:    {recall:.4f} (target: >= 0.9957)")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  TN={cm[0][0]:4d}  FP={cm[0][1]:4d}")
    print(f"  FN={cm[1][0]:4d}  TP={cm[1][1]:4d}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=["legitimate", "phishing"]))

    # Log to MLflow
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    with mlflow.start_run(run_name="distilbert-evaluation"):
        mlflow.log_metrics({
            "test_accuracy": accuracy,
            "test_precision": precision,
            "test_recall": recall,
            "test_f1": f1,
            "test_roc_auc": roc_auc,
        })
        print("Metrics logged to MLflow.")

    return metrics


if __name__ == "__main__":
    evaluate()
