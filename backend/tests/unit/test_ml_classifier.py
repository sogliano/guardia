import pytest

from app.services.pipeline.ml_classifier import MLClassifier


class TestMLClassifier:
    @pytest.fixture
    def classifier(self):
        return MLClassifier()

    async def test_predict_returns_result(self, classifier):
        # TODO: Implement test
        pass
