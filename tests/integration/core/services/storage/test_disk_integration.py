import os

import pytest

from isw.core.services.storage import StorageService
from tests import BaseTest


class TestDiskStorageServiceIntegration(BaseTest):
    test_bucket_name = "textlayer-integration-test-artifacts-1"

    @pytest.mark.integration
    def test_disc_stream(self):
        file_content = b"foobarbaz"
        file_name = "example.txt"
        storage_service = StorageService(provider="disk", bucket_name=self.test_bucket_name, use_temp_dir=True)

        with storage_service.stream_write(file_name) as ws:
            ws.write(file_content)

        with storage_service.stream_read(file_name) as rs:
            assert rs.read() == file_content

        storage_service.remove(file_name)

    @pytest.mark.integration
    def test_disc_extract(self):
        fixture = "sample-compressed.zip"
        storage_service = StorageService(
            provider="disk",
            bucket_name=os.path.join(
                os.path.dirname(__file__),
                "fixtures",
            ),
            use_temp_dir=False,
        )

        storage_service.extract(fixture)
        files = storage_service.list_files_in_folder()

        # the contents of our zipped fixture
        assert any(file["key"].endswith("artifact.rtf") for file in files)

        for file in files:
            if file["key"].endswith(".zip"):
                continue
            else:
                storage_service.remove(file["key"])
