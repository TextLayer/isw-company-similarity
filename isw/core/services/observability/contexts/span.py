from __future__ import annotations

from typing import List, Optional, Union

from .base import BaseContext


class TraceContext(BaseContext):
    """Context for trace-level spans (top-level operations)."""

    def tags(self, tags: List[str]) -> TraceContext:
        """Add tags to the trace."""
        self._span.set_attribute("tags", tags)
        return self

    def user(self, user_id: str) -> TraceContext:
        """Set the user ID for the trace."""
        self._span.set_attribute("user.id", user_id)
        return self

    def session(self, session_id: str) -> TraceContext:
        """Set the session ID for the trace."""
        self._span.set_attribute("session.id", session_id)
        return self

    def score(self, name: str, value: Union[float, str], comment: Optional[str] = None) -> TraceContext:
        """Add a trace-level score."""
        self._add_score(name, value, comment, score_type="trace_score")
        return self


class SpanContext(BaseContext):
    """Context for regular spans (sub-operations)."""

    def score(self, name: str, value: Union[float, str], comment: Optional[str] = None) -> SpanContext:
        """Add an observation-level score."""
        self._add_score(name, value, comment, score_type="score")
        return self
