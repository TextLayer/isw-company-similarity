from typing import Optional

from isw.core.commands.base import WriteCommand
from isw.core.errors import ValidationException
from isw.core.schemas.base import id_schema
from isw.core.schemas.recruitment_schemas import JobData, job_schema
from isw.core.services.search.service import SearchService
from isw.shared.config import with_config


class UpdateJobCommand(WriteCommand):
    def __init__(self, id: str, **kwargs: Optional[JobData]):
        self.__dict__.update(kwargs)
        self.id = id

    def validate(self):
        id_schema.load({"id": self.id})
        job_schema.load(self.__dict__, partial=True)

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        search = SearchService("opensearch")
        response = search.update_document(
            index=recruitment_jobs_index,
            document_id=self.id,
            document=self.__dict__,
        )

        if not search.did_update(response):
            raise ValidationException("Job data could not be updated")

        doc = search.get_document(
            index=recruitment_jobs_index,
            document_id=self.id,
        )

        return {
            **doc.get("_source"),
            "id": doc.get("_id"),
        }
