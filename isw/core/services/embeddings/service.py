import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingService:
    """Service for generating text embeddings using OpenAI's API."""

    # Embedding dimensions by model
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize the embedding service.

        Args:
            api_key: OpenAI API key.
            model: Embedding model to use.
        """
        if not api_key:
            raise EmbeddingServiceError("OpenAI API key is required")

        self.model = model
        self._client = OpenAI(api_key=api_key)

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions for the configured model."""
        return self.MODEL_DIMENSIONS.get(self.model, 1536)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            EmbeddingServiceError: If embedding generation fails.
        """
        if not text or not text.strip():
            raise EmbeddingServiceError("Text cannot be empty")

        try:
            response = self._client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error("Failed to generate embedding: %s", e)
            raise EmbeddingServiceError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a single API call.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.

        Raises:
            EmbeddingServiceError: If embedding generation fails.
        """
        if not texts:
            return []

        # Filter out empty texts and track indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            raise EmbeddingServiceError("All texts are empty")

        try:
            response = self._client.embeddings.create(
                input=valid_texts,
                model=self.model,
            )

            # Map embeddings back to original indices
            embeddings: list[list[float] | None] = [None] * len(texts)
            for j, embedding_data in enumerate(response.data):
                original_index = valid_indices[j]
                embeddings[original_index] = embedding_data.embedding

            # Fill in empty texts with zero vectors
            zero_vector = [0.0] * self.dimensions
            return [emb if emb is not None else zero_vector for emb in embeddings]

        except Exception as e:
            logger.error("Failed to generate embeddings: %s", e)
            raise EmbeddingServiceError(f"Failed to generate embeddings: {e}") from e
