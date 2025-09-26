from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .base import Exporter


class DatadogExporter(Exporter):
    """Exporter for Datadog APM."""

    REQUIRED_ENV_VARS = {"DD_API_KEY": "Datadog API key"}
    OPTIONAL_ENV_VARS = {"DD_SITE": ("datadoghq.com", "site")}

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        api_key = self.config.require("DD_API_KEY")
        site = self.config.get("DD_SITE", "datadoghq.com")
        endpoint = f"https://api.{site}/v0.3/traces"
        headers = {"DD-API-KEY": api_key}

        return BatchSpanProcessor(HTTPTraceExporter(endpoint=endpoint, headers=headers))

    def get_name(self) -> str:
        return "datadog"
