from typing import Any, Dict

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from .base import Exporter


class ConsoleExporter(Exporter):
    """Console exporter for debugging purposes."""

    REQUIRED_ENV_VARS: Dict[str, str] = {}
    OPTIONAL_ENV_VARS: Dict[str, Any] = {}

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        return BatchSpanProcessor(ConsoleSpanExporter())

    def get_name(self) -> str:
        return "console"
