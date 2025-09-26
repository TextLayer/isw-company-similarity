from unittest.mock import Mock, patch

import pytest

from tests import BaseCommandTest
from isw.core.commands.onboarding.list_textlayer_core_versions import ListTextlayerCoreVersionsCommand
from isw.core.errors import ProcessingException, ValidationException


class TestListTextlayerCoreVersionsCommand(BaseCommandTest):
    def test_init_with_valid_repository_name(self):
        command = ListTextlayerCoreVersionsCommand("test-repo")
        assert command.repository_name == "test-repo"

    def test_validate_with_empty_repository_name(self):
        command = ListTextlayerCoreVersionsCommand("")
        self.assert_validation_fails(command, "Missing repository name")

    def test_validate_with_none_repository_name(self):
        command = ListTextlayerCoreVersionsCommand(None)
        self.assert_validation_fails(command, "Missing repository name")

    def test_validate_with_valid_repository_name(self):
        command = ListTextlayerCoreVersionsCommand("valid-repo")
        try:
            command.validate()
        except ValidationException:
            pytest.fail("Validation should not fail with valid repository name")

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.StorageService")
    def test_extract_versions_from_s3_success(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service

        mock_objects = [
            {"key": "test-repo-1.0.0.zip"},
            {"key": "test-repo-2.1.0.zip"},
            {"key": "test-repo-1.5.2.zip"},
            {"key": "other-repo-1.0.0.zip"},
            {"key": "test-repo-3.0.0.zip"},
        ]
        mock_storage_service.iter_files_in_folder.return_value = mock_objects

        command = ListTextlayerCoreVersionsCommand("test-repo")
        versions = command._extract_versions_from_s3("test-bucket")

        expected_versions = ["1.0.0", "2.1.0", "1.5.2", "3.0.0"]
        assert versions == expected_versions

        mock_storage_service.iter_files_in_folder.assert_called_once_with(folder="test-repo/")

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.StorageService")
    def test_extract_versions_from_s3_no_matches(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service

        mock_objects = [
            {"key": "other-repo-1.0.0.zip"},
            {"key": "unrelated-file.txt"},
            {"key": "test-repo-invalid.zip"},
        ]
        mock_storage_service.iter_files_in_folder.return_value = mock_objects

        command = ListTextlayerCoreVersionsCommand("test-repo")
        versions = command._extract_versions_from_s3("test-bucket")

        assert versions == []

    def test_sort_versions_semantically(self):
        command = ListTextlayerCoreVersionsCommand("test-repo")

        unsorted_versions = ["1.0.0", "2.1.0", "1.5.2", "3.0.0", "1.0.1"]
        sorted_versions = command._sort_versions_semantically(unsorted_versions)

        expected_order = ["3.0.0", "2.1.0", "1.5.2", "1.0.1", "1.0.0"]
        assert sorted_versions == expected_order

    def test_sort_versions_semantically_with_patch_versions(self):
        command = ListTextlayerCoreVersionsCommand("test-repo")

        unsorted_versions = ["1.0.0", "1.0.1", "1.0.10", "1.0.2"]
        sorted_versions = command._sort_versions_semantically(unsorted_versions)

        expected_order = ["1.0.10", "1.0.2", "1.0.1", "1.0.0"]
        assert sorted_versions == expected_order

    def test_sort_versions_semantically_empty_list(self):
        command = ListTextlayerCoreVersionsCommand("test-repo")

        sorted_versions = command._sort_versions_semantically([])
        assert sorted_versions == []

    def test_sort_versions_semantically_single_version(self):
        command = ListTextlayerCoreVersionsCommand("test-repo")

        sorted_versions = command._sort_versions_semantically(["1.0.0"])
        assert sorted_versions == ["1.0.0"]

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.StorageService")
    def test_execute_success(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_objects = [{"key": "test-repo-1.0.0.zip"}, {"key": "test-repo-2.1.0.zip"}, {"key": "test-repo-1.5.2.zip"}]

        mock_storage_service.iter_files_in_folder.return_value = mock_objects

        command = ListTextlayerCoreVersionsCommand("test-repo")
        result = command.execute()

        expected_result = {"versions": ["2.1.0", "1.5.2", "1.0.0"]}
        assert result == expected_result

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.StorageService")
    def test_execute_with_storage_service_error(self, mock_storage_service_class, mock_config):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_storage_service.iter_files_in_folder.side_effect = Exception("S3 connection error")

        command = ListTextlayerCoreVersionsCommand("test-repo")

        with pytest.raises(ProcessingException) as exc_info:
            command.execute()

        assert "S3 list versions error: S3 connection error" in str(exc_info.value)

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    def test_execute_with_config_error(self, mock_config):
        mock_config.side_effect = Exception("Config error")

        command = ListTextlayerCoreVersionsCommand("test-repo")

        with pytest.raises(ProcessingException) as exc_info:
            command.execute()

        assert "S3 list versions error: Config error" in str(exc_info.value)

    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.StorageService")
    @patch("textlayer.core.commands.onboarding.list_textlayer_core_versions.config")
    def test_run_method_integration(self, mock_config, mock_storage_service_class):
        mock_config.return_value.onboarding_core_s3_bucket = "test-bucket"

        mock_storage_service = Mock()
        mock_storage_service_class.return_value = mock_storage_service
        mock_objects = [{"key": "test-repo-1.0.0.zip"}, {"key": "test-repo-2.1.0.zip"}]

        mock_storage_service.iter_files_in_folder.return_value = mock_objects

        command = ListTextlayerCoreVersionsCommand("test-repo")
        result = command.run()

        expected_result = {"versions": ["2.1.0", "1.0.0"]}
        assert result == expected_result

    def test_run_method_with_validation_failure(self):
        command = ListTextlayerCoreVersionsCommand("")

        with pytest.raises(ValidationException) as exc_info:
            command.run()

        assert "Missing repository name" in str(exc_info.value)
