import base64

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .base import Exporter


class LangfuseExporter(Exporter):
    """Exporter for Langfuse observability platform."""

    REQUIRED_ENV_VARS = {"LANGFUSE_PUBLIC_KEY": "public key", "LANGFUSE_SECRET_KEY": "secret key"}
    OPTIONAL_ENV_VARS = {"LANGFUSE_HOST": (None, "custom host"), "LANGFUSE_REGION": ("EU", "US or EU")}

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        pk = self.config.require("LANGFUSE_PUBLIC_KEY")
        sk = self.config.require("LANGFUSE_SECRET_KEY")
        host = self.config.get("LANGFUSE_HOST")
        region = self.config.get("LANGFUSE_REGION", "EU")

        if host:
            endpoint = f"{host}/api/public/otel/v1/traces"
        elif region == "US":
            endpoint = "https://us.cloud.langfuse.com/api/public/otel/v1/traces"
        else:
            endpoint = "https://cloud.langfuse.com/api/public/otel/v1/traces"

        token = base64.b64encode(f"{pk}:{sk}".encode()).decode()
        headers = {"authorization": f"Basic {token}"}

        return BatchSpanProcessor(HTTPTraceExporter(endpoint=endpoint, headers=headers, timeout=10.0))

    def get_name(self) -> str:
        return "langfuse"
