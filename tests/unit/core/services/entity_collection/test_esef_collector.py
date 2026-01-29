"""Unit tests for ESEF collector internal logic.

These tests focus on complex internal logic like LEI validation and jurisdiction mapping.
Integration tests cover data parsing from real API responses.
"""

import unittest

from isw.core.services.entity_collection import ESEFCollector, Jurisdiction


class TestESEFCollectorLogic(unittest.TestCase):
    """Unit tests for ESEFCollector internal logic."""

    def test_is_valid_lei_correct_format(self):
        """Test valid 20-character alphanumeric LEI."""
        collector = ESEFCollector()

        assert collector._is_valid_lei("W38RGI023J3WT1HWRP32") is True
        assert collector._is_valid_lei("ABCDEFGHIJ0123456789") is True
        assert collector._is_valid_lei("12345678901234567890") is True

    def test_is_valid_lei_wrong_length(self):
        """Test LEIs with wrong length are rejected."""
        collector = ESEFCollector()

        assert collector._is_valid_lei("SHORT") is False
        assert collector._is_valid_lei("TOOLONGABCDEFGHIJ12345") is False
        assert collector._is_valid_lei("") is False

    def test_is_valid_lei_special_characters(self):
        """Test LEIs with special characters are rejected."""
        collector = ESEFCollector()

        assert collector._is_valid_lei("SPECIAL!@#$%^&*()CHAR") is False
        assert collector._is_valid_lei("CONTAINS-DASH-123456") is False
        assert collector._is_valid_lei("HAS_UNDERSCORE_12345") is False

    def test_is_valid_lei_none(self):
        """Test None LEI is rejected."""
        collector = ESEFCollector()
        assert collector._is_valid_lei(None) is False

    def test_get_jurisdiction_uk(self):
        """Test UK country codes map to UK jurisdiction."""
        collector = ESEFCollector()

        assert collector._get_jurisdiction("GB") == Jurisdiction.UK
        assert collector._get_jurisdiction("UK") == Jurisdiction.UK
        assert collector._get_jurisdiction("gb") == Jurisdiction.UK

    def test_get_jurisdiction_eu(self):
        """Test EU country codes map to EU jurisdiction."""
        collector = ESEFCollector()

        assert collector._get_jurisdiction("DE") == Jurisdiction.EU
        assert collector._get_jurisdiction("FR") == Jurisdiction.EU
        assert collector._get_jurisdiction("NL") == Jurisdiction.EU
        assert collector._get_jurisdiction("IT") == Jurisdiction.EU
        assert collector._get_jurisdiction("ES") == Jurisdiction.EU

    def test_get_source_name(self):
        """Test source name is correct."""
        collector = ESEFCollector()
        assert collector.get_source_name() == "filings.xbrl.org"

    def test_build_entity_map(self):
        """Test building entity map from included resources."""
        collector = ESEFCollector()

        included = [
            {
                "type": "entity",
                "id": "123",
                "attributes": {"identifier": "ABCD1234567890123456", "name": "Test Co"},
            },
            {
                "type": "entity",
                "id": "456",
                "attributes": {"identifier": "EFGH0987654321098765", "name": "Other Co"},
            },
            {"type": "filing", "id": "789"},  # Should be ignored
        ]

        entity_map = collector._build_entity_map(included)

        assert len(entity_map) == 2
        assert entity_map["123"]["identifier"] == "ABCD1234567890123456"
        assert entity_map["456"]["name"] == "Other Co"
