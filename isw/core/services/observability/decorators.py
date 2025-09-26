from __future__ import annotations

import json
from functools import wraps
from typing import Any, Callable, Dict, Literal, Optional

from opentelemetry import trace
from opentelemetry.trace import ProxyTracerProvider, Status, StatusCode


def _get_span_kind(as_type: Optional[Literal["span", "generation", "trace"]]) -> trace.SpanKind:
    """Determine the appropriate span kind based on the observation type."""
    return trace.SpanKind.INTERNAL if as_type != "trace" else trace.SpanKind.SERVER


def _set_span_attributes(span: trace.Span, attributes: Optional[Dict[str, Any]], as_type: Optional[str]) -> None:
    """Set attributes on the span, including type-specific and custom attributes."""
    if as_type == "generation":
        span.set_attribute("observation.type", "generation")

    if attributes:
        for k, v in attributes.items():
            try:
                span.set_attribute(k, v)
            except (TypeError, ValueError):
                span.set_attribute(k, str(v))


def _capture_input(span: trace.Span, args: tuple, kwargs: dict) -> None:
    """Capture function input arguments as span attributes."""
    try:
        input_data = {"args": args, "kwargs": kwargs}
        try:
            input_str = json.dumps(input_data, default=str, ensure_ascii=False, indent=None)
        except (TypeError, ValueError, RecursionError):
            input_str = repr(input_data)

        span.set_attribute("input", input_str)
    except Exception:
        pass


def _capture_output(span: trace.Span, result: Any) -> None:
    """Capture function output as span attributes."""
    try:
        try:
            output_str = json.dumps(result, default=str, ensure_ascii=False, indent=None)
        except (TypeError, ValueError, RecursionError):
            output_str = repr(result)

        span.set_attribute("output", output_str)
    except Exception:
        pass


def _handle_exception(span: trace.Span, e: Exception) -> None:
    """Record exception details in the span."""
    span.set_attribute("error", True)
    span.set_attribute("error.type", type(e).__name__)
    span.set_attribute("error.message", str(e))
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR, str(e)))


def observe(
    name: Optional[str] = None,
    *,
    as_type: Optional[Literal["span", "generation", "trace"]] = None,
    capture_input: bool = True,
    capture_output: bool = True,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for observing function execution with OpenTelemetry spans.

    Args:
        name: Custom name for the span (defaults to function name)
        as_type: Type of observation:
            - "span" (default): Creates a regular child span
            - "generation": Creates a span marked as LLM generation
            - "trace": Creates a root span
        capture_input: Whether to capture function arguments
        capture_output: Whether to capture function return value
        attributes: Additional attributes to add to the span

    The decorator will:
    - Create INTERNAL spans by default
    - Only create SERVER spans when explicitly marked as_type="trace"
    - Skip tracing if observability is not initialized
    """

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        span_name = name or fn.__name__

        @wraps(fn)
        def _wrapped(*args, **kwargs):
            tracer = trace.get_tracer("observability")

            provider = trace.get_tracer_provider()
            if provider is None or isinstance(provider, ProxyTracerProvider):
                return fn(*args, **kwargs)

            span_kind = _get_span_kind(as_type)
            with tracer.start_as_current_span(span_name, kind=span_kind) as span:
                _set_span_attributes(span, attributes, as_type)

                if capture_input and (args or kwargs):
                    _capture_input(span, args, kwargs)

                try:
                    result = fn(*args, **kwargs)

                    if capture_output:
                        _capture_output(span, result)

                    return result

                except Exception as e:
                    _handle_exception(span, e)
                    raise

        return _wrapped

    return _decorator
