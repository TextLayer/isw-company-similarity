import pytest

from isw.core.services.search.exceptions import ValidationError
from isw.core.services.search.types import SearchQuery
from isw.core.services.search.validation import (
    validate_document_id,
    validate_index_name,
    validate_search_query,
)


class TestValidateSearchQuery:
    """Tests for search query validation."""

    def test_valid_search_query_dict(self):
        """Test validation with valid dictionary input."""
        query_dict = {
            "query": {"match": {"title": "test"}},
            "size": 10,
            "from_": 0,
        }
        result = validate_search_query(query_dict)
        assert isinstance(result, SearchQuery)
        assert result.query == {"match": {"title": "test"}}

    def test_valid_search_query_object(self):
        """Test validation with SearchQuery object."""
        query = SearchQuery(query={"match_all": {}})
        result = validate_search_query(query)
        assert result is query

    def test_empty_query_raises_error(self):
        """Test that empty query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            validate_search_query({"query": None})

    def test_invalid_query_type_raises_error(self):
        """Test that non-dict query raises ValidationError."""
        with pytest.raises(ValidationError, match="Query must be a dictionary"):
            validate_search_query({"query": "invalid"})

    def test_negative_size_raises_error(self):
        """Test that negative size raises ValidationError."""
        with pytest.raises(ValidationError, match="Size must be non-negative"):
            validate_search_query({"query": {"match_all": {}}, "size": -1})

    def test_size_exceeds_limit_raises_error(self):
        """Test that size > 10000 raises ValidationError."""
        with pytest.raises(ValidationError, match="Size cannot exceed 10000"):
            validate_search_query({"query": {"match_all": {}}, "size": 10001})

    def test_from_plus_size_exceeds_limit_raises_error(self):
        """Test that from + size > 10000 raises ValidationError."""
        with pytest.raises(ValidationError, match="From \\+ size cannot exceed 10000"):
            validate_search_query({"query": {"match_all": {}}, "from_": 9999, "size": 2})

    def test_invalid_sort_type_raises_error(self):
        """Test that non-list sort raises ValidationError."""
        with pytest.raises(ValidationError, match="Sort must be a list"):
            validate_search_query({"query": {"match_all": {}}, "sort": "invalid"})

    def test_valid_complex_query(self):
        """Test validation with complex query including all features."""
        query_dict = {
            "query": {"bool": {"must": [{"match": {"title": "test"}}]}},
            "size": 20,
            "from_": 10,
            "sort": [{"created_at": "desc"}, "_score"],
            "aggregations": {"categories": {"terms": {"field": "category"}}},
            "highlight": {"fields": {"title": {}}},
            "source_includes": ["title", "author"],
            "source_excludes": ["content"],
        }
        result = validate_search_query(query_dict)
        assert result.aggregations is not None
        assert result.highlight is not None
        assert result.sort is not None


class TestValidateIndexName:
    """Tests for index name validation."""

    def test_valid_index_name(self):
        """Test validation with valid index name."""
        validate_index_name("my-index-123")  # Should not raise

    def test_empty_index_name_raises_error(self):
        """Test that empty index name raises ValidationError."""
        with pytest.raises(ValidationError, match="Index name cannot be empty"):
            validate_index_name("")

    def test_non_string_index_name_raises_error(self):
        """Test that non-string index name raises ValidationError."""
        with pytest.raises(ValidationError, match="Index name must be a string"):
            validate_index_name(123)

    def test_uppercase_index_name_raises_error(self):
        """Test that uppercase index name raises ValidationError."""
        with pytest.raises(ValidationError, match="Index name must be lowercase"):
            validate_index_name("MyIndex")

    def test_invalid_start_character_raises_error(self):
        """Test that index starting with invalid char raises ValidationError."""
        for char in ["_", "-", "+"]:
            with pytest.raises(ValidationError, match="Index name cannot start with"):
                validate_index_name(f"{char}index")

    def test_invalid_characters_raise_error(self):
        """Test that index with invalid chars raises ValidationError."""
        invalid_names = [
            "my\\index",
            "my/index",
            "my*index",
            "my?index",
            "my index",
            "my,index",
            "my#index",
        ]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                validate_index_name(name)

    def test_double_dots_raise_error(self):
        """Test that index with .. raises ValidationError."""
        with pytest.raises(ValidationError, match="Index name cannot contain \\.\\."):
            validate_index_name("my..index")

    def test_too_long_index_name_raises_error(self):
        """Test that index name > 255 chars raises ValidationError."""
        long_name = "a" * 256
        with pytest.raises(ValidationError, match="cannot exceed 255 characters"):
            validate_index_name(long_name)


class TestValidateDocumentId:
    """Tests for document ID validation."""

    def test_valid_document_id(self):
        """Test validation with valid document ID."""
        validate_document_id("doc-123-abc")  # Should not raise

    def test_empty_document_id_raises_error(self):
        """Test that empty document ID raises ValidationError."""
        with pytest.raises(ValidationError, match="Document ID cannot be empty"):
            validate_document_id("")

    def test_non_string_document_id_raises_error(self):
        """Test that non-string document ID raises ValidationError."""
        with pytest.raises(ValidationError, match="Document ID must be a string"):
            validate_document_id(123)

    def test_too_long_document_id_raises_error(self):
        """Test that document ID > 512 bytes raises ValidationError."""
        long_id = "a" * 513
        with pytest.raises(ValidationError, match="Document ID cannot exceed 512 bytes"):
            validate_document_id(long_id)
