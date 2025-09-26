from datetime import UTC, datetime

from ....shared.config import config
from ....shared.logging.logger import logger
from ...errors import ProcessingException, ValidationException
from ...services.storage.service import StorageService
from ..base import ReadCommand


class GetTextlayerCoreCommand(ReadCommand):
    def __init__(self, token: dict, key: str):
        self.decoded = token
        self.key = key

    def validate(self) -> bool:
        if not self.decoded or not self.key:
            raise ValidationException("Missing token or key")

    def execute(self) -> dict:
        conf = config()

        expires_at = datetime.fromtimestamp(self.decoded["exp"], UTC)
        expires_in_seconds = int((expires_at - datetime.now(UTC)).total_seconds())

        try:
            presigned_url = StorageService(bucket_name=conf.onboarding_core_s3_bucket).get_download_url(
                key=self.key,
                expires_in=expires_in_seconds,
            )
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise ProcessingException(f"Error generating presigned URL: {str(e)}") from e

        return {"url": presigned_url}
