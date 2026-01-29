"""Training script for Guard-IA DistilBERT classifier.

Fine-tunes distilbert-base-uncased on email phishing data.
Tracks experiments with MLflow.
"""

import json
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

from src.config import (
    BATCH_SIZE,
    DATA_SPLITS_DIR,
    EPOCHS,
    LEARNING_RATE,
    MAX_SEQ_LENGTH,
    MLFLOW_EXPERIMENT_NAME,
    MODEL_NAME,
    MODEL_OUTPUT_DIR,
    NUM_LABELS,
    WARMUP_STEPS,
    WEIGHT_DECAY,
)
from src.preprocess import preprocess_text


def _load_splits(splits_dir: str = DATA_SPLITS_DIR) -> tuple[Dataset, Dataset]:
    """Load train and val splits as HuggingFace Datasets."""
    splits_path = Path(splits_dir)
    train_df = pd.read_csv(splits_path / "train.csv")
    val_df = pd.read_csv(splits_path / "val.csv")

    # Ensure text is preprocessed
    train_df["text"] = train_df["text"].apply(preprocess_text)
    val_df["text"] = val_df["text"].apply(preprocess_text)

    train_ds = Dataset.from_pandas(train_df[["text", "label"]])
    val_ds = Dataset.from_pandas(val_df[["text", "label"]])
    return train_ds, val_ds


def _compute_metrics(eval_pred) -> dict:
    """Compute metrics during training evaluation."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "precision": precision_score(labels, predictions, zero_division=0),
        "recall": recall_score(labels, predictions, zero_division=0),
        "f1": f1_score(labels, predictions, zero_division=0),
    }


def train() -> None:
    """Fine-tune DistilBERT on email phishing dataset.

    Architecture:
    - Base model: distilbert-base-uncased (66M params)
    - Task: Binary classification (phishing vs legitimate)
    - Hardware: Apple M-series with MPS acceleration or CUDA
    """
    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=NUM_LABELS
    )

    # Device selection
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    # Load data
    print("Loading data splits...")
    train_ds, val_ds = _load_splits()
    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}")

    # Tokenize
    def tokenize_fn(examples):
        return tokenizer(
            examples["text"],
            max_length=MAX_SEQ_LENGTH,
            truncation=True,
            padding="max_length",
        )

    train_ds = train_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    val_ds = val_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    train_ds.set_format("torch")
    val_ds.set_format("torch")

    # Training arguments
    output_dir = Path(MODEL_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE * 2,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        warmup_steps=WARMUP_STEPS,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=10,
        fp16=device == "cuda",
        use_mps_device=device == "mps",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=_compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # Train with MLflow tracking
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    with mlflow.start_run(run_name="distilbert-finetune"):
        mlflow.log_params({
            "model_name": MODEL_NAME,
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "max_seq_length": MAX_SEQ_LENGTH,
            "weight_decay": WEIGHT_DECAY,
            "train_samples": len(train_ds),
            "val_samples": len(val_ds),
            "device": device,
        })

        print("Starting training...")
        train_result = trainer.train()

        # Log training metrics
        mlflow.log_metrics({
            "train_loss": train_result.metrics.get("train_loss", 0),
            "train_runtime": train_result.metrics.get("train_runtime", 0),
        })

        # Evaluate on validation set
        eval_metrics = trainer.evaluate()
        mlflow.log_metrics({
            f"val_{k}": v for k, v in eval_metrics.items()
            if isinstance(v, (int, float))
        })

        # Save model
        print(f"Saving model to {output_dir}...")
        trainer.save_model(str(output_dir))
        tokenizer.save_pretrained(str(output_dir))

        # Save Guard-IA version tag in config
        config_path = output_dir / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            config["_guard_ia_version"] = "0.1.0"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

        # Log model artifact
        mlflow.log_artifacts(str(output_dir), "model")

        print("Training complete!")
        print(f"Eval metrics: {eval_metrics}")


if __name__ == "__main__":
    train()
