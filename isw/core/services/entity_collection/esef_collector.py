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


class ESEFCollector(EntityCollector):
    """
    Collector for EU/UK ESEF filings from filings.xbrl.org.

    Queries the filings.xbrl.org JSON API to retrieve ESEF filers,
    extracting their LEI (Legal Entity Identifier) from the entity
    relationship and jurisdiction from the filing country.

    ESEF (European Single Electronic Format) is mandatory for EU-listed
    companies' annual reports.
    """

    API_URL = "https://filings.xbrl.org/api/filings"

    def __init__(
        self,
        page_size: int = 100,
        timeout: float = 60.0,
        max_pages: int = 1000,
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

        Queries the JSON API with pagination, includes entity data,
        extracts unique entities by LEI, and assigns jurisdiction
        based on filing country code.

        Returns:
            List of EntityRecord objects for EU/UK companies.

        Raises:
            DownloadError: If API requests fail.
        """
        logger.info(f"Fetching entities from {self.get_source_name()}")

        entities = self._fetch_all_entities()

        logger.info(f"Collected {len(entities)} unique entities from {self.get_source_name()}")
        return entities

    def _fetch_all_entities(self) -> list[EntityRecord]:
        """
        Fetch all entities from the API with pagination.

        The filings.xbrl.org JSON API uses page[number] pagination.
        Entity data is included via the include=entity parameter.

        Returns:
            List of unique EntityRecord objects.

        Raises:
            DownloadError: If API requests fail.
        """
        seen_leis: set[str] = set()
        entities: list[EntityRecord] = []
        page = 1

        with httpx.Client(timeout=self.timeout) as client:
            while page <= self.max_pages:
                logger.debug(f"Fetching page {page}")

                try:
                    page_entities, has_more = self._fetch_page(client, page)
                except Exception as e:
                    logger.error(f"Failed to fetch page {page}: {e}")
                    raise

                for entity in page_entities:
                    if entity.identifier not in seen_leis:
                        seen_leis.add(entity.identifier)
                        entities.append(entity)

                if not has_more:
                    logger.info(f"Completed fetching after {page} pages")
                    break

                page += 1

        logger.info(f"Fetched {len(entities)} unique entities")
        return entities

    def _fetch_page(self, client: httpx.Client, page_number: int) -> tuple[list[EntityRecord], bool]:
        """
        Fetch a single page of filings with entity data from the API.

        Args:
            client: HTTP client instance.
            page_number: Page number (1-indexed).

        Returns:
            Tuple of (entities from this page, whether more pages exist).

        Raises:
            DownloadError: If the request fails.
        """
        params = {
            "page[size]": self.page_size,
            "page[number]": page_number,
            "include": "entity",
        }

        try:
            response = client.get(self.API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            filings = data.get("data", [])
            included = data.get("included", [])

            entity_map = self._build_entity_map(included)
            entities = self._extract_entities_from_filings(filings, entity_map)

            has_more = len(filings) >= self.page_size
            return entities, has_more

        except httpx.HTTPStatusError as e:
            raise DownloadError(f"API returned HTTP {e.response.status_code}: {e}") from e
        except httpx.RequestError as e:
            raise DownloadError(f"Failed to fetch from filings.xbrl.org: {e}") from e

    def _build_entity_map(self, included: list[dict]) -> dict[str, dict]:
        """
        Build a map of entity ID to entity data from included resources.

        Args:
            included: List of included resources from JSON API response.

        Returns:
            Dict mapping entity ID to entity attributes.
        """
        entity_map = {}
        for item in included:
            if item.get("type") == "entity":
                entity_id = item.get("id")
                if entity_id:
                    entity_map[entity_id] = item.get("attributes", {})
        return entity_map

    def _extract_entities_from_filings(self, filings: list[dict], entity_map: dict[str, dict]) -> list[EntityRecord]:
        """
        Extract EntityRecords from filings using entity relationship.

        Args:
            filings: List of filing records from JSON API.
            entity_map: Map of entity ID to entity attributes.

        Returns:
            List of EntityRecord objects.
        """
        entities = []

        for filing in filings:
            try:
                entity = self._parse_filing_with_entity(filing, entity_map)
                if entity:
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse filing: {e}")
                continue

        return entities

    def _parse_filing_with_entity(self, filing: dict, entity_map: dict[str, dict]) -> EntityRecord | None:
        """
        Parse a filing and its related entity into an EntityRecord.

        Args:
            filing: Filing record from JSON API.
            entity_map: Map of entity ID to entity attributes.

        Returns:
            EntityRecord if valid, None otherwise.
        """
        filing_attrs = filing.get("attributes", {})
        country = filing_attrs.get("country", "")

        entity_rel = filing.get("relationships", {}).get("entity", {})
        entity_id = entity_rel.get("data", {}).get("id")

        if not entity_id or entity_id not in entity_map:
            return None

        entity_attrs = entity_map[entity_id]
        lei = entity_attrs.get("identifier", "")
        name = entity_attrs.get("name", "").strip()

        if not lei or not self._is_valid_lei(lei):
            return None

        if not name:
            return None

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
        if country_code.upper() in ("GB", "UK"):
            return Jurisdiction.UK

        return Jurisdiction.EU
