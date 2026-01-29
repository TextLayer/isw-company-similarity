"""Integration tests for SEC EDGAR collector.

These tests verify that the collector correctly parses real SEC submission formats.
"""

import io
import json
import unittest
import zipfile
from unittest.mock import MagicMock, patch

from isw.core.services.entity_collection import (
    DownloadError,
    IdentifierType,
    Jurisdiction,
    SECEdgarCollector,
)
from tests.fixtures.entity_collection import load_fixture


def create_zip_from_fixtures(*fixture_names: str) -> bytes:
    """Create a mock submissions.zip from fixture files."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in fixture_names:
            fixture = load_fixture(name)
            cik = str(fixture.get("cik", "0")).zfill(10)
            filename = f"CIK{cik}.json"
            zf.writestr(filename, json.dumps(fixture))

        zf.writestr("submissions.json", json.dumps({"version": "1.0"}))

    return buffer.getvalue()


class TestSECEdgarCollectorIntegration(unittest.TestCase):
    """Integration tests for SECEdgarCollector with realistic SEC data."""

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_parses_real_sec_submission_format(self, mock_client_class):
        """Test parsing actual SEC submission JSON structure."""
        mock_zip = create_zip_from_fixtures("sec_submission_apple.json")

        mock_response = MagicMock()
        mock_response.content = mock_zip
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0")
        entities = collector.fetch_entities()

        assert len(entities) == 1
        entity = entities[0]

        assert entity.name == "Apple Inc."
        assert entity.identifier == "0000320193"
        assert entity.jurisdiction == Jurisdiction.US
        assert entity.identifier_type == IdentifierType.CIK

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_filters_companies_without_10k(self, mock_client_class):
        """Test that companies without 10-K filings are excluded."""
        mock_zip = create_zip_from_fixtures(
            "sec_submission_apple.json",
            "sec_submission_no_10k.json",
        )

        mock_response = MagicMock()
        mock_response.content = mock_zip
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0")
        entities = collector.fetch_entities()

        assert len(entities) == 1
        assert entities[0].name == "Apple Inc."

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_filters_old_10k_filings(self, mock_client_class):
        """Test that companies with only old 10-K filings are excluded."""
        mock_zip = create_zip_from_fixtures(
            "sec_submission_apple.json",
            "sec_submission_old_10k.json",
        )

        mock_response = MagicMock()
        mock_response.content = mock_zip
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0", years_lookback=3)
        entities = collector.fetch_entities()

        assert len(entities) == 1
        assert entities[0].name == "Apple Inc."

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_handles_download_error(self, mock_client_class):
        """Test proper error handling when download fails."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection refused")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0")

        with self.assertRaises(DownloadError) as ctx:
            collector.fetch_entities()

        assert "Connection refused" in str(ctx.exception)

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_extracts_all_required_fields(self, mock_client_class):
        """Test that all required entity fields are correctly extracted."""
        mock_zip = create_zip_from_fixtures("sec_submission_apple.json")

        mock_response = MagicMock()
        mock_response.content = mock_zip
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0")
        entities = collector.fetch_entities()

        entity = entities[0]
        entity_dict = entity.to_dict()

        assert "name" in entity_dict
        assert "identifier" in entity_dict
        assert "jurisdiction" in entity_dict
        assert "identifier_type" in entity_dict

        assert entity_dict["name"] == "Apple Inc."
        assert entity_dict["identifier"] == "0000320193"
        assert entity_dict["jurisdiction"] == "US"
        assert entity_dict["identifier_type"] == "CIK"
