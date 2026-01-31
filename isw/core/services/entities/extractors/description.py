from typing import Literal

from isw.core.services.entities.errors import DescriptionExtractionError
from isw.core.services.entities.extractors.prompts import (
    FILING_SYSTEM_PROMPT,
    FILING_USER_TEMPLATE,
    WEB_CONTENT_SYSTEM_PROMPT,
    WEB_CONTENT_USER_TEMPLATE,
)
from isw.core.services.entities.models import BusinessDescription, ExtractedBusinessDescription
from isw.core.services.llm import LLMService, LLMServiceError
from isw.core.services.web_search import WebSearchService
from isw.shared.logging.logger import logger


class DescriptionExtractor:
    """
    Extracts standardized business descriptions from filings and web search.

    All descriptions are processed through an LLM to ensure consistent format
    and structure, regardless of source (SEC 10-K, ESEF XBRL, or web search).
    Web search is used as a fallback when filing content is unavailable or
    insufficient.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
        web_search: WebSearchService | None = None,
        llm_model: str = "gpt-4o-mini",
        web_search_backend: Literal["perplexity", "firecrawl"] = "perplexity",
        timeout: float = 30.0,
    ):
        self.llm_service = llm_service or LLMService(model=llm_model)
        self._web_search = web_search or WebSearchService(
            primary=web_search_backend,
            timeout=timeout,
        )

    @property
    def web_search_available(self) -> bool:
        return self._web_search.is_available

    def from_filing_content(
        self,
        raw_content: dict[str, str],
        company_name: str | None = None,
        filing_type: str = "10-K",
    ) -> BusinessDescription | None:
        """Extract from raw filing content (10-K business section, XBRL fields, etc.)."""
        if not raw_content:
            raise DescriptionExtractionError("No raw content provided")

        messages = self._build_filing_messages(raw_content, company_name)

        try:
            result = self.llm_service.structured_output(
                messages=messages,
                output_structure=ExtractedBusinessDescription,
            )
            text = result.format()

            if not text or len(text.strip()) < 50:
                return None

            return BusinessDescription(
                text=text,
                source_filing_type=filing_type,
                source_accession=None,
                extraction_method="llm_extract",
            )
        except LLMServiceError as e:
            logger.error("LLM extraction failed: %s", e)
            raise DescriptionExtractionError(f"Failed to extract description: {e}") from e

    def from_web_search(
        self,
        company_name: str,
        country: str | None = None,
        identifier: str | None = None,
    ) -> BusinessDescription | None:
        """Extract via web search when filing content is unavailable."""
        if not self.web_search_available:
            logger.warning("Web search not available (no API key configured)")
            return None

        try:
            query = self._build_search_query(company_name, country, identifier)
            result = self._web_search.search(query)

            if not result:
                return None

            # Always process web content through LLM for consistent formatting
            text = self._process_web_content(company_name, result.content)

            if not text:
                return None

            return BusinessDescription(
                text=text,
                source_filing_type="WEB",
                source_accession=None,
                extraction_method=f"web_search_{result.source}",
            )
        except Exception as e:
            logger.error("Web search extraction failed: %s", e)
            raise DescriptionExtractionError(f"Web search failed: {e}") from e

    def _build_search_query(
        self,
        company_name: str,
        country: str | None,
        identifier: str | None,
    ) -> str:
        """Build the search query string from company information."""
        parts = [company_name]
        if country:
            parts.append(f"({country})")
        if identifier:
            parts.append(identifier)
        return " ".join(parts)

    def _build_filing_messages(
        self,
        raw_content: dict[str, str],
        company_name: str | None,
    ) -> list[dict]:
        company_context = f"Company: {company_name}\n\n" if company_name else ""

        content_sections = []
        for field_name, text in raw_content.items():
            truncated_text = text[:8000] if len(text) > 8000 else text
            content_sections.append(f"### {field_name.replace('_', ' ').title()}\n\n{truncated_text}")

        raw_text = "\n\n".join(content_sections)
        user_prompt = FILING_USER_TEMPLATE.format(
            company_context=company_context,
            raw_text=raw_text,
        )

        return [
            {"role": "system", "content": FILING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _process_web_content(self, company_name: str, content: str) -> str | None:
        """Process web search content through LLM for consistent extraction."""
        user_prompt = WEB_CONTENT_USER_TEMPLATE.format(
            company_name=company_name,
            content=content,
        )

        messages = [
            {"role": "system", "content": WEB_CONTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            result = self.llm_service.structured_output(
                messages=messages,
                output_structure=ExtractedBusinessDescription,
            )
            return result.format()
        except LLMServiceError as e:
            logger.warning("LLM processing of web content failed: %s", e)
            return None
