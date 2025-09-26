import shutil
import zipfile
from io import BufferedReader, BufferedWriter
from pathlib import Path
from typing import Iterator, Optional

from isw.core.services.storage.providers.base import StorageProvider, StorageProviderFactory
from isw.core.services.storage.providers.types import StorageObjectMetadata
from isw.core.services.storage.providers.utils import (
    create_shared_temp_dir,
    remove_leading_slash,
    write_access_permissions,
)
from isw.shared.logging.logger import logger


class DiskStorageProvider(StorageProvider):
    """
    A storage provider that uses the local disk for file storage.

    This provider creates a shared temporary directory and manages files within it.
    It supports basic file operations like read, write, delete, and zip extraction.
    All files are stored in a temporary directory that can be cleaned up.

    Attributes:
        base_dir (Path): The shared temporary directory for all disk storage instances.
        bucket (Path): The specific bucket directory for this instance.
    """

    base_dir = create_shared_temp_dir()

    def __get_path(self, key: str) -> Path:
        """
        Get the full file path for a given key.

        Args:
            key (str): The file key/name.

        Returns:
            Path: The full path to the file within the bucket.
        """
        return Path(self.bucket) / key

    def __init__(self, bucket_name: str = "default", use_temp_dir: Optional[bool] = True):
        """
        Initialize the disk storage provider.

        Args:
            bucket_name (str): The name of the bucket/directory to use.
                              Defaults to "default".
            use_temp_dir (Optional[bool]): Whether to use the shared temporary directory.
                                         If False, uses the bucket_name as an absolute path.
                                         Defaults to True.
        """
        self.bucket = self.base_dir / remove_leading_slash(bucket_name) if use_temp_dir else Path(bucket_name)
        self.bucket.mkdir(parents=True, exist_ok=True)
        write_access_permissions(self.bucket)

    def extract(self, key: str) -> str:
        """
        Extract a zip file to a directory.

        Extracts the contents of a zip file to a directory named after the zip file
        (without the .zip extension). Skips macOS metadata files.

        Args:
            key (str): The name of the zip file to extract.

        Returns:
            str: The path to the extracted directory.

        Raises:
            FileNotFoundError: If the zip file doesn't exist.
            zipfile.BadZipFile: If the file is not a valid zip file.
        """
        output_path = Path(self.bucket) / key.removesuffix(".zip")
        output_path.mkdir(parents=True, exist_ok=True)
        write_access_permissions(output_path)

        with zipfile.ZipFile(self.__get_path(key), "r") as zip_ref:
            for item in zip_ref.infolist():
                if "__MACOSX" in item.filename:
                    continue

                zip_ref.extract(item, output_path)

        return str(output_path)

    def get_bucket_path(self) -> Path:
        return self.bucket

    def get_download_url(self, key: str):
        raise NotImplementedError("Local storage provider does not support download URLs")

    def get_upload_request(self, key: str):
        raise NotImplementedError("Local storage provider does not support upload requests")

    def has(self, key: str) -> bool:
        return self.__get_path(key).exists()

    def list(self, folder: Optional[str] = "**") -> Iterator[StorageObjectMetadata]:
        """
        List all files in the bucket or a specific folder.

        Args:
            folder (Optional[str]): The folder to list files from.
                                  Uses "**" to list all files recursively.
                                  Defaults to "**".

        Yields:
            StorageObjectMetadata: Metadata for each file found.
        """
        for path in self.bucket.glob(f"{folder}/*"):
            if path.is_file():
                yield StorageObjectMetadata(
                    key=str(path.relative_to(self.bucket)),
                    size=path.stat().st_size,
                    last_modified=path.stat().st_mtime,
                )

    def remove(self, key: str) -> bool:
        """
        Remove a file from the bucket.

        Args:
            key (str): The name of the file to remove.

        Returns:
            bool: True if the file was successfully removed, False if it didn't exist.
        """
        path = self.__get_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def remove_bucket(self) -> bool:
        """
        Remove the entire bucket directory and all its contents.

        This is useful for cleanup after processing is complete.

        Returns:
            bool: True if the bucket was successfully removed, False otherwise.
        """
        try:
            shutil.rmtree(self.bucket)
            logger.debug(f"Cleaned up temp directory {self.bucket}")
            return True
        except OSError:
            logger.warning("Failed to cleanup temp directory")
            return False

    def stream_read(self, key: str) -> BufferedReader:
        """
        Open a file for reading in binary mode.

        Args:
            key (str): The name of the file to read.

        Returns:
            BufferedReader: A file object opened for reading.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        return open(self.__get_path(key), mode="rb")

    def stream_write(self, key: str) -> BufferedWriter:
        """
        Open a file for writing in binary mode.

        Args:
            key (str): The name of the file to write.

        Returns:
            BufferedWriter: A file object opened for writing.
        """
        path = self.__get_path(key)
        logger.debug(f"Writing to {path}")
        return open(self.__get_path(key), mode="wb")

    def upload(self, key: str, file_blob: bytes) -> bool:
        """
        Upload a file as bytes to the bucket.

        Args:
            key (str): The name of the file to create.
            file_blob (bytes): The file content as bytes.

        Returns:
            bool: True if the upload was successful.
        """
        path = self.__get_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file_blob)
        return True


StorageProviderFactory.register("disk", DiskStorageProvider)
