# ML Model Training Guide

Guía completa para entrenar, evaluar y deployar el modelo DistilBERT de detección de phishing en Guard-IA.

---

## Overview

Guard-IA usa **DistilBERT** (66M parámetros) fine-tuned para clasificación binaria:
- **Clase 0:** Legitimate email
- **Clase 1:** Phishing email

**Ventajas de DistilBERT:**
- 40% más pequeño que BERT-base (109M params)
- 60% más rápido en inferencia (~18ms vs ~45ms)
- Retiene 97% del performance de BERT
- Ideal para producción (baja latencia, bajo costo)

---

## Prerequisites

### Hardware Requirements

| Entorno | RAM | GPU | Tiempo de training |
|---------|-----|-----|-------------------|
| **Mínimo** | 16GB | No (CPU) | ~3-4 horas |
| **Recomendado** | 32GB | NVIDIA (8GB+ VRAM) | ~30-45 min |
| **Producción** | 64GB | NVIDIA A100/V100 | ~15-20 min |

### Software Requirements

```bash
# Python 3.11+
python --version

# Install dependencies
cd ml
pip install -r requirements.txt

# Key packages:
# - transformers==4.37.0
# - torch==2.1.2
# - datasets==2.16.1
# - scikit-learn==1.4.0
# - mlflow==2.10.0
```

### Dataset Requirements

**Tamaño mínimo:** 5,000 emails labeled
**Recomendado:** 10,000+ emails
**Distribución:** 50/50 phishing vs legitimate (balanced)

---

## Dataset Preparation

### 1. Collect Data Sources

#### Phishing Emails

**Fuentes públicas:**
- [PhishTank](https://www.phishtank.com/) - 100k+ phishing reports
- [OpenPhish](https://openphish.com/) - Real-time phishing feed
- [Kaggle Phishing Datasets](https://www.kaggle.com/datasets)
- [APWG eCrime Research](https://apwg.org/)

**Fuentes internas (Strike Security):**
- Reported phishing incidents
- Quarantined emails (historical)
- Honeypot captures

#### Legitimate Emails

**Fuentes públicas:**
- [Enron Email Dataset](https://www.cs.cmu.edu/~enron/) - 500k+ legitimate emails
- [SpamAssassin Ham Corpus](https://spamassassin.apache.org/old/publiccorpus/)

**Fuentes internas:**
- Whitelisted senders (partners, vendors)
- Internal communications (anonymized)

### 2. Format Dataset

Crear CSV con estructura:

```csv
text,label
"Dear customer, your account will be suspended unless you verify...",1
"Hi John, attached is the quarterly report we discussed.",0
"URGENT: Click here to claim your prize now!",1
"Meeting rescheduled to 3pm tomorrow. See you then.",0
```

**Columnas:**
- `text` (string): Email completo (subject + body)
- `label` (int): 0=legitimate, 1=phishing

**Preprocessing:**
- Concatenar subject + body: `f"{subject}\n\n{body}"`
- Remover HTML tags (usar BeautifulSoup)
- Remover headers técnicos (Received, X-Mailer, etc.)
- Mantener URLs (importantes para detección)
- Normalizar whitespace

### 3. Clean & Balance Dataset

```python
# ml/src/preprocess.py
import pandas as pd
from sklearn.model_selection import train_test_split

# Load raw data
df = pd.read_csv("data/raw/emails.csv")

# Remove duplicates
df = df.drop_duplicates(subset=["text"])

# Remove empty
df = df[df["text"].str.strip() != ""]

# Balance classes (si está desbalanceado)
df_phishing = df[df["label"] == 1]
df_legitimate = df[df["label"] == 0]

# Undersample majority class
min_count = min(len(df_phishing), len(df_legitimate))
df_phishing = df_phishing.sample(n=min_count, random_state=42)
df_legitimate = df_legitimate.sample(n=min_count, random_state=42)

df_balanced = pd.concat([df_phishing, df_legitimate], ignore_index=True)
df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"Total samples: {len(df_balanced)}")
print(f"Phishing: {(df_balanced['label'] == 1).sum()}")
print(f"Legitimate: {(df_balanced['label'] == 0).sum()}")

# Save processed
df_balanced.to_csv("data/processed/emails_clean.csv", index=False)
```

### 4. Split Dataset

**Distribución (ver `ml/src/config.py`):**
- **Train:** 80% (para entrenar el modelo)
- **Validation:** 10% (para tuning de hyperparámetros)
- **Test:** 10% (para evaluación final)

```python
# Split train/val/test
train_df, temp_df = train_test_split(
    df_balanced, test_size=0.2, random_state=42, stratify=df_balanced["label"]
)
val_df, test_df = train_test_split(
    temp_df, test_size=0.5, random_state=42, stratify=temp_df["label"]
)

# Save splits
train_df.to_csv("data/splits/train.csv", index=False)
val_df.to_csv("data/splits/val.csv", index=False)
test_df.to_csv("data/splits/test.csv", index=False)

print(f"Train: {len(train_df)} samples")
print(f"Val: {len(val_df)} samples")
print(f"Test: {len(test_df)} samples")
```

### 5. Verify Files

```bash
cd ml
tree data/

# Expected structure:
# data/
# ├── raw/
# │   └── emails.csv
# ├── processed/
# │   └── emails_clean.csv
# └── splits/
#     ├── train.csv (80%)
#     ├── val.csv (10%)
#     └── test.csv (10%)
```

---

## Training Process

### 1. Configure Hyperparameters

```python
# ml/src/config.py
from dataclasses import dataclass

@dataclass
class TrainingConfig:
    # Model
    model_name: str = "distilbert-base-uncased"
    num_labels: int = 2

    # Tokenization
    max_length: int = 512  # Max tokens per email (DistilBERT native support)
    truncation: bool = True
    padding: str = "max_length"

    # Training
    batch_size: int = 16  # Reduce to 8 si OOM en GPU
    learning_rate: float = 2e-5
    num_epochs: int = 3  # 3-5 epochs es suficiente
    weight_decay: float = 0.01
    warmup_steps: int = 500

    # Optimizer
    optimizer: str = "adamw"
    adam_epsilon: float = 1e-8

    # Paths
    train_file: str = "data/splits/train.csv"
    val_file: str = "data/splits/val.csv"
    test_file: str = "data/splits/test.csv"
    output_dir: str = "models/distilbert-guardia"

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "guardia-phishing-detection"

config = TrainingConfig()
```

### 2. Load & Tokenize Data

```python
# ml/src/train.py
from transformers import AutoTokenizer
from datasets import load_dataset

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(config.model_name)

# Load datasets
dataset = load_dataset(
    "csv",
    data_files={
        "train": config.train_file,
        "validation": config.val_file,
        "test": config.test_file,
    },
)

# Tokenize
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=config.truncation,
        max_length=config.max_length,
        padding=config.padding,
    )

tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset = tokenized_dataset.rename_column("label", "labels")
tokenized_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

print(f"Train samples: {len(tokenized_dataset['train'])}")
print(f"Val samples: {len(tokenized_dataset['validation'])}")
print(f"Test samples: {len(tokenized_dataset['test'])}")
```

### 3. Initialize Model

```python
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    config.model_name,
    num_labels=config.num_labels,
)

# Verificar device (GPU si está disponible)
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

print(f"Training on: {device}")
print(f"Model parameters: {model.num_parameters():,}")
```

### 4. Setup MLflow Tracking

```python
import mlflow
import mlflow.transformers

mlflow.set_tracking_uri(config.mlflow_tracking_uri)
mlflow.set_experiment(config.mlflow_experiment_name)

# Start run
mlflow.start_run()

# Log hyperparameters
mlflow.log_params({
    "model_name": config.model_name,
    "max_length": config.max_length,
    "batch_size": config.batch_size,
    "learning_rate": config.learning_rate,
    "num_epochs": config.num_epochs,
    "optimizer": config.optimizer,
})
```

### 5. Train Model

```python
from transformers import Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=-1)

    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary"
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

training_args = TrainingArguments(
    output_dir=config.output_dir,
    num_train_epochs=config.num_epochs,
    per_device_train_batch_size=config.batch_size,
    per_device_eval_batch_size=config.batch_size,
    learning_rate=config.learning_rate,
    weight_decay=config.weight_decay,
    warmup_steps=config.warmup_steps,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,  # Guardar solo 2 últimos checkpoints
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_dir="logs",
    logging_steps=100,
    report_to="none",  # MLflow log manual
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["validation"],
    compute_metrics=compute_metrics,
)

# Train
print("Starting training...")
trainer.train()

# Log metrics to MLflow
for log in trainer.state.log_history:
    if "eval_loss" in log:
        mlflow.log_metrics({
            "eval_loss": log["eval_loss"],
            "eval_accuracy": log["eval_accuracy"],
            "eval_precision": log["eval_precision"],
            "eval_recall": log["eval_recall"],
            "eval_f1": log["eval_f1"],
        }, step=log["epoch"])
```

### 6. Save Model

```python
# Save best model
trainer.save_model(config.output_dir)
tokenizer.save_pretrained(config.output_dir)

print(f"Model saved to {config.output_dir}")

# Log model to MLflow
mlflow.transformers.log_model(
    transformers_model={"model": model, "tokenizer": tokenizer},
    artifact_path="model",
)
```

---

## Evaluation

### 1. Test Set Evaluation

```python
# ml/src/evaluate.py
from transformers import pipeline

# Load model
classifier = pipeline(
    "text-classification",
    model=config.output_dir,
    device=0 if torch.cuda.is_available() else -1,
)

# Load test data
test_df = pd.read_csv(config.test_file)

# Predict
predictions = []
for text in test_df["text"]:
    result = classifier(text, truncation=True, max_length=config.max_length)
    pred_label = 1 if result[0]["label"] == "LABEL_1" else 0
    predictions.append(pred_label)

test_df["predicted"] = predictions

# Compute metrics
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)

y_true = test_df["label"]
y_pred = test_df["predicted"]

accuracy = accuracy_score(y_true, y_pred)
precision, recall, f1, _ = precision_recall_fscore_support(
    y_true, y_pred, average="binary"
)

print("=" * 50)
print("TEST SET EVALUATION")
print("=" * 50)
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")
print()

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:")
print(f"                Predicted")
print(f"                Legit  Phishing")
print(f"Actual Legit    {cm[0][0]:<6} {cm[0][1]:<6}")
print(f"Actual Phishing {cm[1][0]:<6} {cm[1][1]:<6}")
print()

# Detailed report
print(classification_report(y_true, y_pred, target_names=["Legitimate", "Phishing"]))

# Log to MLflow
mlflow.log_metrics({
    "test_accuracy": accuracy,
    "test_precision": precision,
    "test_recall": recall,
    "test_f1": f1,
})
```

### 2. Target Metrics

Para considerar el modelo **production-ready**:

| Métrica | Target | Razón |
|---------|--------|-------|
| **Accuracy** | ≥95% | Precisión general alta |
| **Precision** | ≥92% | Minimizar falsos positivos (legítimos marcados como phishing) |
| **Recall** | ≥88% | Detectar la mayoría de phishing (algunos pueden pasar) |
| **F1-score** | ≥90% | Balance entre precision y recall |

**Nota:** Preferimos **alta precisión** sobre alta recall porque:
- Falso positivo = email legítimo bloqueado (malo para negocio)
- Falso negativo = phishing pasa (mitigado por heuristics + LLM)

### 3. Error Analysis

```python
# Analizar falsos positivos
false_positives = test_df[(test_df["label"] == 0) & (test_df["predicted"] == 1)]
print(f"False Positives: {len(false_positives)}")
print("\nExamples:")
for idx, row in false_positives.head(5).iterrows():
    print(f"- {row['text'][:100]}...")

# Analizar falsos negativos
false_negatives = test_df[(test_df["label"] == 1) & (test_df["predicted"] == 0)]
print(f"\nFalse Negatives: {len(false_negatives)}")
print("\nExamples:")
for idx, row in false_negatives.head(5).iterrows():
    print(f"- {row['text'][:100]}...")

# Save errors for review
false_positives.to_csv("data/evaluation/false_positives.csv", index=False)
false_negatives.to_csv("data/evaluation/false_negatives.csv", index=False)
```

---

## Deployment

### 1. Prepare Model for Production

```bash
cd ml

# Verificar que modelo está completo
ls -lh models/distilbert-guardia/

# Debe contener:
# - config.json
# - pytorch_model.bin (o model.safetensors)
# - tokenizer_config.json
# - vocab.txt
# - special_tokens_map.json
```

### 2. Copy Model to Backend

```bash
# Copiar modelo a backend
cp -r models/distilbert-guardia backend/ml_models/

# Verificar
ls -lh backend/ml_models/distilbert-guardia/
```

### 3. Test Model Loading

```python
# Test en backend/app/services/pipeline/ml_classifier.py
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="ml_models/distilbert-guardia",
    device=-1,  # CPU en producción
)

# Test inference
test_email = "URGENT: Your account will be suspended unless you click here"
result = classifier(test_email, truncation=True, max_length=512)

print(f"Result: {result}")
# Expected: [{'label': 'LABEL_1', 'score': 0.92}]
```

### 4. Update Version in Backend

```python
# backend/app/core/constants.py
ML_MODEL_VERSION = "distilbert-guardia-v1.2"  # Update version
ML_MODEL_PATH = "ml_models/distilbert-guardia"
```

### 5. Deploy to Production

```bash
# Build Docker image con nuevo modelo
cd backend
docker build -t guardia-backend:latest .

# Deploy a Cloud Run
gcloud run deploy guardia-backend \
  --image gcr.io/<PROJECT>/guardia-backend:latest \
  --region us-east1 \
  --platform managed

# Verificar logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

## MLflow Tracking

### View Experiments

```bash
# Start MLflow UI
cd ml
mlflow ui --host 0.0.0.0 --port 5000

# Open browser: http://localhost:5000
```

### MLflow Artifacts

Para cada run, MLflow guarda:
- **Metrics:** accuracy, precision, recall, f1, loss (por epoch)
- **Parameters:** hyperparámetros (lr, batch_size, epochs)
- **Model:** modelo completo (pytorch + tokenizer)
- **Artifacts:** confusion matrix, training logs

### Compare Runs

En MLflow UI:
1. Select múltiples runs
2. Click "Compare"
3. Ver métricas side-by-side
4. Determinar mejor modelo

---

## Model Updates

### When to Retrain

Retrain el modelo cuando:
1. **Accuracy drops <90%** (monitorear en producción)
2. **Nuevos tipos de phishing** aparecen (BEC, deepfakes)
3. **Quarterly review** (cada 3 meses)
4. **Dataset grows** (>20% más samples)

### Retraining Process

```bash
# 1. Collect new labeled data
# 2. Append to existing dataset
cat data/processed/emails_clean.csv new_emails.csv > data/processed/emails_v2.csv

# 3. Re-split
python src/preprocess.py

# 4. Train new version
python src/train.py

# 5. Evaluate
python src/evaluate.py

# 6. Compare with current model (MLflow)
# 7. If better, deploy to staging
# 8. A/B test in staging (50/50 traffic)
# 9. If metrics improve, deploy to production
```

### A/B Testing

```python
# backend/app/services/pipeline/ml_classifier.py
import random

class MLClassifier:
    def __init__(self):
        self.model_a = load_model("ml_models/distilbert-v1.2")  # Current
        self.model_b = load_model("ml_models/distilbert-v1.3")  # New

    async def classify(self, text: str) -> float:
        # 50/50 split
        model = self.model_a if random.random() < 0.5 else self.model_b

        result = model(text)
        score = result[0]["score"] if result[0]["label"] == "LABEL_1" else 0.0

        # Log which model was used (para análisis)
        logger.info("ml_prediction", model=model.name, score=score)

        return score
```

---

## Troubleshooting

### OOM (Out of Memory) en Training

**Síntoma:** `RuntimeError: CUDA out of memory`

**Solución:**
```python
# Reducir batch size
config.batch_size = 8  # o 4

# Reducir max_length
config.max_length = 256  # de 512 a 256

# Usar gradient accumulation
training_args.gradient_accumulation_steps = 2  # Simula batch_size=16
```

### Model no converge (loss no baja)

**Síntoma:** Val loss no mejora después de 3 epochs

**Solución:**
```python
# Aumentar learning rate
config.learning_rate = 5e-5  # de 2e-5 a 5e-5

# Aumentar epochs
config.num_epochs = 5  # de 3 a 5

# Verificar data balanceada
print(train_df["label"].value_counts())
```

### Inference muy lenta (>100ms)

**Síntoma:** ML stage tarda >100ms (target: <20ms)

**Solución:**
```python
# 1. Usar GPU en producción
device = torch.device("cuda")

# 2. Reducir max_length
max_length = 256  # de 512 a 256

# 3. Batch inference (si es posible)
results = classifier(texts, batch_size=8)

# 4. Usar ONNX para optimizar
# (ver https://huggingface.co/docs/transformers/serialization)
```

---

## Resources

- [HuggingFace Transformers Docs](https://huggingface.co/docs/transformers/)
- [DistilBERT Paper](https://arxiv.org/abs/1910.01108)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [PyTorch Lightning](https://pytorch-lightning.readthedocs.io/) (alternativa a Trainer)

---

## Next Steps

1. ✅ Collect & prepare dataset (5k-10k samples)
2. ✅ Train DistilBERT model (3-5 epochs)
3. ✅ Evaluate on test set (≥90% F1)
4. ✅ Deploy to backend
5. ⏳ Monitor in production (accuracy, latency)
6. ⏳ Retrain quarterly con nuevo data

**Para dudas:** Ver [ARCHITECTURE.md](./ARCHITECTURE.md) o [DEVELOPER_SETUP.md](./DEVELOPER_SETUP.md).
