from __future__ import annotations

from typing import Any, Dict, Optional, Union

from opentelemetry.trace import Span, Status, StatusCode


class BaseContext:
    """Base context class for all span contexts."""

    def __init__(self, span: Span):
        self._span = span

    @property
    def span(self) -> Span:
        """Get the underlying OpenTelemetry span."""
        return self._span

    def _set_attributes(self, prefix: Optional[str] = None, **attributes) -> None:
        """Helper to set attributes with optional prefix."""
        for key, value in attributes.items():
            if value is not None:
                attr_key = f"{prefix}.{key}" if prefix else key
                self._span.set_attribute(attr_key, str(value))

    def _add_score(
        self, name: str, value: Union[float, str], comment: Optional[str] = None, score_type: str = "score"
    ) -> None:
        """Helper to add a score with consistent formatting."""
        self._span.set_attribute(f"{score_type}.{name}.value", str(value))
        if comment:
            self._span.set_attribute(f"{score_type}.{name}.comment", comment)

        event_data = {"name": name, "value": str(value), "comment": comment or ""}
        self._span.add_event(score_type, event_data)

    def metadata(self, data: Dict[str, Any]) -> BaseContext:
        """Add metadata to the span."""
        self._set_attributes(prefix="metadata", **data)
        return self

    def error(self, exception: Exception) -> BaseContext:
        """Record an error on the span."""
        self._span.set_attribute("error", True)
        self._span.set_attribute("error.type", type(exception).__name__)
        self._span.set_attribute("error.message", str(exception))
        self._span.record_exception(exception)
        self._span.set_status(Status(StatusCode.ERROR, str(exception)))
        return self
