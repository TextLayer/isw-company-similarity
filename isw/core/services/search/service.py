from typing import Any, Dict, List, Optional

from isw.core.services.search.providers import SearchProviderFactory
from isw.core.services.search.types import (
    BulkOperationResult,
    Document,
    DocumentId,
    IndexConfig,
    IndexName,
    SearchQuery,
    SearchResult,
    TermVector,
)
from isw.shared.config import config
from isw.shared.logging.logger import logger


class SearchService:
    """Search service that delegates to configured provider."""

    def __init__(self, provider: Optional[str] = None, **provider_kwargs):
        """
        Initialize search service.

        Args:
            provider: Search provider to use (defaults to config)
            **provider_kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider or config().search_provider
        self.provider = SearchProviderFactory.create(self.provider_name, **provider_kwargs)

    def search(self, index: IndexName, query: SearchQuery) -> SearchResult:
        """
        Search for documents in the specified index.

        Args:
            index: Index to search in
            query: Search query parameters

        Returns:
            SearchResult containing matching documents
        """

        return self.provider.search(index, query)

    def create_document(
        self, index: IndexName, document: Document, document_id: Optional[DocumentId] = None
    ) -> Dict[str, Any]:
        """
        Create or update a document in the index.

        Args:
            index: Index to create document in
            document: Document data
            document_id: Optional document ID (auto-generated if not provided)

        Returns:
            Response containing document metadata
        """
        logger.info(f"Creating document in index '{index}' via {self.provider_name}")
        return self.provider.create(index, document, document_id)

    def bulk_create_documents(
        self, index: IndexName, documents: List[Document], request_timeout: int = 180
    ) -> BulkOperationResult:
        """
        Bulk create multiple documents.

        Args:
            index: Index to create documents in
            documents: List of documents to create
            request_timeout: Timeout for bulk operation

        Returns:
            BulkOperationResult with success count and errors
        """
        logger.info(f"Bulk creating {len(documents)} documents in index '{index}' via {self.provider_name}")
        return self.provider.bulk_create(index, documents, request_timeout)

    def update_document(
        self,
        index: IndexName,
        document_id: DocumentId,
        document: Optional[Document] = None,
        script: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a document in the index.

        Args:
            index: Index containing the document
            document_id: ID of document to update
            document: Partial document for update
            script: Painless script for update
            params: Parameters for script

        Returns:
            Updated document response or None if not found
        """
        logger.info(f"Updating document '{document_id}' in index '{index}' via {self.provider_name}")
        return self.provider.update(index, document_id, document, script, params)

    def bulk_update_documents(
        self, index: IndexName, updates: List[Dict[str, Any]], request_timeout: int = 180
    ) -> BulkOperationResult:
        """
        Bulk update multiple documents.

        Args:
            index: Index to update documents in
            updates: List of update operations
            request_timeout: Timeout for bulk operation

        Returns:
            BulkOperationResult with success count and errors
        """
        logger.info(f"Bulk updating {len(updates)} documents in index '{index}' via {self.provider_name}")
        return self.provider.bulk_update(index, updates, request_timeout)

    def delete_document(self, index: IndexName, document_id: DocumentId) -> Optional[Dict[str, Any]]:
        """
        Delete a document from the index.

        Args:
            index: Index to delete from
            document_id: ID of document to delete

        Returns:
            Delete response or None if not found
        """
        logger.info(f"Deleting document '{document_id}' from index '{index}' via {self.provider_name}")
        return self.provider.delete(index, document_id)

    def delete_by_query(self, index: IndexName, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Delete documents matching a query.

        Args:
            index: Index to delete from
            query: Query to match documents for deletion

        Returns:
            Response with deletion count
        """
        logger.info(f"Deleting documents by query from index '{index}' via {self.provider_name}")
        return self.provider.delete_by_query(index, query)

    def get_document(self, index: IndexName, document_id: DocumentId) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            index: Index to search in
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        logger.debug(f"Getting document '{document_id}' from index '{index}' via {self.provider_name}")
        return self.provider.get_by_id(index, document_id)

    def document_exists(self, index: IndexName, document_id: DocumentId) -> bool:
        """
        Check if a document exists.

        Args:
            index: Index to check in
            document_id: Document ID

        Returns:
            True if document exists
        """
        return self.provider.exists(index, document_id)

    # Term vector operations
    def get_term_vector(self, index: IndexName, document_id: DocumentId, fields: List[str]) -> Optional[TermVector]:
        """
        Get term vector for a document.

        Args:
            index: Index containing the document
            document_id: Document ID
            fields: Fields to get term vectors for

        Returns:
            Term vector data
        """
        logger.info(f"Getting term vector for document '{document_id}' in index '{index}' via {self.provider_name}")
        return self.provider.get_term_vector(index, document_id, fields)

    def get_multi_term_vectors(self, index: IndexName, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get term vectors for multiple documents.

        Args:
            index: Index to query
            query: Query for documents

        Returns:
            Term vectors for multiple documents
        """
        logger.info(f"Getting multiple term vectors from index '{index}' via {self.provider_name}")
        return self.provider.get_multi_term_vectors(index, query)

    # Index management operations
    def create_index(self, index_config: IndexConfig) -> Optional[Dict[str, Any]]:
        """
        Create a new index.

        Args:
            index_config: Index configuration

        Returns:
            Creation response
        """
        logger.info(f"Creating index '{index_config.name}' via {self.provider_name}")
        return self.provider.create_index(index_config)

    def delete_index(self, index: IndexName) -> bool:
        """
        Delete an index.

        Args:
            index: Index name to delete

        Returns:
            True if successful
        """
        logger.warning(f"Deleting index '{index}' via {self.provider_name}")
        return self.provider.delete_index(index)

    def index_exists(self, index: IndexName) -> bool:
        """
        Check if an index exists.

        Args:
            index: Index name

        Returns:
            True if index exists
        """
        return self.provider.index_exists(index)

    def get_index_info(self, index: IndexName) -> Optional[Dict[str, Any]]:
        """
        Get index information.

        Args:
            index: Index name

        Returns:
            Index metadata
        """
        logger.debug(f"Getting info for index '{index}' via {self.provider_name}")
        return self.provider.get_index_info(index)

    def update_index_mapping(self, index: IndexName, mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update index mapping.

        Args:
            index: Index name
            mapping: New mapping configuration

        Returns:
            Update response
        """
        logger.info(f"Updating mapping for index '{index}' via {self.provider_name}")
        return self.provider.update_index_mapping(index, mapping)

    def get_provider_name(self) -> str:
        """Get the name of the search provider."""
        return self.provider_name

    def did_create(self, response: Dict[str, Any]) -> bool:
        """Check if the create was successful."""
        return self.provider.did_create(response)

    def did_update(self, response: Dict[str, Any]) -> bool:
        """Check if the update was successful."""
        return self.provider.did_update(response)

    def did_delete(self, response: Dict[str, Any]) -> bool:
        """Check if the delete was successful."""
        return self.provider.did_delete(response)
