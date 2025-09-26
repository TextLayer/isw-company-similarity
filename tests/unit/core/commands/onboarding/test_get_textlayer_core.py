from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from isw.core.commands.onboarding.get_textlayer_core import GetTextlayerCoreCommand
from isw.core.errors import ProcessingException, ValidationException
from tests import BaseCommandTest


class TestGetTextlayerCoreCommand(BaseCommandTest):
    def test_init_with_valid_parameters(self):
        token = {"exp": datetime.now(UTC).timestamp()}
        key = "test-key"
        command = GetTextlayerCoreCommand(token, key)
        assert command.decoded == token
        assert command.key == key

    def test_validate_with_valid_parameters(self):
        token = {"exp": datetime.now(UTC).timestamp()}
        key = "test-key"
        command = GetTextlayerCoreCommand(token, key)
        try:
            command.validate()
        except ValidationException:
            pytest.fail("Validation should not fail with valid parameters")

    def test_validate_with_missing_token(self):
        command = GetTextlayerCoreCommand(None, "test-key")
        self.assert_validation_fails(command, "Missing token or key")

    def test_validate_with_missing_key(self):
        token = {"exp": datetime.now(UTC).timestamp()}
        command = GetTextlayerCoreCommand(token, "")
        self.assert_validation_fails(command, "Missing token or key")

    def test_validate_with_both_missing(self):
        command = GetTextlayerCoreCommand(None, None)
        self.assert_validation_fails(command, "Missing token or key")

    @patch("textlayer.core.commands.onboarding.get_textlayer_core.config")
    @patch("textlayer.core.commands.onboarding.get_textlayer_core.StorageService")
    def test_execute_success(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.get_download_url.return_value = "https://test-url.com/file.zip"

        future_time = datetime.now(UTC).timestamp() + 3600
        token = {"exp": future_time}
        key = "test-key"

        command = GetTextlayerCoreCommand(token, key)
        result = command.execute()

        expected_result = {"url": "https://test-url.com/file.zip"}
        assert result == expected_result

        mock_storage_service.get_download_url.assert_called_once()
        call_args = mock_storage_service.get_download_url.call_args
        assert call_args[1]["key"] == "test-key"
        assert call_args[1]["expires_in"] > 0

    @patch("textlayer.core.commands.onboarding.get_textlayer_core.config")
    @patch("textlayer.core.commands.onboarding.get_textlayer_core.StorageService")
    def test_execute_with_storage_service_error(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.get_download_url.side_effect = Exception("S3 error")

        future_time = datetime.now(UTC).timestamp() + 3600
        token = {"exp": future_time}
        key = "test-key"

        command = GetTextlayerCoreCommand(token, key)

        with pytest.raises(ProcessingException) as exc_info:
            command.execute()

        assert "Error generating presigned URL: S3 error" in str(exc_info.value)

    @patch("textlayer.core.commands.onboarding.get_textlayer_core.config")
    @patch("textlayer.core.commands.onboarding.get_textlayer_core.StorageService")
    def test_execute_with_expired_token(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.get_download_url.side_effect = Exception("Invalid expiration time")

        past_time = datetime.now(UTC).timestamp() - 3600
        token = {"exp": past_time}
        key = "test-key"

        command = GetTextlayerCoreCommand(token, key)

        with pytest.raises(ProcessingException) as exc_info:
            command.execute()

        assert "Error generating presigned URL: Invalid expiration time" in str(exc_info.value)

    @patch("textlayer.core.commands.onboarding.get_textlayer_core.StorageService")
    @patch("textlayer.core.commands.onboarding.get_textlayer_core.config")
    def test_run_method_integration(self, mock_config, mock_storage_service_class):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.get_download_url.return_value = "https://test-url.com/file.zip"

        future_time = datetime.now(UTC).timestamp() + 3600
        token = {"exp": future_time}
        key = "test-key"

        command = GetTextlayerCoreCommand(token, key)
        result = command.run()

        expected_result = {"url": "https://test-url.com/file.zip"}
        assert result == expected_result

    def test_run_method_with_validation_failure(self):
        command = GetTextlayerCoreCommand(None, "test-key")

        with pytest.raises(ValidationException) as exc_info:
            command.run()

        assert "Missing token or key" in str(exc_info.value)
