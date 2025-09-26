from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from isw.core.services.search.types import (
    BulkOperationResult,
    IndexConfig,
    SearchQuery,
    SearchResult,
    TermVector,
)
from isw.core.utils.factory import GenericProviderFactory


class SearchProvider(ABC):
    """Base class for search providers."""

    @abstractmethod
    def search(self, index: str, query: SearchQuery) -> SearchResult:
        """
        Search for documents in the specified index.

        Args:
            index: Index to search in
            query: Search query parameters

        Returns:
            SearchResult containing matching documents
        """
        pass

    @abstractmethod
    def create(self, index: str, document: Dict[str, Any], document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update a document in the index.

        Args:
            index: Index to create document in
            document: Document data
            document_id: Optional document ID (auto-generated if not provided)

        Returns:
            Response containing document metadata
        """
        pass

    @abstractmethod
    def bulk_create(
        self, index: str, documents: List[Dict[str, Any]], request_timeout: int = 180
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
        pass

    @abstractmethod
    def update(
        self,
        index: str,
        document_id: str,
        document: Optional[Dict[str, Any]] = None,
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
        pass

    @abstractmethod
    def bulk_update(self, index: str, updates: List[Dict[str, Any]], request_timeout: int = 180) -> BulkOperationResult:
        """
        Bulk update multiple documents.

        Args:
            index: Index to update documents in
            updates: List of update operations
            request_timeout: Timeout for bulk operation

        Returns:
            BulkOperationResult with success count and errors
        """
        pass

    @abstractmethod
    def update_by_query(
        self, index: str, query: SearchQuery | Dict[str, Any], update: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update documents matching a query.

        Args:
            index: Index to update documents in
            query: Query to match documents for update
            update: Update operation

        Returns:
            Update response
        """
        pass

    @abstractmethod
    def delete(self, index: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Delete a document from the index.

        Args:
            index: Index to delete from
            document_id: ID of document to delete

        Returns:
            Delete response or None if not found
        """
        pass

    @abstractmethod
    def delete_by_query(self, index: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Delete documents matching a query.

        Args:
            index: Index to delete from
            query: Query to match documents for deletion

        Returns:
            Response with deletion count
        """
        pass

    @abstractmethod
    def get_by_id(self, index: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            index: Index to search in
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    def exists(self, index: str, document_id: str) -> bool:
        """
        Check if a document exists.

        Args:
            index: Index to check in
            document_id: Document ID

        Returns:
            True if document exists
        """
        pass

    @abstractmethod
    def get_term_vector(self, index: str, document_id: str, fields: List[str]) -> Optional[TermVector]:
        """
        Get term vector for a document.

        Args:
            index: Index containing the document
            document_id: Document ID
            fields: Fields to get term vectors for

        Returns:
            Term vector data
        """
        pass

    @abstractmethod
    def get_multi_term_vectors(self, index: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get term vectors for multiple documents.

        Args:
            index: Index to query
            query: Query for documents

        Returns:
            Term vectors for multiple documents
        """
        pass

    # Index management methods
    @abstractmethod
    def create_index(self, index_config: IndexConfig) -> Optional[Dict[str, Any]]:
        """
        Create a new index.

        Args:
            index_config: Index configuration

        Returns:
            Creation response
        """
        pass

    @abstractmethod
    def delete_index(self, index: str) -> bool:
        """
        Delete an index.

        Args:
            index: Index name to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def index_exists(self, index: str) -> bool:
        """
        Check if an index exists.

        Args:
            index: Index name

        Returns:
            True if index exists
        """
        pass

    @abstractmethod
    def get_index_info(self, index: str) -> Optional[Dict[str, Any]]:
        """
        Get index information.

        Args:
            index: Index name

        Returns:
            Index metadata
        """
        pass

    @abstractmethod
    def update_index_mapping(self, index: str, mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update index mapping.

        Args:
            index: Index name
            mapping: New mapping configuration

        Returns:
            Update response
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        pass

    @abstractmethod
    def did_create(self, response: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def did_update(self, response: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def did_delete(self, response: Dict[str, Any]) -> bool:
        pass


SearchProviderFactory = GenericProviderFactory[SearchProvider]("Search")
