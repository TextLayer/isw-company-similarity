import io

import pytest
import requests

from tests import BaseTest
from isw.core.services.storage import StorageService
from isw.interfaces.api.utils.response import Response


class TestAWSS3StorageServiceIntegration(BaseTest):
    test_artifact_key = "artifact.rtf"
    test_bucket_name = "textlayer-integration-test-artifacts-1"

    @pytest.mark.integration
    def test_s3_get_download_url(self):
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)
        url = storage_service.get_download_url(self.test_artifact_key)
        assert url is not None
        assert url.startswith("https://")

    @pytest.mark.integration
    def test_s3_iterate_files_in_folder(self):
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)

        for item in storage_service.iter_files_in_folder():
            if item["key"] == self.test_artifact_key:
                return

        pytest.fail("Artifact not found")

    @pytest.mark.integration
    def test_s3_list_files_in_folder(self):
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)
        results = storage_service.list_files_in_folder()

        assert len(results) > 0
        assert any(item["key"] == self.test_artifact_key for item in results)

    @pytest.mark.integration
    def test_s3_get_upload_request_body(self):
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)
        body = storage_service.get_upload_request("test_direct_upload.txt")

        assert body is not None
        assert body["url"] is not None
        assert body["url"].startswith("https://")

    @pytest.mark.integration
    def test_s3_use_upload_request_body(self):
        file_name = "test_upload.txt"
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)

        body = storage_service.get_upload_request(file_name)
        files = {"file": (file_name, io.BytesIO(b"foobar"))}

        response = requests.post(
            body["url"],
            data=body["fields"],
            files=files,
        )

        assert response.status_code == Response.HTTP_NO_CONTENT
        assert storage_service.remove(file_name)

    @pytest.mark.integration
    def test_s3_upload(self):
        file_name = "test_programmatic_upload.txt"
        storage_service = StorageService(provider="aws_s3", bucket_name=self.test_bucket_name)
        assert storage_service.upload(file_name, b"foobar")
        assert storage_service.remove(file_name)
