from unittest.mock import Mock, patch

import pytest
from opensearchpy import ConnectionError as OSConnectionError
from opensearchpy import NotFoundError

from isw.core.services.search import (
    IndexConfig,
    IndexNotFoundError,
    SearchConnectionError,
    SearchQuery,
    SearchService,
)


class TestSearchIntegration:
    """Integration tests for search service error scenarios."""

    @pytest.fixture
    def mock_opensearch_client(self):
        """Create a mock OpenSearch client for integration testing."""
        return Mock()

    @pytest.fixture
    def search_service(self, mock_opensearch_client):
        """Create search service with mocked OpenSearch client."""
        with patch(
            "isw.core.services.search.providers.opensearch.OpenSearch", return_value=mock_opensearch_client
        ):
            with patch("isw.core.services.search.providers.opensearch.config") as mock_config:
                mock_config.return_value.opensearch_host = "http://localhost:9200"
                mock_config.return_value.opensearch_username = "test"
                mock_config.return_value.opensearch_password = "test"
                mock_config.return_value.search_provider = "opensearch"
                return SearchService(provider="opensearch")

    def test_search_with_non_existent_index(self, search_service, mock_opensearch_client):
        """Test searching in non-existent index raises appropriate error."""
        mock_opensearch_client.search.side_effect = NotFoundError(
            404, "index_not_found_exception", {"error": {"type": "index_not_found_exception"}}
        )

        query = SearchQuery(query={"match": {"title": "test"}})

        with pytest.raises(IndexNotFoundError) as exc_info:
            search_service.search("non-existent-index", query)

        assert exc_info.value.index == "non-existent-index"

    def test_connection_failure_handling(self, search_service, mock_opensearch_client):
        """Test that connection failures are properly handled."""
        mock_opensearch_client.search.side_effect = OSConnectionError("Connection refused to localhost:9200")

        query = SearchQuery(query={"match_all": {}})

        with pytest.raises(SearchConnectionError) as exc_info:
            search_service.search("test-index", query)

        assert "Failed to connect to OpenSearch" in str(exc_info.value)

    def test_create_then_search_workflow(self, search_service, mock_opensearch_client):
        """Test creating a document and then searching for it."""
        mock_opensearch_client.index.return_value = {
            "_index": "products",
            "_id": "prod-123",
            "_version": 1,
            "result": "created",
        }

        doc = {"name": "Test Product", "price": 99.99, "category": "Electronics"}
        create_result = search_service.create_document("products", doc, "prod-123")
        assert create_result["result"] == "created"

        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "prod-123",
                        "_score": 1.0,
                        "_source": doc,
                        "_index": "products",
                    }
                ],
            },
            "took": 5,
        }

        query = SearchQuery(query={"match": {"name": "Test Product"}})
        search_result = search_service.search("products", query)

        assert search_result.total == 1
        assert search_result.hits[0].id == "prod-123"
        assert search_result.hits[0].source["name"] == "Test Product"

    def test_index_lifecycle(self, search_service, mock_opensearch_client):
        """Test complete index lifecycle: create, check exists, delete."""
        index_name = "test-lifecycle-index"

        mock_opensearch_client.indices.create.return_value = {"acknowledged": True, "index": index_name}

        config = IndexConfig(
            name=index_name,
            settings={"number_of_shards": 1},
            mappings={"properties": {"title": {"type": "text"}}},
        )
        create_result = search_service.create_index(config)
        assert create_result["acknowledged"] is True

        mock_opensearch_client.indices.exists.return_value = True

        exists = search_service.index_exists(index_name)
        assert exists is True

        mock_opensearch_client.indices.delete.return_value = {"acknowledged": True}

        delete_result = search_service.delete_index(index_name)
        assert delete_result is True

        mock_opensearch_client.indices.create.assert_called_once()
        mock_opensearch_client.indices.exists.assert_called_once()
        mock_opensearch_client.indices.delete.assert_called_once()
