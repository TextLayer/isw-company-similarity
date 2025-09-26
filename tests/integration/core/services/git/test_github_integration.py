import os
import uuid

import pytest

from isw.core.services.git import GitService
from isw.core.services.storage import StorageService
from tests import BaseTest


class TestDiskStorageServiceIntegration(BaseTest):
    @pytest.mark.integration
    def test_github_smoke_integration(self):
        # create the fixtures programatically so they can be trashed afterwards
        working_dir = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
        )

        disk = StorageService(provider="disk", bucket_name=working_dir, use_temp_dir=False)
        disk.upload("README.md", b"foobar")

        branch_name = f"test-branch-{uuid.uuid4()}"
        git = GitService(
            repo_name=".github",
            working_dir=working_dir,
            working_dir_indicators=[
                {"is_folder": False, "name": "README.md"},
            ],
        )

        # create a branch
        git.create_branch(branch_name)
        git.commit_all("automated-branch")
        git.merge()
        git.push()

        git.create_pull_request(
            title=branch_name,
            body="test-automated-pr",
        )

        # delete everything so git state doesn't persist
        disk.remove_bucket()
