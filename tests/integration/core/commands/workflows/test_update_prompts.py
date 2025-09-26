from unittest.mock import ANY, Mock, patch

from isw.core.commands.workflows.update_prompts import UpdatePromptsCommand
from tests import BaseTest


class TestUpdatePromptsCommand(BaseTest):
    def test_service_calls(self):
        with patch("textlayer.core.commands.workflows.update_prompts.GitService") as mock_git_service_class:
            mock_git_service_instance = Mock()
            mock_git_service_class.return_value = mock_git_service_instance
            mock_git_service_instance.commit_all.return_value = mock_git_service_instance
            mock_git_service_instance.push.return_value = mock_git_service_instance
            mock_git_service_instance.create_pull_request.return_value = "https://github.com/textlayer/textlayer/pull/1"

            with patch("textlayer.core.commands.workflows.update_prompts.StorageService") as mock_storage_service_class:
                mock_storage_service_instance = Mock()
                mock_storage_service_class.return_value = mock_storage_service_instance

                UpdatePromptsCommand().run()

                # saves the prompt from eval service
                mock_storage_service_instance.upload.assert_any_call(
                    "apps/backend-new/textlayer/templates/prompts/for_integration_tests.md",
                    ANY,
                )

                # pushes changes to github
                mock_git_service_instance.create_pull_request.assert_called_with(
                    title="chore(webhook): update prompts",
                    body="",
                    branch_name="staging",
                )
