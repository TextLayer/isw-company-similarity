import re

import httpx
from bs4 import BeautifulSoup

from isw.core.services.entities.errors import RateLimitError, StorageError
from isw.core.services.entities.identifiers import LEI, EntityIdentifier
from isw.core.services.entities.models import Filing
from isw.core.services.entities.storage.base import StorageAdapter, XBRLContent
from isw.core.utils.text import strip_html


class ESEFAdapter(StorageAdapter):
    """
    ESEF storage adapter using the filings.xbrl.org API.

    Provides access to European Single Electronic Format filings,
    including XBRL-JSON data and HTML reports.
    """

    BASE_URL = "https://filings.xbrl.org"
    FILINGS_URL = f"{BASE_URL}/api/filings"

    BUSINESS_DESCRIPTION_TAGS = [
        "ifrs-full:DisclosureOfGeneralInformationAboutFinancialStatementsExplanatory",
        "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities",
        "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory",
    ]

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    @property
    def source_name(self) -> str:
        return "filings.xbrl.org"

    def get_filing(self, identifier: EntityIdentifier, filing_type: str) -> Filing | None:
        filings = self.list_filings(identifier, filing_type=filing_type, limit=1)
        return filings[0] if filings else None

    def get_latest_annual_filing(self, identifier: EntityIdentifier) -> Filing | None:
        filings = self.list_filings(identifier, limit=10)

        for filing in filings:
            if self._is_annual_filing(filing):
                return filing

        return filings[0] if filings else None

    def list_filings(
        self,
        identifier: EntityIdentifier,
        filing_type: str | None = None,
        limit: int = 10,
    ) -> list[Filing]:
        if not isinstance(identifier, LEI):
            return []

        try:
            with httpx.Client(timeout=self.timeout) as client:
                params = {
                    "filter[entity.identifier]": identifier.value,
                    "page[size]": limit,
                    "sort": "-period_end",
                }
                response = client.get(self.FILINGS_URL, params=params)
                response.raise_for_status()
                data = response.json()

                filings = []
                for item in data.get("data", []):
                    filing = self._parse_filing(item, identifier.value)
                    if filing and (filing_type is None or filing.filing_type == filing_type):
                        filings.append(filing)

                return filings[:limit]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limited by filings.xbrl.org") from e
            raise StorageError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise StorageError(f"Request failed: {e}") from e

    def get_xbrl_json(self, filing: Filing) -> XBRLContent | None:
        """Fetch XBRL-JSON data for a filing (used for revenue/description extraction)."""
        if not filing.raw_data:
            return None

        json_url = filing.raw_data.get("json_url")
        if not json_url:
            return None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                full_url = f"{self.BASE_URL}{json_url}"
                response = client.get(full_url)
                response.raise_for_status()
                data = response.json()

                return XBRLContent(
                    facts=data.get("facts", {}),
                    period_end=filing.period_end,
                )
        except httpx.HTTPError:
            return None

    def get_html_report(self, filing: Filing) -> str | None:
        """Fetch the HTML report for a filing."""
        if not filing.document_url:
            return None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                full_url = f"{self.BASE_URL}{filing.document_url}"
                response = client.get(full_url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError:
            return None

    def get_raw_business_content(self, identifier: EntityIdentifier) -> dict[str, str] | None:
        """Get raw business description content for LLM processing."""
        filing = self.get_latest_annual_filing(identifier)
        if not filing:
            return None

        xbrl = self.get_xbrl_json(filing)
        if not xbrl:
            return None

        content = {}
        for tag in self.BUSINESS_DESCRIPTION_TAGS:
            text = self._extract_fact_by_concept(xbrl.facts, tag)
            if text and len(text) > 20:
                field_name = self._tag_to_field_name(tag)
                content[field_name] = text

        # Fall back to HTML parsing if no XBRL tags found
        if not content:
            html_content = self._extract_from_html_report(filing)
            if html_content:
                content["html_report_extract"] = html_content

        return content if content else None

    def _parse_filing(self, item: dict, identifier: str) -> Filing | None:
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

    def _is_annual_filing(self, filing: Filing) -> bool:
        """
        Heuristic to detect annual vs half-year filings.

        December 28-31 is treated as fiscal year end. June 30 is commonly
        used for half-year reports in UK/EU.
        """
        if not filing.period_end:
            return False

        try:
            parts = filing.period_end.split("-")
            if len(parts) != 3:
                return True

            month = int(parts[1])
            day = int(parts[2])

            if month == 12 and day >= 28:
                return True
            if month == 6 and day == 30:
                return False

            return True
        except (ValueError, IndexError):
            return True

    def _extract_fact_by_concept(self, facts: dict, concept: str) -> str | None:
        for fact in facts.values():
            dimensions = fact.get("dimensions", {})
            if dimensions.get("concept") == concept:
                value = fact.get("value")
                if value:
                    return strip_html(value)
        return None

    def _tag_to_field_name(self, tag: str) -> str:
        tag_mapping = {
            "ifrs-full:DisclosureOfGeneralInformationAboutFinancialStatementsExplanatory": "general_information",
            "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities": "nature_of_operations",
            "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory": "reportable_segments",
        }
        return tag_mapping.get(tag, tag.split(":")[-1])

    def _extract_from_html_report(self, filing: Filing) -> str | None:
        html_content = self.get_html_report(filing)
        if not html_content:
            return None

        return self._parse_html_report_for_business_info(html_content)

    def _parse_html_report_for_business_info(self, html_content: str) -> str | None:
        """
        Extract business description from HTML report when XBRL tags are missing.

        Looks for iXBRL tags with relevant concepts, then falls back to
        section headers like "Business Description" or "Principal Activities".
        """
        soup = BeautifulSoup(html_content, "lxml")

        for element in soup(["script", "style"]):
            element.decompose()

        extracted_sections = []

        # Try iXBRL tags first
        ix_tags = soup.find_all(["ix:nonnumeric"])
        for tag in ix_tags:
            tag_name = tag.get("name", "").lower()
            if any(
                keyword in tag_name
                for keyword in ["description", "nature", "principal", "activity", "business", "operation"]
            ):
                text = tag.get_text(separator=" ").strip()
                if len(text) > 50:
                    extracted_sections.append(text)

        # Fall back to header-based extraction
        section_keywords = [
            "business description",
            "company description",
            "principal activities",
            "nature of business",
            "about the company",
            "company overview",
            "our business",
            "what we do",
        ]

        for header in soup.find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
            header_text = header.get_text(separator=" ").strip().lower()
            if any(keyword in header_text for keyword in section_keywords):
                content_parts = []
                for sibling in header.find_next_siblings()[:5]:
                    sibling_text = sibling.get_text(separator=" ").strip()
                    if len(sibling_text) > 30:
                        content_parts.append(sibling_text)
                    if len(content_parts) >= 3:
                        break
                if content_parts:
                    extracted_sections.append(" ".join(content_parts))

        if not extracted_sections:
            return None

        combined = "\n\n".join(extracted_sections[:5])
        combined = re.sub(r"\s+", " ", combined).strip()

        return combined if len(combined) > 100 else None
