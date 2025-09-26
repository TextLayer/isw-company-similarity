import pytest

from tests import BaseTest
from isw.interfaces.worker.tasks import task_registry


@pytest.mark.integration
class TestProcessTechnicalSubmission(BaseTest):
    @pytest.mark.skip(reason="This is an active repo that we don't want to clutter with test data")
    def test_process_technical_submission(self):
        task_registry.defer(
            "process_technical_submission",
            {
                "bucket_name": "textlayer-integration-test-artifacts-1",
                "key": "submissions/d2771b79-1426-47d7-a965-ed095615bca7/d518d588-3c50-45ec-9f7f-223647eee5a0.zip",
            },
        )
