from typing import Literal

from isw.core.services.web_search.base import WebSearchProvider, WebSearchResult
from isw.core.services.web_search.firecrawl import FirecrawlProvider
from isw.core.services.web_search.perplexity import PerplexityProvider
from isw.shared.logging.logger import logger


class WebSearchService:
    """
    Unified web search with automatic fallback between providers.

    Provides a simple interface: query in, content out. The caller
    doesn't need to know which provider was used.
    """

    def __init__(
        self,
        primary: Literal["perplexity", "firecrawl"] = "perplexity",
        perplexity: PerplexityProvider | None = None,
        firecrawl: FirecrawlProvider | None = None,
        timeout: float = 30.0,
    ):
        self._perplexity = perplexity or PerplexityProvider(timeout=timeout)
        self._firecrawl = firecrawl or FirecrawlProvider(timeout=timeout)
        self._primary = primary

    @property
    def is_available(self) -> bool:
        return self._perplexity.is_available or self._firecrawl.is_available

    def search(self, query: str) -> WebSearchResult | None:
        """
        Search with automatic fallback between providers.

        Args:
            query: The search query (e.g., "Apple Inc (US)")

        Returns:
            WebSearchResult with content and source, or None if all providers fail.
        """
        for provider in self._get_provider_order():
            if not provider.is_available:
                logger.debug("Skipping %s (not configured)", provider.name)
                continue

            logger.info("Searching with %s: %s", provider.name, query[:50])
            result = provider.search(query)

            if result:
                return result

            logger.debug("%s returned no results, trying next provider", provider.name)

        logger.warning("All web search providers failed for query: %s", query)
        return None

    def _get_provider_order(self) -> list[WebSearchProvider]:
        if self._primary == "firecrawl":
            return [self._firecrawl, self._perplexity]
        return [self._perplexity, self._firecrawl]
