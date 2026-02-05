"""XAI Explainability module using attention weights.

Provides token-level importance scores for ML classifier predictions.
Uses the last-layer attention from [CLS] token to identify
which tokens most influenced the classification decision.
"""

import asyncio
import re
import string
import threading
import time
from typing import Any

import structlog

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

from app.config import settings

logger = structlog.get_logger()

# Characters to filter out (punctuation and special characters)
_FILTER_CHARS = set(string.punctuation + string.whitespace + "''""–—…·•►▪")


def _is_meaningful_token(token: str, min_length: int = 2) -> bool:
    """Check if a token is meaningful for XAI display.
    
    Filters out:
    - Punctuation-only tokens
    - Single characters (except meaningful ones)
    - Digits-only tokens
    - Pure whitespace
    - Subword markers
    """
    # Remove subword markers
    clean = token.replace("##", "").replace("Ġ", "").replace("▁", "").strip()
    
    if not clean:
        return False
    
    # Filter punctuation-only tokens
    if all(c in _FILTER_CHARS for c in clean):
        return False
    
    # Filter very short tokens (unless they're meaningful abbreviations)
    if len(clean) < min_length:
        return False
    
    # Filter digits-only tokens
    if clean.isdigit():
        return False
    
    # Filter URL fragments and common noise
    noise_patterns = ["http", "www", ":/", "//", "...", "===", "---"]
    if any(p in clean.lower() for p in noise_patterns):
        return False
    
    return True

# Module-level singleton
_explainer_instance: "AttentionExplainer | None" = None
_explainer_lock = threading.Lock()


def get_attention_explainer() -> "AttentionExplainer":
    """Return the singleton AttentionExplainer instance (thread-safe)."""
    global _explainer_instance
    if _explainer_instance is None:
        with _explainer_lock:
            if _explainer_instance is None:
                _explainer_instance = AttentionExplainer()
    return _explainer_instance


class AttentionExplainer:
    """Produces token-level importances from the model's last-layer attention.

    Returns the top-k most influential tokens for a given prediction,
    based on the attention weights from [CLS] to other tokens.
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._tokenizer: Any = None
        self._available = False
        self._load_attempted = False

    def _load_model(self) -> None:
        """Attempt to load model with attention output enabled."""
        if self._load_attempted:
            return
        self._load_attempted = True

        if not _TORCH_AVAILABLE:
            logger.warning("xai_torch_not_available", msg="torch/transformers not installed")
            return

        from pathlib import Path

        model_path = Path(settings.ml_model_path)
        if not model_path.exists():
            logger.info("xai_model_not_found_locally", path=str(model_path), msg="Attempting download from Hugging Face Hub...")
            try:
                # Download model from HF Hub
                model_name = settings.ml_model_hf_repo
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    output_attentions=True,
                )
                
                # Save locally
                model_path.mkdir(parents=True, exist_ok=True)
                self._tokenizer.save_pretrained(str(model_path))
                self._model.save_pretrained(str(model_path))
                
                self._model.eval()
                self._available = True
                logger.info("xai_model_downloaded_and_loaded", path=str(model_path))
                return
                
            except Exception as e:
                logger.warning(
                    "xai_model_download_failed",
                    error=str(e),
                    msg="XAI explainer will be unavailable",
                )
                return

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self._model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                output_attentions=True,  # Enable attention output
            )
            self._model.eval()
            self._available = True
            logger.info("xai_explainer_loaded", path=str(model_path))
        except Exception as exc:
            logger.error("xai_model_load_failed", error=str(exc))
            self._model = None
            self._tokenizer = None
            self._available = False

    def _explain_sync(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Extract top-k influential tokens synchronously."""
        start = time.monotonic()
        self._load_model()

        if not self._available or self._model is None or self._tokenizer is None:
            return []

        try:
            # Tokenize input
            encoded = self._tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=settings.ml_max_seq_length,
            )

            # Run inference with attention output
            with torch.no_grad():
                outputs = self._model(**encoded, output_attentions=True)

            attentions = outputs.attentions
            if attentions is None:
                logger.warning("xai_no_attentions", msg="Model did not return attentions")
                return []

            # Extract attention from last layer, [CLS] token (index 0)
            # Shape: (batch, heads, seq, seq)
            last_attn = attentions[-1]
            cls_attn = last_attn[0, :, 0, :]  # attention from CLS to all tokens
            token_importance = cls_attn.mean(dim=0)  # average over heads

            # Convert token IDs to actual tokens
            tokens = self._tokenizer.convert_ids_to_tokens(encoded["input_ids"][0])
            scores = token_importance.tolist()

            # Filter out special tokens and build result
            token_scores: list[tuple[str, float]] = []
            special_tokens = set(self._tokenizer.all_special_tokens)

            for tok, score in zip(tokens, scores):
                if tok in special_tokens:
                    continue
                # Clean up subword markers (## for BERT-style tokenizers)
                clean_tok = tok.replace("##", "").replace("Ġ", "").replace("▁", "").strip()
                
                # Only include meaningful tokens (no punctuation, single chars, etc.)
                if _is_meaningful_token(clean_tok):
                    token_scores.append((clean_tok, float(score)))

            # Sort by importance descending and take top-k
            token_scores = sorted(token_scores, key=lambda x: x[1], reverse=True)[:top_k]

            elapsed = int((time.monotonic() - start) * 1000)
            logger.debug(
                "xai_explain_complete",
                top_k=top_k,
                tokens_found=len(token_scores),
                duration_ms=elapsed,
            )

            return token_scores

        except Exception as exc:
            logger.error("xai_explain_failed", error=str(exc))
            return []

    async def explain(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Extract top-k influential tokens (offloaded to thread pool)."""
        return await asyncio.to_thread(self._explain_sync, text, top_k)

    @property
    def available(self) -> bool:
        """Check if explainer is available after load attempt."""
        if not self._load_attempted:
            self._load_model()
        return self._available
