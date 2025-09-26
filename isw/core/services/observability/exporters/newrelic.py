from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .base import Exporter


class NewRelicExporter(Exporter):
    """Exporter for New Relic observability platform."""

    REQUIRED_ENV_VARS = {"NEW_RELIC_API_KEY": "New Relic API key"}
    OPTIONAL_ENV_VARS = {"NEW_RELIC_REGION": ("US", "US|EU")}

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        api_key = self.config.require("NEW_RELIC_API_KEY")
        region = self.config.get("NEW_RELIC_REGION", "US")
        endpoint = "https://otlp.eu01.nr-data.net/v1/traces" if region == "EU" else "https://otlp.nr-data.net/v1/traces"
        headers = {"api-key": api_key}

        return BatchSpanProcessor(HTTPTraceExporter(endpoint=endpoint, headers=headers))

    def get_name(self) -> str:
        return "newrelic"
