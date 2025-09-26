from typing import Any, Dict, List, Literal, Optional

import tiktoken
from litellm.utils import get_model_info

from ....shared.config import config
from ....shared.logging.logger import logger
from ..observability import get_current_observation_id, get_current_trace_id


class LLMClient:
    """
    Base class for LLM clients that encapsulates common functionality.
    Provides minimal wrappers around LiteLLM's core functions.
    """

    def __init__(self) -> None:
        self.tokenizer = tiktoken.get_encoding("p50k_base")

    def validate_models(
        self, names: List[str], model_type: str, dimension: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Validate and collect model info for provided names.

        Args:
            names: List of model names to validate
            model_type: Expected model mode, e.g. "chat" or "embedding"
            dimension: For embedding models, expected output vector size

        Returns:
            List of validated model info dictionaries

        Raises:
            ValueError: If none of the provided models are valid
        """
        validated_models: List[Dict[str, Any]] = []
        for name in names:
            try:
                validated_models.append(self.validate_model(name, model_type, dimension))
            except ValueError as e:
                logger.warning("Skipping invalid %s model '%s': %s", model_type, name, e)
        if not validated_models:
            raise ValueError(f"No valid {model_type} models configured")
        return validated_models

    def _build_router_config(self, infos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Construct Router keyword args: model_list and optional fallbacks.
        """
        model_list = [{"model_name": info["key"], "litellm_params": {"model": info["key"]}} for info in infos]
        config: Dict[str, Any] = {"model_list": model_list}
        if len(infos) > 1:
            primary_key = infos[0]["key"]
            fallback_keys = [info["key"] for info in infos[1:]]
            config["fallbacks"] = [{primary_key: fallback_keys}]
            logger.info(
                "Router configured for embeddings: primary=%s, fallbacks=%s",
                primary_key,
                fallback_keys,
            )
        return config

    def validate_model(
        self,
        model_name: str,
        model_type: Optional[str] = None,
        dimension: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validate that a model exists and is of the expected type.

        Args:
            model_name: Name of the model to validate
            model_type: Optional type to validate against ('chat' or 'embedding')

        Returns:
            Model information dictionary

        Raises:
            ValueError: If the model is invalid or wrong type
        """
        if not model_name:
            raise ValueError("Model name cannot be empty")

        # Check that the model exists
        try:
            model_info = self.get_model_info(model_name)
        except Exception as e:
            # Let the caller handle the specific error, e.g., by logging a warning
            raise ValueError(f"Could not retrieve info for model {model_name}") from e

        # Ensure model_info is valid before proceeding
        if not model_info:
            raise ValueError(f"Model {model_name} information could not be retrieved or is empty.")

        # Ensure that the model "mode" equals the model_type, if specified
        if model_type:
            mode = model_info.get("mode")
            if mode is None:
                raise ValueError(f"Model {model_name} info is missing 'mode' field.")
            if mode != model_type:
                raise ValueError(f"Model {model_name} (mode: {mode}) is not a {model_type} model.")

            if model_type == "embedding" and dimension is not None:
                # Ensure the model's output vector size matches the expected dimension
                output_vector_size = model_info.get("output_vector_size")
                if output_vector_size is None:
                    raise ValueError(f"Model {model_name} info is missing 'output_vector_size' field.")
                if output_vector_size != dimension:
                    raise ValueError(
                        f"Model {model_name} (output vector size: {output_vector_size}) does not match expected "
                        f"dimension {dimension}."
                    )

        return model_info

    def encode_tokens(self, text: str) -> List[int]:
        """
        Encode text into token IDs.
        """
        return self.tokenizer.encode(text, disallowed_special=())

    def decode_tokens(self, tokens: List[int]) -> str:
        """
        Decode a list of token IDs back to text.

        Args:
            tokens: List of integer token IDs

        Returns:
            Decoded text string
        """
        return self.tokenizer.decode(tokens)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in the provided text.
        """
        return len(self.encode_tokens(text))

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information from LiteLLM.

        Args:
            model_name: Name of the model to get info for

        Returns:
            Dictionary of model information
        """
        try:
            return get_model_info(model_name)
        except Exception as e:
            logger.error("Error getting info for model %s: %s", model_name, e)
            return {}

    def get_models(self, model_type: Literal["chat", "embedding"]) -> List[Dict[str, Any]]:
        models = config().embedding_models if model_type == "embedding" else config().chat_models
        output = []

        for model in models:
            if info := self.get_model_info(model):
                output.append(
                    {
                        "id": model,
                        "name": info["key"],
                        "metadata": info,
                    }
                )

        return output

    @property
    def primary_model_key(self) -> Optional[str]:
        """
        Convenience accessor for the selected primary model key, if set by subclass.
        """
        primary = getattr(self, "primary", None)
        return primary.get("key") if isinstance(primary, dict) else None

    def _get_metadata(self) -> Dict[str, str]:
        """
        Retrieve metadata for API calls (e.g., for tracking).
        Subclasses may extend this to add specific metadata.

        Returns:
            Dictionary of metadata for API calls
        """

        return {
            "existing_trace_id": get_current_trace_id(),
            "parent_observation_id": get_current_observation_id(),
        }
