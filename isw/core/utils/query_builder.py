from abc import ABC, abstractmethod

from isw.core.services.search import SearchQuery


class QueryBuilder(ABC):
    from_ = 0
    query = {"match_all": {}}
    source_includes = []

    def __init__(self, results_per_page: int):
        self.size = results_per_page

    def build(self):
        return SearchQuery(
            from_=self.from_,
            query=self.query,
            size=self.size,
            source_includes=self.source_includes,
        )

    def set_page(self, page: int):
        """Construct pagination offset."""
        self.from_ = (page - 1) * self.size
        return self

    @abstractmethod
    def set_search_query(self, search_query: str):
        """Set the search query."""
        return self
