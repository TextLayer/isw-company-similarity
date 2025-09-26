from typing import Any, Dict, Optional


class SearchServiceError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class SearchConnectionError(SearchServiceError):
    pass


class SearchIndexError(SearchServiceError):
    def __init__(self, message: str, index: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.index = index


class IndexNotFoundError(SearchIndexError):
    pass


class IndexAlreadyExistsError(SearchIndexError):
    pass


class DocumentNotFoundError(SearchServiceError):
    def __init__(self, message: str, index: str, document_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.index = index
        self.document_id = document_id


class SearchQueryError(SearchServiceError):
    pass


class BulkOperationError(SearchServiceError):
    def __init__(
        self,
        message: str,
        success_count: int,
        failed_count: int,
        errors: list,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.success_count = success_count
        self.failed_count = failed_count
        self.errors = errors


class ValidationError(SearchServiceError):
    pass
