"""Integration tests for ESEF collector.

These tests verify parsing of real filings.xbrl.org API responses.
Includes both fixture-based tests and live API tests.
"""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from isw.core.services.entity_collection import (
    ESEFCollector,
    IdentifierType,
    Jurisdiction,
)

REAL_ESEF_FIXTURES = (
    Path(__file__).parent.parent.parent.parent.parent / "fixtures" / "entity_collection" / "real_esef_data"
)


class TestESEFCollectorWithRealFixtures(unittest.TestCase):
    """Integration tests using real downloaded API responses."""

    @classmethod
    def setUpClass(cls):
        """Skip tests if fixtures don't exist."""
        if not REAL_ESEF_FIXTURES.exists():
            raise unittest.SkipTest("Real ESEF fixtures not downloaded")

    def _load_fixture(self, name: str) -> dict:
        """Load a real API response fixture."""
        filepath = REAL_ESEF_FIXTURES / name
        with open(filepath) as f:
            return json.load(f)

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_parses_real_gb_filings(self, mock_client_class):
        """Test parsing real UK (GB) filings from API."""
        fixture = self._load_fixture("gb_filings.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        # Return empty second page to stop pagination
        empty_response = MagicMock()
        empty_response.json.return_value = {"data": [], "included": []}
        empty_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response, empty_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=100)
        entities = collector.fetch_entities()

        assert len(entities) > 0

        for entity in entities:
            assert entity.jurisdiction == Jurisdiction.UK
            assert entity.identifier_type == IdentifierType.LEI
            assert len(entity.identifier) == 20
            assert entity.name

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_parses_real_eu_filings(self, mock_client_class):
        """Test parsing real EU filings from API."""
        fr_fixture = self._load_fixture("fr_filings.json")
        nl_fixture = self._load_fixture("nl_filings.json")

        # Combine fixtures
        combined = {
            "data": fr_fixture["data"] + nl_fixture["data"],
            "included": fr_fixture.get("included", []) + nl_fixture.get("included", []),
        }

        mock_response = MagicMock()
        mock_response.json.return_value = combined
        mock_response.raise_for_status = MagicMock()

        empty_response = MagicMock()
        empty_response.json.return_value = {"data": [], "included": []}
        empty_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response, empty_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=100)
        entities = collector.fetch_entities()

        assert len(entities) > 0

        for entity in entities:
            assert entity.jurisdiction == Jurisdiction.EU
            assert entity.identifier_type == IdentifierType.LEI
            assert len(entity.identifier) == 20

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_deduplicates_entities_by_lei(self, mock_client_class):
        """Test that entities are deduplicated by LEI across pages."""
        fixture = self._load_fixture("gb_filings.json")

        # Create duplicate by returning same data twice
        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        empty_response = MagicMock()
        empty_response.json.return_value = {"data": [], "included": []}
        empty_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response, mock_response, empty_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=5)
        entities = collector.fetch_entities()

        leis = [e.identifier for e in entities]
        assert len(leis) == len(set(leis)), "Duplicate LEIs found"

    @patch("isw.core.services.entity_collection.esef_collector.httpx.Client")
    def test_serialization_roundtrip(self, mock_client_class):
        """Test that entities serialize and deserialize correctly."""
        fixture = self._load_fixture("gb_filings.json")

        mock_response = MagicMock()
        mock_response.json.return_value = fixture
        mock_response.raise_for_status = MagicMock()

        empty_response = MagicMock()
        empty_response.json.return_value = {"data": [], "included": []}
        empty_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.side_effect = [mock_response, empty_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = ESEFCollector(page_size=100)
        entities = collector.fetch_entities()

        from isw.core.services.entity_collection import EntityRecord

        for entity in entities:
            entity_dict = entity.to_dict()
            restored = EntityRecord.from_dict(entity_dict)
            assert restored.name == entity.name
            assert restored.identifier == entity.identifier
            assert restored.jurisdiction == entity.jurisdiction
            assert restored.identifier_type == entity.identifier_type


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_API_TESTS") != "1",
    reason="Live API tests disabled. Set RUN_LIVE_API_TESTS=1 to run.",
)
class TestESEFCollectorLiveAPI(unittest.TestCase):
    """Integration tests that hit the real filings.xbrl.org API.

    These tests are skipped by default. Run with:
        RUN_LIVE_API_TESTS=1 pytest tests/integration/.../test_esef_collector.py -k Live
    """

    def test_live_api_fetch_entities(self):
        """Test fetching entities from the real API."""
        collector = ESEFCollector(page_size=10, max_pages=2)
        entities = collector.fetch_entities()

        assert len(entities) > 0

        for entity in entities:
            assert entity.name
            assert len(entity.identifier) == 20
            assert entity.identifier.isalnum()
            assert entity.identifier_type == IdentifierType.LEI
            assert entity.jurisdiction in (Jurisdiction.UK, Jurisdiction.EU)

    def test_live_api_handles_pagination(self):
        """Test that pagination works with real API."""
        collector = ESEFCollector(page_size=5, max_pages=3)
        entities = collector.fetch_entities()

        # With 3 pages of 5, we should have multiple entities
        assert len(entities) > 5

        leis = [e.identifier for e in entities]
        assert len(leis) == len(set(leis)), "Duplicate LEIs found"
