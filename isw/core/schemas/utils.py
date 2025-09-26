import math

from marshmallow import Schema, ValidationError

from isw.core.errors import ValidationException
from isw.core.services.search import SearchResult


def is_between(min_value: int, max_value: int):
    def _validator(value):
        if not (min_value <= value <= max_value):
            raise ValidationError(f"Value must be between {min_value} and {max_value}")
        return value

    return _validator


def from_search_result(search_result: SearchResult, schema: Schema, results_per_page: int):
    """
    Formats a search result into an API-ready response.

    Args:
        search_result: Search result to format
        schema: Schema to use to format the hits
        results_per_page: Number of results per page

    Returns:
        Dictionary with the formatted search result
    """
    formatted_hits = [
        formatted_hit
        for hit in search_result.hits
        if (formatted_hit := safe_load(schema, {**hit.source, "id": hit.id})) is not None
    ]

    if len(formatted_hits) != len(search_result.hits):
        raise ValidationException("Source data could not be loaded into the schema")

    return {
        "hits": formatted_hits,
        "page_count": math.ceil(search_result.total / results_per_page),
        "total": search_result.total,
    }


def safe_load(schema: Schema, data: dict) -> dict | None:
    """
    Safely loads data into a schema (e.g. swallows errors).

    Args:
        schema: Schema to use to load the data
        data: Data to load into the schema

    Returns:
        Dictionary with the loaded data or None if the data is invalid
    """
    try:
        return schema.load(data)
    except Exception:
        return None
