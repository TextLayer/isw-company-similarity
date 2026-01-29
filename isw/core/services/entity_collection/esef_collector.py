"""filings.xbrl.org collector for EU/UK public companies."""

import httpx

from isw.shared.logging.logger import logger

from .base import (
    DownloadError,
    EntityCollector,
    EntityRecord,
    IdentifierType,
    Jurisdiction,
)

# filings.xbrl.org API endpoint
FILINGS_XBRL_API_URL = "https://filings.xbrl.org/api/filings"

# Default page size for API requests
DEFAULT_PAGE_SIZE = 100

# Maximum pages to fetch (safety limit)
MAX_PAGES = 1000


class ESEFCollector(EntityCollector):
    """
    Collector for EU/UK ESEF filings from filings.xbrl.org.

    Queries the filings.xbrl.org API to retrieve all ESEF filers,
    extracting their LEI (Legal Entity Identifier) and jurisdiction.

    ESEF (European Single Electronic Format) is mandatory for EU-listed
    companies' annual reports.
    """

    def __init__(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
        timeout: float = 60.0,
        max_pages: int = MAX_PAGES,
    ):
        """
        Initialize the ESEF collector.

        Args:
            page_size: Number of results per API page.
            timeout: HTTP request timeout in seconds.
            max_pages: Maximum number of pages to fetch (safety limit).
        """
        self.page_size = page_size
        self.timeout = timeout
        self.max_pages = max_pages

    def get_source_name(self) -> str:
        """Return the name of this data source."""
        return "filings.xbrl.org"

    def fetch_entities(self) -> list[EntityRecord]:
        """
        Fetch all EU/UK public companies from filings.xbrl.org.

        Queries the API with pagination to retrieve all ESEF filers,
        extracts unique entities by LEI, and assigns jurisdiction
        based on country code.

        Returns:
            List of EntityRecord objects for EU/UK companies.

        Raises:
            DownloadError: If API requests fail.
            ParseError: If parsing the response fails.
        """
        logger.info(f"Fetching entities from {self.get_source_name()}")

        # Collect all filings with pagination
        all_filings = self._fetch_all_filings()

        # Extract unique entities by LEI
        entities = self._extract_unique_entities(all_filings)

        logger.info(f"Collected {len(entities)} unique entities from {self.get_source_name()}")
        return entities

    def _fetch_all_filings(self) -> list[dict]:
        """
        Fetch all filings from the API with pagination.

        Returns:
            List of filing records from the API.

        Raises:
            DownloadError: If API requests fail.
        """
        all_filings = []
        offset = 0
        page = 0

        with httpx.Client(timeout=self.timeout) as client:
            while page < self.max_pages:
                page += 1
                logger.debug(f"Fetching page {page} (offset={offset})")

                try:
                    filings = self._fetch_page(client, offset)
                except Exception as e:
                    logger.error(f"Failed to fetch page {page}: {e}")
                    raise

                if not filings:
                    # No more results
                    logger.info(f"Completed fetching after {page} pages")
                    break

                all_filings.extend(filings)
                offset += len(filings)

                # If we got fewer results than page_size, we're done
                if len(filings) < self.page_size:
                    break

        logger.info(f"Fetched {len(all_filings)} total filings")
        return all_filings

    def _fetch_page(self, client: httpx.Client, offset: int) -> list[dict]:
        """
        Fetch a single page of filings from the API.

        Args:
            client: HTTP client instance.
            offset: Pagination offset.

        Returns:
            List of filing records.

        Raises:
            DownloadError: If the request fails.
        """
        params = {
            "limit": self.page_size,
            "offset": offset,
            # Filter for ESEF filings (annual reports)
            "report_type": "AFR",  # Annual Financial Report
        }

        try:
            response = client.get(FILINGS_XBRL_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # API returns {"data": [...], "meta": {...}}
            if isinstance(data, dict):
                return data.get("data", [])
            elif isinstance(data, list):
                return data
            else:
                return []

        except httpx.HTTPStatusError as e:
            raise DownloadError(f"API returned HTTP {e.response.status_code}: {e}") from e
        except httpx.RequestError as e:
            raise DownloadError(f"Failed to fetch from filings.xbrl.org: {e}") from e

    def _extract_unique_entities(self, filings: list[dict]) -> list[EntityRecord]:
        """
        Extract unique entities from filings by LEI.

        Args:
            filings: List of filing records from the API.

        Returns:
            List of unique EntityRecord objects.
        """
        seen_leis: set[str] = set()
        entities: list[EntityRecord] = []

        for filing in filings:
            try:
                entity = self._parse_filing(filing)
                if entity and entity.identifier not in seen_leis:
                    seen_leis.add(entity.identifier)
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse filing: {e}")
                continue

        return entities

    def _parse_filing(self, filing: dict) -> EntityRecord | None:
        """
        Parse a filing record into an EntityRecord.

        Args:
            filing: Filing record from the API.

        Returns:
            EntityRecord if valid, None otherwise.
        """
        # Extract LEI (Legal Entity Identifier)
        lei = filing.get("lei") or filing.get("entity_lei")
        if not lei or not self._is_valid_lei(lei):
            return None

        # Extract entity name
        name = filing.get("entity_name") or filing.get("name", "").strip()
        if not name:
            return None

        # Determine jurisdiction from country code
        country = filing.get("country") or filing.get("entity_country", "")
        jurisdiction = self._get_jurisdiction(country)

        return EntityRecord(
            name=name,
            identifier=lei,
            jurisdiction=jurisdiction,
            identifier_type=IdentifierType.LEI,
        )

    def _is_valid_lei(self, lei: str) -> bool:
        """
        Validate LEI format (20 alphanumeric characters).

        Args:
            lei: LEI string to validate.

        Returns:
            True if valid LEI format.
        """
        if not lei or len(lei) != 20:
            return False
        return lei.isalnum()

    def _get_jurisdiction(self, country_code: str) -> Jurisdiction:
        """
        Map country code to jurisdiction.

        Args:
            country_code: ISO country code (e.g., "GB", "DE", "FR").

        Returns:
            Jurisdiction enum value.
        """
        # UK has its own jurisdiction
        if country_code.upper() in ("GB", "UK"):
            return Jurisdiction.UK

        # All other countries are EU
        return Jurisdiction.EU
