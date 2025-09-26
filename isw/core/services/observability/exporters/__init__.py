import os
from typing import Any, Dict, Type

from .base import EnvironmentConfig, Exporter
from .console import ConsoleExporter
from .datadog import DatadogExporter
from .honeycomb import HoneycombExporter
from .langfuse import LangfuseExporter
from .newrelic import NewRelicExporter
from .otlp import OTLPExporter

# Registry of available exporters
EXPORTERS: Dict[str, Type[Exporter]] = {
    "console": ConsoleExporter,
    "datadog": DatadogExporter,
    "honeycomb": HoneycombExporter,
    "langfuse": LangfuseExporter,
    "otlp": OTLPExporter,
    "newrelic": NewRelicExporter,
}


def get_exporter(name: str) -> Exporter:
    """Get an exporter instance by name.

    Args:
        name: Name of the exporter (e.g., 'langfuse', 'datadog')

    Returns:
        Configured exporter instance

    Raises:
        ValueError: If the exporter name is unknown
    """
    if name not in EXPORTERS:
        raise ValueError(f"Unknown exporter: {name}")
    return EXPORTERS[name]()


def get_exporter_info() -> Dict[str, Dict[str, Any]]:
    """Get information about all available exporters.

    Returns:
        Dictionary mapping exporter names to their required and optional env vars
    """
    return {
        name: {"required": cls.REQUIRED_ENV_VARS, "optional": cls.OPTIONAL_ENV_VARS} for name, cls in EXPORTERS.items()
    }


def check_exporter_availability() -> Dict[str, bool]:
    """Check which exporters have their required environment variables configured.

    Returns:
        Dictionary mapping exporter names to availability status
    """
    out = {}
    for name, cls in EXPORTERS.items():
        out[name] = all(os.environ.get(var) for var in cls.REQUIRED_ENV_VARS)
    return out


__all__ = [
    "Exporter",
    "EnvironmentConfig",
    "ConsoleExporter",
    "DatadogExporter",
    "HoneycombExporter",
    "LangfuseExporter",
    "NewRelicExporter",
    "OTLPExporter",
    "EXPORTERS",
    "get_exporter",
    "get_exporter_info",
    "check_exporter_availability",
]
