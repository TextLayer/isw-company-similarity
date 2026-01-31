import pandas as pd
from edgar import Company, set_identity

from isw.core.services.entities.errors import RateLimitError, StorageError
from isw.core.services.entities.identifiers import CIK, EntityIdentifier
from isw.core.services.entities.models import Filing
from isw.core.services.entities.storage.base import (
    CompanyFacts,
    StorageAdapter,
    TenKContent,
)
from isw.shared.logging.logger import logger


class EdgarAdapter(StorageAdapter):
    """
    SEC EDGAR storage adapter using the edgartools library.

    Provides access to SEC filings, company facts (XBRL data), and
    parsed 10-K content for US public companies.
    """

    def __init__(self, user_agent: str, timeout: float = 30.0):
        self.user_agent = user_agent
        self.timeout = timeout
        set_identity(user_agent)

    @property
    def source_name(self) -> str:
        return "SEC EDGAR"

    def _get_company(self, identifier: EntityIdentifier) -> Company | None:
        if not isinstance(identifier, CIK):
            return None

        try:
            company = Company(identifier.value)
            # EdgarTools returns placeholder for invalid CIKs
            if company.name.startswith("Entity "):
                logger.debug("Invalid CIK (placeholder entity): %s", identifier.value)
                return None
            return company
        except Exception as e:
            logger.debug("Failed to get company for CIK %s: %s", identifier.value, e)
            return None

    def get_filing(self, identifier: EntityIdentifier, filing_type: str) -> Filing | None:
        filings = self.list_filings(identifier, filing_type=filing_type, limit=1)
        return filings[0] if filings else None

    def get_latest_annual_filing(self, identifier: EntityIdentifier) -> Filing | None:
        return self.get_filing(identifier, "10-K")

    def list_filings(
        self,
        identifier: EntityIdentifier,
        filing_type: str | None = None,
        limit: int = 10,
    ) -> list[Filing]:
        company = self._get_company(identifier)
        if not company:
            return []

        try:
            if filing_type:
                edgar_filings = company.get_filings(form=filing_type)
            else:
                edgar_filings = company.get_filings()

            if not edgar_filings:
                return []

            filings = []
            for i, ef in enumerate(edgar_filings):
                if i >= limit:
                    break

                document_url = None
                if hasattr(ef, "document") and ef.document:
                    if hasattr(ef.document, "url"):
                        document_url = ef.document.url

                filing = Filing(
                    identifier=identifier.value,
                    filing_type=ef.form,
                    period_end=str(ef.period_of_report) if ef.period_of_report else "",
                    filed_at=str(ef.filing_date) if ef.filing_date else None,
                    accession_number=ef.accession_number,
                    document_url=document_url,
                    raw_data={
                        "cik": company.cik,
                        "company_name": company.name,
                    },
                )
                filings.append(filing)

            return filings

        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                raise RateLimitError("Rate limited by SEC EDGAR") from e
            raise StorageError(f"Failed to list filings: {e}") from e

    def get_company_facts(self, identifier: EntityIdentifier) -> CompanyFacts | None:
        """Get structured XBRL facts for a company (used for revenue extraction)."""
        company = self._get_company(identifier)
        if not company:
            return None

        try:
            facts = company.get_facts()
            if not facts:
                return None

            return CompanyFacts(
                cik=company.cik,
                company_name=company.name,
                facts={"dataframe": facts.to_dataframe()},
            )
        except Exception as e:
            logger.warning("Failed to get company facts for %s: %s", identifier.value, e)
            return None

    def get_company_facts_df(self, identifier: EntityIdentifier) -> pd.DataFrame | None:
        """Get company facts as a pandas DataFrame for easier querying."""
        facts = self.get_company_facts(identifier)
        if not facts:
            return None
        return facts.facts.get("dataframe")

    def get_10k_content(self, identifier: EntityIdentifier) -> TenKContent | None:
        """Get parsed 10-K content including the business section."""
        company = self._get_company(identifier)
        if not company:
            return None

        try:
            filings = company.get_filings(form="10-K")
            if not filings or len(filings) == 0:
                return None

            latest = filings.latest()
            if not latest:
                return None

            tenk = latest.obj()
            if not tenk or not hasattr(tenk, "business"):
                return None

            business_text = tenk.business
            if not business_text or len(str(business_text)) < 100:
                return None

            return TenKContent(
                accession_number=latest.accession_number,
                business_section=str(business_text),
            )

        except Exception as e:
            logger.warning("Failed to get 10-K content for %s: %s", identifier.value, e)
            return None

    def get_raw_business_content(self, identifier: EntityIdentifier) -> dict[str, str] | None:
        """Get raw business section content for LLM processing."""
        content = self.get_10k_content(identifier)
        if not content or not content.business_section:
            return None

        return {"item_1_business": content.business_section}
