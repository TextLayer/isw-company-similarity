import uuid
from typing import Optional

from ....shared.logging.logger import logger
from ...commands.base import WriteCommand
from ...errors import ProcessingException
from ...services.evals import EvalsService
from ...services.git import GitService
from ...services.storage import StorageService
from ...utils.helpers import to_snake_case


class UpdatePromptsCommand(WriteCommand):
    initial_branch = "staging"
    repo_name = "textlayer"

    def __init__(self, provider_name: Optional[str] = None):
        self.bucket_name = f"prompts-{uuid.uuid4()}"
        self.disk = StorageService("disk", bucket_name=self.bucket_name)
        self.evals = EvalsService(provider_name)
        self.git = GitService(
            repo_name=self.repo_name,
            working_dir=self.disk.get_bucket_path(),
        )

    def validate(self):
        pass

    def execute(self):
        """Update the prompt templates with the latest prompts from the service provider."""
        try:
            self.__set_up_git()
            self.__sync_prompts()
            self.__update_git()
        except Exception as e:
            logger.error(f"Error in prompt update: {e}")
            raise ProcessingException("Prompt update failed") from e

    def __get_monorepo_prompt_path(self, prompt_name: str) -> str:
        """Get the path to the prompt in the monorepo or create one"""
        supported_extensions = [".md", ".txt"]
        paths = map(
            lambda ext: f"apps/backend-new/textlayer/templates/prompts/{to_snake_case(prompt_name)}{ext}",
            supported_extensions,
        )

        for path in paths:
            if self.disk.has(path):
                return path

        return supported_extensions[0]

    def __set_up_git(self):
        self.git.create_branch(self.bucket_name)
        self.git.pull(self.initial_branch)

    def __sync_prompts(self):
        for prompt in self.evals.get_prompts():
            self.disk.upload(
                self.__get_monorepo_prompt_path(prompt["name"]),
                prompt["content"].encode("utf-8"),
            )

    def __update_git(self):
        (
            self.git.commit_all("chore: update prompts")
            .push()
            .create_pull_request(
                body="",
                branch_name=self.initial_branch,
                title="chore(webhook): update prompts",
            )
        )
