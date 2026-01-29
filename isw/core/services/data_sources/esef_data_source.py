"""ESEF data source for fetching EU/UK company filings from filings.xbrl.org."""

import httpx

from isw.core.services.data_sources.base import (
    BaseDataSource,
    BusinessDescription,
    DataSourceError,
    Filing,
    RateLimitError,
    RevenueData,
)

API_BASE_URL = "https://filings.xbrl.org"
API_FILINGS_URL = f"{API_BASE_URL}/api/filings"

# IFRS XBRL tags for extracting data
BUSINESS_DESCRIPTION_TAG = "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities"
REVENUE_TAG = "ifrs-full:Revenue"


class FilingsXBRLDataSource(BaseDataSource):
    """
    Data source for ESEF filings via filings.xbrl.org.

    Fetches EU/UK company filings and extracts business descriptions
    and financial data from XBRL-tagged annual reports.

    The business description is extracted from the IFRS tag:
    ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    @property
    def source_name(self) -> str:
        return "filings.xbrl.org"

    def supports_identifier(self, identifier: str) -> bool:
        """Check if identifier is a valid LEI (20 alphanumeric characters)."""
        return len(identifier) == 20 and identifier.isalnum()

    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        """Retrieve a specific filing by LEI and type."""
        filings = self.list_filings(identifier, filing_type=filing_type, limit=1)
        return filings[0] if filings else None

    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        """Get the most recent annual report for an entity."""
        filings = self.list_filings(identifier, limit=1)
        return filings[0] if filings else None

    def get_business_description(self, identifier: str) -> BusinessDescription | None:
        """
        Extract business description from the latest annual filing.

        Uses the IFRS XBRL tag:
        ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities
        """
        filing = self.get_latest_annual_filing(identifier)
        if not filing:
            return None

        xbrl_data = self._fetch_xbrl_json(filing)
        if not xbrl_data:
            return None

        text = self._extract_fact_by_concept(xbrl_data, BUSINESS_DESCRIPTION_TAG)
        if not text:
            return None

        return BusinessDescription(
            text=text,
            source_filing_type="AFR",
            source_accession=None,
            extraction_method="xbrl_extract",
        )

    def get_revenue(self, identifier: str) -> RevenueData | None:
        """Get the most recent annual revenue for an entity."""
        filing = self.get_latest_annual_filing(identifier)
        if not filing:
            return None

        xbrl_data = self._fetch_xbrl_json(filing)
        if not xbrl_data:
            return None

        facts = xbrl_data.get("facts", {})
        revenue_fact = self._find_most_recent_revenue_fact(facts)
        if not revenue_fact:
            return None

        return self._parse_revenue_fact(revenue_fact, filing.period_end)

    def list_filings(self, identifier: str, filing_type: str | None = None, limit: int = 10) -> list[Filing]:
        """List available filings for an entity by LEI."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                params = {
                    "filter[entity.identifier]": identifier,
                    "page[size]": limit,
                    "sort": "-period_end",
                }
                response = client.get(API_FILINGS_URL, params=params)
                response.raise_for_status()
                data = response.json()

                filings = []
                for item in data.get("data", []):
                    filing = self._parse_filing(item, identifier)
                    if filing and (filing_type is None or filing.filing_type == filing_type):
                        filings.append(filing)

                return filings[:limit]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limited by filings.xbrl.org") from e
            raise DataSourceError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise DataSourceError(f"Request failed: {e}") from e

    def _fetch_xbrl_json(self, filing: Filing) -> dict | None:
        """Fetch the XBRL-JSON file for a filing."""
        if not filing.raw_data:
            return None

        json_url = filing.raw_data.get("json_url")
        if not json_url:
            return None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                full_url = f"{API_BASE_URL}{json_url}"
                response = client.get(full_url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return None

    def _parse_filing(self, item: dict, identifier: str) -> Filing | None:
        """Parse a filing from the API response."""
        attrs = item.get("attributes", {})
        period_end = attrs.get("period_end")
        if not period_end:
            return None

        return Filing(
            identifier=identifier,
            filing_type="AFR",
            period_end=period_end,
            document_url=attrs.get("report_url"),
            raw_data={
                "json_url": attrs.get("json_url"),
                "viewer_url": attrs.get("viewer_url"),
                "country": attrs.get("country"),
            },
        )

    def _extract_fact_by_concept(self, xbrl_data: dict, concept: str) -> str | None:
        """Extract the value of a fact by its concept tag."""
        facts = xbrl_data.get("facts", {})
        for fact in facts.values():
            dimensions = fact.get("dimensions", {})
            if dimensions.get("concept") == concept:
                return fact.get("value")
        return None

    def _find_most_recent_revenue_fact(self, facts: dict) -> dict | None:
        """Find the most recent revenue fact from XBRL facts."""
        revenue_facts = []
        for fact in facts.values():
            dimensions = fact.get("dimensions", {})
            if dimensions.get("concept") == REVENUE_TAG:
                period = dimensions.get("period", "")
                if "/" in period:
                    revenue_facts.append((period, fact))

        if not revenue_facts:
            return None

        revenue_facts.sort(key=lambda x: x[0], reverse=True)
        return revenue_facts[0][1]

    def _parse_revenue_fact(self, fact: dict, period_end: str) -> RevenueData | None:
        """Parse a revenue fact into RevenueData."""
        value = fact.get("value")
        if not value:
            return None

        try:
            amount = int(float(value))
        except ValueError:
            return None

        dimensions = fact.get("dimensions", {})
        unit = dimensions.get("unit", "")
        currency = self._extract_currency_from_unit(unit)

        return RevenueData(
            amount=amount,
            currency=currency,
            period_end=period_end,
            source_tag=REVENUE_TAG,
        )

    def _extract_currency_from_unit(self, unit: str) -> str:
        """Extract currency code from XBRL unit (e.g., 'iso4217:GBP' -> 'GBP')."""
        if ":" in unit:
            return unit.split(":")[-1]
        return unit or "Unknown"
