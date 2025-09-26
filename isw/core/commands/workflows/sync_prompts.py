import os
from typing import Optional

from ....shared.logging.logger import logger
from ...commands.base import WriteCommand
from ...errors import ProcessingException
from ...services.evals import EvalsService
from ...services.storage import StorageService
from ...utils.helpers import get_file_name_without_extension


class SyncPromptsCommand(WriteCommand):
    def __init__(self, provider_name: Optional[str] = None):
        self.bucket_name = os.path.join(os.getcwd(), "textlayer/templates/prompts")
        self.provider_name = provider_name

    def validate(self):
        pass

    def execute(self):
        """Sync prompts with the service provider."""
        try:
            disk = StorageService("disk", bucket_name=self.bucket_name, use_temp_dir=False)
            evals = EvalsService(self.provider_name)

            for file in disk.list_files_in_folder():
                key = file.get("key")
                if key is not None and (key.endswith(".md") or key.endswith(".txt")):
                    evals.create_prompt(
                        get_file_name_without_extension(key),
                        disk.stream_read(key).read().decode("utf-8"),
                    )
        except Exception as e:
            logger.error(f"Error in prompt sync: {e}")
            raise ProcessingException("Prompt sync failed") from e
