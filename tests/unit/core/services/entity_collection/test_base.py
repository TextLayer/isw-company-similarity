"""Tests for entity collection base classes."""

import unittest

from isw.core.services.entity_collection import (
    EntityRecord,
    IdentifierType,
    Jurisdiction,
)


class TestEntityRecord(unittest.TestCase):
    """Tests for EntityRecord dataclass."""

    def test_create_us_entity(self):
        """Test creating a US entity with CIK."""
        entity = EntityRecord(
            name="Apple Inc.",
            identifier="0000320193",
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

        assert entity.name == "Apple Inc."
        assert entity.identifier == "0000320193"
        assert entity.jurisdiction == Jurisdiction.US
        assert entity.identifier_type == IdentifierType.CIK

    def test_create_eu_entity(self):
        """Test creating an EU entity with LEI."""
        entity = EntityRecord(
            name="Siemens AG",
            identifier="W38RGI023J3WT1HWRP32",
            jurisdiction=Jurisdiction.EU,
            identifier_type=IdentifierType.LEI,
        )

        assert entity.name == "Siemens AG"
        assert entity.identifier == "W38RGI023J3WT1HWRP32"
        assert entity.jurisdiction == Jurisdiction.EU
        assert entity.identifier_type == IdentifierType.LEI

    def test_create_uk_entity(self):
        """Test creating a UK entity with LEI."""
        entity = EntityRecord(
            name="BP plc",
            identifier="213800LH1BZH3DI6G760",
            jurisdiction=Jurisdiction.UK,
            identifier_type=IdentifierType.LEI,
        )

        assert entity.jurisdiction == Jurisdiction.UK

    def test_to_dict(self):
        """Test converting entity to dictionary."""
        entity = EntityRecord(
            name="Test Corp",
            identifier="0000123456",
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

        result = entity.to_dict()

        assert result == {
            "name": "Test Corp",
            "identifier": "0000123456",
            "jurisdiction": "US",
            "identifier_type": "CIK",
        }

    def test_from_dict(self):
        """Test creating entity from dictionary."""
        data = {
            "name": "Test Corp",
            "identifier": "0000123456",
            "jurisdiction": "US",
            "identifier_type": "CIK",
        }

        entity = EntityRecord.from_dict(data)

        assert entity.name == "Test Corp"
        assert entity.identifier == "0000123456"
        assert entity.jurisdiction == Jurisdiction.US
        assert entity.identifier_type == IdentifierType.CIK

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are inverses."""
        original = EntityRecord(
            name="Roundtrip Test",
            identifier="ABCDEFGHIJ0123456789",
            jurisdiction=Jurisdiction.EU,
            identifier_type=IdentifierType.LEI,
        )

        serialized = original.to_dict()
        restored = EntityRecord.from_dict(serialized)

        assert restored.name == original.name
        assert restored.identifier == original.identifier
        assert restored.jurisdiction == original.jurisdiction
        assert restored.identifier_type == original.identifier_type


class TestJurisdiction(unittest.TestCase):
    """Tests for Jurisdiction enum."""

    def test_jurisdiction_values(self):
        """Test jurisdiction enum values."""
        assert Jurisdiction.US.value == "US"
        assert Jurisdiction.EU.value == "EU"
        assert Jurisdiction.UK.value == "UK"

    def test_jurisdiction_from_string(self):
        """Test creating jurisdiction from string value."""
        assert Jurisdiction("US") == Jurisdiction.US
        assert Jurisdiction("EU") == Jurisdiction.EU
        assert Jurisdiction("UK") == Jurisdiction.UK


class TestIdentifierType(unittest.TestCase):
    """Tests for IdentifierType enum."""

    def test_identifier_type_values(self):
        """Test identifier type enum values."""
        assert IdentifierType.CIK.value == "CIK"
        assert IdentifierType.LEI.value == "LEI"

    def test_identifier_type_from_string(self):
        """Test creating identifier type from string value."""
        assert IdentifierType("CIK") == IdentifierType.CIK
        assert IdentifierType("LEI") == IdentifierType.LEI
