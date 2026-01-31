"""Unit tests for EmbeddingService.

Tests initialization, validation, and dimensions logic.
Actual OpenAI API interactions are tested via integration tests.
"""

import unittest

from isw.core.services.embeddings import EmbeddingService, EmbeddingServiceError


class TestEmbeddingServiceInit(unittest.TestCase):
    def test_raises_without_api_key(self):
        with self.assertRaises(EmbeddingServiceError) as ctx:
            EmbeddingService(api_key="")
        assert "API key is required" in str(ctx.exception)

    def test_raises_with_none_api_key(self):
        with self.assertRaises(EmbeddingServiceError):
            EmbeddingService(api_key=None)


class TestEmbeddingServiceDimensions(unittest.TestCase):
    """Test dimension calculations - pure logic, no API calls."""

    def test_small_model_dimensions(self):
        assert EmbeddingService.MODEL_DIMENSIONS["text-embedding-3-small"] == 1536

    def test_large_model_dimensions(self):
        assert EmbeddingService.MODEL_DIMENSIONS["text-embedding-3-large"] == 3072
