import os
import time
from functools import cached_property
from typing import Optional

import jwt
import requests
from github import Auth, Github

from git import Repo
from isw.core.errors.service import ServiceException
from isw.core.schemas.recruitment_schemas import github_app_schema
from isw.core.utils.git import WorkingDirIndicator, determine_working_dir, format_private_key
from isw.shared.config import config
from isw.shared.logging.logger import logger


class GithubService:
    """
    A service for interacting with GitHub repositories using GitHub App authentication.

    This service provides functionality to clone repositories, create branches,
    commit changes, push to remote, and create pull requests. It uses GitHub
    App authentication for secure access to repositories.

    Attributes:
        app_id (str): The GitHub App ID.
        installation_id (str): The GitHub App installation ID.
        private_key (str): The private key for GitHub App authentication.
        remote_origin (str): The full repository name (e.g., "TextLayer/repo-name").
        repo (Repo): The GitPython repository object.
        current_branch (str): The currently checked out branch.
    """

    def __del__(self):
        """
        Cleanup method to close the repository when the service is destroyed.

        Attempts to close the GitPython repository object to free resources.
        Logs a warning if the cleanup fails.
        """
        try:
            self.repo.close()
        except Exception as e:
            logger.debug(f"Couldn't close repo: {e}")

    def __init__(self, repo_name: str, working_dir: str, working_dir_indicators: list[WorkingDirIndicator] = None):
        """
        Initialize the GitHub service.

        Sets up the repository connection, validates GitHub App credentials,
        and initializes the local Git repository.

        Args:
            repo_name (str): The name of the repository (without organization).
            working_dir (str): The base working directory for Git operations.

        Raises:
            ServiceException: If initialization fails due to invalid credentials
                           or repository setup issues.
        """
        try:
            c = config()
            self.app_id = c.github_app_id
            self.installation_id = c.github_app_installation_id
            self.private_key = c.github_app_private_key
            self.remote_origin = f"TextLayer/{repo_name}"

            github_app_schema.load(
                {
                    "app_id": self.app_id,
                    "installation_id": self.installation_id,
                    "private_key": self.private_key,
                }
            )

            self.repo = self.__init_repo(working_dir, working_dir_indicators)
        except Exception as e:
            logger.warning(f"Error initializing GithubService: {e}")
            raise ServiceException("Failed to initialize GithubService") from e

    def __init_repo(self, working_dir: str, working_dir_indicators: list[WorkingDirIndicator]):
        """
        Initialize the Git repository.
        """
        resolved_working_dir = determine_working_dir(working_dir, working_dir_indicators)

        if os.path.exists(os.path.join(resolved_working_dir, ".git")):
            return Repo(resolved_working_dir)
        else:
            repo = Repo.init(resolved_working_dir)
            repo.git.config("user.name", "TextLayer Bot")
            repo.git.config("user.email", "bot@textlayer.ai")
            repo.git.remote("add", "origin", self.remote_url)
            return repo

    def commit_all(self, message: str):
        """
        Commit all staged and unstaged changes to the current branch.

        This method stages all changes (including new files, modifications, and deletions)
        and creates a commit with the specified message.

        Args:
            message (str): The commit message to use for the commit.
        """
        self.repo.git.add(A=True)
        self.repo.index.commit(message)
        return self

    def create_branch(self, branch_name: str):
        """
        Create a new branch or checkout an existing branch.

        If the branch already exists locally, it will be checked out.
        If the branch doesn't exist, a new branch will be created from the current branch.

        Args:
            branch_name (str): The name of the branch to create or checkout.
        """
        self.current_branch = branch_name

        if branch_name in self.repo.heads:
            self.repo.git.checkout(branch_name)
        else:
            self.repo.git.checkout("-b", branch_name)

        return self

    def create_pull_request(self, title: str, body: str, branch_name: Optional[str] = "main") -> str:
        """
        Create a pull request from the current branch to the main branch.

        Creates a pull request using the GitHub API with the current branch
        as the source and 'main' as the target branch.

        Args:
            title (str): The title of the pull request.
            body (str): The body/description of the pull request.

        Returns:
            str: The HTML URL of the created pull request.

        Raises:
            ServiceException: If pull request creation fails due to API errors,
                           authentication issues, or invalid repository state.
        """
        try:
            return (
                self.github_app.get_repo(self.remote_origin)
                .create_pull(
                    base=branch_name,
                    body=body,
                    head=self.current_branch,
                    title=title,
                )
                .html_url
            )
        except Exception as e:
            logger.warning(f"Error creating pull request: {e}")
            raise ServiceException("Pull request creation failed") from e

    @cached_property
    def github_app(self):
        """
        Get an authenticated GitHub API client.

        Creates and caches a GitHub API client using GitHub App authentication.
        The client is cached to avoid recreating it for each API call.

        Returns:
            Github: An authenticated GitHub API client.
        """
        auth = Auth.AppAuth(app_id=int(self.app_id), private_key=format_private_key(self.private_key))
        installation_auth = auth.get_installation_auth(int(self.installation_id))
        return Github(auth=installation_auth)

    def merge(self, branch_name: Optional[str] = "main"):
        """
        This method fetches the latest changes from the remote, merges them
        with the current branch using 'ours' strategy.

        Parameters:
            branch_name (Optional[str]): The name of the branch to merge. Defaults to "main".
        """
        try:
            if "origin" not in [r.name for r in self.repo.remotes]:
                self.repo.create_remote("origin", self.remote_url)

            self.repo.remotes.origin.fetch()
            self.repo.git.merge(f"origin/{branch_name}", X="ours", allow_unrelated_histories=True)
            return self
        except Exception as e:
            logger.warning(f"Error merging branch: {e}")
            raise ServiceException("Merge branch failed") from e

    def pull(self, branch_name: Optional[str] = None):
        """
        Pull the latest changes from the remote repository.

        Args:
            branch_name (Optional[str]): The name of the branch to pull. Defaults to None.
        """
        try:
            self.repo.remotes.origin.pull(branch_name)
            return self
        except Exception as e:
            logger.warning(f"Error pulling branch: {e}")
            raise ServiceException("Pull branch failed") from e

    def push(self):
        """
        Push the current branch to the remote repository.
        """
        try:
            self.repo.remote("origin").push(refspec=f"{self.current_branch}:{self.current_branch}", force=True)
            return self
        except Exception as e:
            logger.warning(f"Error pushing to remote: {e}")
            raise ServiceException("Push to remote failed") from e

    @cached_property
    def remote_url(self) -> str:
        """
        Generate a GitHub access token and construct the remote URL.

        Creates a JWT token for GitHub App authentication, exchanges it for
        an access token, and constructs the remote URL with the token embedded.

        Returns:
            str: The remote URL with embedded access token, or None if token
                 creation fails.

        Note:
            The access token is valid for 10 minutes and is automatically
            refreshed when this property is accessed.
        """
        try:
            now = int(time.time())
            payload = {
                "exp": now + (10 * 60),  # Token expires in 10 minutes
                "iat": now - 60,  # Issued 1 minute ago
                "iss": self.app_id,
            }

            # NOTE: didn't use jwt service because the signing is different for github
            bearer_token = jwt.encode(payload, format_private_key(self.private_key), algorithm="RS256")
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {bearer_token}",
            }

            url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"

            response = requests.post(url, headers=headers)
            response.raise_for_status()

            return f"https://x-access-token:{response.json()['token']}@github.com/{self.remote_origin}.git"
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            return None
