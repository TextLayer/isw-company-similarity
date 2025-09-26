from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode, Tracer

from ..semconv import ERR, GENAI, set_kv

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import AgentAction, AgentFinish, LLMResult

    HAS_LANGCHAIN = True
except ImportError:
    BaseCallbackHandler = object  # type: ignore
    AgentAction = Any  # type: ignore
    AgentFinish = Any  # type: ignore
    LLMResult = Any  # type: ignore
    HAS_LANGCHAIN = False


class LangchainCallbackHandler(BaseCallbackHandler):  # type: ignore[misc]
    """
    LangChain callback handler for OpenTelemetry tracing.

    Converts LangChain operations into OpenTelemetry spans following
    GenAI semantic conventions. Supports LLMs, chains, tools, and agents.
    """

    def __init__(self, tracer: Optional[Tracer] = None, trace_content: bool = True, **kwargs: Any):
        """
        Initialize the LangChain callback handler.

        Args:
            tracer: OpenTelemetry tracer to use (defaults to global tracer)
            trace_content: Whether to capture prompts/completions in traces
            **kwargs: Additional configuration options
        """
        if not HAS_LANGCHAIN:
            raise ImportError("LangChain is not installed. Install it with: pip install langchain")

        super().__init__()
        self.tracer = tracer or trace.get_tracer("langchain")
        self.trace_content = trace_content
        self._spans: Dict[UUID, Span] = {}

    # ---------- LLM Lifecycle ----------

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an LLM starts generating."""
        model = self._extract_model_name(serialized)
        span = self.tracer.start_span(f"langchain.llm.{run_id}")

        # Set standard attributes
        set_kv(span, "observation.type", "generation")
        set_kv(span, GENAI["req_model"], model)
        set_kv(span, GENAI["op_name"], "chat")

        # Capture prompts if content tracing is enabled
        if self.trace_content:
            self._set_prompts(span, prompts)

        self._spans[run_id] = span

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an LLM finishes generating."""
        span = self._spans.pop(run_id, None)
        if not span:
            return

        try:
            # Capture completions
            if self.trace_content:
                self._set_completions(span, response)

            # Capture token usage
            self._set_usage_metrics(span, response)

            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            self._record_error(span, e)
        finally:
            span.end()

    def on_llm_error(self, error: Exception, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an LLM encounters an error."""
        span = self._spans.pop(run_id, None)
        if span:
            self._record_error(span, error)
            span.end()

    # ---------- Chain Lifecycle ----------

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when a chain starts."""
        self._add_event("chain_start", name=serialized.get("name", "unknown"), inputs=self._truncate(str(inputs)))

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: UUID, **kwargs: Any) -> None:
        """Called when a chain completes."""
        self._add_event("chain_end", outputs=self._truncate(str(outputs)))

    def on_chain_error(self, error: Exception, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when a chain encounters an error."""
        self._add_error_event("chain_error", error)

    # ---------- Tool Lifecycle ----------

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when a tool starts."""
        self._add_event("tool_start", name=serialized.get("name", "unknown"), input=self._truncate(input_str))

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when a tool completes."""
        self._add_event("tool_end", output=self._truncate(str(output)))

    def on_tool_error(self, error: Exception, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when a tool encounters an error."""
        self._add_error_event("tool_error", error)

    # ---------- Agent Lifecycle ----------

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an agent takes an action."""
        self._add_event("agent_action", tool=action.tool, log=self._truncate(action.log, max_length=500))

    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an agent finishes."""
        self._add_event("agent_finish", return_values=self._truncate(str(finish.return_values)))

    # ---------- Helper Methods ----------

    def _extract_model_name(self, serialized: Dict[str, Any]) -> str:
        """Extract model name from serialized data."""
        model_id = serialized.get("id")

        if isinstance(model_id, list):
            return model_id[0] if model_id else "unknown"
        elif model_id:
            return str(model_id)

        return serialized.get("name", "unknown")

    def _set_prompts(self, span: Span, prompts: List[str]) -> None:
        """Set prompt attributes on the span."""
        for i, prompt in enumerate(prompts):
            set_kv(span, GENAI["prompt_role"].format(i=i), "user")
            set_kv(span, GENAI["prompt_content"].format(i=i), prompt)

    def _set_completions(self, span: Span, response: LLMResult) -> None:
        """Set completion attributes on the span."""
        if not hasattr(response, "generations"):
            return

        idx = 0
        for generation_batch in response.generations:
            for generation in generation_batch:
                text = getattr(generation, "text", "")
                set_kv(span, GENAI["comp_role"].format(i=idx), "assistant")
                set_kv(span, GENAI["comp_content"].format(i=idx), text)
                idx += 1

    def _set_usage_metrics(self, span: Span, response: LLMResult) -> None:
        """Set token usage metrics on the span."""
        llm_output = getattr(response, "llm_output", {}) or {}
        usage = llm_output.get("token_usage") or {}

        if not usage:
            return

        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")

        # Calculate total if not provided
        if total_tokens is None and (prompt_tokens or completion_tokens):
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

        set_kv(span, GENAI["usage_prompt"], prompt_tokens)
        set_kv(span, GENAI["usage_completion"], completion_tokens)
        set_kv(span, GENAI["usage_total"], total_tokens)

    def _record_error(self, span: Span, error: Exception) -> None:
        """Record an error on the span."""
        set_kv(span, ERR["flag"], True)
        set_kv(span, ERR["type"], type(error).__name__)
        set_kv(span, ERR["message"], str(error))
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))

    def _add_event(self, event_name: str, **attributes: Any) -> None:
        """Add an event to the current span."""
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span.add_event(event_name, attributes)

    def _add_error_event(self, event_name: str, error: Exception) -> None:
        """Add an error event to the current span."""
        self._add_event(event_name, type=type(error).__name__, message=str(error))

    def _truncate(self, text: str, max_length: int = 1000) -> str:
        """Truncate text to a maximum length."""
        return text[:max_length] if len(text) > max_length else text
