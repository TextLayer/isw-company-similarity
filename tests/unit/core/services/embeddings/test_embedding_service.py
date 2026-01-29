import unittest
from unittest.mock import MagicMock, patch

from isw.core.services.embeddings import EmbeddingService, EmbeddingServiceError


class TestEmbeddingServiceInit(unittest.TestCase):
    def test_raises_without_api_key(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            EmbeddingService(api_key="")
        assert "API key is required" in str(ctx.exception)

    def test_raises_with_none_api_key(self):
        with self.assertRaises(EmbeddingServiceError):
            EmbeddingService(api_key=None)

    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_creates_client_with_api_key(self, mock_openai):
        EmbeddingService(api_key="test-key")
        mock_openai.assert_called_once_with(api_key="test-key")

    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_default_model(self, mock_openai):
        service = EmbeddingService(api_key="test-key")
        assert service.model == "text-embedding-3-small"

    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_custom_model(self, mock_openai):
        service = EmbeddingService(api_key="test-key", model="text-embedding-3-large")
        assert service.model == "text-embedding-3-large"


class TestEmbeddingServiceDimensions(unittest.TestCase):
    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_small_model_dimensions(self, mock_openai):
        service = EmbeddingService(api_key="test-key", model="text-embedding-3-small")
        assert service.dimensions == 1536

    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_large_model_dimensions(self, mock_openai):
        service = EmbeddingService(api_key="test-key", model="text-embedding-3-large")
        assert service.dimensions == 3072

    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_unknown_model_defaults_to_1536(self, mock_openai):
        service = EmbeddingService(api_key="test-key", model="unknown-model")
        assert service.dimensions == 1536

    @patch("isw.core.services.embeddings.service.logger")
    @patch("isw.core.services.embeddings.service.OpenAI")
    def test_unknown_model_logs_warning(self, mock_openai, mock_logger):
        EmbeddingService(api_key="test-key", model="unknown-model")
        mock_logger.warning.assert_called_once()
        assert "unknown-model" in str(mock_logger.warning.call_args)


class TestEmbedText(unittest.TestCase):
    @patch("isw.core.services.embeddings.service.OpenAI")
    def setUp(self, mock_openai):
        self.mock_client = MagicMock()
        mock_openai.return_value = self.mock_client
        self.service = EmbeddingService(api_key="test-key")

    def test_returns_embedding_vector(self):
        expected_embedding = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=expected_embedding)]
        self.mock_client.embeddings.create.return_value = mock_response

        result = self.service.embed_text("test text")

        assert result == expected_embedding
        self.mock_client.embeddings.create.assert_called_once_with(
            input="test text",
            model="text-embedding-3-small",
        )

    def test_raises_for_none_text(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_text(None)
        assert "cannot be empty" in str(ctx.exception)

    def test_raises_for_empty_text(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_text("")
        assert "cannot be empty" in str(ctx.exception)

    def test_raises_for_whitespace_only_text(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_text("   ")
        assert "cannot be empty" in str(ctx.exception)

    def test_raises_on_api_error(self):
        self.mock_client.embeddings.create.side_effect = Exception("API error")

        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_text("test text")
        assert "Failed to generate embedding" in str(ctx.exception)


class TestEmbedTexts(unittest.TestCase):
    @patch("isw.core.services.embeddings.service.OpenAI")
    def setUp(self, mock_openai):
        self.mock_client = MagicMock()
        mock_openai.return_value = self.mock_client
        self.service = EmbeddingService(api_key="test-key")

    def test_returns_empty_list_for_empty_input(self):
        result = self.service.embed_texts([])
        assert result == []

    def test_returns_embeddings_for_multiple_texts(self):
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=emb, index=i) for i, emb in enumerate(embeddings)]
        self.mock_client.embeddings.create.return_value = mock_response

        result = self.service.embed_texts(["text 1", "text 2"])

        assert result == embeddings

    def test_raises_for_all_empty_texts(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_texts(["", "   "])
        assert "All texts are empty" in str(ctx.exception)

    def test_handles_mixed_empty_and_valid_texts(self):
        embedding = [0.1, 0.2]
        mock_response = MagicMock()
        # Index 0 in valid_texts maps to original index 1 (second element)
        mock_response.data = [MagicMock(embedding=embedding, index=0)]
        self.mock_client.embeddings.create.return_value = mock_response

        result = self.service.embed_texts(["", "valid text", "   "])

        # First and third should be zero vectors, second should be the embedding
        assert len(result) == 3
        assert result[0] == [0.0] * 1536  # Zero vector for empty
        assert result[1] == embedding
        assert result[2] == [0.0] * 1536  # Zero vector for whitespace

    def test_raises_on_api_error(self):
        self.mock_client.embeddings.create.side_effect = Exception("API error")

        with self.assertRaises(EmbeddingServiceError) as ctx:
            self.service.embed_texts(["test text"])
        assert "Failed to generate embeddings" in str(ctx.exception)
