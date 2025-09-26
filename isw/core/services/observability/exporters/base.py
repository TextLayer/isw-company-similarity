from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor


class EnvironmentConfig:
    """Helper class for managing environment variable configuration."""

    @staticmethod
    def require(var_name: str, error_message: Optional[str] = None) -> str:
        value = os.environ.get(var_name)
        if not value:
            raise ValueError(error_message or f"Required environment variable {var_name} is not set")
        return value

    @staticmethod
    def get(var_name: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(var_name, default)

    @staticmethod
    def get_bool(var_name: str, default: bool = False) -> bool:
        v = os.environ.get(var_name, "")
        if not v:
            return default
        return v.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def get_dict(var_name: str, delimiter: str = ",", separator: str = "=") -> Dict[str, str]:
        raw = os.environ.get(var_name, "")
        if not raw:
            return {}
        out: Dict[str, str] = {}
        for pair in raw.split(delimiter):
            if separator in pair:
                k, val = pair.split(separator, 1)
                out[k.strip()] = val.strip()
        return out


class Exporter(ABC):
    """Base class for all observability exporters."""

    REQUIRED_ENV_VARS: Dict[str, str] = {}
    OPTIONAL_ENV_VARS: Dict[str, Any] = {}

    def __init__(self) -> None:
        self.config = EnvironmentConfig()
        self.validate_environment()

    def validate_environment(self) -> None:
        """Validate that all required environment variables are set."""
        for k, desc in self.REQUIRED_ENV_VARS.items():
            self.config.require(k, f"{self.get_name().capitalize()} exporter requires {k}: {desc}")

    @abstractmethod
    def create_span_processor(self, resource: Resource) -> SpanProcessor:
        """Create and return the span processor for this exporter."""
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this exporter."""
        ...
