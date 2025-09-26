from isw.core.services.search import SearchQuery
from isw.core.utils.keyword import Keyword


class ResearchPapersQueryBuilder:
    def __init__(self, results_per_page: int):
        self.filter = []
        self.must = []
        self.should = []
        self.size = results_per_page

    def add_categories(self, categories: list[str]):
        """Add categories to the query."""
        for category in categories:
            self.add_category(category)

        return self

    def add_category(self, category: str):
        """Add a category to the query, using filters to not affect the score."""
        self.filter.append(
            {
                "bool": {
                    "should": [
                        {"term": {"l1_domains": category}},
                        {"term": {"l2_domains": category}},
                    ]
                }
            }
        )

        return self

    def add_fuzzy_search(self, fuzzy_search_query: str):
        """Add a fuzzy search to the query, with a slight boost for titles."""
        self.should.append(
            {
                "multi_match": {
                    "query": fuzzy_search_query,
                    "fields": ["authors", "external_id", "summary", "title^1.5"],
                    "fuzziness": 1,
                }
            }
        )

        return self

    def add_phrase(self, phrase: str):
        """Add a phrase to the query, favouring direct matches with authors and external_ids."""
        self.must.append(
            {
                "multi_match": {
                    "query": phrase,
                    "fields": [
                        "authors^5",
                        "external_id^10",
                        "summary^1",
                        "title^5",
                    ],
                    "type": "phrase",
                }
            }
        )

        return self

    def build(self):
        """Build the query, using a gaussian decay for published_date."""
        return SearchQuery(
            from_=self.from_,
            query={
                "function_score": {
                    "boost_mode": "sum",
                    "functions": [
                        {
                            "gauss": {
                                "published_date": {
                                    "origin": "now",
                                    "scale": "120d",
                                    "decay": 0.5,
                                },
                            },
                        }
                    ],
                    "max_boost": 5,
                    "query": {
                        "bool": {
                            "filter": self.filter,
                            "must": self.must,
                            "should": self.should,
                        }
                    },
                    "score_mode": "sum",
                },
            },
            size=self.size,
            source_includes=[
                "authors",
                "external_id",
                "id",
                "image_path",
                "l1_domains",
                "l2_domains",
                "published_date",
                "summary",
                "title",
            ],
        )

    def set_page(self, page: int):
        """Construct pagination offset."""
        self.from_ = (page - 1) * self.size
        return self

    def set_search_query(self, search_query: str):
        """Add a search query, using a keyword object to split the query into phrases."""
        keyword = Keyword(search_query)
        [self.add_phrase(phrase) for phrase in keyword.split_into_phrases()]
        self.add_fuzzy_search(keyword.clean())
        return self
