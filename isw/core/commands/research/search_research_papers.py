from typing import List

from isw.core.commands.base import BaseCommand
from isw.core.errors import ValidationException
from isw.core.schemas.research_schemas import research_paper_schema, research_papers_query_schema
from isw.core.schemas.utils import from_search_result
from isw.core.services.search import SearchService
from isw.core.utils.research import ResearchPapersQueryBuilder
from isw.shared.config import config
from isw.shared.logging.logger import logger


class SearchResearchPapersCommand(BaseCommand):
    def __init__(self, categories: List[str] = None, search_query: str = None, page: int = 1):
        conf = config()
        self.categories = categories
        self.index = conf.research_papers_index
        self.page = page
        self.results_per_page = conf.research_papers_results_per_page
        self.search_query = search_query

    def validate(self):
        query = ResearchPapersQueryBuilder(results_per_page=self.results_per_page)
        validated = research_papers_query_schema.load(self.__dict__)

        try:
            if len(validated["categories"]) > 0:
                query.add_categories(validated["categories"])
            if validated["search_query"]:
                query.set_search_query(validated["search_query"])
            if validated["page"]:
                query.set_page(validated["page"])

            self.query = query.build()
        except Exception as e:
            logger.warning(f"Research papers query failed to build: {e}")
            raise ValidationException("Could not validate research papers query") from e

    def execute(self):
        search_result = SearchService("opensearch").search(self.index, self.query)
        return from_search_result(
            search_result=search_result,
            schema=research_paper_schema,
            results_per_page=self.results_per_page,
        )
