from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .base import Exporter


class HoneycombExporter(Exporter):
    """Exporter for Honeycomb observability platform."""

    REQUIRED_ENV_VARS = {"HONEYCOMB_API_KEY": "Honeycomb team key"}
    OPTIONAL_ENV_VARS = {
        "HONEYCOMB_DATASET": ("llm-traces", "dataset"),
        "HONEYCOMB_ENDPOINT": ("https://api.honeycomb.io", "endpoint"),
    }

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        key = self.config.require("HONEYCOMB_API_KEY")
        dataset = self.config.get("HONEYCOMB_DATASET", "llm-traces")
        endpoint = self.config.get("HONEYCOMB_ENDPOINT", "https://api.honeycomb.io")
        headers = {"x-honeycomb-team": key, "x-honeycomb-dataset": dataset}

        return BatchSpanProcessor(HTTPTraceExporter(endpoint=f"{endpoint}/v1/traces", headers=headers))

    def get_name(self) -> str:
        return "honeycomb"
