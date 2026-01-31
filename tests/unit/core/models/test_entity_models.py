"""Unit tests for Entity model."""

import unittest

from isw.core.models.entity_models import Entity
from isw.core.services.entities import (
    EntityRecord,
    IdentifierType,
    Jurisdiction,
)


class TestEntityModel(unittest.TestCase):
    """Tests for Entity model."""

    def test_from_entity_record_us(self):
        """Test creating Entity from US EntityRecord."""
        record = EntityRecord(
            name="Apple Inc.",
            identifier="0000320193",
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

        entity = Entity.from_entity_record(record)

        assert entity.name == "Apple Inc."
        assert entity.identifier == "0000320193"
        assert entity.identifier_type == "CIK"
        assert entity.jurisdiction == "US"

    def test_from_entity_record_eu(self):
        """Test creating Entity from EU EntityRecord."""
        record = EntityRecord(
            name="Siemens AG",
            identifier="W38RGI023J3WT1HWRP32",
            jurisdiction=Jurisdiction.EU,
            identifier_type=IdentifierType.LEI,
        )

        entity = Entity.from_entity_record(record)

        assert entity.name == "Siemens AG"
        assert entity.identifier == "W38RGI023J3WT1HWRP32"
        assert entity.identifier_type == "LEI"
        assert entity.jurisdiction == "EU"

    def test_from_entity_record_uk(self):
        """Test creating Entity from UK EntityRecord."""
        record = EntityRecord(
            name="BP p.l.c.",
            identifier="213800LH1BZH3DI6G760",
            jurisdiction=Jurisdiction.UK,
            identifier_type=IdentifierType.LEI,
        )

        entity = Entity.from_entity_record(record)

        assert entity.name == "BP p.l.c."
        assert entity.identifier == "213800LH1BZH3DI6G760"
        assert entity.identifier_type == "LEI"
        assert entity.jurisdiction == "UK"

    def test_get_identifier_type_enum(self):
        """Test getting identifier type as enum."""
        entity = Entity(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            name="Test",
        )

        assert entity.get_identifier_type_enum() == IdentifierType.CIK

    def test_get_jurisdiction_enum(self):
        """Test getting jurisdiction as enum."""
        entity = Entity(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            name="Test",
        )

        assert entity.get_jurisdiction_enum() == Jurisdiction.US

    def test_to_dict_includes_fields(self):
        """Test that to_dict includes all identifier fields."""
        entity = Entity(
            id=1,
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            name="Apple Inc.",
        )

        result = entity.to_dict()

        assert result["identifier"] == "0000320193"
        assert result["identifier_type"] == "CIK"
        assert result["jurisdiction"] == "US"
        assert result["name"] == "Apple Inc."

    def test_repr(self):
        """Test string representation."""
        entity = Entity(
            identifier="0000320193",
            identifier_type="CIK",
            jurisdiction="US",
            name="Apple Inc.",
        )

        repr_str = repr(entity)

        assert "0000320193" in repr_str
        assert "CIK" in repr_str
        assert "Apple Inc." in repr_str
