from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

Document = Dict[str, Any]
DocumentId = str
IndexName = str


@dataclass
class SearchResultItem:
    """Individual search result item."""

    id: str
    score: float
    source: Document
    index: str
    highlights: Optional[Dict[str, List[str]]] = None


@dataclass
class SearchResult:
    """Search operation result."""

    total: int
    hits: List[SearchResultItem]
    aggregations: Optional[Dict[str, Any]] = None
    took_ms: Optional[int] = None


@dataclass
class SearchQuery:
    """Search query parameters."""

    query: Dict[str, Any]
    size: int = 10
    from_: int = 0
    sort: Optional[List[Dict[str, Any]]] = None
    aggregations: Optional[Dict[str, Any]] = None
    highlight: Optional[Dict[str, Any]] = None
    source_includes: Optional[List[str]] = None
    source_excludes: Optional[List[str]] = None


@dataclass
class BulkOperationResult:
    """Result of bulk operations."""

    success_count: int
    errors: List[Dict[str, Any]]
    failed_count: int = 0
    total_count: int = 0


@dataclass
class IndexConfig:
    """Index configuration."""

    name: str
    settings: Dict[str, Any] = field(default_factory=dict)
    mappings: Dict[str, Any] = field(default_factory=dict)
    aliases: Optional[Dict[str, Any]] = None


@dataclass
class TermVector:
    """Term vector information."""

    terms: Dict[str, Dict[str, Any]]
    field_statistics: Optional[Dict[str, Any]] = None
    document_count: Optional[int] = None
