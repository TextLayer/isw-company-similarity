from unittest.mock import Mock, patch

import pytest
from opensearchpy import ConflictError, NotFoundError, RequestError
from opensearchpy import ConnectionError as OSConnectionError

from isw.core.services.search.exceptions import (
    IndexAlreadyExistsError,
    IndexNotFoundError,
    SearchConnectionError,
    SearchQueryError,
    SearchServiceError,
    ValidationError,
)
from isw.core.services.search.providers.opensearch import OpenSearchProvider
from isw.core.services.search.types import IndexConfig, SearchQuery


class TestOpenSearchProviderErrorHandling:
    """Test error handling in OpenSearch provider."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock OpenSearch client."""
        return Mock()

    @pytest.fixture
    def provider(self, mock_client):
        """Create provider with mocked client."""
        with patch("textlayer.core.services.search.providers.opensearch.OpenSearch", return_value=mock_client):
            with patch("textlayer.core.services.search.providers.opensearch.config") as mock_config:
                mock_config.return_value.opensearch_host = "http://localhost:9200"
                mock_config.return_value.opensearch_username = "admin"
                mock_config.return_value.opensearch_password = "admin"
                return OpenSearchProvider()

    def test_search_index_not_found(self, provider, mock_client):
        """Test search raises IndexNotFoundError when index doesn't exist."""
        mock_client.search.side_effect = NotFoundError(404, "index_not_found_exception", {"error": "Index not found"})

        query = SearchQuery(query={"match_all": {}})
        with pytest.raises(IndexNotFoundError) as exc_info:
            provider.search("non-existent-index", query)

        assert exc_info.value.index == "non-existent-index"
        assert "not found" in str(exc_info.value)

    def test_search_query_parsing_error(self, provider, mock_client):
        """Test search raises SearchQueryError for malformed queries."""
        error_info = {
            "error": {
                "type": "parsing_exception",
                "reason": "Unknown query type [invalid_query]",
            }
        }
        mock_client.search.side_effect = RequestError(400, "parsing_exception", error_info)

        query = SearchQuery(query={"invalid_query": {}})
        with pytest.raises(SearchQueryError) as exc_info:
            provider.search("test-index", query)

        assert "Invalid query" in str(exc_info.value)

    def test_search_connection_error(self, provider, mock_client):
        """Test search raises SearchConnectionError on connection failure."""
        error = OSConnectionError("Connection refused")
        mock_client.search.side_effect = error

        query = SearchQuery(query={"match_all": {}})
        with pytest.raises(SearchConnectionError) as exc_info:
            provider.search("test-index", query)

        assert "Failed to connect to OpenSearch" in str(exc_info.value)

    def test_create_document_connection_error(self, provider, mock_client):
        """Test create raises SearchConnectionError on connection failure."""
        error = OSConnectionError("Connection timeout")
        mock_client.index.side_effect = error

        with pytest.raises(SearchConnectionError) as exc_info:
            provider.create("test-index", {"title": "Test"})

        assert "Failed to connect to OpenSearch" in str(exc_info.value)

    def test_create_document_conflict_error(self, provider, mock_client):
        """Test create handles version conflicts."""
        mock_client.index.side_effect = ConflictError(409, "version_conflict", {"error": "Version conflict"})

        with pytest.raises(SearchServiceError) as exc_info:
            provider.create("test-index", {"title": "Test"}, "doc-123")

        assert "version conflict" in str(exc_info.value).lower()

    def test_bulk_create_partial_failure(self, provider, mock_client):
        """Test bulk create returns partial results on failure."""
        with patch("textlayer.core.services.search.providers.opensearch.helpers.bulk") as mock_bulk:
            mock_bulk.return_value = (1, [{"index": {"_id": "2", "error": "Document too large"}}])

            documents = [{"id": "1", "title": "Doc 1"}, {"id": "2", "title": "Doc 2"}]
            result = provider.bulk_create("test-index", documents)

            assert result.success_count == 1
            assert result.failed_count == 1
            assert len(result.errors) == 1
            assert result.errors[0]["index"]["error"] == "Document too large"

    def test_bulk_create_request_error(self, provider, mock_client):
        """Test bulk create handles RequestError by returning failure result."""
        with patch("textlayer.core.services.search.providers.opensearch.helpers.bulk") as mock_bulk:
            mock_bulk.side_effect = RequestError(400, "bulk_error", {"error": "Bulk operation failed"})

            documents = [{"id": "1", "title": "Doc 1"}, {"id": "2", "title": "Doc 2"}]
            result = provider.bulk_create("test-index", documents)

            assert result.success_count == 0
            assert result.failed_count == 2
            assert len(result.errors) == 1
            assert "request_error" in result.errors[0]["type"]

    def test_delete_document_not_found(self, provider, mock_client):
        """Test delete returns None for non-existent document."""
        mock_client.delete.side_effect = NotFoundError(404, "not_found", {"error": "Document not found"})

        result = provider.delete("test-index", "non-existent-doc")

        assert result is None

    def test_get_by_id_index_not_found(self, provider, mock_client):
        """Test get_by_id raises IndexNotFoundError when index doesn't exist."""
        error_info = {"error": {"type": "index_not_found_exception"}}
        mock_client.get.side_effect = RequestError(404, "index_not_found_exception", error_info)

        with pytest.raises(IndexNotFoundError) as exc_info:
            provider.get_by_id("non-existent-index", "doc-123")

        assert exc_info.value.index == "non-existent-index"

    def test_create_index_already_exists(self, provider, mock_client):
        """Test create_index raises IndexAlreadyExistsError for existing index."""
        error_info = {
            "error": {
                "type": "resource_already_exists_exception",
                "reason": "Index already exists",
            }
        }
        mock_client.indices.create.side_effect = RequestError(400, "resource_already_exists_exception", error_info)

        config = IndexConfig(name="existing-index")
        with pytest.raises(IndexAlreadyExistsError) as exc_info:
            provider.create_index(config)

        assert exc_info.value.index == "existing-index"

    def test_index_name_validation(self, provider):
        """Test that invalid index names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            provider.search("UPPERCASE", SearchQuery(query={"match_all": {}}))

        assert "must be lowercase" in str(exc_info.value)

    def test_document_id_validation(self, provider):
        """Test that invalid document IDs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            provider.get_by_id("test-index", "")

        assert "Document ID cannot be empty" in str(exc_info.value)

    def test_search_query_validation(self, provider):
        """Test that invalid queries are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            provider.search("test-index", {"query": None})

        assert "Query cannot be empty" in str(exc_info.value)

    def test_update_by_query_validation(self, provider):
        """Test update_by_query validates update structure."""
        query = SearchQuery(query={"match_all": {}})

        with pytest.raises(ValidationError) as exc_info:
            provider.update_by_query("test-index", query, {})

        assert "must contain either 'source' or 'script'" in str(exc_info.value)
