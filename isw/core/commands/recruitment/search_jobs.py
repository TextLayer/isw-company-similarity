from isw.core.commands.base import ReadCommand
from isw.core.errors import ValidationException
from isw.core.schemas.recruitment_schemas import job_schema, jobs_query_schema
from isw.core.schemas.utils import from_search_result
from isw.core.services.search import SearchService
from isw.core.utils.recruitment import JobsQueryBuilder
from isw.shared.config import config, with_config
from isw.shared.logging.logger import logger


class SearchJobsCommand(ReadCommand):
    def __init__(self, search_query: str = None, page: int = 1):
        conf = config()
        self.page = page
        self.results_per_page = conf.recruitment_jobs_results_per_page
        self.search_query = search_query

    def validate(self):
        query = JobsQueryBuilder(results_per_page=self.results_per_page)
        validated = jobs_query_schema.load(self.__dict__)

        try:
            if validated["search_query"]:
                query.set_search_query(validated["search_query"])
            if validated["page"]:
                query.set_page(validated["page"])

            self.query = query.build()
        except Exception as e:
            logger.warning(f"Jobs query failed to build: {e}")
            raise ValidationException("Could not validate jobs query") from e

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        search_result = SearchService("opensearch").search(
            index=recruitment_jobs_index,
            query=self.query,
        )

        return from_search_result(
            search_result=search_result,
            schema=job_schema,
            results_per_page=self.results_per_page,
        )
