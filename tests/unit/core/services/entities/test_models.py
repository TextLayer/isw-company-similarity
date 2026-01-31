"""Unit tests for entity models and data classes."""

from isw.core.services.entities import (
    BusinessDescription,
    EntityRecord,
    ExtractedBusinessDescription,
    Filing,
    IdentifierType,
    Jurisdiction,
    RevenueData,
)


class TestEntityRecord:
    """Tests for EntityRecord data class."""

    def test_to_dict(self):
        """EntityRecord should serialize to dictionary correctly."""
        record = EntityRecord(
            name="Apple Inc.",
            identifier="0000320193",
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )
        result = record.to_dict()

        assert result["name"] == "Apple Inc."
        assert result["identifier"] == "0000320193"
        assert result["jurisdiction"] == "US"
        assert result["identifier_type"] == "CIK"

    def test_from_dict(self):
        """EntityRecord should deserialize from dictionary correctly."""
        data = {
            "name": "Kainos Group plc",
            "identifier": "213800H2PQMIF3OVZY47",
            "jurisdiction": "UK",
            "identifier_type": "LEI",
        }
        record = EntityRecord.from_dict(data)

        assert record.name == "Kainos Group plc"
        assert record.identifier == "213800H2PQMIF3OVZY47"
        assert record.jurisdiction == Jurisdiction.UK
        assert record.identifier_type == IdentifierType.LEI

    def test_roundtrip(self):
        """to_dict and from_dict should be inverse operations."""
        original = EntityRecord(
            name="Test Company",
            identifier="1234567890",
            jurisdiction=Jurisdiction.EU,
            identifier_type=IdentifierType.LEI,
        )
        reconstructed = EntityRecord.from_dict(original.to_dict())

        assert original == reconstructed


class TestExtractedBusinessDescription:
    """Tests for ExtractedBusinessDescription Pydantic model."""

    def test_format_full(self):
        """format() should include all sections when present."""
        desc = ExtractedBusinessDescription(
            company_overview="Test company overview.",
            products_and_services="Test products.",
            markets_and_segments="Test markets.",
            key_differentiators="Test differentiators.",
        )
        result = desc.format()

        assert "Test company overview." in result
        assert "Products and Services" in result
        assert "Test products." in result
        assert "Markets and Segments" in result
        assert "Test markets." in result
        assert "Competitive Position" in result
        assert "Test differentiators." in result

    def test_format_minimal(self):
        """format() should work with only required fields."""
        desc = ExtractedBusinessDescription(
            company_overview="Just an overview.",
            products_and_services="Just products.",
        )
        result = desc.format()

        assert "Just an overview." in result
        assert "Just products." in result
        assert "Markets and Segments" not in result
        assert "Competitive Position" not in result

    def test_format_removes_citations(self):
        """format() should clean citation brackets from text."""
        desc = ExtractedBusinessDescription(
            company_overview="Test company [1] with citations [2][3].",
            products_and_services="Products [4].",
        )
        result = desc.format()

        assert "[1]" not in result
        assert "[2]" not in result
        assert "[3]" not in result
        assert "[4]" not in result


class TestFiling:
    """Tests for Filing data class."""

    def test_filing_creation_minimal(self):
        """Filing should work with minimal required fields."""
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            period_end="2024-09-30",
        )
        assert filing.identifier == "0000320193"
        assert filing.filing_type == "10-K"
        assert filing.filed_at is None
        assert filing.raw_data is None

    def test_filing_creation_full(self):
        """Filing should accept all optional fields."""
        filing = Filing(
            identifier="0000320193",
            filing_type="10-K",
            period_end="2024-09-30",
            filed_at="2024-11-01",
            accession_number="0000320193-24-000123",
            document_url="https://sec.gov/...",
            raw_data={"key": "value"},
        )
        assert filing.accession_number == "0000320193-24-000123"
        assert filing.raw_data == {"key": "value"}


class TestRevenueData:
    """Tests for RevenueData data class."""

    def test_revenue_creation(self):
        """RevenueData should store all revenue information."""
        revenue = RevenueData(
            amount=383285000000,
            currency="USD",
            period_end="2024-09-30",
            source_tag="us-gaap:Revenues",
        )
        assert revenue.amount == 383285000000
        assert revenue.currency == "USD"
        assert revenue.source_tag == "us-gaap:Revenues"


class TestBusinessDescription:
    """Tests for BusinessDescription data class."""

    def test_business_description_creation(self):
        """BusinessDescription should store extraction metadata."""
        desc = BusinessDescription(
            text="Apple designs and manufactures...",
            source_filing_type="10-K",
            source_accession="0000320193-24-000123",
            extraction_method="llm_extract",
        )
        assert "Apple designs" in desc.text
        assert desc.source_filing_type == "10-K"
        assert desc.extraction_method == "llm_extract"
