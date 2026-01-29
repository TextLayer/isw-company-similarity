"""Base data source abstraction for fetching filing data."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class DataSourceError(Exception):
    """Base exception for data source errors."""


class FilingNotFoundError(DataSourceError):
    """Raised when a requested filing cannot be found."""


class RateLimitError(DataSourceError):
    """Raised when rate limited by the data source."""


@dataclass
class Filing:
    """Represents a filing retrieved from a data source."""

    identifier: str
    filing_type: str
    filing_date: str
    accession_number: str | None = None
    document_url: str | None = None
    raw_data: dict[str, Any] | None = None


@dataclass
class BusinessDescription:
    """Extracted business description from a filing."""

    text: str
    source_filing: str
    extraction_method: str


@dataclass
class RevenueData:
    """Revenue data extracted from a filing."""

    amount: int
    currency: str
    period_end: str
    source_tag: str


class BaseDataSource(ABC):
    """
    Abstract base class for data sources that retrieve filing information.

    Data sources fetch SEC filings, ESEF filings, or cached versions from
    various providers. Each source handles its own identifier format and
    API-specific logic.

    Concrete implementations:
    - EDGARDataSource: SEC EDGAR for US filings (CIK identifier)
    - FilingsXBRLDataSource: filings.xbrl.org for EU/UK filings (LEI identifier)
    - AzureBlobDataSource: Cached filings from Azure Blob Storage
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name for this data source."""
        ...

    @abstractmethod
    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        """
        Retrieve a specific filing by identifier and type.

        Args:
            identifier: Entity identifier (CIK for US, LEI for EU/UK).
            filing_type: Type of filing (e.g., "10-K", "AFR").

        Returns:
            Filing if found, None otherwise.

        Raises:
            DataSourceError: If retrieval fails.
            RateLimitError: If rate limited.
        """
        ...

    @abstractmethod
    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        """
        Get the most recent annual report for an entity.

        For US entities, this is the 10-K. For EU/UK, the Annual Financial Report.

        Args:
            identifier: Entity identifier.

        Returns:
            Most recent annual Filing if found, None otherwise.
        """
        ...

    @abstractmethod
    def get_business_description(self, identifier: str) -> BusinessDescription | None:
        """
        Extract the business description from the latest annual filing.

        For SEC filings, this is Item 1 of the 10-K. For ESEF filings,
        the equivalent business overview section.

        Args:
            identifier: Entity identifier.

        Returns:
            BusinessDescription if extraction succeeds, None otherwise.
        """
        ...

    @abstractmethod
    def get_revenue(self, identifier: str) -> RevenueData | None:
        """
        Get the most recent annual revenue for an entity.

        Extracts from XBRL tags (us-gaap:Revenues or equivalent).

        Args:
            identifier: Entity identifier.

        Returns:
            RevenueData if found, None otherwise.
        """
        ...

    @abstractmethod
    def list_filings(self, identifier: str, filing_type: str | None = None, limit: int = 10) -> list[Filing]:
        """
        List available filings for an entity.

        Args:
            identifier: Entity identifier.
            filing_type: Optional filter by filing type.
            limit: Maximum number of filings to return.

        Returns:
            List of Filing objects, most recent first.
        """
        ...

    def supports_identifier(self, identifier: str) -> bool:
        """
        Check if this data source can handle the given identifier.

        Override in subclasses to implement identifier validation.
        Default returns True.
        """
        return True
