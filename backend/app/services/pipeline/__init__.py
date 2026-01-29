"""Guard-IA Detection Pipeline.

3-layer sequential pipeline:
  Layer 1: Heuristic rules (~5ms)
  Layer 2: DistilBERT ML classifier (~18ms)
  Layer 3: LLM explainer (~2-3s)
"""

from app.services.pipeline.heuristics import HeuristicEngine
from app.services.pipeline.llm_explainer import LLMExplainer
from app.services.pipeline.ml_classifier import MLClassifier, get_ml_classifier
from app.services.pipeline.models import (
    EvidenceItem,
    HeuristicResult,
    LLMResult,
    MLResult,
    PipelineResult,
)
from app.services.pipeline.orchestrator import PipelineOrchestrator

__all__ = [
    "EvidenceItem",
    "HeuristicEngine",
    "HeuristicResult",
    "LLMExplainer",
    "LLMResult",
    "MLClassifier",
    "MLResult",
    "PipelineOrchestrator",
    "PipelineResult",
    "get_ml_classifier",
]
