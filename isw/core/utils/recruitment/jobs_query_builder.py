from isw.core.utils.query_builder import QueryBuilder


class JobsQueryBuilder(QueryBuilder):
    def __init__(self, results_per_page: int):
        super().__init__(results_per_page)
        self.source_includes = [
            "description",
            "expectations",
            "flags",
            "id",
            "qualifications",
            "responsibilities",
            "title",
        ]

    def set_search_query(self, search_query: str):
        """Lookup jobs by title strictly."""
        if search_query:
            self.query = {
                "match": {
                    "title": search_query,
                },
            }

        return self
