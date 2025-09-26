from isw.core.commands.base import WriteCommand
from isw.core.schemas.recruitment_schemas import download_technical_submission_schema
from isw.core.services.storage.service import StorageService
from isw.shared.logging.logger import logger


class DownloadTechnicalSubmissionCommand(WriteCommand):
    def __init__(self, bucket_name: str, key: str, stash_path: str):
        self.bucket_name = bucket_name
        self.key = key
        self.stash_path = stash_path

    def validate(self):
        download_technical_submission_schema.load(self.__dict__)

    def execute(self) -> str:
        try:
            # note: drop parent directories from key
            file_name = self.key.split("/").pop()
            disk = StorageService(provider="disk", bucket_name=self.stash_path, use_temp_dir=True)
            s3 = StorageService(provider="aws_s3", bucket_name=self.bucket_name)

            with s3.stream_read(key=self.key) as rs:
                with disk.stream_write(key=file_name) as ws:
                    for chunk in rs:
                        ws.write(chunk)

            return disk.extract(key=file_name)
        except Exception as e:
            logger.fatal(f"Download technical submission failed: {e}")
            raise Exception("Could not download technical submission") from e
