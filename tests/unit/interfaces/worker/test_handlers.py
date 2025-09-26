import unittest
from unittest.mock import patch

from isw.interfaces.worker.handlers import handle_process_technical_submission


class TestTaskRegistry(unittest.TestCase):
    @patch("textlayer.interfaces.worker.handlers.process_technical_submission")
    def test_handle_process_technical_submission(self, mock_process_technical_submission):
        mock_process_technical_submission.return_value = True

        bucket_name = "test-bucket"
        key = "test-key"

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": bucket_name,
                        },
                        "object": {
                            "key": key,
                        },
                    },
                }
            ]
        }

        handle_process_technical_submission(event)
        mock_process_technical_submission.assert_called_once_with(
            {
                "bucket_name": bucket_name,
                "key": key,
            }
        )
