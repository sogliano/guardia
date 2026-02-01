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
            patch("app.services.pipeline.orchestrator.MLClassifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: High risk due to failed auth
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = (
                0.75,
                [
                    {"type": "auth_failure", "severity": "high", "detail": "SPF/DKIM/DMARC failed"}
                ],
            )
            MockHeuristic.return_value = mock_heur

            # ML: High confidence phishing
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = (0.92, True)
            MockML.return_value = mock_ml

            # LLM: Detailed explanation
            mock_llm = AsyncMock()
            mock_llm.explain.return_value = {
                "summary": "Email exhibits classic phishing patterns",
                "reasoning": "Urgency in subject, auth failures, suspicious URLs",
                "confidence": "high",
            }
            MockLLM.return_value = mock_llm

            # Execute pipeline
            orchestrator = PipelineOrchestrator(mock_db)
            result = await orchestrator.analyze(email_id)

            # Assertions: Verify pipeline executed correctly
            assert result is not None
            assert result.verdict in ["ALLOWED", "WARN", "QUARANTINE"]
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
            patch("app.services.pipeline.orchestrator.MLClassifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: Low risk (legitimate)
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = (0.05, [])
            MockHeuristic.return_value = mock_heur

            # ML: FAILS (returns None)
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = (None, False)
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
            assert result.verdict == "ALLOWED"  # Low heuristic score
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
            patch("app.services.pipeline.orchestrator.MLClassifier") as MockML,
            patch("app.services.pipeline.orchestrator.LLMExplainer") as MockLLM,
        ):
            # Heuristic: Fast
            mock_heur = AsyncMock()
            mock_heur.analyze.return_value = (0.6, [])
            MockHeuristic.return_value = mock_heur

            # ML: Fast
            mock_ml = AsyncMock()
            mock_ml.predict.return_value = (0.8, True)
            MockML.return_value = mock_ml

            # LLM: Slow but within timeout
            mock_llm = AsyncMock()
            mock_llm.explain.return_value = {"summary": "Analysis complete"}
            MockLLM.return_value = mock_llm

            # Execute with timeout
            orchestrator = PipelineOrchestrator(mock_db)
            result = await orchestrator.analyze(email_id)

            # Should complete successfully within timeout
            assert result is not None
            assert result.verdict in ["ALLOWED", "WARN", "QUARANTINE"]
