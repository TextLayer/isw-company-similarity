from __future__ import annotations

from typing import Any, Dict, Optional, Union

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode


def _get_current_span() -> Optional[Span]:
    """Get the current span if valid."""
    try:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return span
    except Exception:
        pass
    return None


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID as a hex string."""
    span = _get_current_span()
    if span:
        ctx = span.get_span_context()
        return format(ctx.trace_id, "032x")
    return None


def get_current_observation_id() -> Optional[str]:
    """Get the current span/observation ID as a hex string."""
    span = _get_current_span()
    if span:
        ctx = span.get_span_context()
        return format(ctx.span_id, "016x")
    return None


def update_current_observation(
    name: Optional[str] = None,
    input: Optional[Any] = None,
    output: Optional[Any] = None,
    level: Optional[str] = None,
    status_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """
    Update the current observation/span with specific attributes.

    This function mimics Langfuse SDK's update_current_observation functionality,
    allowing you to modify the current observation's properties from within a decorated function.

    Args:
        name: New name for the observation
        input: Input data for the observation
        output: Output data from the observation
        level: Log level (e.g., "INFO", "WARNING", "ERROR")
        status_message: Status message to record
        metadata: Additional metadata dictionary
        **kwargs: Additional attributes to set on the span

    Example:
        # Update observation name and add metadata
        update_current_observation(
            name="Updated Function Name",
            metadata={"key": "value", "processing_step": "validation"}
        )

        # Update input/output for generation context
        update_current_observation(
            input={"param1": "value1"},
            output="Result of processing"
        )

        # Set warning level with status message
        update_current_observation(
            level="WARNING",
            status_message="Some important warning"
        )

        # Update multiple properties at once
        update_current_observation(
            name="Final Processing Step",
            input={"data": "processed_data"},
            output={"result": "success"},
            level="INFO",
            status_message="Processing completed successfully",
            metadata={"duration_ms": 150, "records_processed": 1000}
        )
    """
    span = _get_current_span()
    if not span:
        return

    # Update observation name
    if name is not None:
        span.set_attribute("observation.name", str(name))
        span.set_attribute("span.name", str(name))

    # Update input/output (for generation contexts)
    if input is not None:
        span.set_attribute("gen_ai.prompt", str(input))
        span.set_attribute("observation.input", str(input))

    if output is not None:
        span.set_attribute("gen_ai.completion", str(output))
        span.set_attribute("observation.output", str(output))

    # Update level
    if level is not None:
        span.set_attribute("observation.level", str(level))
        # Map level to appropriate status
        if level.upper() in ["ERROR", "CRITICAL"]:
            span.set_status(Status(StatusCode.ERROR, status_message or f"Level: {level}"))
        elif level.upper() in ["WARNING"]:
            span.set_status(Status(StatusCode.ERROR, status_message or f"Level: {level}"))
        else:
            span.set_status(Status(StatusCode.OK, status_message or ""))

    # Update status message
    if status_message is not None:
        span.set_attribute("observation.status_message", str(status_message))
        # Update span status if level wasn't provided
        if level is None:
            span.set_status(Status(StatusCode.OK, str(status_message)))

    # Update metadata
    if metadata is not None:
        for key, value in metadata.items():
            span.set_attribute(f"metadata.{key}", str(value))

    # Handle additional attributes
    for key, value in kwargs.items():
        span.set_attribute(key, str(value))


def update_current_trace(**kwargs) -> None:
    """
    Update the current trace/span with additional attributes.

    Supported kwargs:
    - user_id: User identifier
    - session_id: Session identifier
    - tags: List of tags
    - metadata: Dictionary of metadata
    - attributes: Dictionary of custom attributes
    - error: Error message to record
    - record_exception: Exception to record
    - status: Tuple of (StatusCode, description)
    """
    span = _get_current_span()
    if not span:
        return

    # Standard attributes
    if user_id := kwargs.get("user_id"):
        span.set_attribute("user.id", user_id)
    if session_id := kwargs.get("session_id"):
        span.set_attribute("session.id", session_id)
    if tags := kwargs.get("tags"):
        span.set_attribute("tags", tags)

    # Metadata
    if metadata := kwargs.get("metadata"):
        for key, value in metadata.items():
            span.set_attribute(f"metadata.{key}", str(value))

    # Custom attributes
    if attributes := kwargs.get("attributes"):
        for key, value in attributes.items():
            span.set_attribute(key, str(value))

    # Error handling
    if error_msg := kwargs.get("error"):
        span.set_attribute("error", True)
        span.set_attribute("error.message", str(error_msg))

    if exception := kwargs.get("record_exception"):
        span.record_exception(exception)

    if status := kwargs.get("status"):
        code, description = status
        span.set_status(Status(code, description or ""))


def score_current_observation(name: str, value: Union[float, str], comment: Optional[str] = None) -> None:
    """Add a score to the current observation/span."""
    span = _get_current_span()
    if span:
        span.set_attribute(f"score.{name}.value", str(value))
        if comment:
            span.set_attribute(f"score.{name}.comment", comment)

        span.add_event("score", {"name": name, "value": str(value), "comment": comment or ""})


def score_current_trace(name: str, value: Union[float, str], comment: Optional[str] = None) -> None:
    """Add a score to the current trace."""
    span = _get_current_span()
    if span:
        span.set_attribute(f"trace_score.{name}.value", str(value))
        if comment:
            span.set_attribute(f"trace_score.{name}.comment", comment)

        span.add_event("trace_score", {"name": name, "value": str(value), "level": "trace", "comment": comment or ""})
