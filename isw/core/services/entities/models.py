from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from isw.core.utils.text import clean_text


class IdentifierType(str, Enum):
    CIK = "CIK"
    LEI = "LEI"


class Jurisdiction(str, Enum):
    US = "US"
    EU = "EU"
    UK = "UK"


@dataclass
class EntityRecord:
    name: str
    identifier: str
    jurisdiction: Jurisdiction
    identifier_type: IdentifierType

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "identifier": self.identifier,
            "jurisdiction": self.jurisdiction.value,
            "identifier_type": self.identifier_type.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntityRecord":
        return cls(
            name=data["name"],
            identifier=data["identifier"],
            jurisdiction=Jurisdiction(data["jurisdiction"]),
            identifier_type=IdentifierType(data["identifier_type"]),
        )


@dataclass
class Filing:
    identifier: str
    filing_type: str
    period_end: str
    filed_at: str | None = None
    accession_number: str | None = None
    document_url: str | None = None
    raw_data: dict[str, Any] | None = None


@dataclass
class BusinessDescription:
    text: str
    source_filing_type: str
    source_accession: str | None
    extraction_method: str


@dataclass
class RevenueData:
    amount: int
    currency: str
    period_end: str
    source_tag: str


class ExtractedBusinessDescription(BaseModel):
    company_overview: str = Field(
        description="2-3 sentence overview of what the company does, its industry, and core business"
    )
    products_and_services: str = Field(description="Description of main products and/or services offered")
    markets_and_segments: str | None = Field(
        default=None,
        description="Geographic markets served and/or business segments, if mentioned",
    )
    key_differentiators: str | None = Field(
        default=None,
        description="What makes this company unique or competitive advantages mentioned",
    )

    def format(self) -> str:
        sections = [clean_text(self.company_overview)]

        if self.products_and_services:
            sections.append(f"\n\nProducts and Services\n{clean_text(self.products_and_services)}")

        if self.markets_and_segments:
            sections.append(f"\n\nMarkets and Segments\n{clean_text(self.markets_and_segments)}")

        if self.key_differentiators:
            sections.append(f"\n\nCompetitive Position\n{clean_text(self.key_differentiators)}")

        return "".join(sections)
