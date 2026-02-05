"""Layer 2: ML Classification (~18ms).

DistilBERT (distilbert-base-multilingual-cased) fine-tuned for phishing detection.
66M parameters, max sequence length 256.

Singleton pattern: model is loaded once and reused.
Graceful degradation: if model is not available, returns score=0.0
and the pipeline continues with heuristics only.

XAI Integration: Extracts top-k influential tokens using attention weights.
"""

import asyncio
import json
import time
import threading
from pathlib import Path

import structlog

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from app.config import settings
from app.core.constants import (
    ML_CLASSIFIER_THRESHOLD_CRITICAL,
    ML_CLASSIFIER_THRESHOLD_HIGH,
    EvidenceType,
    Severity,
)
from app.services.pipeline.models import EvidenceItem, MLResult

logger = structlog.get_logger()

# Module-level singleton
_instance: "MLClassifier | None" = None
_lock = threading.Lock()

# XAI Configuration
XAI_TOP_K_TOKENS = 5  # Number of top tokens to extract for explanations


def get_ml_classifier() -> "MLClassifier":
    """Return the singleton MLClassifier instance (thread-safe)."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = MLClassifier()
    return _instance


class MLClassifier:
    """DistilBERT-based phishing classifier with XAI capabilities.

    Loads the model lazily on first prediction. If the model
    directory does not exist, operates in degraded mode.

    XAI: Extracts attention-based token importances alongside predictions.
    """

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._model_available = False
        self._load_attempted = False
        self._model_version = ""

    @staticmethod
    def _is_meaningful_token(token: str, min_length: int = 2) -> bool:
        """Check if a token is meaningful for XAI display.
        
        Filters out:
        - Punctuation-only tokens
        - Single characters (except meaningful abbreviations)
        - Digits-only tokens
        - Pure whitespace
        - URL fragments and common noise
        """
        import string
        
        if not token:
            return False
        
        # Set of characters to filter
        filter_chars = set(string.punctuation + string.whitespace + "''""–—…·•►▪")
        
        # Filter punctuation-only tokens
        if all(c in filter_chars for c in token):
            return False
        
        # Filter very short tokens
        if len(token) < min_length:
            return False
        
        # Filter digits-only tokens
        if token.isdigit():
            return False
        
        # Filter URL fragments and common noise
        noise_patterns = ["http", "www", ":/", "//", "...", "===", "---"]
        if any(p in token.lower() for p in noise_patterns):
            return False
        
        return True

    def _load_model(self) -> None:
        """Attempt to load DistilBERT model and tokenizer."""
        if self._load_attempted:
            return
        self._load_attempted = True

        model_path = Path(settings.ml_model_path)
        if not model_path.exists():
            logger.info("ml_model_not_found_locally", path=str(model_path), msg="Attempting download from Hugging Face Hub...")
            try:
                # Download model from HF Hub
                model_name = settings.ml_model_hf_repo
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                # Save locally for future use
                model_path.mkdir(parents=True, exist_ok=True)
                self._tokenizer.save_pretrained(str(model_path))
                self._model.save_pretrained(str(model_path))
                logger.info("ml_model_downloaded_and_saved", path=str(model_path))
                
            except Exception as e:
                logger.warning(
                    "ml_model_download_failed",
                    error=str(e),
                    msg="ML classifier will operate in degraded mode (heuristics only)",
                )
                return

        if not _TORCH_AVAILABLE:
            logger.warning("ml_torch_not_installed", msg="torch/transformers not available")
            return

        try:
            if not self._tokenizer:
                self._tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            if not self._model:
                # Load model with attention output enabled for XAI
                self._model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                output_attentions=True,  # Enable attention for XAI
            )
            self._model.eval()

            # Read model version from config if available
            config_path = model_path / "config.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                # Try common version fields
                self._model_version = config.get(
                    "_guard_ia_version",
                    config.get("model_version", "distilbert-guardia-v2")
                )

            self._model_available = True
            logger.info(
                "ml_model_loaded",
                path=str(model_path),
                version=self._model_version,
                params=sum(p.numel() for p in self._model.parameters()),
                xai_enabled=True,
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

    def _extract_top_tokens(
        self, inputs: dict, attentions: tuple, top_k: int = XAI_TOP_K_TOKENS
    ) -> list[tuple[str, float]]:
        """Extract top-k influential tokens from attention weights.

        Uses the last-layer attention from [CLS] token to determine
        which tokens most influenced the classification decision.
        """
        if attentions is None or len(attentions) == 0:
            return []

        try:
            # Extract attention from last layer, [CLS] token (index 0)
            # Shape: (batch, heads, seq, seq)
            last_attn = attentions[-1]
            cls_attn = last_attn[0, :, 0, :]  # attention from CLS to all tokens
            token_importance = cls_attn.mean(dim=0)  # average over heads

            # Convert token IDs to actual tokens
            tokens = self._tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            scores = token_importance.tolist()

            # Filter out special tokens and build result
            token_scores: list[tuple[str, float]] = []
            special_tokens = set(self._tokenizer.all_special_tokens)

            for tok, score in zip(tokens, scores):
                if tok in special_tokens:
                    continue
                # Skip padding tokens
                if tok == "[PAD]" or tok == "<pad>":
                    continue
                # Clean up subword markers (## for BERT-style tokenizers)
                clean_tok = tok.replace("##", "").replace("▁", "").replace("Ġ", "").strip()
                
                # Filter out punctuation, single chars, and noise
                if self._is_meaningful_token(clean_tok):
                    token_scores.append((clean_tok.lower(), float(score)))

            # Deduplicate: aggregate scores for repeated tokens (keep max)
            token_max_scores: dict[str, float] = {}
            for tok, score in token_scores:
                if tok in token_max_scores:
                    token_max_scores[tok] = max(token_max_scores[tok], score)
                else:
                    token_max_scores[tok] = score
            
            # Convert back to list and sort by importance descending
            unique_token_scores = [(tok, score) for tok, score in token_max_scores.items()]
            unique_token_scores = sorted(unique_token_scores, key=lambda x: x[1], reverse=True)[:top_k]
            return unique_token_scores

        except Exception as exc:
            logger.warning("xai_token_extraction_failed", error=str(exc))
            return []

    def _predict_sync(self, text: str) -> MLResult:
        """Run inference synchronously with XAI (called via asyncio.to_thread)."""
        start = time.monotonic()
        self._load_model()

        if not self._model_available or self._model is None or self._tokenizer is None:
            return MLResult(
                score=0.0,
                confidence=0.0,
                model_available=False,
                model_version="",
                execution_time_ms=int((time.monotonic() - start) * 1000),
                top_tokens=[],
                xai_available=False,
            )

        try:
            # Tokenize
            inputs = self._tokenizer(
                text,
                max_length=settings.ml_max_seq_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt",
            )

            # Inference with attention output for XAI
            with torch.no_grad():
                outputs = self._model(**inputs, output_attentions=True)
                logits = outputs.logits
                attentions = outputs.attentions

            # Softmax for probabilities
            probs = torch.softmax(logits, dim=-1)

            # Assuming binary classification: [legitimate, phishing]
            phishing_score = probs[0][1].item()
            confidence = max(probs[0][0].item(), probs[0][1].item())

            # Extract XAI top tokens
            top_tokens = self._extract_top_tokens(inputs, attentions)
            xai_available = len(top_tokens) > 0

            evidences: list[EvidenceItem] = []
            if phishing_score > ML_CLASSIFIER_THRESHOLD_HIGH:
                # Include top tokens in evidence description
                token_context = ""
                if top_tokens:
                    token_names = [t[0] for t in top_tokens[:3]]
                    token_context = f" Key words: {', '.join(token_names)}"

                evidences.append(EvidenceItem(
                    type=EvidenceType.ML_HIGH_SCORE,
                    severity=Severity.HIGH if phishing_score > ML_CLASSIFIER_THRESHOLD_CRITICAL else Severity.MEDIUM,
                    description=(
                        f"ML classifier scored {phishing_score:.4f} "
                        f"(confidence: {confidence:.4f}).{token_context}"
                    ),
                    raw_data={
                        "score": round(phishing_score, 4),
                        "confidence": round(confidence, 4),
                        "model_version": self._model_version,
                        "top_tokens": [{"token": t, "score": round(s, 4)} for t, s in top_tokens],
                    },
                ))

            elapsed = int((time.monotonic() - start) * 1000)
            logger.info(
                "ml_prediction_complete",
                score=round(phishing_score, 4),
                confidence=round(confidence, 4),
                duration_ms=elapsed,
                xai_tokens=len(top_tokens),
            )

            return MLResult(
                score=phishing_score,
                confidence=confidence,
                model_available=True,
                model_version=self._model_version,
                evidences=evidences,
                execution_time_ms=elapsed,
                top_tokens=top_tokens,
                xai_available=xai_available,
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
                top_tokens=[],
                xai_available=False,
            )

    async def predict(self, text: str) -> MLResult:
        """Run inference on email text with XAI (offloaded to thread pool)."""
        return await asyncio.to_thread(self._predict_sync, text)
