"""Integration tests for ESEF collector.

These tests verify that the collector correctly parses real filings.xbrl.org API responses.
"""

import unittest
from unittest.mock import MagicMock, patch

from isw.core.services.entity_collection import (
    DownloadError,
    ESEFCollector,
    Jurisdiction,
)
from tests.fixtures.entity_collection import load_fixture


class TestESEFCollectorIntegration(unittest.TestCase):
    """Integration tests for ESEFCollector with realistic API responses."""

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_parses_real_api_response_format(self, mock_client_class):
        """Test parsing actual filings.xbrl.org JSON API response structure."""
        fixture = load_fixture("esef_filings_response.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        # Should have 4 unique entities (Siemens appears twice)
        assert len(entities) == 4

        names = {e.name for e in entities}
        assert "Siemens AG" in names
        assert "BP p.l.c." in names
        assert "TotalEnergies SE" in names
        assert "Royal Philips N.V." in names

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_correctly_assigns_jurisdictions(self, mock_client_class):
        """Test that jurisdictions are correctly assigned from country codes."""
        fixture = load_fixture("esef_filings_response.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        by_name = {e.name: e for e in entities}

        # GB -> UK
        assert by_name["BP p.l.c."].jurisdiction == Jurisdiction.UK
        # DE -> EU
        assert by_name["Siemens AG"].jurisdiction == Jurisdiction.EU
        # FR -> EU
        assert by_name["TotalEnergies SE"].jurisdiction == Jurisdiction.EU
        # NL -> EU
        assert by_name["Royal Philips N.V."].jurisdiction == Jurisdiction.EU

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_deduplicates_by_lei(self, mock_client_class):
        """Test that duplicate filings for same entity are deduplicated."""
        fixture = load_fixture("esef_filings_response.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        # Siemens has 2 filings but should appear only once
        siemens_count = sum(1 for e in entities if e.name == "Siemens AG")
        assert siemens_count == 1

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_filters_invalid_leis(self, mock_client_class):
        """Test that entities with invalid LEIs are filtered out."""
        fixture = load_fixture("esef_filings_invalid_lei.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        # Only the valid 20-char LEI should be included
        assert len(entities) == 1
        assert entities[0].name == "Valid Company SpA"
        assert entities[0].identifier == "ABCDEFGHIJ1234567890"

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_handles_download_error(self, mock_client_class):
        """Test proper error handling when API request fails."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection timeout")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()

        with self.assertRaises(DownloadError) as ctx:
            collector.fetch_entities()

        assert "Connection timeout" in str(ctx.exception)

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_extracts_all_required_fields(self, mock_client_class):
        """Test that all required entity fields are correctly extracted."""
        fixture = load_fixture("esef_filings_response.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector()
        entities = collector.fetch_entities()

        entity = next(e for e in entities if e.name == "Siemens AG")
        entity_dict = entity.to_dict()

        assert entity_dict["name"] == "Siemens AG"
        assert entity_dict["identifier"] == "W38RGI023J3WT1HWRP32"
        assert entity_dict["jurisdiction"] == "EU"
        assert entity_dict["identifier_type"] == "LEI"

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_handles_pagination(self, mock_client_class):
        """Test that pagination is handled correctly."""
        page1 = {
            "data": [
                {
                    "type": "filing",
                    "id": "1",
                    "attributes": {
                        "country": "DE",
                        "entity_name": "Company 1",
                        "lei": "AAAABBBBCCCCDDDDEEEE",
                        "report_type": "AFR",
                    },
                }
                for _ in range(10)
            ]
        }
        # Change LEIs to be unique
        for i, item in enumerate(page1["data"]):
            item["attributes"]["lei"] = f"AAAABBBBCCCC{i:08d}"
            item["attributes"]["entity_name"] = f"Company {i}"

        page2 = {
            "data": [
                {
                    "type": "filing",
                    "id": "2",
                    "attributes": {
                        "country": "FR",
                        "entity_name": "Company 10",
                        "lei": "FFFFGGGGHHHHIIIIJJJJ",
                        "report_type": "AFR",
                    },
                }
            ]
        }

        mock_response1 = MagicMock()
        mock_response1.json.return_value = page1
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()
        mock_response2.json.return_value = page2
        mock_response2.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response1, mock_response2]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=10)
        entities = collector.fetch_entities()

        # 10 from page 1 + 1 from page 2
        assert len(entities) == 11
