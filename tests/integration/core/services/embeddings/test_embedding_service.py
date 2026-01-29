import json
import math
import os
import unittest

import pytest

from isw.core.services.embeddings import EmbeddingService
from tests.conftest import get_fixture_path

SEC_FIXTURES = get_fixture_path("data_sources", "sec_data")
XBRL_FIXTURES = get_fixture_path("data_sources", "xbrl_json")


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def load_apple_description() -> str:
    """Load Apple's business description from fixture."""
    with open(SEC_FIXTURES / "apple_10k_item1_business.json") as f:
        data = json.load(f)
    return data["item1_business_text"]


def load_kainos_description() -> str:
    """Load Kainos' business description from fixture."""
    with open(XBRL_FIXTURES / "kainos_2022.json") as f:
        data = json.load(f)
    return data["facts"]["fact-1"]["value"]


# Sample descriptions for similarity testing
SAMSUNG_DESCRIPTION = """
Samsung Electronics is a global leader in technology, opening new possibilities for people everywhere.
Through relentless innovation and discovery, we are transforming the worlds of TVs, smartphones,
wearable devices, tablets, digital appliances, network systems, and memory, system LSI, foundry,
and LED solutions. Samsung Electronics focuses on consumer electronics, IT & mobile communications,
and device solutions including semiconductors and display panels.
"""

BANK_DESCRIPTION = """
JPMorgan Chase & Co. is a leading global financial services firm with assets of $3.7 trillion.
The firm is a leader in investment banking, financial services for consumers and small businesses,
commercial banking, financial transaction processing, and asset management. A component of the
Dow Jones Industrial Average, JPMorgan Chase serves millions of customers in the United States
and many of the world's most prominent corporate, institutional and government clients globally.
"""


@pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY") is None or os.environ.get("OPENAI_API_KEY") == "",
    reason="OPENAI_API_KEY not set. Set it to run embedding integration tests.",
)
class TestEmbeddingSimilarity(unittest.TestCase):
    """Integration tests verifying embedding semantic similarity."""

    @classmethod
    def setUpClass(cls):
        api_key = os.environ.get("OPENAI_API_KEY")
        cls.service = EmbeddingService(api_key=api_key)

        # Load fixture descriptions
        cls.apple_desc = load_apple_description()[:4000]  # Truncate for API limits
        cls.kainos_desc = load_kainos_description()

        # Generate embeddings once for all tests
        cls.embeddings = cls.service.embed_texts(
            [
                cls.apple_desc,
                cls.kainos_desc,
                SAMSUNG_DESCRIPTION,
                BANK_DESCRIPTION,
            ]
        )
        cls.apple_embedding = cls.embeddings[0]
        cls.kainos_embedding = cls.embeddings[1]
        cls.samsung_embedding = cls.embeddings[2]
        cls.bank_embedding = cls.embeddings[3]

    def test_embeddings_have_correct_dimensions(self):
        """Embeddings should have the expected number of dimensions."""
        assert len(self.apple_embedding) == self.service.dimensions
        assert len(self.kainos_embedding) == self.service.dimensions
        assert len(self.samsung_embedding) == self.service.dimensions

    def test_embeddings_are_normalized(self):
        """Embedding vectors should be approximately unit length."""
        apple_norm = math.sqrt(sum(x * x for x in self.apple_embedding))
        # OpenAI embeddings are normalized to unit length
        assert 0.99 < apple_norm < 1.01

    def test_apple_more_similar_to_samsung_than_kainos(self):
        """Apple (hardware) should be more similar to Samsung (hardware) than Kainos (software services)."""
        apple_samsung_sim = cosine_similarity(self.apple_embedding, self.samsung_embedding)
        apple_kainos_sim = cosine_similarity(self.apple_embedding, self.kainos_embedding)

        # Apple and Samsung are both consumer electronics companies
        # Kainos is a software consulting company
        assert apple_samsung_sim > apple_kainos_sim, (
            f"Expected Apple-Samsung similarity ({apple_samsung_sim:.4f}) > "
            f"Apple-Kainos similarity ({apple_kainos_sim:.4f})"
        )

    def test_apple_more_similar_to_samsung_than_bank(self):
        """Apple (tech) should be more similar to Samsung (tech) than JPMorgan (bank)."""
        apple_samsung_sim = cosine_similarity(self.apple_embedding, self.samsung_embedding)
        apple_bank_sim = cosine_similarity(self.apple_embedding, self.bank_embedding)

        # Tech companies should cluster together, separate from financial services
        assert apple_samsung_sim > apple_bank_sim, (
            f"Expected Apple-Samsung similarity ({apple_samsung_sim:.4f}) > "
            f"Apple-Bank similarity ({apple_bank_sim:.4f})"
        )

    def test_kainos_more_similar_to_apple_than_bank(self):
        """Kainos (tech/software) should be more similar to Apple (tech) than JPMorgan (bank)."""
        kainos_apple_sim = cosine_similarity(self.kainos_embedding, self.apple_embedding)
        kainos_bank_sim = cosine_similarity(self.kainos_embedding, self.bank_embedding)

        # Both Kainos and Apple are tech companies, just different segments
        assert kainos_apple_sim > kainos_bank_sim, (
            f"Expected Kainos-Apple similarity ({kainos_apple_sim:.4f}) > "
            f"Kainos-Bank similarity ({kainos_bank_sim:.4f})"
        )

    def test_same_text_has_similarity_one(self):
        """Same text embedded twice should have similarity ~1.0."""
        # Embed the same text twice
        embeddings = self.service.embed_texts([SAMSUNG_DESCRIPTION, SAMSUNG_DESCRIPTION])
        similarity = cosine_similarity(embeddings[0], embeddings[1])

        # Should be essentially identical (allowing for floating point)
        assert similarity > 0.9999, f"Expected same-text similarity > 0.9999, got {similarity}"


@pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY") is None or os.environ.get("OPENAI_API_KEY") == "",
    reason="OPENAI_API_KEY not set. Set it to run embedding integration tests.",
)
class TestEmbeddingFromFixtures(unittest.TestCase):
    """Integration tests using real fixture data."""

    @classmethod
    def setUpClass(cls):
        api_key = os.environ.get("OPENAI_API_KEY")
        cls.service = EmbeddingService(api_key=api_key)

    def test_embeds_apple_description(self):
        """Should successfully embed Apple's business description."""
        apple_desc = load_apple_description()[:4000]
        embedding = self.service.embed_text(apple_desc)

        assert len(embedding) == self.service.dimensions
        assert all(isinstance(x, float) for x in embedding)

    def test_embeds_kainos_description(self):
        """Should successfully embed Kainos' business description."""
        kainos_desc = load_kainos_description()
        embedding = self.service.embed_text(kainos_desc)

        assert len(embedding) == self.service.dimensions
        assert all(isinstance(x, float) for x in embedding)

    def test_batch_embedding_matches_individual(self):
        """Batch embedding should produce same results as individual calls."""
        apple_desc = load_apple_description()[:2000]
        kainos_desc = load_kainos_description()

        # Get individual embeddings
        apple_individual = self.service.embed_text(apple_desc)
        kainos_individual = self.service.embed_text(kainos_desc)

        # Get batch embeddings
        batch = self.service.embed_texts([apple_desc, kainos_desc])

        # Should be essentially identical
        apple_sim = cosine_similarity(apple_individual, batch[0])
        kainos_sim = cosine_similarity(kainos_individual, batch[1])

        assert apple_sim > 0.999, f"Apple batch/individual similarity: {apple_sim}"
        assert kainos_sim > 0.999, f"Kainos batch/individual similarity: {kainos_sim}"
