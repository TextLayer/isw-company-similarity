from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from isw.core.services.entities.identifiers import EntityIdentifier
from isw.core.services.entities.models import Filing


@dataclass
class CompanyFacts:
    """SEC EDGAR company facts containing XBRL financial data."""

    cik: str
    company_name: str
    facts: dict[str, Any]


@dataclass
class TenKContent:
    """Parsed content from an SEC 10-K filing."""

    accession_number: str
    business_section: str | None


@dataclass
class XBRLContent:
    """XBRL-JSON content from an ESEF filing."""

    facts: dict[str, Any]
    period_end: str


class StorageAdapter(ABC):
    """
    Abstract base for filing storage adapters.

    Implementations provide access to filing metadata and content for
    a specific jurisdiction (SEC EDGAR for US, filings.xbrl.org for ESEF).
    """

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def get_filing(self, identifier: EntityIdentifier, filing_type: str) -> Filing | None: ...

    @abstractmethod
    def get_latest_annual_filing(self, identifier: EntityIdentifier) -> Filing | None: ...

    @abstractmethod
    def list_filings(
        self,
        identifier: EntityIdentifier,
        filing_type: str | None = None,
        limit: int = 10,
    ) -> list[Filing]: ...
