"""Base classes for entity collection from various data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class IdentifierType(str, Enum):
    """Type of entity identifier."""

    CIK = "CIK"  # SEC Central Index Key (US)
    LEI = "LEI"  # Legal Entity Identifier (EU/UK)


class Jurisdiction(str, Enum):
    """Jurisdiction of the entity."""

    US = "US"
    EU = "EU"
    UK = "UK"


@dataclass
class EntityRecord:
    """
    Represents a collected entity from a data source.

    This is the standardized output format for all entity collectors,
    used to create a unified master list of companies across jurisdictions.
    """

    name: str
    identifier: str
    jurisdiction: Jurisdiction
    identifier_type: IdentifierType

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "identifier": self.identifier,
            "jurisdiction": self.jurisdiction.value,
            "identifier_type": self.identifier_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntityRecord":
        """Create an EntityRecord from a dictionary."""
        return cls(
            name=data["name"],
            identifier=data["identifier"],
            jurisdiction=Jurisdiction(data["jurisdiction"]),
            identifier_type=IdentifierType(data["identifier_type"]),
        )


class EntityCollector(ABC):
    """
    Abstract base class for entity collectors.

    Entity collectors are responsible for fetching lists of companies
    from various data sources (SEC EDGAR, filings.xbrl.org, etc.).

    Each collector should implement:
    - fetch_entities(): Retrieve all entities from the source
    - get_source_name(): Return an identifier for logging/debugging
    """

    @abstractmethod
    def fetch_entities(self) -> list[EntityRecord]:
        """
        Fetch all entities from this data source.

        Returns:
            List of EntityRecord objects representing companies.

        Raises:
            EntityCollectionError: If collection fails.
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the name of this data source.

        Used for logging and debugging purposes.

        Returns:
            Human-readable source name (e.g., "SEC EDGAR", "filings.xbrl.org")
        """
        ...


class EntityCollectionError(Exception):
    """Base exception for entity collection errors."""

    pass


class DownloadError(EntityCollectionError):
    """Error downloading data from a source."""

    pass


class ParseError(EntityCollectionError):
    """Error parsing data from a source."""

    pass
