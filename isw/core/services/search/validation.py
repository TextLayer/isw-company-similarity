from typing import Any, Dict, Union

from isw.core.services.search.exceptions import ValidationError
from isw.core.services.search.types import SearchQuery


def validate_search_query(query: Union[SearchQuery, Dict[str, Any]]) -> SearchQuery:
    """
    Validate and normalize a search query.

    Args:
        query: SearchQuery object or dictionary to validate

    Returns:
        Valid SearchQuery object

    Raises:
        ValidationError: If query is invalid
    """
    if isinstance(query, dict):
        try:
            query = SearchQuery(**query)
        except TypeError as e:
            raise ValidationError(f"Invalid query parameters: {str(e)}") from e

    if not isinstance(query, SearchQuery):
        raise ValidationError(f"Query must be a SearchQuery or dictionary, got {type(query).__name__}")

    if not query.query:
        raise ValidationError("Query cannot be empty")

    if not isinstance(query.query, dict):
        raise ValidationError(f"Query must be a dictionary, got {type(query.query).__name__}")

    if query.size < 0:
        raise ValidationError(f"Size must be non-negative, got {query.size}")

    if query.size > 10000:
        raise ValidationError(f"Size cannot exceed 10000, got {query.size}")

    if query.from_ < 0:
        raise ValidationError(f"From must be non-negative, got {query.from_}")

    if query.from_ + query.size > 10000:
        raise ValidationError(f"From + size cannot exceed 10000, got {query.from_ + query.size}")

    if query.aggregations:
        if not isinstance(query.aggregations, dict):
            raise ValidationError(f"Aggregations must be a dictionary, got {type(query.aggregations).__name__}")

    if query.sort:
        if not isinstance(query.sort, list):
            raise ValidationError(f"Sort must be a list, got {type(query.sort).__name__}")

        for sort_item in query.sort:
            if not isinstance(sort_item, (dict, str)):
                raise ValidationError(f"Sort items must be dictionaries or strings, got {type(sort_item).__name__}")

    if query.highlight:
        if not isinstance(query.highlight, dict):
            raise ValidationError(f"Highlight must be a dictionary, got {type(query.highlight).__name__}")

        if "fields" in query.highlight and not isinstance(query.highlight["fields"], dict):
            raise ValidationError("Highlight fields must be a dictionary")

    if query.source_includes:
        if not isinstance(query.source_includes, list):
            raise ValidationError(f"Source includes must be a list, got {type(query.source_includes).__name__}")

        for field in query.source_includes:
            if not isinstance(field, str):
                raise ValidationError("Source include fields must be strings")

    if query.source_excludes:
        if not isinstance(query.source_excludes, list):
            raise ValidationError(f"Source excludes must be a list, got {type(query.source_excludes).__name__}")

        for field in query.source_excludes:
            if not isinstance(field, str):
                raise ValidationError("Source exclude fields must be strings")

    return query


def validate_index_name(index: str) -> None:
    """
    Validate an index name according to OpenSearch rules.

    Args:
        index: Index name to validate

    Raises:
        ValidationError: If index name is invalid
    """
    if not index:
        raise ValidationError("Index name cannot be empty")

    if not isinstance(index, str):
        raise ValidationError(f"Index name must be a string, got {type(index).__name__}")

    if index.startswith("_") or index.startswith("-") or index.startswith("+"):
        raise ValidationError(f"Index name cannot start with _, -, or +: '{index}'")

    if index != index.lower():
        raise ValidationError(f"Index name must be lowercase: '{index}'")

    if ".." in index:
        raise ValidationError(f"Index name cannot contain ..: '{index}'")

    invalid_chars = ["\\", "/", "*", "?", '"', "<", ">", "|", " ", ",", "#"]
    for char in invalid_chars:
        if char in index:
            raise ValidationError(f"Index name cannot contain '{char}': '{index}'")

    if len(index) > 255:
        raise ValidationError(f"Index name cannot exceed 255 characters: '{index}'")


def validate_document_id(document_id: str) -> None:
    """
    Validate a document ID.

    Args:
        document_id: Document ID to validate

    Raises:
        ValidationError: If document ID is invalid
    """
    if not document_id:
        raise ValidationError("Document ID cannot be empty")

    if not isinstance(document_id, str):
        raise ValidationError(f"Document ID must be a string, got {type(document_id).__name__}")

    if len(document_id) > 512:
        raise ValidationError(f"Document ID cannot exceed 512 bytes: '{document_id}'")


def validate_bulk_actions(actions: list) -> None:
    """
    Validate bulk actions list.

    Args:
        actions: List of bulk actions to validate

    Raises:
        ValidationError: If actions are invalid
    """
    if not actions:
        raise ValidationError("Bulk actions cannot be empty")

    if not isinstance(actions, list):
        raise ValidationError(f"Bulk actions must be a list, got {type(actions).__name__}")

    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ValidationError(f"Bulk action {i} must be a dictionary, got {type(action).__name__}")
