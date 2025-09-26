from unittest.mock import Mock, patch

from isw.core.commands.workflows.sync_prompts import SyncPromptsCommand
from isw.core.utils.matchers import StringMatcher
from tests import BaseTest


class TestSyncPromptsCommand(BaseTest):
    def test_sync_prompts(self):
        with patch("textlayer.core.commands.workflows.sync_prompts.EvalsService") as mock_evals_service_class:
            mock_evals_service_instance = Mock()
            mock_evals_service_class.return_value = mock_evals_service_instance
            mock_evals_service_instance.create_prompt.return_value = None

            SyncPromptsCommand().run()
            mock_evals_service_instance.create_prompt.assert_any_call(
                "resume_parser",
                StringMatcher(),
            )
