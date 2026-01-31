import os

import httpx

from isw.core.services.web_search.base import WebSearchProvider, WebSearchResult
from isw.core.utils.text import clean_text
from isw.shared.logging.logger import logger


class PerplexityProvider(WebSearchProvider):
    """
    Web search using Perplexity's Sonar API.

    Accepts a query string and internally wraps it in chat messages.
    Returns synthesized content from web sources.
    """

    API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self._api_key = api_key or os.environ.get("PERPLEXITY_API_KEY", "")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "perplexity"

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
                        "model": "sonar",
                        "messages": [{"role": "user", "content": query}],
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                )
                response.raise_for_status()
                data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                logger.warning("Perplexity returned empty response for query: %s", query)
                return None

            return WebSearchResult(
                content=clean_text(content),
                source="perplexity",
            )

        except httpx.HTTPError as e:
            logger.error("Perplexity request failed: %s", e)
            return None
