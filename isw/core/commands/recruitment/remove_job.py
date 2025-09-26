from isw.core.commands.base import WriteCommand
from isw.core.errors import ValidationException
from isw.core.schemas.base import id_schema
from isw.core.services.search.service import SearchService
from isw.shared.config import with_config
from isw.shared.logging.logger import logger


class RemoveJobCommand(WriteCommand):
    def __init__(self, id: str):
        self.id = id

    def validate(self):
        id_schema.load(self.__dict__)

    @with_config("recruitment_jobs_index")
    def execute(self, recruitment_jobs_index: str):
        try:
            search = SearchService("opensearch")
            response = search.delete_document(
                index=recruitment_jobs_index,
                document_id=self.id,
            )

            if not search.did_delete(response):
                raise Exception(f"Incorrect response result: {response.get('result')}")
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            raise ValidationException("Job data could not be deleted") from e
