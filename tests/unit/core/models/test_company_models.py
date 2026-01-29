"""Unit tests for Company model."""

import unittest

from isw.core.models.company_models import Company
from isw.core.services.entity_collection.base import (
    EntityRecord,
    IdentifierType,
    Jurisdiction,
)


class TestCompanyModel(unittest.TestCase):
    """Tests for Company model."""

    def test_from_entity_record_us(self):
        """Test creating Company from US EntityRecord."""
        record = EntityRecord(
            name="Apple Inc.",
            identifier="0000320193",
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

        company = Company.from_entity_record(record)

        assert company.company_name == "Apple Inc."
        assert company.identifier == "0000320193"
        assert company.identifier_type == "CIK"
        assert company.jurisdiction == "US"

    def test_from_entity_record_eu(self):
        """Test creating Company from EU EntityRecord."""
        record = EntityRecord(
            name="Siemens AG",
            identifier="W38RGI023J3WT1HWRP32",
            jurisdiction=Jurisdiction.EU,
            identifier_type=IdentifierType.LEI,
        )

        company = Company.from_entity_record(record)

        assert company.company_name == "Siemens AG"
        assert company.identifier == "W38RGI023J3WT1HWRP32"
        assert company.identifier_type == "LEI"
        assert company.jurisdiction == "EU"

    def test_from_entity_record_uk(self):
        """Test creating Company from UK EntityRecord."""
        record = EntityRecord(
            name="BP p.l.c.",
            identifier="213800LH1BZH3DI6G760",
            jurisdiction=Jurisdiction.UK,
            identifier_type=IdentifierType.LEI,
        )

        company = Company.from_entity_record(record)

        assert company.company_name == "BP p.l.c."
        assert company.identifier == "213800LH1BZH3DI6G760"
        assert company.identifier_type == "LEI"
        assert company.jurisdiction == "UK"

    def test_get_identifier_type_enum(self):
        """Test getting identifier type as enum."""
        company = Company(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            company_name="Test",
        )

        assert company.get_identifier_type_enum() == IdentifierType.CIK

    def test_get_jurisdiction_enum(self):
        """Test getting jurisdiction as enum."""
        company = Company(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            company_name="Test",
        )

        assert company.get_jurisdiction_enum() == Jurisdiction.US

    def test_to_dict_includes_new_fields(self):
        """Test that to_dict includes identifier fields."""
        company = Company(
            id=1,
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            company_name="Apple Inc.",
        )

        result = company.to_dict()

        assert result["identifier"] == "0000320193"
        assert result["identifier_type"] == "CIK"
        assert result["jurisdiction"] == "US"
        assert result["company_name"] == "Apple Inc."

    def test_repr(self):
        """Test string representation."""
        company = Company(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            company_name="Apple Inc.",
        )

        repr_str = repr(company)

        assert "0000320193" in repr_str
        assert "CIK" in repr_str
        assert "Apple Inc." in repr_str
