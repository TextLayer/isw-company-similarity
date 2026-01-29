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
    period_end: str  # Fiscal period end date (YYYY-MM-DD)
    filed_at: str | None = None  # When the filing was submitted (SEC has this, ESEF may not)
    accession_number: str | None = None  # SEC-specific identifier
    document_url: str | None = None
    raw_data: dict[str, Any] | None = None


@dataclass
class BusinessDescription:
    """Raw business description text extracted from a filing.

    This is the unprocessed text from the filing (e.g., Item 1 from SEC 10-K).
    LLM summarization/processing happens separately in the LLM Extraction Service.

    Note: Not all filings have a business description section.
    - SEC 10-K: Has "Item 1. Business" (required)
    - SEC 10-Q: Does NOT have Item 1
    - ESEF: May have equivalent section, varies by jurisdiction
    """

    text: str
    source_filing_type: str  # e.g., "10-K", "AFR"
    source_accession: str | None  # SEC accession number if applicable
    extraction_method: str  # e.g., "html_parse", "xbrl_extract"


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
        Extract raw business description text from the latest annual filing.

        Returns the unprocessed text from the filing. For SEC 10-K filings,
        this is "Item 1. Business". For ESEF, the equivalent section if available.

        This is RAW text extraction only. LLM summarization/processing
        happens separately in the LLM Extraction Service.

        Args:
            identifier: Entity identifier.

        Returns:
            BusinessDescription with raw text if available, None if:
            - No annual filing exists
            - Filing type doesn't have a business description section
            - Extraction fails
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
