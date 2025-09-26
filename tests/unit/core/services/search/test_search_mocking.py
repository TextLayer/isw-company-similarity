from unittest.mock import Mock

import pytest

from isw.core.services.search import SearchResult, SearchResultItem, SearchService


class TestSearchServiceMocking:
    """Examples of mocking search service for use in other tests."""

    @pytest.fixture
    def mock_search_service(self):
        """Create a fully mocked search service."""
        service = Mock(spec=SearchService)

        service.search.return_value = SearchResult(total=0, hits=[])
        service.create_document.return_value = {"_id": "mock-id", "result": "created"}
        service.get_document.return_value = None
        service.document_exists.return_value = False
        service.index_exists.return_value = True

        return service

    def test_component_using_search(self, mock_search_service):
        """Example of testing a component that uses search service."""

        def search_products(search_service: SearchService, query: str):
            """Example function that uses search service."""
            from isw.core.services.search import SearchQuery

            search_query = SearchQuery(query={"match": {"name": query}})
            results = search_service.search("products", search_query)
            return [hit.source for hit in results.hits]

        mock_search_service.search.return_value = SearchResult(
            total=2,
            hits=[
                SearchResultItem(
                    id="1",
                    score=1.0,
                    source={"name": "Product 1", "price": 10.0},
                    index="products",
                ),
                SearchResultItem(
                    id="2",
                    score=0.8,
                    source={"name": "Product 2", "price": 20.0},
                    index="products",
                ),
            ],
        )

        results = search_products(mock_search_service, "Product")

        assert len(results) == 2
        assert results[0]["name"] == "Product 1"
        assert results[1]["price"] == 20.0

        mock_search_service.search.assert_called_once()
        call_args = mock_search_service.search.call_args
        assert call_args[0][0] == "products"  # index name
        assert call_args[0][1].query == {"match": {"name": "Product"}}  # query

    def test_error_handling_with_mock(self, mock_search_service):
        """Example of testing error handling."""
        from isw.core.services.search import IndexNotFoundError

        mock_search_service.search.side_effect = IndexNotFoundError("Index not found", index="products")

        def safe_search(search_service: SearchService, index: str, query: dict):
            """Example function with error handling."""
            from isw.core.services.search import IndexNotFoundError, SearchQuery

            try:
                search_query = SearchQuery(query=query)
                return search_service.search(index, search_query)
            except IndexNotFoundError:
                return SearchResult(total=0, hits=[])

        result = safe_search(mock_search_service, "products", {"match_all": {}})

        assert result.total == 0
        assert len(result.hits) == 0
        mock_search_service.search.assert_called_once()

    def test_bulk_operations_mock(self, mock_search_service):
        """Example of mocking bulk operations."""
        from isw.core.services.search import BulkOperationResult

        mock_search_service.bulk_create_documents.return_value = BulkOperationResult(
            success_count=95,
            errors=[
                {"index": {"_id": "96", "error": "Document too large"}},
                {"index": {"_id": "97", "error": "Invalid field"}},
            ],
            failed_count=2,
            total_count=97,
        )

        def bulk_import_products(search_service: SearchService, products: list):
            """Example function that does bulk import."""
            result = search_service.bulk_create_documents("products", products)

            if result.failed_count > 0:
                print(f"Warning: {result.failed_count} documents failed to import")
                for error in result.errors:
                    print(f"  - Error: {error}")

            return result.success_count

        products = [{"id": str(i), "name": f"Product {i}"} for i in range(97)]
        success_count = bulk_import_products(mock_search_service, products)

        assert success_count == 95
        mock_search_service.bulk_create_documents.assert_called_once_with("products", products)
