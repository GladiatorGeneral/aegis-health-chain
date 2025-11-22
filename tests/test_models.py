"""Tests for HuggingFace models"""
import os
import pytest
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Allow skipping HF-heavy tests in CI by setting SKIP_HF_MODELS=1
if os.environ.get("SKIP_HF_MODELS") == "1":
    pytest.skip("Skipping heavy HuggingFace model tests in CI", allow_module_level=True)

from src.huggingface_models import ClinicalForecastingModels


class TestClinicalModels:
    def setup_method(self):
        self.models = ClinicalForecastingModels(device="cpu")

    def test_model_loading(self):
        model = self.models.load_model("clinical_bert")
        assert model is not None

    def test_embedding_generation(self):
        test_text = "Patient with asthma"
        embeddings = self.models.get_clinical_embeddings(test_text)
        assert embeddings.shape[0] == 1  # Batch size 1
        assert embeddings.shape[1] > 0

    def test_available_models(self):
        models = self.models.list_available_models()
        assert "clinical_bert" in models
        assert "sentence_transformer" in models
