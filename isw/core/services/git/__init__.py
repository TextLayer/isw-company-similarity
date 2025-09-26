from .github import GithubService

# note: alias in case we add other git services in the future
GitService = GithubService

__all__ = ["GitService"]
