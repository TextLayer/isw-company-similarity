from typing import Any, Dict, List, Optional

from opensearchpy import ConflictError, NotFoundError, OpenSearch, RequestError, helpers
from opensearchpy import ConnectionError as OSConnectionError

from isw.core.services.search.exceptions import (
    IndexAlreadyExistsError,
    IndexNotFoundError,
    SearchConnectionError,
    SearchQueryError,
    SearchServiceError,
    ValidationError,
)
from isw.core.services.search.providers.base import SearchProvider, SearchProviderFactory
from isw.core.services.search.types import (
    BulkOperationResult,
    IndexConfig,
    SearchQuery,
    SearchResult,
    SearchResultItem,
    TermVector,
)
from isw.core.services.search.validation import (
    validate_document_id,
    validate_index_name,
    validate_search_query,
)
from isw.shared.config import config
from isw.shared.logging.logger import logger


def _get_error_message(err: Exception) -> str:
    """Extract error message from exception, handling special cases."""
    try:
        return str(err)
    except Exception as e:
        logger.error(f"Failed to convert exception to string: {e!r}")
        # Handle cases where str() fails (e.g., opensearchpy.ConnectionError)
        if hasattr(err, "args") and err.args:
            try:
                return str(err.args[0])
            except Exception as e2:
                logger.error(f"Failed to convert exception args to string: {e2!r}")


class OpenSearchProvider(SearchProvider):
    """OpenSearch implementation of SearchProvider."""

    def __init__(
        self,
        host: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize OpenSearch provider.

        Args:
            host: OpenSearch host URL
            username: OpenSearch username
            password: OpenSearch password
            **kwargs: Additional OpenSearch client options
        """
        self.host = host or config().opensearch_host
        self.username = username or config().opensearch_username
        self.password = password or config().opensearch_password

        if not all([self.host, self.username, self.password]):
            raise ValueError("OpenSearch host, username, and password are required")

        self.client = OpenSearch(
            hosts=[self.host],
            http_auth=(self.username, self.password),
            **kwargs,
        )
        logger.info(f"Connected to OpenSearch at {self.host}")

    def search(self, index: str, query: SearchQuery | Dict[str, Any]) -> SearchResult:
        """Search for documents in the specified index."""
        validate_index_name(index)
        query = validate_search_query(query)

        try:
            body = {"query": query.query}
            if query.size:
                body["size"] = query.size
            if query.from_:
                body["from"] = query.from_
            if query.sort:
                body["sort"] = query.sort
            if query.aggregations:
                body["aggs"] = query.aggregations
            if query.highlight:
                body["highlight"] = query.highlight
            if query.source_includes or query.source_excludes:
                body["_source"] = {}
                if query.source_includes:
                    body["_source"]["includes"] = query.source_includes
                if query.source_excludes:
                    body["_source"]["excludes"] = query.source_excludes

            response = self.client.search(index=index, body=body)

            # Parse response
            hits = []
            for hit in response.get("hits", {}).get("hits", []):
                item = SearchResultItem(
                    id=hit["_id"],
                    score=hit.get("_score", 0.0),
                    source=hit["_source"],
                    index=hit["_index"],
                    highlights=hit.get("highlight"),
                )
                hits.append(item)

            return SearchResult(
                total=response.get("hits", {}).get("total", {}).get("value", 0),
                hits=hits,
                aggregations=response.get("aggregations"),
                took_ms=response.get("took"),
            )
        except NotFoundError as err:
            logger.error(f"Index not found: '{index}'")
            raise IndexNotFoundError(f"Index '{index}' not found", index=index, details={"error": str(err)}) from err
        except RequestError as err:
            logger.error(f"Request error when searching in index '{index}': {err}")
            # Parse the error to provide more specific information
            if hasattr(err, "info") and isinstance(err.info, dict):
                error_type = err.info.get("error", {}).get("type", "")
                error_reason = err.info.get("error", {}).get("reason", str(err))
                if "parsing_exception" in error_type or "query_shard_exception" in error_type:
                    raise SearchQueryError(f"Invalid query: {error_reason}", details={"error": err.info}) from err
            raise SearchServiceError(f"Search failed: {str(err)}", details={"error": str(err)}) from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while searching: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err
        except Exception as err:
            logger.error(f"Unexpected error during search: {err}")
            raise SearchServiceError(f"Unexpected error during search: {str(err)}") from err

    def create(self, index: str, document: Dict[str, Any], document_id: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a document in the index."""
        validate_index_name(index)
        if document_id:
            validate_document_id(document_id)

        if not isinstance(document, dict):
            raise ValidationError(f"Document must be a dictionary, got {type(document).__name__}")

        try:
            response = self.client.index(index=index, id=document_id, body=document)
            document_id_str = document_id or response["_id"]
            operation = "updated" if document_id else "created"
            logger.info(f"Document {operation} in index '{index}' (ID: {document_id_str})")
            return response
        except NotFoundError as err:
            logger.error(f"Index not found: '{index}'")
            raise IndexNotFoundError(f"Index '{index}' not found", index=index) from err
        except ConflictError as err:
            logger.error(f"Document version conflict for ID '{document_id}' in index '{index}'")
            raise SearchServiceError(f"Document version conflict: {str(err)}") from err
        except RequestError as err:
            logger.error(f"Failed to create/update document in index '{index}': {err}")
            raise SearchServiceError(f"Failed to create document: {str(err)}") from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while creating document: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err

    def bulk_create(
        self, index: str, documents: List[Dict[str, Any]], request_timeout: int = 180
    ) -> BulkOperationResult:
        """Bulk create multiple documents."""
        validate_index_name(index)

        if not documents:
            logger.warning(f"No documents provided for bulk insert into index '{index}'")
            return BulkOperationResult(success_count=0, errors=[], total_count=0)

        if not isinstance(documents, list):
            raise ValidationError(f"Documents must be a list, got {type(documents).__name__}")

        bulk_actions = []
        for doc in documents:
            if "id" in doc:
                action = {"_index": index, "_id": doc["id"], "_source": doc}
            else:
                action = {"_index": index, "_source": doc}
            bulk_actions.append(action)

        try:
            success_count, errors = helpers.bulk(self.client, bulk_actions, request_timeout=request_timeout)
            logger.info(f"Bulk insert: {success_count} documents added to index '{index}'")

            if errors:
                logger.warning(f"Bulk insert into '{index}' completed with {len(errors)} errors")

            return BulkOperationResult(
                success_count=success_count,
                errors=errors,
                failed_count=len(errors),
                total_count=len(documents),
            )
        except RequestError as err:
            logger.error(f"Bulk insert failed for index '{index}': {err}")
            # Return partial success if some documents were indexed
            return BulkOperationResult(
                success_count=0,
                errors=[{"error": str(err), "type": "request_error"}],
                failed_count=len(documents),
                total_count=len(documents),
            )
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error during bulk insert: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err
        except Exception as err:
            logger.error(f"Unexpected error during bulk create: {err}")
            raise SearchServiceError(f"Bulk operation failed: {str(err)}") from err

    def update(
        self,
        index: str,
        document_id: str,
        document: Optional[Dict[str, Any]] = None,
        script: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a document in the index."""
        update_body = {}

        if document:
            update_body["doc"] = document

        if script:
            update_body["script"] = {"source": script, "lang": "painless"}
            if params:
                update_body["script"]["params"] = params

        try:
            response = self.client.update(index=index, id=document_id, body=update_body, retry_on_conflict=3)
            logger.info(f"Document with ID '{document_id}' updated in index '{index}'")
            return response
        except NotFoundError:
            logger.warning(f"Document with ID '{document_id}' not found in index '{index}'")
            return None
        except RequestError as err:
            logger.error(f"Failed to update document '{document_id}' in index '{index}': {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while updating document '{document_id}': {error_msg}")
            raise

    def bulk_update(self, index: str, updates: List[Dict[str, Any]], request_timeout: int = 180) -> BulkOperationResult:
        """Bulk update multiple documents."""
        if not updates:
            logger.warning(f"No updates provided for bulk update in index '{index}'")
            return BulkOperationResult(success_count=0, errors=[], total_count=0)

        bulk_actions = []
        for update in updates:
            if "id" not in update:
                logger.warning("Update missing 'id' field, skipping")
                continue

            action = {
                "_op_type": "update",
                "_index": index,
                "_id": update["id"],
            }

            if "doc" in update:
                action["doc"] = update["doc"]
            if "script" in update:
                action["script"] = update["script"]

            bulk_actions.append(action)

        try:
            success_count, errors = helpers.bulk(self.client, bulk_actions, request_timeout=request_timeout)
            logger.info(f"Bulk update: {success_count} documents updated in index '{index}'")

            if errors:
                logger.warning(f"Bulk update in '{index}' completed with {len(errors)} errors")

            return BulkOperationResult(
                success_count=success_count,
                errors=errors,
                failed_count=len(errors),
                total_count=len(updates),
            )
        except RequestError as err:
            logger.error(f"Bulk update failed for index '{index}': {err}")
            raise
        except OSConnectionError as err:
            logger.error(f"OpenSearch connection error during bulk update in index '{index}': {err}")
            raise

    def update_by_query(
        self, index: str, query: SearchQuery | Dict[str, Any], update: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update documents matching a query."""
        validate_index_name(index)
        query = validate_search_query(query)

        if not isinstance(update, dict):
            raise ValidationError(f"Update must be a dictionary, got {type(update).__name__}")

        if "source" not in update and "script" not in update:
            raise ValidationError("Update must contain either 'source' or 'script' field")

        try:
            response = self.client.update_by_query(index=index, body={"query": query.query, "script": update})
            logger.info(f"Updated {response.get('updated', 0)} documents in index '{index}' using query")
            return response
        except RequestError as err:
            logger.error(f"Failed to update documents in index '{index}' with query {query}: {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while updating documents in index '{index}': {error_msg}")
            raise

    def delete(self, index: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Delete a document from the index."""
        validate_index_name(index)
        validate_document_id(document_id)

        try:
            response = self.client.delete(index=index, id=document_id)
            logger.info(f"Document with ID '{document_id}' deleted from index '{index}'")
            return response
        except NotFoundError:
            logger.debug(f"Document with ID '{document_id}' not found in index '{index}'")
            return None
        except RequestError as err:
            logger.error(f"Failed to delete document with ID '{document_id}': {err}")
            if hasattr(err, "info") and "index_not_found_exception" in str(err.info):
                raise IndexNotFoundError(f"Index '{index}' not found", index=index) from err
            raise SearchServiceError(f"Failed to delete document: {str(err)}") from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while deleting document: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err

    def delete_by_query(self, index: str, query: SearchQuery | Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Delete documents matching a query."""
        validate_index_name(index)
        query = validate_search_query(query)

        try:
            response = self.client.delete_by_query(index=index, body={"query": query.query})
            deleted_count = response.get("deleted", 0)
            logger.info(f"Deleted {deleted_count} documents from index '{index}' using query")
            return response
        except RequestError as err:
            logger.error(f"Failed to delete documents in index '{index}' with query {query}: {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while deleting by query in index '{index}': {error_msg}")
            raise

    def get_by_id(self, index: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        validate_index_name(index)
        validate_document_id(document_id)

        try:
            document = self.client.get(index=index, id=document_id)
            logger.info(f"Retrieved document '{document_id}' from index '{index}'")
            return document
        except NotFoundError:
            logger.debug(f"Document '{document_id}' not found in index '{index}'")
            return None
        except RequestError as err:
            logger.error(f"Request error when retrieving document '{document_id}': {err}")
            if hasattr(err, "info") and "index_not_found_exception" in str(err.info):
                raise IndexNotFoundError(f"Index '{index}' not found", index=index) from err
            raise SearchServiceError(f"Failed to retrieve document: {str(err)}") from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while retrieving document: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err

    def exists(self, index: str, document_id: str) -> bool:
        """Check if a document exists."""
        validate_index_name(index)
        validate_document_id(document_id)

        try:
            exists = self.client.exists(index=index, id=document_id)
            logger.debug(f"Document '{document_id}' exists in index '{index}': {exists}")
            return exists
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while checking document existence: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err
        except RequestError as err:
            logger.error(f"Request error when checking document existence: {err}")
            if hasattr(err, "info") and "index_not_found_exception" in str(err.info):
                raise IndexNotFoundError(f"Index '{index}' not found", index=index) from err
            raise SearchServiceError(f"Failed to check document existence: {str(err)}") from err

    def get_term_vector(self, index: str, document_id: str, fields: List[str]) -> Optional[TermVector]:
        """Get term vector for a document."""
        try:
            response = self.client.termvectors(index=index, id=document_id, fields=fields, term_statistics=True)
            logger.info(f"Retrieved term vector for document '{document_id}' in index '{index}'")

            # Parse the response into TermVector
            terms = {}
            for field, field_data in response.get("term_vectors", {}).items():
                terms[field] = field_data.get("terms", {})

            return TermVector(
                terms=terms,
                field_statistics=response.get("term_vectors", {}).get("field_statistics"),
                document_count=response.get("_index", {}).get("doc_count"),
            )
        except NotFoundError:
            logger.warning(f"Document '{document_id}' not found in index '{index}' for term vector retrieval")
            return None
        except RequestError as err:
            logger.error(f"Request error when retrieving term vector for document '{document_id}': {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(
                f"OpenSearch connection error while retrieving term vector for document '{document_id}': {error_msg}"
            )
            raise

    def get_multi_term_vectors(self, index: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get term vectors for multiple documents."""
        try:
            response = self.client.mtermvectors(index=index, body=query)
            logger.info("Retrieved term vectors for multiple documents")
            return response
        except RequestError as err:
            logger.error(f"Request error when retrieving multiple term vectors: {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while retrieving multiple term vectors: {error_msg}")
            raise

    def create_index(self, index_config: IndexConfig) -> Optional[Dict[str, Any]]:
        """Create a new index."""
        validate_index_name(index_config.name)

        try:
            body = {
                "settings": index_config.settings,
                "mappings": index_config.mappings,
            }
            if index_config.aliases:
                body["aliases"] = index_config.aliases

            response = self.client.indices.create(index=index_config.name, body=body)
            logger.info(f"Index '{index_config.name}' created successfully")
            return response
        except RequestError as err:
            logger.error(f"Failed to create index '{index_config.name}': {err}")
            if hasattr(err, "info") and err.info:
                error_type = err.info.get("error", {}).get("type", "")
                if "resource_already_exists_exception" in error_type:
                    raise IndexAlreadyExistsError(
                        f"Index '{index_config.name}' already exists",
                        index=index_config.name,
                        details={"error": err.info},
                    ) from err
            raise SearchServiceError(f"Failed to create index: {str(err)}") from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while creating index: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err

    def delete_index(self, index: str) -> bool:
        """Delete an index."""
        validate_index_name(index)

        try:
            self.client.indices.delete(index=index)
            logger.info(f"Index '{index}' deleted successfully")
            return True
        except NotFoundError:
            logger.debug(f"Index '{index}' not found for deletion")
            return False
        except RequestError as err:
            logger.error(f"Failed to delete index '{index}': {err}")
            raise SearchServiceError(f"Failed to delete index: {str(err)}") from err
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while deleting index: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err

    def index_exists(self, index: str) -> bool:
        """Check if an index exists."""
        validate_index_name(index)

        try:
            exists = self.client.indices.exists(index=index)
            logger.debug(f"Index '{index}' exists: {exists}")
            return exists
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"Connection error while checking index existence: {error_msg}")
            raise SearchConnectionError(f"Failed to connect to OpenSearch: {error_msg}") from err
        except RequestError as err:
            logger.error(f"Request error when checking index existence '{index}': {err}")
            raise SearchServiceError(f"Failed to check index existence: {str(err)}") from err

    def get_index_info(self, index: str) -> Optional[Dict[str, Any]]:
        """Get index information."""
        try:
            info = self.client.indices.get(index=index)
            logger.info(f"Retrieved info for index '{index}'")
            return info
        except NotFoundError:
            logger.warning(f"Index '{index}' not found")
            return None
        except RequestError as err:
            logger.error(f"Request error when getting index info '{index}': {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while getting index info '{index}': {error_msg}")
            raise

    def update_index_mapping(self, index: str, mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update index mapping."""
        try:
            response = self.client.indices.put_mapping(index=index, body=mapping)
            logger.info(f"Updated mapping for index '{index}'")
            return response
        except NotFoundError:
            logger.warning(f"Index '{index}' not found for mapping update")
            return None
        except RequestError as err:
            logger.error(f"Failed to update mapping for index '{index}': {err}")
            raise
        except OSConnectionError as err:
            error_msg = _get_error_message(err)
            logger.error(f"OpenSearch connection error while updating mapping for index '{index}': {error_msg}")
            raise

    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        return "opensearch"

    def did_create(self, response: Dict[str, Any]) -> bool:
        """Check if the create was successful."""
        return response.get("result") == "created"

    def did_update(self, response: Dict[str, Any]) -> bool:
        """Check if the update was successful."""
        return response.get("result") == "updated" or response.get("result") == "noop"

    def did_delete(self, response: Dict[str, Any]) -> bool:
        """Check if the delete was successful."""
        return response.get("result") == "deleted"


# Register the provider
SearchProviderFactory.register("opensearch", OpenSearchProvider)
