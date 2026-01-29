"""Tests for SEC EDGAR collector."""

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


def create_mock_submission(cik: str, name: str, has_10k: bool = True, recent_10k: bool = True) -> dict:
    """Create a mock SEC submission JSON structure."""
    forms = ["10-K", "10-Q", "8-K"] if has_10k else ["10-Q", "8-K"]
    dates = ["2025-03-15", "2024-11-15", "2024-08-15"] if recent_10k else ["2020-03-15", "2019-11-15", "2019-08-15"]

    return {
        "cik": cik,
        "name": name,
        "filings": {
            "recent": {
                "form": forms,
                "filingDate": dates,
            }
        },
    }


def create_mock_zip(submissions: list[dict]) -> bytes:
    """Create a mock submissions.zip file."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add individual company files
        for i, submission in enumerate(submissions):
            cik = str(submission.get("cik", i)).zfill(10)
            filename = f"CIK{cik}.json"
            zf.writestr(filename, json.dumps(submission))

        # Add index file
        zf.writestr("submissions.json", json.dumps({"version": "1.0"}))

    return buffer.getvalue()


class TestSECEdgarCollector(unittest.TestCase):
    """Tests for SECEdgarCollector."""

    def test_get_source_name(self):
        """Test source name is correct."""
        collector = SECEdgarCollector(user_agent="test/1.0")
        assert collector.get_source_name() == "SEC EDGAR"

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_fetch_entities_with_10k_filers(self, mock_client_class):
        """Test fetching entities filters for 10-K filers."""
        # Create mock submissions
        submissions = [
            create_mock_submission("320193", "Apple Inc.", has_10k=True, recent_10k=True),
            create_mock_submission("789019", "Microsoft Corp", has_10k=True, recent_10k=True),
            create_mock_submission("000001", "No 10K Company", has_10k=False),
        ]
        mock_zip = create_mock_zip(submissions)

        # Setup mock HTTP response
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

        assert len(entities) == 2
        names = {e.name for e in entities}
        assert "Apple Inc." in names
        assert "Microsoft Corp" in names

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_fetch_entities_filters_old_10k(self, mock_client_class):
        """Test that old 10-K filings are filtered out."""
        submissions = [
            create_mock_submission("123456", "Recent Filer", has_10k=True, recent_10k=True),
            create_mock_submission("654321", "Old Filer", has_10k=True, recent_10k=False),
        ]
        mock_zip = create_mock_zip(submissions)

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
        assert entities[0].name == "Recent Filer"

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_entity_record_fields(self, mock_client_class):
        """Test that entity records have correct fields."""
        submissions = [
            create_mock_submission("320193", "Apple Inc.", has_10k=True, recent_10k=True),
        ]
        mock_zip = create_mock_zip(submissions)

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
        assert entity.identifier == "0000320193"  # Padded to 10 digits
        assert entity.jurisdiction == Jurisdiction.US
        assert entity.identifier_type == IdentifierType.CIK

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_download_error_handling(self, mock_client_class):
        """Test that download errors are properly raised."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        collector = SECEdgarCollector(user_agent="test/1.0")

        with self.assertRaises(DownloadError):
            collector.fetch_entities()

    def test_has_recent_10k_with_amendment(self):
        """Test that 10-K/A (amended) filings are counted."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {
            "filings": {
                "recent": {
                    "form": ["10-K/A", "10-Q"],
                    "filingDate": ["2025-04-15", "2024-11-15"],
                }
            }
        }

        assert collector._has_recent_10k(submission) is True

    def test_has_recent_10k_empty_filings(self):
        """Test handling of empty filings."""
        collector = SECEdgarCollector(user_agent="test/1.0")

        submission = {"filings": {"recent": {"form": [], "filingDate": []}}}

        assert collector._has_recent_10k(submission) is False
