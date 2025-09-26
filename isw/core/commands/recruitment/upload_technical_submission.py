import os
from pathlib import Path

from isw.core.commands.base import WriteCommand
from isw.core.errors.validation import ValidationException
from isw.core.schemas.recruitment_schemas import upload_technical_submission_schema
from isw.core.services.ats import ATSService
from isw.core.services.git import GitService
from isw.shared.logging.logger import logger


class UploadTechnicalSubmissionCommand(WriteCommand):
    def __init__(self, application_id: str, candidate_id: str, candidate_name: str, repo_name: str, path: str):
        self.application_id = application_id
        self.candidate_id = candidate_id
        self.candidate_name = candidate_name
        self.path = path
        self.repo_name = repo_name

    def validate(self):
        upload_technical_submission_schema.load(self.__dict__)
        if not os.path.exists(Path(self.path)):
            raise ValidationException("Path to submission does not exist")

    def execute(self):
        try:
            git = (
                GitService(
                    repo_name=self.repo_name,
                    working_dir=self.path,
                    working_dir_indicators=[
                        {"is_folder": True, "name": "app"},
                        {"is_folder": False, "name": "Makefile"},
                    ],
                )
                .create_branch(f"assessment-{self.candidate_id}")
                .commit_all("upload")
                .merge()
                .push()
            )

            url = ATSService().generate_candidate_profile_url(
                candidate_id=self.candidate_id,
                application_id=self.application_id,
            )

            git.create_pull_request(
                title=f"Assessment for {self.candidate_name}",
                body=f"[Visit candidate profile on Ashby]({url})",
            )
        except Exception as e:
            logger.fatal(f"Upload technical submission failed: {e}")
            raise Exception("Could not upload technical submission") from e
