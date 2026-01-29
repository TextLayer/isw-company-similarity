"""Tests for ESEF collector."""

import unittest
from unittest.mock import MagicMock, patch

from isw.core.services.entity_collection import (
    DownloadError,
    ESEFCollector,
    IdentifierType,
    Jurisdiction,
)


def create_mock_filing(lei: str, name: str, country: str) -> dict:
    """Create a mock filing record from filings.xbrl.org API."""
    return {
        "lei": lei,
        "entity_name": name,
        "country": country,
        "report_type": "AFR",
    }


class TestESEFCollector(unittest.TestCase):
    """Tests for ESEFCollector."""

    def test_get_source_name(self):
        """Test source name is correct."""
        collector = ESEFCollector()
        assert collector.get_source_name() == "filings.xbrl.org"

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_fetch_entities_basic(self, mock_client_class):
        """Test basic entity fetching."""
        filings = [
            create_mock_filing("W38RGI023J3WT1HWRP32", "Siemens AG", "DE"),
            create_mock_filing("213800LH1BZH3DI6G760", "BP plc", "GB"),
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": filings}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=100)
        entities = collector.fetch_entities()

        assert len(entities) == 2

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_jurisdiction_assignment(self, mock_client_class):
        """Test that jurisdictions are correctly assigned."""
        filings = [
            create_mock_filing("A1B2C3D4E5F6G7H8I9J0", "German Corp", "DE"),
            create_mock_filing("B2C3D4E5F6G7H8I9J0K1", "French Corp", "FR"),
            create_mock_filing("C3D4E5F6G7H8I9J0K1L2", "UK Corp", "GB"),
            create_mock_filing("D4E5F6G7H8I9J0K1L2M3", "UK Corp 2", "UK"),
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": filings}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        jurisdictions = {e.identifier: e.jurisdiction for e in entities}

        # German and French should be EU
        assert jurisdictions["A1B2C3D4E5F6G7H8I9J0"] == Jurisdiction.EU
        assert jurisdictions["B2C3D4E5F6G7H8I9J0K1"] == Jurisdiction.EU

        # GB and UK should be UK
        assert jurisdictions["C3D4E5F6G7H8I9J0K1L2"] == Jurisdiction.UK
        assert jurisdictions["D4E5F6G7H8I9J0K1L2M3"] == Jurisdiction.UK

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_deduplication_by_lei(self, mock_client_class):
        """Test that duplicate LEIs are filtered out."""
        same_lei = "W38RGI023J3WT1HWRP32"
        filings = [
            create_mock_filing(same_lei, "Company Filing 1", "DE"),
            create_mock_filing(same_lei, "Company Filing 2", "DE"),  # Same LEI
            create_mock_filing("XDIFFERENT1234567890", "Other Company", "FR"),  # 20 chars
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": filings}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        # Should only get 2 unique entities
        assert len(entities) == 2
        leis = {e.identifier for e in entities}
        assert same_lei in leis
        assert "XDIFFERENT1234567890" in leis

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_entity_record_fields(self, mock_client_class):
        """Test that entity records have correct fields."""
        filings = [
            create_mock_filing("W38RGI023J3WT1HWRP32", "Siemens AG", "DE"),
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": filings}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        assert len(entities) == 1
        entity = entities[0]

        assert entity.name == "Siemens AG"
        assert entity.identifier == "W38RGI023J3WT1HWRP32"
        assert entity.jurisdiction == Jurisdiction.EU
        assert entity.identifier_type == IdentifierType.LEI

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_pagination(self, mock_client_class):
        """Test that pagination is handled correctly."""
        # First page has full results
        page1_filings = [create_mock_filing(f"LEI{i:017d}", f"Company {i}", "DE") for i in range(10)]
        # Second page has partial results (end of data)
        page2_filings = [create_mock_filing(f"LEI{i:017d}", f"Company {i}", "DE") for i in range(10, 15)]

        mock_response1 = MagicMock()
        mock_response1.json.return_value = {"data": page1_filings}
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"data": page2_filings}
        mock_response2.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response1, mock_response2]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=10)
        entities = collector.fetch_entities()

        # Should get all 15 entities
        assert len(entities) == 15

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_invalid_lei_filtered(self, mock_client_class):
        """Test that invalid LEIs are filtered out."""
        filings = [
            create_mock_filing("W38RGI023J3WT1HWRP32", "Valid LEI Corp", "DE"),
            create_mock_filing("TOOLONG1234567890ABCD", "Invalid LEI", "DE"),  # 21 chars
            create_mock_filing("SHORT", "Short LEI", "DE"),  # Too short
            create_mock_filing("", "Empty LEI", "DE"),
            {"entity_name": "No LEI Corp", "country": "DE"},  # Missing LEI
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": filings}
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        # Only valid LEI should be included
        assert len(entities) == 1
        assert entities[0].name == "Valid LEI Corp"

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_download_error_handling(self, mock_client_class):
        """Test that download errors are properly raised."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()

        with self.assertRaises(DownloadError):
            collector.fetch_entities()

    def test_is_valid_lei(self):
        """Test LEI validation."""
        collector = ESEFCollector()

        # Valid LEI (20 alphanumeric characters)
        assert collector._is_valid_lei("W38RGI023J3WT1HWRP32") is True
        assert collector._is_valid_lei("ABCDEFGHIJ0123456789") is True

        # Invalid LEIs
        assert collector._is_valid_lei("") is False
        assert collector._is_valid_lei("SHORT") is False
        assert collector._is_valid_lei("TOOLONG1234567890ABCDE") is False
        assert collector._is_valid_lei("SPECIAL!@#$%^&*()CHAR") is False

    def test_get_jurisdiction(self):
        """Test jurisdiction mapping from country codes."""
        collector = ESEFCollector()

        # UK countries
        assert collector._get_jurisdiction("GB") == Jurisdiction.UK
        assert collector._get_jurisdiction("UK") == Jurisdiction.UK
        assert collector._get_jurisdiction("gb") == Jurisdiction.UK

        # EU countries
        assert collector._get_jurisdiction("DE") == Jurisdiction.EU
        assert collector._get_jurisdiction("FR") == Jurisdiction.EU
        assert collector._get_jurisdiction("NL") == Jurisdiction.EU
        assert collector._get_jurisdiction("IT") == Jurisdiction.EU
