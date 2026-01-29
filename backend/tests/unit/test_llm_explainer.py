import pytest

from app.services.pipeline.llm_explainer import LLMExplainer


class TestLLMExplainer:
    @pytest.fixture
    def explainer(self):
        return LLMExplainer()

    async def test_explain_returns_result(self, explainer):
        # TODO: Implement test
        pass
