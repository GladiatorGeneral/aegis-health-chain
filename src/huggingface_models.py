"""HuggingFace model integration for clinical forecasting

This module is written to be resilient in environments where heavy
dependencies (torch, transformers) may not be installed. Imports are
attempted at module load but failures are handled so the package can be
imported in CI or lightweight environments. Use `SKIP_HF_MODELS=1` in
CI to skip heavy model tests.
"""
from typing import Dict, Any, List, Optional
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing heavy ML libraries; if unavailable, set flags and
# provide graceful degradation so tests and CI can import this module.
HAS_TORCH = True
HAS_TRANSFORMERS = True
try:
    import torch
except Exception:
    HAS_TORCH = False

try:
    from transformers import AutoModel, AutoTokenizer, pipeline
except Exception:
    HAS_TRANSFORMERS = False
    # Provide placeholders to allow attribute access without raising at import
    AutoModel = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    pipeline = None  # type: ignore


class ClinicalForecastingModels:
    """Manager for HuggingFace models in clinical forecasting

    Methods will raise `RuntimeError` if heavy dependencies are not
    available. This allows importing the package in CI where we may
    skip heavy model tests.
    """

    def __init__(self, device: str = None):
        if HAS_TORCH:
            self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device or "cpu"

        logger.info(f"Using device: {self.device}")

        # Model registry (strings only; loading is dynamic)
        self.available_models = {
            "clinical_bert": "emilyalsentzer/Bio_ClinicalBERT",
            "sentence_transformer": "sentence-transformers/all-mpnet-base-v2",
            "clinical_pubmed_bert": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
        }

        self.loaded_models: Dict[str, Any] = {}

    def load_model(self, model_key: str, task: str = None) -> Any:
        """Load a HuggingFace model. Raises RuntimeError if transformers/torch missing."""
        if model_key not in self.available_models:
            raise ValueError(f"Model {model_key} not available. Choices: {list(self.available_models.keys())}")

        if not (HAS_TRANSFORMERS and HAS_TORCH):
            raise RuntimeError("torch and transformers are required to load models")

        if model_key in self.loaded_models:
            return self.loaded_models[model_key]

        model_name = self.available_models[model_key]
        logger.info(f"Loading model: {model_name}")

        try:
            if task:
                model = pipeline(
                    task,
                    model=model_name,
                    device=0 if self.device == "cuda" else -1,
                )
            else:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name).to(self.device)
                model = {"model": model, "tokenizer": tokenizer}

            self.loaded_models[model_key] = model
            return model

        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            raise

    def get_clinical_embeddings(self, text: str, model_key: str = "clinical_bert"):
        """Get embeddings for clinical text.

        Requires `torch` and `transformers`. Raises `RuntimeError` otherwise.
        """
        if not (HAS_TRANSFORMERS and HAS_TORCH):
            raise RuntimeError("torch and transformers are required for embedding extraction")

        model_info = self.load_model(model_key)

        if isinstance(model_info, dict):
            tokenizer = model_info["tokenizer"]
            model = model_info["model"]

            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
            return embeddings.cpu()
        else:
            raise ValueError("Embedding extraction requires model+tokenizer format")

    def predict_risk(self, patient_data: Dict[str, Any], model_key: str = "clinical_bert") -> Dict[str, Any]:
        """Predict health risk using clinical data. Requires ML libs."""
        embeddings = self.get_clinical_embeddings(self._patient_data_to_text(patient_data), model_key)
        risk_score = torch.sigmoid(embeddings.mean()).item()
        return {
            "risk_score": risk_score,
            "embeddings_shape": embeddings.shape,
            "model_used": model_key,
        }

    def _patient_data_to_text(self, patient_data: Dict[str, Any]) -> str:
        """Convert patient data to natural language text for model input"""
        text_parts: List[str] = []

        if "patient" in patient_data:
            patient = patient_data["patient"]
            text_parts.append(f"Patient is {patient.get('gender', 'unknown') }.")

            if "birthDate" in patient:
                text_parts.append(f"Born {patient['birthDate']}.")

        for key, value in patient_data.items():
            if key != "patient" and isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(str(v) for v in value)}")

        return " ".join(text_parts)

    def list_available_models(self) -> List[str]:
        """List all available models"""
        return list(self.available_models.keys())


# Global instance
clinical_models = ClinicalForecastingModels()

if __name__ == "__main__":
    models = ClinicalForecastingModels()
    print("Available models:", models.list_available_models())
    try:
        embeddings = models.get_clinical_embeddings("Patient with asthma and hypertension")
        print(f"Embeddings shape: {embeddings.shape}")
    except RuntimeError:
        print("ML libs not available in this environment")
