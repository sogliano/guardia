"""Tests for ML classifier graceful degradation and load/predict flows."""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.pipeline.ml_classifier import MLClassifier, get_ml_classifier, _lock
import app.services.pipeline.ml_classifier as ml_module


@pytest.mark.asyncio
async def test_predict_degraded_when_model_missing():
    """No model file → returns score 0.0, model_available=False."""
    with patch("app.services.pipeline.ml_classifier.settings") as mock_settings:
        mock_settings.ml_model_path = "/nonexistent/path"
        classifier = MLClassifier()
        result = await classifier.predict("test email text")

    assert result.score == 0.0
    assert result.model_available is False
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_predict_exception_returns_zero():
    """If model inference raises, returns score 0.0 without crashing."""
    classifier = MLClassifier()
    classifier._load_attempted = True
    classifier._model_available = True
    classifier._model_version = "test"

    # Mock tokenizer to return something, and mock torch at import level
    mock_torch = MagicMock()
    mock_tokenizer = MagicMock(return_value={"input_ids": MagicMock()})
    classifier._tokenizer = mock_tokenizer

    # Model call inside torch.no_grad() raises
    classifier._model = MagicMock(side_effect=RuntimeError("boom"))

    with patch.dict("sys.modules", {"torch": mock_torch}):
        result = await classifier.predict("test")

    assert result.score == 0.0


def test_singleton_pattern():
    """get_ml_classifier returns same instance."""
    # Reset singleton
    ml_module._instance = None
    try:
        with patch("app.services.pipeline.ml_classifier.settings") as mock_settings:
            mock_settings.ml_model_path = "/nonexistent"
            a = get_ml_classifier()
            b = get_ml_classifier()
        assert a is b
    finally:
        ml_module._instance = None


@pytest.mark.asyncio
async def test_predict_happy_path_high_score():
    """Mock torch + model to simulate a high phishing score prediction with XAI."""
    classifier = MLClassifier()
    classifier._load_attempted = True
    classifier._model_available = True
    classifier._model_version = "test-v1"

    mock_torch = MagicMock()
    # Simulate softmax output: [0.1 legitimate, 0.9 phishing]
    mock_probs = MagicMock()
    mock_probs.__getitem__ = lambda self, idx: mock_probs
    mock_item_scores = [0.1, 0.9]  # [legitimate, phishing]

    mock_tensor_legit = MagicMock()
    mock_tensor_legit.item.return_value = 0.1
    mock_tensor_phish = MagicMock()
    mock_tensor_phish.item.return_value = 0.9

    mock_probs_row = MagicMock()
    mock_probs_row.__getitem__ = lambda self, idx: mock_tensor_legit if idx == 0 else mock_tensor_phish

    mock_probs_outer = MagicMock()
    mock_probs_outer.__getitem__ = lambda self, idx: mock_probs_row

    mock_torch.softmax.return_value = mock_probs_outer
    mock_torch.no_grad.return_value.__enter__ = MagicMock()
    mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

    mock_logits = MagicMock()
    mock_model = MagicMock()
    # Include attentions in model output for XAI
    mock_model.return_value.logits = mock_logits
    mock_model.return_value.attentions = None  # XAI will return empty list
    classifier._model = mock_model

    mock_tokenizer = MagicMock(return_value={"input_ids": MagicMock()})
    classifier._tokenizer = mock_tokenizer

    with patch.dict(sys.modules, {"torch": mock_torch}):
        setattr(ml_module, "torch", mock_torch)
        try:
            result = await classifier.predict("this is a suspicious phishing email text with enough words to pass the short text dampening threshold and get a full score from the model")
        finally:
            if not getattr(ml_module, "_TORCH_AVAILABLE", False):
                delattr(ml_module, "torch")

    assert result.score == 0.9
    assert result.confidence == 0.9
    assert result.model_available is True
    assert result.model_version == "test-v1"
    assert len(result.evidences) == 1
    assert result.evidences[0].type == "ml_high_score"
    # XAI fields present (may be empty if attentions not mocked)
    assert hasattr(result, "top_tokens")
    assert hasattr(result, "xai_available")


@pytest.mark.asyncio
async def test_predict_happy_path_low_score():
    """Low score → no evidence generated."""
    classifier = MLClassifier()
    classifier._load_attempted = True
    classifier._model_available = True
    classifier._model_version = "test-v1"

    mock_torch = MagicMock()
    mock_tensor_legit = MagicMock()
    mock_tensor_legit.item.return_value = 0.85
    mock_tensor_phish = MagicMock()
    mock_tensor_phish.item.return_value = 0.15

    mock_probs_row = MagicMock()
    mock_probs_row.__getitem__ = lambda self, idx: mock_tensor_legit if idx == 0 else mock_tensor_phish
    mock_probs_outer = MagicMock()
    mock_probs_outer.__getitem__ = lambda self, idx: mock_probs_row

    mock_torch.softmax.return_value = mock_probs_outer
    mock_torch.no_grad.return_value.__enter__ = MagicMock()
    mock_torch.no_grad.return_value.__enter__ = MagicMock()
    mock_torch.no_grad.return_value.__exit__ = MagicMock(return_value=False)

    mock_model = MagicMock()
    mock_model.return_value.logits = MagicMock()
    mock_model.return_value.attentions = None  # XAI will be empty
    classifier._model = mock_model
    classifier._tokenizer = MagicMock(return_value={"input_ids": MagicMock()})

    with patch.dict(sys.modules, {"torch": mock_torch}):
        setattr(ml_module, "torch", mock_torch)
        try:
            result = await classifier.predict("this is a clean legitimate email with enough words to pass the short text dampening threshold and get a full score from the model")
        finally:
            if not getattr(ml_module, "_TORCH_AVAILABLE", False):
                delattr(ml_module, "torch")

    assert result.score == 0.15
    assert result.evidences == []
    # XAI fields should be present
    assert result.top_tokens == []
    assert result.xai_available is False


def test_load_model_path_not_exists():
    """_load_model with nonexistent path → degraded mode."""
    with patch("app.services.pipeline.ml_classifier.settings") as mock_settings:
        mock_settings.ml_model_path = "/nonexistent/model/path"
        classifier = MLClassifier()
        classifier._load_model()

    assert classifier._model_available is False
    assert classifier._load_attempted is True
    assert classifier._model is None


def test_load_model_import_fails(tmp_path):
    """_load_model when transformers import fails → degraded mode."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}")

    with patch("app.services.pipeline.ml_classifier.settings") as mock_settings:
        mock_settings.ml_model_path = str(model_dir)
        classifier = MLClassifier()
        # The import of torch/transformers will fail in test environment
        classifier._load_model()

    assert classifier._load_attempted is True
    # Model won't load because torch/transformers aren't properly installed for inference
    assert classifier._model_available is False


def test_load_model_caches_attempt():
    """Second _load_model call is a no-op."""
    with patch("app.services.pipeline.ml_classifier.settings") as mock_settings:
        mock_settings.ml_model_path = "/nonexistent"
        classifier = MLClassifier()
        classifier._load_model()
        classifier._load_model()  # should be cached

    assert classifier._load_attempted is True
