from isw.core.commands.base import WriteCommand
from isw.core.schemas.recruitment_schemas import application_metadata_schema
from isw.core.services.storage import StorageService
from isw.core.utils.recruitment import format_storage_key_with_candidate_details
from isw.shared.config import config


class GenerateTechnicalSubmissionRequestCommand(WriteCommand):
    def __init__(self, application_id: str, candidate_id: str):
        conf = config()
        self.application_id = application_id
        self.bucket_name = conf.recruitment_submission_s3_bucket
        self.candidate_id = candidate_id
        self.storage_key_prefix = conf.recruitment_submission_s3_key

    def validate(self):
        application_metadata_schema.load(self.__dict__)

    def execute(self):
        storage_key = format_storage_key_with_candidate_details(
            application_id=self.application_id,
            candidate_id=self.candidate_id,
            prefix=self.storage_key_prefix,
        )

        return StorageService("aws_s3", bucket_name=self.bucket_name).get_upload_request(key=storage_key)
