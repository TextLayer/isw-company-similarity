import logging

import httpx

from isw.core.services.data_sources.base import (
    BaseDataSource,
    BusinessDescription,
    DataSourceError,
    Filing,
    RateLimitError,
    RevenueData,
)
from isw.core.services.data_sources.parsers import parse_10k_business_section

logger = logging.getLogger(__name__)


class SECEdgarDataSource(BaseDataSource):
    """Data source for SEC EDGAR filings."""

    BASE_URL = "https://www.sec.gov"
    ARCHIVES_URL = f"{BASE_URL}/Archives/edgar/data"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions"
    COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts"

    # Revenue tags to search for in company facts (in order of preference)
    # RevenueFromContractWithCustomerExcludingAssessedTax is the modern tag (ASC 606)
    REVENUE_TAGS = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "TotalRevenuesAndOtherIncome",
    ]

    def __init__(self, user_agent: str, timeout: float = 30.0):
        """
        Initialize the SEC EDGAR data source.

        Args:
            user_agent: User-Agent header for SEC requests (required by SEC).
                        Should be in format "Company Name AdminEmail@company.com"
            timeout: HTTP request timeout in seconds.
        """
        self.user_agent = user_agent
        self.timeout = timeout

    @property
    def source_name(self) -> str:
        return "SEC EDGAR"

    def supports_identifier(self, identifier: str) -> bool:
        """Check if identifier is a valid CIK (numeric, up to 10 digits)."""
        if not identifier:
            return False
        # Remove leading zeros for validation
        stripped = identifier.lstrip("0")
        return stripped.isdigit() and len(stripped) <= 10

    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        """Retrieve a specific filing by CIK and type."""
        filings = self.list_filings(identifier, filing_type=filing_type, limit=1)
        return filings[0] if filings else None

    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        """Get the most recent 10-K filing for an entity."""
        return self.get_filing(identifier, "10-K")

    def get_business_description(self, identifier: str) -> BusinessDescription | None:
        """
        Extract business description from the latest 10-K filing.

        Parses the HTML of the 10-K filing and extracts the text from
        "Item 1. Business" up to "Item 1A. Risk Factors".
        """
        filing = self.get_latest_annual_filing(identifier)
        if not filing or not filing.document_url:
            return None

        html_content = self._fetch_filing_html(filing.document_url)
        if not html_content:
            return None

        text = parse_10k_business_section(html_content)
        if not text:
            return None

        return BusinessDescription(
            text=text,
            source_filing_type="10-K",
            source_accession=filing.accession_number,
            extraction_method="html_parse",
        )

    def get_revenue(self, identifier: str) -> RevenueData | None:
        """Get the most recent annual revenue from SEC company facts API."""
        cik = self._normalize_cik(identifier)
        facts_url = f"{self.COMPANY_FACTS_URL}/CIK{cik}.json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    facts_url,
                    headers={"User-Agent": self.user_agent},
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()

                return self._extract_revenue_from_facts(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limited by SEC EDGAR") from e
            raise DataSourceError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise DataSourceError(f"Request failed: {e}") from e

    def list_filings(self, identifier: str, filing_type: str | None = None, limit: int = 10) -> list[Filing]:
        """List available filings for an entity by CIK."""
        cik = self._normalize_cik(identifier)
        submissions_url = f"{self.SUBMISSIONS_URL}/CIK{cik}.json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    submissions_url,
                    headers={"User-Agent": self.user_agent},
                )
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()

                return self._parse_filings(data, cik, filing_type, limit)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limited by SEC EDGAR") from e
            raise DataSourceError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise DataSourceError(f"Request failed: {e}") from e

    def _normalize_cik(self, cik: str) -> str:
        """Normalize CIK to 10-digit zero-padded format."""
        return cik.zfill(10)

    def _parse_filings(self, data: dict, cik: str, filing_type: str | None, limit: int) -> list[Filing]:
        """Parse filings from SEC submissions API response."""
        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []

        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_documents = recent.get("primaryDocument", [])

        filings = []
        for i, form in enumerate(forms):
            if filing_type and form != filing_type:
                continue

            accession = accession_numbers[i] if i < len(accession_numbers) else None
            if not accession:
                continue

            # Build document URL
            # URL format: /Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_doc}
            accession_no_dashes = accession.replace("-", "")
            primary_doc = primary_documents[i] if i < len(primary_documents) else None
            document_url = None
            if primary_doc:
                # Use CIK without leading zeros for URL
                cik_for_url = cik.lstrip("0") or "0"
                document_url = f"{self.ARCHIVES_URL}/{cik_for_url}/{accession_no_dashes}/{primary_doc}"

            filing = Filing(
                identifier=cik,
                filing_type=form,
                period_end=report_dates[i] if i < len(report_dates) else "",
                filed_at=filing_dates[i] if i < len(filing_dates) else None,
                accession_number=accession,
                document_url=document_url,
                raw_data={
                    "cik": cik,
                    "primary_document": primary_doc,
                },
            )
            filings.append(filing)

            if len(filings) >= limit:
                break

        return filings

    def _fetch_filing_html(self, url: str) -> str | None:
        """Fetch the HTML content of a filing."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                )
                if response.status_code == 404:
                    logger.debug("Filing not found: %s", url)
                    return None
                response.raise_for_status()
                return response.text

        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error fetching filing %s: %s", url, e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("Request error fetching filing %s: %s", url, e)
            return None

    def _extract_revenue_from_facts(self, facts_data: dict) -> RevenueData | None:
        """Extract revenue data from SEC company facts API response."""
        us_gaap = facts_data.get("facts", {}).get("us-gaap", {})
        if not us_gaap:
            return None

        # Try each revenue tag in order of preference
        for tag in self.REVENUE_TAGS:
            if tag in us_gaap:
                revenue_data = us_gaap[tag]
                units = revenue_data.get("units", {})

                # Find USD values
                usd_values = units.get("USD", [])
                if not usd_values:
                    continue

                # Find most recent 10-K value (annual, not quarterly)
                annual_values = [v for v in usd_values if v.get("form") == "10-K" and v.get("val") is not None]

                if not annual_values:
                    continue

                # Sort by end date descending
                annual_values.sort(key=lambda x: x.get("end", ""), reverse=True)
                latest = annual_values[0]

                return RevenueData(
                    amount=int(latest["val"]),
                    currency="USD",
                    period_end=latest.get("end", ""),
                    source_tag=f"us-gaap:{tag}",
                )

        return None
