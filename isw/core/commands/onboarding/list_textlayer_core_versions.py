import re
from typing import List

from ....shared.config import config
from ....shared.logging.logger import logger
from ...errors import ProcessingException, ValidationException
from ...services.storage.service import StorageService
from ..base import ReadCommand


class ListTextlayerCoreVersionsCommand(ReadCommand):
    def __init__(self, repository_name: str):
        self.repository_name = repository_name

    def validate(self):
        if not self.repository_name:
            raise ValidationException("Missing repository name")

    def execute(self) -> dict:
        try:
            conf = config()

            versions = self._extract_versions_from_s3(conf.onboarding_core_s3_bucket)

            sorted_versions = self._sort_versions_semantically(versions)

            return {"versions": sorted_versions}

        except Exception as e:
            logger.error(f"Failed to list S3 versions: {str(e)}")
            raise ProcessingException(f"S3 list versions error: {str(e)}") from e

    def _extract_versions_from_s3(self, bucket_name: str) -> List[str]:
        """Extract version numbers from S3 objects matching the repository pattern."""
        pattern = re.compile(f"{re.escape(self.repository_name)}-(\\d+\\.\\d+\\.\\d+)\\.zip$")

        storage_service = StorageService(bucket_name=bucket_name)
        folder_path = f"{self.repository_name}/"

        versions = []
        for obj in storage_service.iter_files_in_folder(folder=folder_path):
            match = pattern.search(obj["key"])
            if match:
                versions.append(match.group(1))

        return versions

    def _sort_versions_semantically(self, versions: List[str]) -> List[str]:
        """Sort versions in semantic version order (newest first)."""

        def version_key(version: str) -> List[int]:
            return [int(part) for part in version.split(".")]

        return sorted(versions, key=version_key, reverse=True)
