from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Tracer

try:
    import litellm  # noqa: F401
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    CustomLogger = object

from ..semconv import CUSTOM, ERR, GENAI, set_kv


class LiteLLMCallbackHandler(CustomLogger):
    """
    LiteLLM callback handler for OpenTelemetry tracing.

    This handler integrates with LiteLLM's callback system to capture
    LLM operations and emit them as OpenTelemetry spans.

    Usage:
        import litellm
        from isw.core.services.observability.integrations import LiteLLMCallbackHandler

        # Create handler
        handler = LiteLLMCallbackHandler()

        # Add to LiteLLM callbacks
        litellm.callbacks = [handler]

        # Now all LiteLLM calls will be traced!
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """

    def __init__(
        self,
        tracer: Optional[Tracer] = None,
        trace_content: bool = True,
        *,
        metadata_allowlist: Optional[Iterable[str]] = None,
    ):
        super().__init__()
        self.tracer = tracer or trace.get_tracer("litellm")
        self.trace_content = trace_content
        self.active_spans: Dict[str, Any] = {}
        self.call_details: Dict[str, Any] = {}
        self.metadata_allowlist = set(metadata_allowlist) if metadata_allowlist else None

    def _determine_operation_type(self, messages: list, kwargs: dict) -> str:
        """Determine the operation type based on request parameters."""
        if kwargs.get("litellm_params", {}).get("api_base", "").endswith("/embeddings"):
            return "embedding"
        return "chat" if messages else "completion"

    def _set_basic_span_attributes(self, span, model: str, op: str) -> None:
        """Set basic span attributes for the LLM request."""
        set_kv(span, "observation.type", "generation")
        set_kv(span, GENAI["req_model"], model)
        set_kv(span, GENAI["op_name"], op)

    def _set_request_parameters(self, span, kwargs: dict) -> None:
        """Set request parameter attributes on the span."""
        optional = kwargs.get("optional_params", {})
        set_kv(span, GENAI["req_temperature"], kwargs.get("temperature", optional.get("temperature")))
        set_kv(span, GENAI["req_max_tokens"], kwargs.get("max_tokens", optional.get("max_tokens")))
        set_kv(span, GENAI["req_top_p"], kwargs.get("top_p", optional.get("top_p")))
        set_kv(span, GENAI["req_stream"], kwargs.get("stream"))

    def _set_user_context(self, span, kwargs: dict) -> None:
        """Set user context attributes if available."""
        if "user" in kwargs:
            set_kv(span, "gen_ai.request.user", kwargs["user"])

    def _set_metadata(self, span, kwargs: dict) -> None:
        """Set metadata attributes if allowlist is configured."""
        if not self.metadata_allowlist:
            return

        metadata = kwargs.get("metadata", {})
        for key in self.metadata_allowlist:
            if key in metadata:
                set_kv(span, f"metadata.{key}", metadata[key])

    def _trace_messages(self, span, messages: list) -> None:
        """Trace message content if enabled."""
        if not self.trace_content or not messages:
            return

        for i, msg in enumerate(messages):
            if not msg:
                continue

            role = msg.get("role", "user")
            set_kv(span, GENAI["prompt_role"].format(i=i), role)

            content = msg.get("content", "")

            if isinstance(content, list):
                # For multimodal messages, extract text parts
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif "text" in part:
                            text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "\n".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)

            set_kv(span, GENAI["prompt_content"].format(i=i), content)

            if "function_call" in msg:
                func_call = msg["function_call"]
                set_kv(span, f"gen_ai.prompt.{i}.function_call.name", func_call.get("name", ""))
                set_kv(span, f"gen_ai.prompt.{i}.function_call.arguments", func_call.get("arguments", ""))

            if "tool_calls" in msg:
                for j, tool_call in enumerate(msg["tool_calls"]):
                    if isinstance(tool_call, dict):
                        set_kv(span, f"gen_ai.prompt.{i}.tool_call.{j}.id", tool_call.get("id", ""))
                        set_kv(span, f"gen_ai.prompt.{i}.tool_call.{j}.type", tool_call.get("type", ""))
                        if "function" in tool_call:
                            func = tool_call["function"]
                            set_kv(span, f"gen_ai.prompt.{i}.tool_call.{j}.function.name", func.get("name", ""))
                            set_kv(
                                span, f"gen_ai.prompt.{i}.tool_call.{j}.function.arguments", func.get("arguments", "")
                            )

            # Handle name field (for function responses)
            if "name" in msg:
                set_kv(span, f"gen_ai.prompt.{i}.name", msg["name"])

    def log_pre_api_call(self, model: str, messages: list, kwargs: dict, **params: Any):
        """Called before the API call is made."""
        call_id = kwargs.get("litellm_call_id", str(time.time()))
        self.call_details[call_id] = {"model": model, "messages": messages, "kwargs": kwargs}

        op = self._determine_operation_type(messages, kwargs)
        span = self.tracer.start_span(name=f"litellm.{op}", kind=trace.SpanKind.CLIENT)

        self._set_basic_span_attributes(span, model, op)
        self._set_request_parameters(span, kwargs)
        self._set_user_context(span, kwargs)
        self._set_metadata(span, kwargs)
        self._trace_messages(span, messages)

        self.active_spans[call_id] = span

    def _trace_response_metadata(self, span, response_obj: Any, call_id: str) -> None:
        """Trace response metadata like model and ID."""
        res_model = getattr(response_obj, "model", None)
        req_model = self.call_details.get(call_id, {}).get("model")
        if res_model and res_model != req_model:
            set_kv(span, GENAI["res_model"], res_model)
        set_kv(span, GENAI["res_id"], getattr(response_obj, "id", None))

        # Finish reason
        if getattr(response_obj, "choices", None):
            fr = getattr(response_obj.choices[0], "finish_reason", None)
            if fr:
                set_kv(span, GENAI["res_finish_reasons"], [fr])

    def _trace_completion_message(self, span, message, index: int) -> None:
        """Trace a single completion message."""
        # Extract role (handle both object and dict formats)
        if hasattr(message, "role"):
            role = message.role
        elif isinstance(message, dict) and "role" in message:
            role = message["role"]
        else:
            role = "assistant"  # Default role
        set_kv(span, GENAI["comp_role"].format(i=index), role)

        content = ""
        if hasattr(message, "content"):
            content = message.content
        elif isinstance(message, dict) and "content" in message:
            content = message["content"]

        if content is None:
            content = ""
        elif not isinstance(content, str):
            content = str(content)

        set_kv(span, GENAI["comp_content"].format(i=index), content)

        func_call = None
        if hasattr(message, "function_call"):
            func_call = message.function_call
        elif isinstance(message, dict) and "function_call" in message:
            func_call = message["function_call"]

        if func_call:
            name = getattr(func_call, "name", None) if hasattr(func_call, "name") else func_call.get("name", "")
            args = (
                getattr(func_call, "arguments", None)
                if hasattr(func_call, "arguments")
                else func_call.get("arguments", "")
            )
            set_kv(span, f"gen_ai.completion.{index}.function_call.name", name)
            set_kv(span, f"gen_ai.completion.{index}.function_call.arguments", args)

        tool_calls = None
        if hasattr(message, "tool_calls"):
            tool_calls = message.tool_calls
        elif isinstance(message, dict) and "tool_calls" in message:
            tool_calls = message["tool_calls"]

        if tool_calls:
            for j, tool_call in enumerate(tool_calls):
                if hasattr(tool_call, "id"):
                    tool_id = tool_call.id
                elif isinstance(tool_call, dict):
                    tool_id = tool_call.get("id", "")
                else:
                    tool_id = ""

                if hasattr(tool_call, "type"):
                    tool_type = tool_call.type
                elif isinstance(tool_call, dict):
                    tool_type = tool_call.get("type", "")
                else:
                    tool_type = ""

                set_kv(span, f"gen_ai.completion.{index}.tool_call.{j}.id", tool_id)
                set_kv(span, f"gen_ai.completion.{index}.tool_call.{j}.type", tool_type)

                func = None
                if hasattr(tool_call, "function"):
                    func = tool_call.function
                elif isinstance(tool_call, dict) and "function" in tool_call:
                    func = tool_call["function"]

                if func:
                    func_name = getattr(func, "name", None) if hasattr(func, "name") else func.get("name", "")
                    func_args = (
                        getattr(func, "arguments", None) if hasattr(func, "arguments") else func.get("arguments", "")
                    )
                    set_kv(span, f"gen_ai.completion.{index}.tool_call.{j}.function.name", func_name)
                    set_kv(span, f"gen_ai.completion.{index}.tool_call.{j}.function.arguments", func_args)

    def _trace_completions(self, span, response_obj: Any, kwargs: dict) -> None:
        """Trace completion messages from the response."""
        if not self.trace_content:
            return

        complete_stream = kwargs.get("complete_streaming_response")
        response_to_trace = complete_stream if complete_stream else response_obj

        # Get choices from the response
        choices = []
        if hasattr(response_to_trace, "choices"):
            choices = response_to_trace.choices
        elif isinstance(response_to_trace, dict) and "choices" in response_to_trace:
            choices = response_to_trace["choices"]

        if not choices:
            return

        for i, choice in enumerate(choices):
            # Try to get the message (non-streaming) or delta (streaming)
            message = None
            if hasattr(choice, "message") and choice.message:
                message = choice.message
            elif hasattr(choice, "delta") and choice.delta:
                message = choice.delta
            elif isinstance(choice, dict):
                message = choice.get("message") or choice.get("delta")

            if message:
                self._trace_completion_message(span, message, i)
            # Fallback for text completions (older OpenAI format)
            elif hasattr(choice, "text") or (isinstance(choice, dict) and "text" in choice):
                text = getattr(choice, "text", None) if hasattr(choice, "text") else choice.get("text", "")
                set_kv(span, GENAI["comp_role"].format(i=i), "assistant")
                set_kv(span, GENAI["comp_content"].format(i=i), text or "")

    def _trace_usage(self, span, response_obj: Any) -> None:
        """Trace token usage metrics."""
        usage = getattr(response_obj, "usage", None)
        if not usage:
            return

        # Extract token counts
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        if prompt_tokens is None and isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens")

        completion_tokens = getattr(usage, "completion_tokens", None)
        if completion_tokens is None and isinstance(usage, dict):
            completion_tokens = usage.get("completion_tokens")

        total_tokens = getattr(usage, "total_tokens", None)
        if total_tokens is None and isinstance(usage, dict):
            total_tokens = usage.get("total_tokens")

        # Calculate total if not provided
        if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
            total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

        # Set attributes
        set_kv(span, GENAI["usage_prompt"], prompt_tokens)
        set_kv(span, GENAI["usage_completion"], completion_tokens)
        set_kv(span, GENAI["usage_total"], total_tokens)

    def _trace_custom_attributes(self, span, kwargs: dict) -> None:
        """Trace custom attributes like cost and cache hits."""
        if "response_cost" in kwargs:
            set_kv(span, CUSTOM["total_cost"], kwargs["response_cost"])
        if "cache_hit" in kwargs:
            set_kv(span, CUSTOM["cache_hit"], kwargs["cache_hit"])

    def log_success_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any):
        """Called when the API call succeeds."""
        call_id = kwargs.get("litellm_call_id", str(start_time))
        span = self.active_spans.get(call_id)
        if not span:
            return

        try:
            self._trace_response_metadata(span, response_obj, call_id)
            self._trace_completions(span, response_obj, kwargs)
            self._trace_usage(span, response_obj)
            self._trace_custom_attributes(span, kwargs)

            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            set_kv(span, ERR["flag"], True)
            set_kv(span, ERR["type"], type(e).__name__)
            set_kv(span, ERR["message"], str(e))
            span.set_status(Status(StatusCode.ERROR, str(e)))
        finally:
            span.end()
            self.active_spans.pop(call_id, None)
            self.call_details.pop(call_id, None)

    def log_post_api_call(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any):
        """Called after the API call completes."""
        call_id = kwargs.get("litellm_call_id", str(start_time))
        span = self.active_spans.get(call_id)
        if span:
            span.add_event("llm.response_received", {})

    def log_failure_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any):
        """Called when the API call fails."""
        call_id = kwargs.get("litellm_call_id", str(start_time))
        span = self.active_spans.get(call_id)
        if not span:
            return
        try:
            exc = kwargs.get("exception", response_obj)
            set_kv(span, ERR["flag"], True)
            set_kv(span, ERR["type"], type(exc).__name__ if exc else "Unknown")
            set_kv(span, ERR["message"], str(exc) if exc else "Unknown")
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
        finally:
            span.end()
            self.active_spans.pop(call_id, None)
            self.call_details.pop(call_id, None)

    def log_stream_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any):
        """Called for each streaming chunk."""
        call_id = kwargs.get("litellm_call_id", str(start_time))
        span = self.active_spans.get(call_id)
        if not span or not self.trace_content:
            return
        try:
            chunk = getattr(response_obj, "choices", None)
            if not chunk:
                return
            c = chunk[0]
            text = getattr(getattr(c, "delta", None), "content", None) or getattr(c, "text", None) or ""
            if text:
                span.add_event("gen_ai.stream.delta", {"content": text[:512]})
        except Exception:
            pass

    async def async_log_pre_api_call(self, model: str, messages: list, kwargs: dict, **params: Any):
        """Async version of log_pre_api_call."""
        self.log_pre_api_call(model, messages, kwargs, **params)

    async def async_log_post_api_call(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any
    ):
        """Async version of log_post_api_call."""
        self.log_post_api_call(kwargs, response_obj, start_time, end_time, **params)

    async def async_log_success_event(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any
    ):
        """Async version of log_success_event."""
        self.log_success_event(kwargs, response_obj, start_time, end_time, **params)

    async def async_log_failure_event(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any
    ):
        """Async version of log_failure_event."""
        self.log_failure_event(kwargs, response_obj, start_time, end_time, **params)

    async def async_log_stream_event(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float, **params: Any
    ):
        """Async version of log_stream_event."""
        self.log_stream_event(kwargs, response_obj, start_time, end_time, **params)
