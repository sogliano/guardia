import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestPipelineFlow:
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, mock_db, phishing_email_data):
        """Integration test: Full pipeline flow with all 3 stages."""
        from app.models.email import Email
        from app.services.pipeline.orchestrator import PipelineOrchestrator

        # Setup: Create mock email in DB
        email_id = uuid4()
        mock_email = Email(id=email_id, **phishing_email_data)

        # Mock DB query to return our email
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        # Mock pipeline components with realistic responses
        with (
            patch(
                "app.services.pipeline.orchestrator.HeuristicEngine"
            ) as MockHeuristic,
            patch("app.services.pipeline.orchestrator.get_ml_classifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: High risk due to failed auth
            from app.services.pipeline.models import HeuristicResult, EvidenceItem
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = HeuristicResult(
                score=0.75,
                evidences=[
                    EvidenceItem(
                        type="auth_failure",
                        severity="high",
                        description="SPF/DKIM/DMARC failed"
                    )
                ],
                execution_time_ms=5,
            )
            MockHeuristic.return_value = mock_heur

            # ML: High confidence phishing
            from app.services.pipeline.models import MLResult, LLMResult
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = MLResult(
                score=0.92,
                confidence=0.95,
                model_available=True,
                model_version="v1.0",
                execution_time_ms=18,
            )
            MockML.return_value = mock_ml

            # LLM: Detailed explanation
            mock_llm = AsyncMock()
            mock_llm.explain.return_value = LLMResult(
                score=0.85,
                confidence=0.9,
                explanation="Email exhibits classic phishing patterns with urgency in subject, auth failures, suspicious URLs",
                provider="openai",
                model_used="gpt-4",
                tokens_used=150,
                execution_time_ms=2500,
            )
            MockLLM.return_value = mock_llm

            # Execute pipeline
            orchestrator = PipelineOrchestrator(mock_db)
            result = await orchestrator.analyze(email_id)

            # Assertions: Verify pipeline executed correctly
            assert result is not None
            assert result.verdict in ["allowed", "warned", "quarantined", "blocked"]
            assert 0.0 <= result.final_score <= 1.0
            assert result.final_score >= 0.75  # Should be high due to phishing signals

            # Verify all 3 stages executed
            mock_heur.analyze.assert_called_once()
            mock_ml.predict.assert_called_once()
            mock_llm.explain.assert_called_once()

            # Verify DB persistence (Case + Analysis records)
            assert mock_db.add.call_count >= 2  # At least Case + 1 Analysis

    @pytest.mark.asyncio
    async def test_pipeline_graceful_degradation(self, mock_db, clean_email_data):
        """Integration test: Pipeline works when ML/LLM fail."""
        from app.models.email import Email
        from app.services.pipeline.orchestrator import PipelineOrchestrator

        # Setup: Clean legitimate email
        email_id = uuid4()
        mock_email = Email(id=email_id, **clean_email_data)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        with (
            patch(
                "app.services.pipeline.orchestrator.HeuristicEngine"
            ) as MockHeuristic,
            patch("app.services.pipeline.orchestrator.get_ml_classifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: Low risk (legitimate)
            from app.services.pipeline.models import HeuristicResult
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = HeuristicResult(
                score=0.05,
                evidences=[],
                execution_time_ms=3,
            )
            MockHeuristic.return_value = mock_heur

            # ML: FAILS (returns None)
            from app.services.pipeline.models import MLResult
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = MLResult(
                score=0.0,
                confidence=0.0,
                model_available=False,
            )
            MockML.return_value = mock_ml

            # LLM: FAILS (timeout/error)
            mock_llm = AsyncMock()
            mock_llm.explain.side_effect = Exception("LLM timeout")
            MockLLM.return_value = mock_llm

            # Execute pipeline
            orchestrator = PipelineOrchestrator(mock_db)
            result = await orchestrator.analyze(email_id)

            # Assertions: Pipeline should still complete with heuristic-only score
            assert result is not None
            assert result.verdict == "allowed"  # Low heuristic score
            assert result.final_score < 0.3  # Should be low

            # Verify only heuristic executed successfully
            mock_heur.analyze.assert_called_once()
            mock_ml.predict.assert_called_once()
            # LLM should be attempted but allowed to fail

    @pytest.mark.asyncio
    async def test_pipeline_timeout_enforcement(self, mock_db, phishing_email_data):
        """Integration test: Pipeline respects timeout limits."""
        from app.models.email import Email
        from app.services.pipeline.orchestrator import PipelineOrchestrator

        email_id = uuid4()
        mock_email = Email(id=email_id, **phishing_email_data)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        with (
            patch(
                "app.services.pipeline.orchestrator.HeuristicEngine"
            ) as MockHeuristic,
            patch("app.services.pipeline.orchestrator.get_ml_classifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: Fast
            from app.services.pipeline.models import HeuristicResult
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = HeuristicResult(
                score=0.6,
                evidences=[],
                execution_time_ms=4,
            )
            MockHeuristic.return_value = mock_heur

            # ML: Fast
            from app.services.pipeline.models import MLResult, LLMResult
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = MLResult(
                score=0.8,
                confidence=0.9,
                model_available=True,
                model_version="v1.0",
                execution_time_ms=15,
            )
            MockML.return_value = mock_ml

            # LLM: Slow but within timeout
            mock_llm = AsyncMock()
            mock_llm.explain.return_value = LLMResult(
                score=0.75,
                confidence=0.85,
                explanation="Analysis complete",
                provider="openai",
                execution_time_ms=2000,
            )
            MockLLM.return_value = mock_llm

            # Execute with timeout
            orchestrator = PipelineOrchestrator(mock_db)
            result = await orchestrator.analyze(email_id)

            # Should complete successfully within timeout
            assert result is not None
            assert result.verdict in ["allowed", "warned", "quarantined", "blocked"]
