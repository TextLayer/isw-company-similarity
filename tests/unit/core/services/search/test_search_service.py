from unittest.mock import Mock, patch

import pytest

from isw.core.services.search import (
    BulkOperationResult,
    IndexConfig,
    SearchQuery,
    SearchResult,
    SearchResultItem,
    SearchService,
)
from isw.core.services.search.exceptions import IndexNotFoundError
from isw.core.services.search.providers import SearchProvider, SearchProviderFactory
from isw.shared.config import set_config
from isw.shared.config.base import BaseConfig


class TestSearchService:
    """Unit tests for search service."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock search provider."""
        provider = Mock(spec=SearchProvider)
        provider.get_provider_name.return_value = "mock"
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        """Create search service with mocked provider."""
        with patch.object(SearchProviderFactory, "create", return_value=mock_provider):
            return SearchService(provider="mock")

    def test_search_returns_results(self, service, mock_provider):
        """Test search returns SearchResult with hits."""
        mock_provider.search.return_value = SearchResult(
            total=2,
            hits=[
                SearchResultItem(id="1", score=1.0, source={"title": "Test 1"}, index="test-index"),
                SearchResultItem(id="2", score=0.8, source={"title": "Test 2"}, index="test-index"),
            ],
            took_ms=10,
        )

        query = SearchQuery(query={"match": {"title": "test"}})
        result = service.search("test-index", query)

        assert result.total == 2
        assert len(result.hits) == 2
        assert result.hits[0].id == "1"
        assert result.hits[0].source["title"] == "Test 1"
        mock_provider.search.assert_called_once_with("test-index", query)

    def test_create_document_success(self, service, mock_provider):
        """Test successful document creation."""
        mock_provider.create.return_value = {
            "_index": "test-index",
            "_id": "doc-123",
            "_version": 1,
            "result": "created",
        }

        document = {"title": "Test Document", "content": "Some content"}
        result = service.create_document("test-index", document, "doc-123")

        assert result["_id"] == "doc-123"
        assert result["result"] == "created"
        mock_provider.create.assert_called_once_with("test-index", document, "doc-123")

    def test_bulk_create_documents_success(self, service, mock_provider):
        """Test successful bulk document creation."""
        mock_provider.bulk_create.return_value = BulkOperationResult(
            success_count=3, errors=[], failed_count=0, total_count=3
        )

        documents = [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
            {"id": "3", "title": "Doc 3"},
        ]
        result = service.bulk_create_documents("test-index", documents)

        assert result.success_count == 3
        assert result.failed_count == 0
        assert len(result.errors) == 0
        mock_provider.bulk_create.assert_called_once()

    def test_bulk_create_with_failures(self, service, mock_provider):
        """Test bulk creation with partial failures."""
        mock_provider.bulk_create.return_value = BulkOperationResult(
            success_count=2,
            errors=[{"index": {"_id": "3", "error": {"type": "validation_error"}}}],
            failed_count=1,
            total_count=3,
        )

        documents = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        result = service.bulk_create_documents("test-index", documents)

        assert result.success_count == 2
        assert result.failed_count == 1
        assert len(result.errors) == 1

    def test_update_document_success(self, service, mock_provider):
        """Test successful document update."""
        mock_provider.update.return_value = {
            "_index": "test-index",
            "_id": "doc-123",
            "_version": 2,
            "result": "updated",
        }

        update = {"title": "Updated Title"}
        result = service.update_document("test-index", "doc-123", update)

        assert result["result"] == "updated"
        mock_provider.update.assert_called_once_with("test-index", "doc-123", update, None, None)

    def test_delete_document_success(self, service, mock_provider):
        """Test successful document deletion."""
        mock_provider.delete.return_value = {
            "_index": "test-index",
            "_id": "doc-123",
            "result": "deleted",
        }

        result = service.delete_document("test-index", "doc-123")

        assert result["result"] == "deleted"
        mock_provider.delete.assert_called_once_with("test-index", "doc-123")

    def test_get_document_found(self, service, mock_provider):
        """Test getting existing document."""
        mock_provider.get_by_id.return_value = {
            "_index": "test-index",
            "_id": "doc-123",
            "_source": {"title": "Test Document"},
        }

        result = service.get_document("test-index", "doc-123")

        assert result["_id"] == "doc-123"
        assert result["_source"]["title"] == "Test Document"
        mock_provider.get_by_id.assert_called_once_with("test-index", "doc-123")

    def test_get_document_not_found(self, service, mock_provider):
        """Test getting non-existent document."""
        mock_provider.get_by_id.return_value = None

        result = service.get_document("test-index", "doc-123")

        assert result is None
        mock_provider.get_by_id.assert_called_once_with("test-index", "doc-123")

    def test_document_exists_true(self, service, mock_provider):
        """Test checking if document exists."""
        mock_provider.exists.return_value = True

        result = service.document_exists("test-index", "doc-123")

        assert result is True
        mock_provider.exists.assert_called_once_with("test-index", "doc-123")

    def test_create_index_success(self, service, mock_provider):
        """Test successful index creation."""
        mock_provider.create_index.return_value = {"acknowledged": True, "index": "test-index"}

        config = IndexConfig(
            name="test-index",
            settings={"number_of_shards": 1},
            mappings={"properties": {"title": {"type": "text"}}},
        )
        result = service.create_index(config)

        assert result["acknowledged"] is True
        mock_provider.create_index.assert_called_once_with(config)

    def test_delete_index_success(self, service, mock_provider):
        """Test successful index deletion."""
        mock_provider.delete_index.return_value = True

        result = service.delete_index("test-index")

        assert result is True
        mock_provider.delete_index.assert_called_once_with("test-index")

    def test_index_exists_check(self, service, mock_provider):
        """Test checking if index exists."""
        mock_provider.index_exists.return_value = True

        result = service.index_exists("test-index")

        assert result is True
        mock_provider.index_exists.assert_called_once_with("test-index")

    def test_search_handles_provider_errors(self, service, mock_provider):
        """Test that service propagates provider exceptions."""
        mock_provider.search.side_effect = IndexNotFoundError("Index not found", index="test-index")

        query = SearchQuery(query={"match_all": {}})
        with pytest.raises(IndexNotFoundError) as exc_info:
            service.search("test-index", query)

        assert exc_info.value.index == "test-index"

    @patch("textlayer.shared.config.config")
    def test_uses_config_defaults(self, mock_config):
        """Test service uses config for default provider."""
        mock_config.return_value.search_provider = "opensearch"

        test_config = BaseConfig.from_env()
        set_config(test_config)

        with patch.object(SearchProviderFactory, "create") as mock_create:
            SearchService()
            mock_create.assert_called_once_with("opensearch")
