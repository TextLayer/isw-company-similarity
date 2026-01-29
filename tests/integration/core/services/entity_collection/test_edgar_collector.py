"""Integration tests for SEC EDGAR collector.

These tests verify parsing of real SEC submission data.
Fixtures are downloaded from the actual SEC EDGAR API.
"""

import io
import json
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from isw.core.services.entity_collection import (
    IdentifierType,
    Jurisdiction,
    SECEdgarCollector,
)

REAL_SEC_FIXTURES = (
    Path(__file__).parent.parent.parent.parent.parent / "fixtures" / "entity_collection" / "real_sec_data"
)


def create_zip_from_real_fixtures(*filenames: str) -> bytes:
    """Create a mock submissions.zip from real downloaded fixtures."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in filenames:
            filepath = REAL_SEC_FIXTURES / name
            if filepath.exists():
                with open(filepath) as f:
                    data = json.load(f)
                cik = str(data.get("cik", "0")).zfill(10)
                zf.writestr(f"CIK{cik}.json", json.dumps(data))

        zf.writestr("submissions.json", json.dumps({"version": "1.0"}))

    return buffer.getvalue()


class TestSECEdgarCollectorWithRealData(unittest.TestCase):
    """Integration tests using real SEC submission data."""

    @classmethod
    def setUpClass(cls):
        """Skip tests if fixtures don't exist."""
        if not REAL_SEC_FIXTURES.exists():
            raise unittest.SkipTest("Real SEC fixtures not downloaded")

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_parses_real_apple_submission(self, mock_client_class):
        """Test parsing real Apple Inc. SEC submission."""
        mock_zip = create_zip_from_real_fixtures("apple_submission.json")

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
    def test_parses_multiple_real_companies(self, mock_client_class):
        """Test parsing multiple real SEC submissions."""
        mock_zip = create_zip_from_real_fixtures(
            "apple_submission.json",
            "microsoft_submission.json",
            "tesla_submission.json",
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

        assert len(entities) == 3

        names = {e.name for e in entities}
        assert "Apple Inc." in names
        assert "MICROSOFT CORP" in names
        assert "Tesla, Inc." in names

        for entity in entities:
            assert entity.jurisdiction == Jurisdiction.US
            assert entity.identifier_type == IdentifierType.CIK
            assert len(entity.identifier) == 10

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_cik_is_zero_padded(self, mock_client_class):
        """Test that CIK identifiers are correctly zero-padded to 10 digits."""
        mock_zip = create_zip_from_real_fixtures("apple_submission.json")

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
        assert entity.identifier == "0000320193"
        assert len(entity.identifier) == 10
        assert entity.identifier.isdigit()

    @patch("isw.core.services.entity_collection.edgar_collector.httpx.Client")
    def test_serialization_roundtrip(self, mock_client_class):
        """Test that entities serialize and deserialize correctly."""
        mock_zip = create_zip_from_real_fixtures("apple_submission.json")

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

        from isw.core.services.entity_collection import EntityRecord

        for entity in entities:
            entity_dict = entity.to_dict()
            restored = EntityRecord.from_dict(entity_dict)
            assert restored.name == entity.name
            assert restored.identifier == entity.identifier
            assert restored.jurisdiction == entity.jurisdiction
            assert restored.identifier_type == entity.identifier_type
