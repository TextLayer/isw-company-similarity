import logging

from isw.core.services.data_sources.base import (
    BaseDataSource,
    BusinessDescription,
    DataSourceError,
    Filing,
    RevenueData,
)
from isw.core.services.data_sources.edgar_data_source import SECEdgarDataSource
from isw.core.services.data_sources.esef_data_source import FilingsXBRLDataSource

logger = logging.getLogger(__name__)


class DataSourceFactory:
    """Factory for creating and routing to appropriate data sources.

    Routes requests to the correct data source based on identifier format:
    - CIK (numeric, up to 10 digits) → SEC EDGAR
    - LEI (20 alphanumeric characters) → filings.xbrl.org (ESEF)
    """

    def __init__(self, sec_user_agent: str, timeout: float = 30.0):
        """Initialize the factory with configuration for data sources.

        Args:
            sec_user_agent: User-Agent header for SEC requests.
            timeout: HTTP request timeout in seconds.
        """
        self._sec_source = SECEdgarDataSource(user_agent=sec_user_agent, timeout=timeout)
        self._esef_source = FilingsXBRLDataSource(timeout=timeout)
        self._sources: list[BaseDataSource] = [self._sec_source, self._esef_source]

    @property
    def sources(self) -> list[BaseDataSource]:
        """Get all registered data sources."""
        return self._sources

    def get_source_for_identifier(self, identifier: str) -> BaseDataSource | None:
        """Get the appropriate data source for an identifier.

        Args:
            identifier: Entity identifier (CIK or LEI).

        Returns:
            The data source that supports this identifier, or None if no match.
        """
        for source in self._sources:
            if source.supports_identifier(identifier):
                return source
        return None

    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        """Get a filing using the appropriate data source.

        Args:
            identifier: Entity identifier (CIK or LEI).
            filing_type: Type of filing (e.g., "10-K", "AFR").

        Returns:
            Filing if found, None otherwise.

        Raises:
            DataSourceError: If no data source supports the identifier.
        """
        source = self.get_source_for_identifier(identifier)
        if not source:
            raise DataSourceError(f"No data source supports identifier: {identifier}")
        return source.get_filing(identifier, filing_type)

    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        """Get the latest annual filing using the appropriate data source.

        Args:
            identifier: Entity identifier (CIK or LEI).

        Returns:
            Filing if found, None otherwise.

        Raises:
            DataSourceError: If no data source supports the identifier.
        """
        source = self.get_source_for_identifier(identifier)
        if not source:
            raise DataSourceError(f"No data source supports identifier: {identifier}")
        return source.get_latest_annual_filing(identifier)

    def get_business_description(self, identifier: str) -> BusinessDescription | None:
        """Get business description using the appropriate data source.

        Args:
            identifier: Entity identifier (CIK or LEI).

        Returns:
            BusinessDescription if found, None otherwise.

        Raises:
            DataSourceError: If no data source supports the identifier.
        """
        source = self.get_source_for_identifier(identifier)
        if not source:
            raise DataSourceError(f"No data source supports identifier: {identifier}")
        return source.get_business_description(identifier)

    def get_revenue(self, identifier: str) -> RevenueData | None:
        """Get revenue data using the appropriate data source.

        Args:
            identifier: Entity identifier (CIK or LEI).

        Returns:
            RevenueData if found, None otherwise.

        Raises:
            DataSourceError: If no data source supports the identifier.
        """
        source = self.get_source_for_identifier(identifier)
        if not source:
            raise DataSourceError(f"No data source supports identifier: {identifier}")
        return source.get_revenue(identifier)

    def list_filings(self, identifier: str, filing_type: str | None = None, limit: int = 10) -> list[Filing]:
        """List filings using the appropriate data source.

        Args:
            identifier: Entity identifier (CIK or LEI).
            filing_type: Optional filter by filing type.
            limit: Maximum number of filings to return.

        Returns:
            List of Filing objects.

        Raises:
            DataSourceError: If no data source supports the identifier.
        """
        source = self.get_source_for_identifier(identifier)
        if not source:
            raise DataSourceError(f"No data source supports identifier: {identifier}")
        return source.list_filings(identifier, filing_type, limit)
