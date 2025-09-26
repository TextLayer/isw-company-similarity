from isw.core.services.search.exceptions import (
    BulkOperationError,
    DocumentNotFoundError,
    IndexAlreadyExistsError,
    IndexNotFoundError,
    SearchConnectionError,
    SearchQueryError,
    SearchServiceError,
    ValidationError,
)
from isw.core.services.search.service import SearchService
from isw.core.services.search.types import (
    BulkOperationResult,
    Document,
    DocumentId,
    IndexConfig,
    IndexName,
    SearchQuery,
    SearchResult,
    SearchResultItem,
    TermVector,
)

__all__ = [
    "SearchService",
    # Types
    "SearchQuery",
    "SearchResult",
    "SearchResultItem",
    "BulkOperationResult",
    "IndexConfig",
    "TermVector",
    "Document",
    "DocumentId",
    "IndexName",
    # Exceptions
    "SearchServiceError",
    "SearchConnectionError",
    "SearchQueryError",
    "IndexNotFoundError",
    "IndexAlreadyExistsError",
    "DocumentNotFoundError",
    "BulkOperationError",
    "ValidationError",
]
