"""Entity collection services for gathering company master lists."""

from .base import (
    DownloadError,
    EntityCollectionError,
    EntityCollector,
    EntityRecord,
    IdentifierType,
    Jurisdiction,
    ParseError,
)
from .edgar_collector import SECEdgarCollector
from .esef_collector import ESEFCollector

__all__ = [
    # Base classes
    "EntityCollector",
    "EntityRecord",
    # Collectors
    "SECEdgarCollector",
    "ESEFCollector",
    # Enums
    "IdentifierType",
    "Jurisdiction",
    # Exceptions
    "EntityCollectionError",
    "DownloadError",
    "ParseError",
]
