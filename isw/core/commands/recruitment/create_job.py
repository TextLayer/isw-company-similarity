from isw.core.commands.base import WriteCommand
from isw.core.errors import ValidationException
from isw.core.schemas.recruitment_schemas import JobData, job_schema
from isw.core.services.search.service import SearchService
from isw.shared.config import with_config


class CreateJobCommand(WriteCommand):
    def __init__(self, **kwargs: JobData):
        self.__dict__.update(kwargs)

    def validate(self):
        job_schema.load(self.__dict__)

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        search = SearchService("opensearch")
        response = search.create_document(
            index=recruitment_jobs_index,
            document=self.__dict__,
            document_id=self.__dict__.get("id", None),
        )

        if not search.did_create(response):
            raise ValidationException("Job data could not be saved")

        return {
            **self.__dict__,
            "id": response.get("_id"),
        }
