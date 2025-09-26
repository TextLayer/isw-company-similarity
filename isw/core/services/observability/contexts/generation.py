from __future__ import annotations

from typing import Any, Optional

from .span import SpanContext


class GenerationContext(SpanContext):
    """Context for generation spans (LLM operations)."""

    def input(self, content: Any) -> GenerationContext:
        """Set the input for the generation."""
        self._span.set_attribute("gen_ai.prompt", str(content))
        return self

    def output(self, content: Any) -> GenerationContext:
        """Set the output of the generation."""
        self._span.set_attribute("gen_ai.completion", str(content))
        return self

    def model(self, model_name: str) -> GenerationContext:
        """Set the model used for generation."""
        self._span.set_attribute("gen_ai.request.model", model_name)
        return self

    def usage(
        self,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ) -> GenerationContext:
        """Set token usage metrics."""
        if prompt_tokens is not None:
            self._span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
        if completion_tokens is not None:
            self._span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)
        if total_tokens is not None:
            self._span.set_attribute("gen_ai.usage.total_tokens", total_tokens)
        return self
