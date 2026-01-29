"""Layer 2: ML Classification (~18ms).

DistilBERT (distilbert-base-uncased) fine-tuned for phishing detection.
66M parameters, max sequence length 256.

Singleton pattern: model is loaded once and reused.
Graceful degradation: if model is not available, returns score=0.0
and the pipeline continues with heuristics only.
"""

import time
import threading
from pathlib import Path

import structlog

from app.config import settings
from app.core.constants import EvidenceType, Severity
from app.services.pipeline.models import EvidenceItem, MLResult

logger = structlog.get_logger()

# Module-level singleton
_instance: "MLClassifier | None" = None
_lock = threading.Lock()


def get_ml_classifier() -> "MLClassifier":
    """Return the singleton MLClassifier instance (thread-safe)."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = MLClassifier()
    return _instance


class MLClassifier:
    """DistilBERT-based phishing classifier.

    Loads the model lazily on first prediction. If the model
    directory does not exist, operates in degraded mode.
    """

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._model_available = False
        self._load_attempted = False
        self._model_version = ""

    def _load_model(self) -> None:
        """Attempt to load DistilBERT model and tokenizer."""
        if self._load_attempted:
            return
        self._load_attempted = True

        model_path = Path(settings.ml_model_path)
        if not model_path.exists():
            logger.warning(
                "ml_model_not_found",
                path=str(model_path),
                msg="ML classifier will operate in degraded mode (heuristics only)",
            )
            return

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self._model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
            self._model.eval()

            # Read model version from config if available
            config_path = model_path / "config.json"
            if config_path.exists():
                import json
                with open(config_path) as f:
                    config = json.load(f)
                self._model_version = config.get("_guard_ia_version", "unknown")

            self._model_available = True
            logger.info(
                "ml_model_loaded",
                path=str(model_path),
                version=self._model_version,
                params=sum(p.numel() for p in self._model.parameters()),
            )
        except Exception as exc:
            logger.error(
                "ml_model_load_failed",
                error=str(exc),
                path=str(model_path),
            )
            self._model = None
            self._tokenizer = None
            self._model_available = False

    async def predict(self, text: str) -> MLResult:
        """Run inference on email text.

        Returns MLResult with score, confidence, and model metadata.
        If model is unavailable, returns degraded result (score=0.0).
        """
        start = time.monotonic()
        self._load_model()

        if not self._model_available or self._model is None or self._tokenizer is None:
            return MLResult(
                score=0.0,
                confidence=0.0,
                model_available=False,
                model_version="",
                execution_time_ms=int((time.monotonic() - start) * 1000),
            )

        try:
            import torch

            # Tokenize
            inputs = self._tokenizer(
                text,
                max_length=settings.ml_max_seq_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )

            # Inference (no gradient computation)
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits

            # Softmax for probabilities
            probs = torch.softmax(logits, dim=-1)

            # Assuming binary classification: [legitimate, phishing]
            phishing_score = probs[0][1].item()
            confidence = max(probs[0][0].item(), probs[0][1].item())

            evidences: list[EvidenceItem] = []
            if phishing_score > 0.5:
                evidences.append(EvidenceItem(
                    type=EvidenceType.ML_HIGH_SCORE,
                    severity=Severity.HIGH if phishing_score > 0.8 else Severity.MEDIUM,
                    description=(
                        f"ML classifier scored {phishing_score:.4f} "
                        f"(confidence: {confidence:.4f})"
                    ),
                    raw_data={
                        "score": round(phishing_score, 4),
                        "confidence": round(confidence, 4),
                        "model_version": self._model_version,
                    },
                ))

            elapsed = int((time.monotonic() - start) * 1000)
            logger.info(
                "ml_prediction_complete",
                score=round(phishing_score, 4),
                confidence=round(confidence, 4),
                duration_ms=elapsed,
            )

            return MLResult(
                score=phishing_score,
                confidence=confidence,
                model_available=True,
                model_version=self._model_version,
                evidences=evidences,
                execution_time_ms=elapsed,
            )

        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            logger.error("ml_prediction_failed", error=str(exc))
            return MLResult(
                score=0.0,
                confidence=0.0,
                model_available=True,
                model_version=self._model_version,
                execution_time_ms=elapsed,
            )
