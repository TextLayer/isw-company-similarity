from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCTraceExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPTraceExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .base import Exporter


class OTLPExporter(Exporter):
    """Generic OTLP exporter for OpenTelemetry-compatible backends."""

    REQUIRED_ENV_VARS = {"OTEL_EXPORTER_OTLP_ENDPOINT": "OTLP endpoint URL"}
    OPTIONAL_ENV_VARS = {
        "OTEL_EXPORTER_OTLP_HEADERS": (None, "key=value,..."),
        "OTEL_EXPORTER_OTLP_PROTOCOL": ("http", "http|grpc"),
        "OTEL_EXPORTER_OTLP_INSECURE": (False, "bool"),
    }

    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        endpoint = self.config.require("OTEL_EXPORTER_OTLP_ENDPOINT")
        protocol = self.config.get("OTEL_EXPORTER_OTLP_PROTOCOL", "http").lower()
        insecure = self.config.get_bool("OTEL_EXPORTER_OTLP_INSECURE", False)
        headers = self.config.get_dict("OTEL_EXPORTER_OTLP_HEADERS")

        if protocol == "grpc":
            endpoint = endpoint.replace("http://", "").replace("https://", "").replace(":4318", ":4317")
            exporter = GRPCTraceExporter(endpoint=endpoint, headers=headers, insecure=insecure)
        else:
            if not endpoint.endswith("/v1/traces"):
                endpoint = f"{endpoint}/v1/traces"
            exporter = HTTPTraceExporter(endpoint=endpoint, headers=headers)

        return BatchSpanProcessor(exporter)

    def get_name(self) -> str:
        return "otlp"
