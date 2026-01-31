from isw.core.services.entities.config import EntityServiceConfig
from isw.core.services.entities.errors import EntityError
from isw.core.services.entities.extractors import DescriptionExtractor, RevenueExtractor
from isw.core.services.entities.identifiers import CIK, LEI, parse_identifier
from isw.core.services.entities.models import (
    BusinessDescription,
    EntityRecord,
    Filing,
    RevenueData,
)
from isw.core.services.entities.registry import EdgarEntityRegistry, ESEFEntityRegistry
from isw.core.services.entities.storage import EdgarAdapter, ESEFAdapter
from isw.shared.logging.logger import logger


class EntityService:
    """
    Unified facade for entity discovery, filing retrieval, and data extraction.

    Automatically routes requests to the appropriate registry/adapter based on
    identifier type (CIK -> SEC EDGAR, LEI -> ESEF). All components are lazily
    initialized to avoid unnecessary setup costs.
    """

    def __init__(
        self,
        edgar_registry: EdgarEntityRegistry | None = None,
        esef_registry: ESEFEntityRegistry | None = None,
        edgar_adapter: EdgarAdapter | None = None,
        esef_adapter: ESEFAdapter | None = None,
        revenue_extractor: RevenueExtractor | None = None,
        description_extractor: DescriptionExtractor | None = None,
        config: EntityServiceConfig | None = None,
    ):
        self._config = config or EntityServiceConfig()
        self._edgar_registry = edgar_registry
        self._esef_registry = esef_registry
        self._edgar_adapter = edgar_adapter
        self._esef_adapter = esef_adapter
        self._revenue_extractor = revenue_extractor
        self._description_extractor = description_extractor

    def discover_edgar_entities(self, years_lookback: int = 3) -> list[EntityRecord]:
        """Fetch all entities with recent 10-K filings from SEC EDGAR."""
        registry = self._get_edgar_registry(years_lookback)
        return registry.fetch_entities()

    def discover_esef_entities(self, limit: int | None = None) -> list[EntityRecord]:
        """Fetch entities from the ESEF filing registry."""
        registry = self._get_esef_registry()
        return registry.fetch_entities(limit=limit)

    def get_filing(self, identifier: str, filing_type: str) -> Filing | None:
        parsed = self._parse_identifier(identifier)

        if isinstance(parsed, CIK):
            return self._get_edgar_adapter().get_filing(parsed, filing_type)
        else:
            return self._get_esef_adapter().get_filing(parsed, filing_type)

    def get_latest_annual_filing(self, identifier: str) -> Filing | None:
        parsed = self._parse_identifier(identifier)

        if isinstance(parsed, CIK):
            return self._get_edgar_adapter().get_latest_annual_filing(parsed)
        else:
            return self._get_esef_adapter().get_latest_annual_filing(parsed)

    def list_filings(
        self,
        identifier: str,
        filing_type: str | None = None,
        limit: int = 10,
    ) -> list[Filing]:
        parsed = self._parse_identifier(identifier)

        if isinstance(parsed, CIK):
            return self._get_edgar_adapter().list_filings(parsed, filing_type, limit)
        else:
            return self._get_esef_adapter().list_filings(parsed, filing_type, limit)

    def get_revenue(self, identifier: str) -> RevenueData | None:
        parsed = self._parse_identifier(identifier)
        extractor = self._get_revenue_extractor()

        if isinstance(parsed, CIK):
            facts_df = self._get_edgar_adapter().get_company_facts_df(parsed)
            if facts_df is None:
                return None
            return extractor.from_edgar_facts_df(facts_df)
        else:
            return self._extract_esef_revenue(parsed, extractor)

    def _extract_esef_revenue(self, identifier: LEI, extractor: RevenueExtractor) -> RevenueData | None:
        adapter = self._get_esef_adapter()
        filings = adapter.list_filings(identifier, limit=10)
        annual_filings = [f for f in filings if self._is_annual_filing(f)]

        if not annual_filings:
            return None

        # Track zero-revenue as fallback since some entities legitimately report zero
        zero_revenue_fallback = None

        for filing in annual_filings:
            xbrl = adapter.get_xbrl_json(filing)
            if not xbrl:
                continue

            revenue_data = extractor.from_xbrl_json(xbrl.facts, filing.period_end)
            if not revenue_data:
                continue

            if revenue_data.amount > 0:
                return revenue_data

            if zero_revenue_fallback is None:
                zero_revenue_fallback = revenue_data

        return zero_revenue_fallback

    def get_business_description(
        self,
        identifier: str,
        company_name: str | None = None,
        country: str | None = None,
    ) -> BusinessDescription | None:
        parsed = self._parse_identifier(identifier)

        if not self._config.use_ai_extraction:
            return self._get_native_description(parsed)

        return self._get_ai_generated_description(parsed, company_name, country)

    def _get_native_description(self, identifier: CIK | LEI) -> BusinessDescription | None:
        """Get description without LLM processing (raw filing content)."""
        if isinstance(identifier, CIK):
            content = self._get_edgar_adapter().get_10k_content(identifier)
            if not content or not content.business_section:
                return None

            return BusinessDescription(
                text=content.business_section,
                source_filing_type="10-K",
                source_accession=content.accession_number,
                extraction_method="edgartools_parse",
            )
        else:
            raw_content = self._get_esef_adapter().get_raw_business_content(identifier)
            if not raw_content:
                return None

            combined_text = "\n\n".join(raw_content.values())
            return BusinessDescription(
                text=combined_text,
                source_filing_type="AFR",
                source_accession=None,
                extraction_method="xbrl_extract",
            )

    def _get_ai_generated_description(
        self,
        identifier: CIK | LEI,
        company_name: str | None,
        country: str | None,
    ) -> BusinessDescription | None:
        extractor = self._get_description_extractor()
        filing_type = "10-K" if isinstance(identifier, CIK) else "AFR"

        if isinstance(identifier, CIK):
            raw_content = self._get_edgar_adapter().get_raw_business_content(identifier)
        else:
            raw_content = self._get_esef_adapter().get_raw_business_content(identifier)

        if not raw_content:
            logger.info("No filing content for %s, using web search", identifier.value)
            return self._try_web_search_fallback(extractor, identifier, company_name, country)

        try:
            result = extractor.from_filing_content(
                raw_content=raw_content,
                company_name=company_name,
                filing_type=filing_type,
            )

            if not result or len(result.text.strip()) < 50:
                logger.info(
                    "LLM extraction returned empty/minimal content for %s, trying web search",
                    identifier.value,
                )
                return self._try_web_search_fallback(extractor, identifier, company_name, country)

            return result

        except Exception as e:
            logger.warning("LLM extraction failed for %s: %s, trying web search", identifier.value, e)
            return self._try_web_search_fallback(extractor, identifier, company_name, country)

    def _try_web_search_fallback(
        self,
        extractor: DescriptionExtractor,
        identifier: CIK | LEI,
        company_name: str | None,
        country: str | None,
    ) -> BusinessDescription | None:
        if not self._config.use_web_search_fallback:
            logger.debug("Web search fallback disabled")
            return None

        if not extractor.web_search_available:
            logger.debug("Web search extractor not available (no API key)")
            return None

        if not company_name:
            logger.warning("Cannot use web search fallback without company name")
            return None

        try:
            logger.info("Using web search fallback for %s (%s)", company_name, identifier.value)
            default_country = "US" if isinstance(identifier, CIK) else None

            return extractor.from_web_search(
                company_name=company_name,
                country=country or default_country,
                identifier=identifier.value,
            )
        except Exception as e:
            logger.warning("Web search fallback failed for %s: %s", identifier.value, e)
            return None

    def _parse_identifier(self, identifier: str) -> CIK | LEI:
        try:
            result = parse_identifier(identifier)
            if isinstance(result, (CIK, LEI)):
                return result
            raise EntityError(f"Unsupported identifier type: {type(result)}")
        except ValueError as e:
            raise EntityError(f"Invalid identifier: {identifier}") from e

    def _is_annual_filing(self, filing: Filing) -> bool:
        """
        Heuristic to detect annual filings based on period end date.

        December 28-31 is treated as fiscal year end. June 30 is treated as
        half-year (common in UK/EU). Other dates default to annual since
        quarterly reports are less common in ESEF.
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

    def _get_edgar_registry(self, years_lookback: int = 3) -> EdgarEntityRegistry:
        if self._edgar_registry is None:
            self._edgar_registry = EdgarEntityRegistry(
                user_agent=self._config.sec_user_agent,
                years_lookback=years_lookback,
                timeout=self._config.timeout,
            )
        return self._edgar_registry

    def _get_esef_registry(self) -> ESEFEntityRegistry:
        if self._esef_registry is None:
            self._esef_registry = ESEFEntityRegistry(timeout=self._config.timeout)
        return self._esef_registry

    def _get_edgar_adapter(self) -> EdgarAdapter:
        if self._edgar_adapter is None:
            self._edgar_adapter = EdgarAdapter(
                user_agent=self._config.sec_user_agent,
                timeout=self._config.timeout,
            )
        return self._edgar_adapter

    def _get_esef_adapter(self) -> ESEFAdapter:
        if self._esef_adapter is None:
            self._esef_adapter = ESEFAdapter(timeout=self._config.timeout)
        return self._esef_adapter

    def _get_revenue_extractor(self) -> RevenueExtractor:
        if self._revenue_extractor is None:
            self._revenue_extractor = RevenueExtractor()
        return self._revenue_extractor

    def _get_description_extractor(self) -> DescriptionExtractor:
        if self._description_extractor is None:
            self._description_extractor = DescriptionExtractor(
                llm_model=self._config.llm_model,
                web_search_backend=self._config.web_search_backend,
                timeout=self._config.timeout,
            )
        return self._description_extractor
