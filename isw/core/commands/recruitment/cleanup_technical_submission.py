from isw.core.commands.base import WriteCommand
from isw.core.errors.validation import ValidationException
from isw.core.services.storage.service import StorageService


class CleanupTechnicalSubmissionCommand(WriteCommand):
    def __init__(self, stash_path: str):
        self.stash_path = stash_path

    def validate(self):
        if not self.stash_path:
            raise ValidationException("Stash path is required")

    def execute(self):
        StorageService(provider="disk", bucket_name=self.stash_path, use_temp_dir=True).remove_bucket()
