from isw.core.commands.base import ReadCommand
from isw.core.errors import NotFoundException
from isw.core.schemas.base import id_schema
from isw.core.schemas.recruitment_schemas import job_schema
from isw.core.services.search.service import SearchService
from isw.shared.config import with_config


class GetJobDetailsCommand(ReadCommand):
    def __init__(self, id: str):
        self.id = id

    def validate(self):
        id_schema.load(self.__dict__)

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        doc = SearchService("opensearch").get_document(
            index=recruitment_jobs_index,
            document_id=self.id,
        )

        if doc is None:
            raise NotFoundException("Job not found")

        return job_schema.load(
            {
                **doc.get("_source"),
                "id": doc.get("_id"),
            }
        )
