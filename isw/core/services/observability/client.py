from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import ProxyTracerProvider, Span

from .contexts.generation import GenerationContext
from .contexts.span import SpanContext, TraceContext
from .exporters import check_exporter_availability, get_exporter

ObservationType = Literal["span", "generation", "event"]


def ensure_initialized(method: Callable) -> Callable:
    """Decorator to ensure the client is initialized before method execution."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._initialized:
            self.init()
        return method(self, *args, **kwargs)

    return wrapper


class ObservabilityClient:
    """
    Unified observability client built on OpenTelemetry with pluggable exporters.

    Features:
    - Auto-detection of exporters based on environment variables
    - Support for multiple simultaneous exporters
    - Clean API for manual tracing
    """

    def __init__(self) -> None:
        self._initialized = False
        self._tracer: Optional[trace.Tracer] = None
        self._exporters = []

    def init(
        self,
        exporters: Optional[Union[str, List[str]]] = None,
        app_name: str = "observability",
        environment: Optional[str] = None,
        version: Optional[str] = None,
    ) -> "ObservabilityClient":
        """
        Initialize the observability client.

        Args:
            exporters: Exporter name(s) or None for auto-detection
            app_name: Service name for tracing
            environment: Deployment environment (e.g., "production", "staging")
            version: Service version

        Returns:
            Self for method chaining
        """
        if self._initialized:
            return self

        resource = Resource.create(
            {
                "service.name": app_name,
                "deployment.environment": environment or "production",
                "service.version": version or "unknown",
            }
        )

        provider = TracerProvider(resource=resource)

        self._setup_exporters(exporters, provider, resource)

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(app_name)
        self._initialized = True
        return self

    def _setup_exporters(
        self, exporters: Optional[Union[str, List[str]]], provider: TracerProvider, resource: Resource
    ) -> None:
        """Set up exporters and add them to the tracer provider."""
        if exporters is None:
            exporters = self._auto_detect_exporters()
        elif isinstance(exporters, str):
            exporters = [exporters]

        self._exporters = []
        errors = []

        for name in exporters:
            try:
                exporter = get_exporter(name.strip())
                self._exporters.append(exporter)
                provider.add_span_processor(exporter.create_span_processor(resource))
            except Exception as e:
                errors.append(f"{name}: {e}")

        if not self._exporters and errors:
            logging.warning("Failed to initialize any exporters:\n" + "\n".join(errors))
        elif errors:
            logging.warning("Some exporters failed to initialize:\n" + "\n".join(errors))

    def _auto_detect_exporters(self) -> List[str]:
        """
        Auto-detect which exporters to use based on environment variables.

        Returns ALL exporters that have their required environment variables configured.

        Priority:
        1. OBSERVABILITY_EXPORTERS environment variable (comma-separated list)
        2. ALL available exporters based on environment variables
        3. Console exporter as fallback if none are configured
        """
        explicit_exporters = os.environ.get("OBSERVABILITY_EXPORTERS")
        if explicit_exporters:
            return [e.strip() for e in explicit_exporters.split(",")]

        availability = check_exporter_availability()

        available_exporters = [
            name for name, is_available in availability.items() if is_available and name != "console"
        ]

        if available_exporters:
            return available_exporters

        return ["console"]

    def _set_span_attributes(self, span: Span, metadata: Optional[Dict[str, Any]] = None, **attributes) -> None:
        """Helper to set attributes on a span."""
        if metadata:
            for key, value in metadata.items():
                span.set_attribute(f"metadata.{key}", str(value))

        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, str(value))

    @contextmanager
    @ensure_initialized
    def trace(
        self,
        name: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **attrs,
    ):
        """
        Create a new trace span (top-level operation).

        Args:
            name: Name of the trace
            user_id: Optional user identifier
            session_id: Optional session identifier
            tags: Optional list of tags
            metadata: Optional metadata dictionary
            **attrs: Additional attributes to set on the span

        Yields:
            TraceContext: A context object for the trace span
        """
        with self._tracer.start_as_current_span(name, kind=trace.SpanKind.SERVER) as span:
            if user_id:
                span.set_attribute("user.id", user_id)
            if session_id:
                span.set_attribute("session.id", session_id)
            if tags:
                span.set_attribute("tags", tags)

            self._set_span_attributes(span, metadata, **attrs)

            yield TraceContext(span)

    @contextmanager
    @ensure_initialized
    def span(self, name: str, *, metadata: Optional[Dict[str, Any]] = None, **attrs):
        """
        Create a new span (sub-operation).

        Args:
            name: Name of the span
            metadata: Optional metadata dictionary
            **attrs: Additional attributes to set on the span

        Yields:
            SpanContext: A context object for the span
        """
        with self._tracer.start_as_current_span(name) as span:
            self._set_span_attributes(span, metadata, **attrs)
            yield SpanContext(span)

    @contextmanager
    @ensure_initialized
    def generation(
        self,
        name: str = "generation",
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **attrs,
    ):
        """
        Create a generation span (LLM operation).

        Args:
            name: Name of the generation span
            model: Model name/identifier
            system: System prompt or configuration
            metadata: Optional metadata dictionary
            **attrs: Additional attributes to set on the span

        Yields:
            GenerationContext: A context object for the generation span
        """
        with self._tracer.start_as_current_span(name) as span:
            span.set_attribute("observation.type", "generation")

            if model:
                span.set_attribute("gen_ai.request.model", model)
            if system:
                span.set_attribute("gen_ai.system", system)

            self._set_span_attributes(span, metadata, **attrs)

            yield GenerationContext(span)

    @ensure_initialized
    def event(self, name: str, *, level: str = "info", metadata: Optional[Dict[str, Any]] = None, **attrs):
        """
        Add an event to the current span.

        Args:
            name: Event name
            level: Event level (e.g., "info", "warning", "error")
            metadata: Optional metadata dictionary
            **attrs: Additional event attributes
        """
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            payload = {"level": level}
            if metadata:
                payload.update(metadata)
            payload.update(attrs)
            span.add_event(name, payload)

    @ensure_initialized
    def score(
        self,
        name: str,
        value: Union[float, str],
        comment: Optional[str] = None,
        target: Literal["observation", "trace"] = "observation",
    ) -> None:
        """
        Add a score to the current observation or trace.

        Args:
            name: Score name/metric
            value: Score value
            comment: Optional comment about the score
            target: Whether to score the observation or entire trace
        """
        span = trace.get_current_span()
        if not span or not span.get_span_context().is_valid:
            return

        prefix = "trace_score" if target == "trace" else "score"
        span.set_attribute(f"{prefix}.{name}.value", str(value))

        if comment:
            span.set_attribute(f"{prefix}.{name}.comment", comment)

        span.add_event(f"{target}_score", {"name": name, "value": str(value), "comment": comment or ""})

    @ensure_initialized
    def flush(self, timeout_ms: int = 30000) -> None:
        """
        Flush all pending traces to exporters.

        Args:
            timeout_ms: Maximum time to wait for flush in milliseconds
        """
        provider = trace.get_tracer_provider()
        if isinstance(provider, ProxyTracerProvider):
            provider.force_flush(timeout_millis=timeout_ms)

    def get_exporter_status(self) -> Dict[str, Any]:
        """
        Get the status of configured exporters.

        Returns:
            Dictionary with exporter information
        """
        return {
            "configured": [e.get_name() for e in self._exporters],
            "available": list(check_exporter_availability().keys()),
            "ready": {name: available for name, available in check_exporter_availability().items()},
        }

    def observe(self, *args, **kwargs):
        """
        Decorator for observing functions.

        This is a convenience method that wraps the observe decorator.
        """
        from .decorators import observe as _observe

        return _observe(*args, **kwargs)
