import pytest

from isw.core.services.llm.base import LLMClient


class TestLLMBase:
    def test_validate_models_skips_invalid_and_keeps_valid(self, monkeypatch):
        client = LLMClient()

        calls = {"count": 0}

        def fake_validate_model(name, model_type, dimension):
            calls["count"] += 1
            if name == "bad-model":
                raise ValueError("invalid")
            return {"key": name, "mode": model_type}

        monkeypatch.setattr(client, "validate_model", fake_validate_model)

        validated = client.validate_models(["good-model", "bad-model"], model_type="chat")
        assert len(validated) == 1
        assert validated[0]["key"] == "good-model"

    def test_validate_model_dimension_mismatch_raises(self, monkeypatch):
        client = LLMClient()

        def fake_get_model_info(name):
            return {"key": name, "mode": "embedding", "output_vector_size": 1536}

        monkeypatch.setattr(client, "get_model_info", fake_get_model_info)

        with pytest.raises(ValueError):
            client.validate_model("embed-model", model_type="embedding", dimension=1024)
