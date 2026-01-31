import os

import httpx

from isw.core.services.web_search.base import WebSearchProvider, WebSearchResult
from isw.shared.logging.logger import logger


class FirecrawlProvider(WebSearchProvider):
    """
    Web search using Firecrawl's scraping API.

    Accepts a query string and returns combined markdown content
    from multiple scraped sources.
    """

    API_URL = "https://api.firecrawl.dev/v2/search"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self._api_key = api_key or os.environ.get("FIRECRAWL_API_KEY", "")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "firecrawl"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    def search(self, query: str) -> WebSearchResult | None:
        if not self.is_available:
            return None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "limit": 5,
                        "scrapeOptions": {"formats": ["markdown"]},
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = data.get("data", [])
            if not results:
                logger.warning("Firecrawl returned no results for query: %s", query)
                return None

            combined = self._combine_results(results[:3])
            if not combined:
                return None

            return WebSearchResult(
                content=combined,
                source="firecrawl",
            )

        except httpx.HTTPError as e:
            logger.error("Firecrawl request failed: %s", e)
            return None

    def _combine_results(self, results: list[dict]) -> str | None:
        sections = []

        for result in results:
            title = result.get("title", "")
            url = result.get("url", "")
            markdown = result.get("markdown", "")
            snippet = result.get("description", "")

            content = markdown[:3000] if markdown else snippet
            if content:
                sections.append(f"Source: {title}\nURL: {url}\n\n{content}")

        if not sections:
            return None

        return "\n\n---\n\n".join(sections)
