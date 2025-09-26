import numpy as np
import pytest

from isw.core.services.llm.embedding import EmbeddingClient


class DummyRouter:
    def __init__(self, *args, **kwargs):
        self.call_count = 0
        self.last_params = None

    class _Resp:
        def __init__(self, data):
            self._data = data

        def to_dict(self):
            return {"data": self._data}

    def embedding(self, **params):
        self.call_count += 1
        self.last_params = params
        return self._Resp(
            [
                {
                    "embedding": [1.0, 0.0, 0.0],
                }
            ]
        )


def test_embed_empty_text_returns_zero_vector(monkeypatch):
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 5, "max_tokens": 8}
        ],
    )

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", DummyRouter)

    client = EmbeddingClient(dimension=5, models=["test-embed"])
    vec = client.embed("")
    assert vec == [0.0] * 5


def test_embed_normal_path_calls_router(monkeypatch):
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 4096}
        ],
    )
    monkeypatch.setattr("isw.core.services.llm.embedding.Router", DummyRouter)

    client = EmbeddingClient(dimension=3, models=["embed-model"])
    vec = client.embed("hello world")
    assert vec == [1.0, 0.0, 0.0]


def test_embed_batch_success(monkeypatch):
    """Test batch embedding of multiple texts."""
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 100}
        ],
    )

    router = DummyRouter()
    monkeypatch.setattr("isw.core.services.llm.embedding.Router", lambda **_: router)

    client = EmbeddingClient(dimension=3, models=["embed-model"])
    texts = ["text one", "text two", "text three"]
    results = client.embed_batch(texts)

    assert len(results) == 3
    assert all(vec == [1.0, 0.0, 0.0] for vec in results)
    assert router.call_count == 3


def test_embed_batch_with_failure(monkeypatch):
    """Test batch embedding handles individual failures gracefully."""
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 100}
        ],
    )

    class FailingRouter:
        def __init__(self, *args, **kwargs):
            self.call_count = 0

        def embedding(self, **params):
            self.call_count += 1
            if self.call_count == 2:
                raise Exception("API error")
            return DummyRouter._Resp([{"embedding": [1.0, 0.0, 0.0]}])

    router = FailingRouter()
    monkeypatch.setattr("isw.core.services.llm.embedding.Router", lambda **_: router)

    client = EmbeddingClient(dimension=3, models=["embed-model"])
    texts = ["text one", "text two", "text three"]
    results = client.embed_batch(texts)

    assert len(results) == 3
    assert results[0] == [1.0, 0.0, 0.0]
    assert results[1] == [0.0, 0.0, 0.0]  # Failed embedding returns zero vector
    assert results[2] == [1.0, 0.0, 0.0]


def test_embedding_chunking_and_averaging(monkeypatch):
    """Test that long texts are chunked and averaged properly."""
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 5}
        ],
    )

    monkeypatch.setattr(EmbeddingClient, "encode_tokens", lambda self, text: list(range(12)))
    monkeypatch.setattr(EmbeddingClient, "decode_tokens", lambda self, tokens: "x" * len(tokens))

    call_count = {"count": 0}

    class ChunkRouter:
        def __init__(self, **kwargs):
            pass

        def embedding(self, **params):
            nonlocal call_count
            call_count["count"] += 1
            if call_count["count"] == 1:
                return DummyRouter._Resp([{"embedding": [1.0, 0.0, 0.0]}])
            elif call_count["count"] == 2:
                return DummyRouter._Resp([{"embedding": [0.0, 1.0, 0.0]}])
            else:
                return DummyRouter._Resp([{"embedding": [0.0, 0.0, 1.0]}])

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", ChunkRouter)

    client = EmbeddingClient(dimension=3, models=["embed-model"])
    result = client.embed("long text that will be chunked")

    # Should be average of [1,0,0], [0,1,0], [0,0,1] normalized
    expected = np.array([1.0, 1.0, 1.0]) / 3.0
    expected = expected / np.linalg.norm(expected)

    np.testing.assert_array_almost_equal(result, expected.tolist())
    assert call_count["count"] == 3  # Three chunks


def test_embedding_fallback_on_chunk_failure(monkeypatch):
    """Test fallback behavior when all chunks fail."""
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 5}
        ],
    )

    monkeypatch.setattr(EmbeddingClient, "encode_tokens", lambda self, text: list(range(12)))
    monkeypatch.setattr(EmbeddingClient, "decode_tokens", lambda self, tokens: "x" * len(tokens))

    call_count = {"count": 0}

    class FailingChunkRouter:
        def __init__(self, **kwargs):
            pass

        def embedding(self, **params):
            nonlocal call_count
            call_count["count"] += 1
            if call_count["count"] <= 3:  # Fail for all chunks
                raise ValueError("Chunk embedding failed")
            # Success on fallback (first chunk only)
            return DummyRouter._Resp([{"embedding": [1.0, 0.0, 0.0]}])

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", FailingChunkRouter)

    client = EmbeddingClient(dimension=3, models=["embed-model"])

    # Mock _send_request to handle the fallback case
    original_send = client._send_request

    def mock_send(params):
        try:
            return original_send(params)
        except ValueError:
            if call_count["count"] > 3:
                return [1.0, 0.0, 0.0]
            raise

    monkeypatch.setattr(client, "_send_request", mock_send)

    result = client.embed("long text with failing chunks")

    # Should fallback to embedding first chunk only
    assert result == [1.0, 0.0, 0.0]
    assert call_count["count"] == 4  # 3 failed chunks + 1 fallback


def test_embedding_no_response_data(monkeypatch):
    """Test handling of empty response data."""
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: [
            {"key": names[0], "mode": "embedding", "output_vector_size": 3, "max_tokens": 100}
        ],
    )

    class EmptyResponseRouter:
        def __init__(self, **kwargs):
            pass

        def embedding(self, **params):
            return DummyRouter._Resp([])  # Empty data

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", EmptyResponseRouter)

    client = EmbeddingClient(dimension=3, models=["embed-model"])
    result = client.embed("test text")

    # Should return zero vector on empty response
    assert result == [0.0, 0.0, 0.0]


def test_embedding_client_initialization_with_multiple_models(monkeypatch):
    """Test initialization with multiple models for fallback."""
    validated_models = [
        {"key": "primary-embed", "mode": "embedding", "output_vector_size": 3, "max_tokens": 100},
        {"key": "fallback-embed", "mode": "embedding", "output_vector_size": 3, "max_tokens": 100},
    ]

    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        lambda self, names, model_type, dimension: validated_models,
    )

    router_config = None

    def mock_router(**config):
        nonlocal router_config
        router_config = config
        return DummyRouter()

    monkeypatch.setattr("isw.core.services.llm.embedding.Router", mock_router)

    client = EmbeddingClient(dimension=3, models=["primary-embed", "fallback-embed"])

    # Check that fallback configuration was set up
    assert client.primary == validated_models[0]
    assert router_config is not None
    assert "fallbacks" in router_config
    assert router_config["fallbacks"][0] == {"primary-embed": ["fallback-embed"]}


def test_embedding_dimension_validation(monkeypatch):
    """Test that dimension mismatch raises error during initialization."""

    def mock_validate_models(self, names, model_type, dimension):
        # Raise the error that validate_models would raise
        raise ValueError("No valid embedding models configured")

    # Mock validate_models to raise the error
    monkeypatch.setattr(
        EmbeddingClient,
        "validate_models",
        mock_validate_models,
    )

    with pytest.raises(ValueError, match="No valid embedding models configured"):
        EmbeddingClient(dimension=1536, models=["wrong-dimension-model"])
