from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WebSearchResult:
    """Result from a web search provider."""

    content: str
    source: str


class WebSearchProvider(ABC):
    """
    Abstract base for web search providers.

    Providers accept a query string and return raw content.
    The caller is responsible for processing the content as needed.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def search(self, query: str) -> WebSearchResult | None:
        """
        Execute a search with the given query string.

        Args:
            query: The search query (e.g., "Apple Inc (US)")

        Returns:
            WebSearchResult with content and source, or None if no results.
        """
        ...
