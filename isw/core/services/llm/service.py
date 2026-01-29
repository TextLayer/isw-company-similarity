from typing import TypeVar

from litellm import completion
from pydantic import BaseModel

from isw.shared.logging.logger import logger

T = TypeVar("T", bound=BaseModel)


class LLMServiceError(Exception):
    """Raised when LLM operations fail."""


class LLMService:
    """Service for LLM completions with structured output via LiteLLM."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def structured_output(self, messages: list[dict], output_structure: type[T]) -> T:
        """Generate a structured response from an LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            output_structure: Pydantic model class defining the expected output.

        Returns:
            Instance of output_structure populated with LLM response.

        Raises:
            LLMServiceError: If the LLM call or parsing fails.
        """
        if not messages:
            raise LLMServiceError("Messages cannot be empty")

        try:
            response = completion(
                model=self.model,
                messages=messages,
                response_format=output_structure,
            )

            content = response.choices[0].message.content
            return output_structure.model_validate_json(content)

        except Exception as e:
            logger.error("LLM structured output failed: %s", e)
            raise LLMServiceError(f"Failed to generate structured output: {e}") from e
