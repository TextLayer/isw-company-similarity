from typing import Any, Dict, List, Optional

import numpy as np
from litellm import Router

from isw.core.services.llm.base import LLMClient
from isw.shared.config import config
from isw.shared.logging.logger import logger


class EmbeddingClient(LLMClient):
    """
    Client for generating text embeddings using LLMs.
    Provides a simplified interface to LiteLLM's embedding functionality.
    """

    def __init__(
        self,
        dimension: int,
        models: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize an embedding client with the specified model.

        Args:
            dimension: Expected output vector size
            models: List of model names or None to use default from config

        Raises:
            ValueError: If model validation fails
        """
        super().__init__()

        # Initialize and validate models list
        names = models or config().embedding_models
        validated = self.validate_models(names, model_type="embedding", dimension=dimension)
        self.primary = validated[0]  # Store primary model info

        # Build and initialize router
        router_conf = self._build_router_config(validated)
        self.router = Router(**router_conf)

    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.

        If the text is within the token limit, embeds directly.
        Otherwise, splits into chunks by token boundaries, embeds each chunk,
        and returns a normalized average of the embeddings.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # Return zero vector for empty input
        if not text or not text.strip():
            logger.warning("Empty text; returning zero vector")
            return [0.0] * self.primary["output_vector_size"]

        # Tokenize once for both checking and potential chunking
        tokens = self.encode_tokens(text)

        # If within token limit, process directly
        if len(tokens) <= self.primary["max_tokens"]:
            return self._send_request(self._build_request_params(text))

        # For longer text, log and process in chunks
        logger.info(
            "Text exceeds token limit (%d > %d); chunking by token count",
            len(tokens),
            self.primary["max_tokens"],
        )
        return self._process_by_chunks(tokens)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in a batch.

        Each text is handled individually with token-limit chunking,
        and failures fallback to zero vectors.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors, one per input text
        """
        results: List[List[float]] = []
        for idx, txt in enumerate(texts, 1):
            try:
                results.append(self.embed(txt))
            except Exception:
                logger.error("Failed to embed text %d; using zero vector", idx, exc_info=True)
                results.append([0.0] * self.primary["output_vector_size"])
        return results

    def _build_request_params(self, text: str) -> Dict[str, Any]:
        """
        Build parameters for a single embedding API call.

        Args:
            text: Text to embed

        Returns:
            Dictionary of parameters for the embedding API
        """
        return {
            "model": self.primary["key"],
            "input": text,
            "metadata": self._get_metadata(),
        }

    def _send_request(self, params: Dict[str, Any]) -> List[float]:
        """
        Send embedding request to the model provider and process the response.

        Args:
            params: Parameters for the embedding API

        Returns:
            Embedding vector as a list of floats

        Raises:
            ValueError: If embedding generation fails
        """
        try:
            resp = self.router.embedding(**params).to_dict()
            data = resp.get("data", [])
            if not data or "embedding" not in data[0]:
                logger.warning(
                    "No embedding in response for model %s",
                    self.primary["key"],
                )
                return [0.0] * self.primary["output_vector_size"]
            return data[0]["embedding"]
        except Exception as e:
            logger.error("Embedding generation failed", exc_info=True)
            raise ValueError(f"Embedding failed: {e}") from e

    def _process_by_chunks(self, tokens: List[int]) -> List[float]:
        """
        Process a long text by splitting into token-sized chunks.

        Args:
            tokens: List of token IDs from the tokenizer

        Returns:
            Normalized average of chunk embeddings
        """
        chunk_size = self.primary["max_tokens"]
        embeddings: List[List[float]] = []
        chunk_count = (len(tokens) + chunk_size - 1) // chunk_size

        logger.debug("Processing text in %d chunks", chunk_count)

        # Process each chunk
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i : i + chunk_size]
            chunk_text = self.decode_tokens(chunk_tokens)
            chunk_num = i // chunk_size + 1

            try:
                logger.debug("Embedding chunk %d/%d", chunk_num, chunk_count)
                embedding_vector = self._send_request(self._build_request_params(chunk_text))
                embeddings.append(embedding_vector)
            except ValueError:
                logger.warning("Failed to embed chunk %d/%d", chunk_num, chunk_count)

        # Handle case where all chunks failed
        if not embeddings:
            logger.warning("No chunks embedded; falling back to first %d tokens", chunk_size)
            fallback_text = self.decode_tokens(tokens[:chunk_size])
            return self._send_request(self._build_request_params(fallback_text))

        # Average embeddings and normalize
        return self._normalize_average_embedding(embeddings)

    def _normalize_average_embedding(self, embeddings: List[List[float]]) -> List[float]:
        """
        Compute the normalized average of multiple embeddings.

        Args:
            embeddings: List of embedding vectors

        Returns:
            Normalized average embedding
        """
        if not embeddings:
            return [0.0] * self.primary["output_vector_size"]

        # Average the embeddings
        arr = np.array(embeddings)
        avg = arr.mean(axis=0)

        # Normalize to unit length
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm

        return avg.tolist()
