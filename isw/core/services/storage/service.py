from io import BufferedReader, BufferedWriter
from pathlib import Path
from typing import Iterator, List, Optional

from isw.core.errors.service import ServiceException
from isw.core.services.storage.providers import StorageProviderFactory
from isw.core.services.storage.providers.types import StorageObjectMetadata, StorageUploadRequest
from isw.shared.config import config
from isw.shared.logging.logger import logger


class StorageService:
    """
    A service class that provides a unified interface for file storage operations.

    This class abstracts storage operations across different storage providers (e.g., AWS S3, local filesystem)
    and provides methods for uploading, downloading, listing, and removing files.

    Attributes:
        provider: The storage provider instance that handles the actual storage operations.
    """

    def __init__(self, provider: Optional[str] = None, **kwargs):
        """
        Initialize the StorageService with a storage provider.

        Args:
            provider: The name of the storage provider to use. If None, uses the provider
                     specified in the configuration.
            bucket_name: The name of the storage bucket/container. If None, uses the default
                        bucket configured for the provider.
        """
        self.provider = StorageProviderFactory.create(
            provider or config().storage_provider,
            **kwargs,
        )

    def extract(self, key: str) -> str:
        try:
            return self.provider.extract(key)
        except Exception as e:
            logger.warning(f"Storage provider extract error: {e}")
            raise ServiceException(f"Could not extract file {key}") from e

    def get_bucket_path(self) -> Path:
        return self.provider.get_bucket_path()

    def get_download_url(self, key: str, **kwargs) -> str:
        """
        Generate a pre-signed download URL for a file.

        Args:
            key: The storage key/path of the file to generate a download URL for.
            expires_in: The number of seconds until the URL expires. If None, uses the
                       provider's default expiration time.

        Returns:
            A pre-signed URL that can be used to download the file.

        Raises:
            ServiceException: If the download URL could not be generated.
        """
        try:
            return self.provider.get_download_url(key, **kwargs)
        except Exception as e:
            logger.warning(f"Storage provider get download URL error: {e}")
            raise ServiceException(f"Could not generate download URL for {key}") from e

    def get_upload_request(self, key: str, **kwargs) -> StorageUploadRequest:
        """
        Generate a pre-signed upload request for a file.

        Args:
            key: The storage key/path where the file will be uploaded.
            expires_in: The number of seconds until the upload request expires. If None,
                       uses the provider's default expiration time.

        Returns:
            A StorageUploadRequest object containing the upload URL and any required fields.

        Raises:
            ServiceException: If the upload request could not be generated.
        """
        try:
            return self.provider.get_upload_request(key, **kwargs)
        except Exception as e:
            logger.warning(f"Storage provider get upload request error: {e}")
            raise ServiceException(f"Could not generate upload URL for {key}") from e

    def has(self, key: str) -> bool:
        """
        Check if a file exists in storage.
        """
        try:
            return self.provider.has(key)
        except Exception:
            return False

    def iter_files_in_folder(self, **kwargs) -> Iterator[StorageObjectMetadata]:
        """
        Get an iterator over files in a folder.

        Args:
            folder: The folder path to list files from. If None, lists files from the root.

        Returns:
            An iterator yielding StorageObjectMetadata objects for each file in the folder.

        Raises:
            ServiceException: If the files could not be listed.
        """
        try:
            return self.provider.list(**kwargs)
        except Exception as e:
            logger.warning(f"Storage provider list error: {e}")
            raise ServiceException("Could not generate iterable files") from e

    def list_files_in_folder(self, **kwargs) -> List[StorageObjectMetadata]:
        """
        Get a list of files in a folder.

        Args:
            folder: The folder path to list files from. If None, lists files from the root.

        Returns:
            A list of StorageObjectMetadata objects for each file in the folder.

        Raises:
            ServiceException: If the files could not be listed.
        """
        try:
            return [item for item in self.provider.list(**kwargs)]
        except Exception as e:
            logger.warning(f"Storage provider list error: {e}")
            raise ServiceException("Could not list files") from e

    def remove(self, key: str) -> bool:
        """
        Remove a file from storage.

        Args:
            key: The storage key/path of the file to remove.

        Returns:
            True if the file was successfully removed, False otherwise.

        Raises:
            ServiceException: If the file could not be removed.
        """
        try:
            return self.provider.remove(key)
        except Exception as e:
            logger.warning(f"Storage provider remove error: {e}")
            raise ServiceException(f"Could not remove file {key}") from e

    def remove_bucket(self) -> bool:
        try:
            return self.provider.remove_bucket()
        except Exception as e:
            logger.warning(f"Storage provider remove bucket error: {e}")
            raise ServiceException("Could not remove bucket") from e

    def stream_read(self, key: str) -> BufferedReader:
        try:
            return self.provider.stream_read(key)
        except Exception as e:
            logger.warning(f"Storage provider stream read error: {e}")
            raise ServiceException(f"Could not stream read file {key}") from e

    def stream_write(self, key: str) -> BufferedWriter:
        try:
            return self.provider.stream_write(key)
        except Exception as e:
            logger.warning(f"Storage provider stream write error: {e}")
            raise ServiceException(f"Could not stream write file {key}") from e

    def upload(self, key: str, file_blob: bytes) -> bool:
        """
        Upload a file to storage.

        Args:
            key: The storage key/path where the file will be stored.
            file_blob: The file content as bytes.

        Returns:
            True if the file was successfully uploaded, False otherwise.

        Raises:
            ServiceException: If the file could not be uploaded.
        """
        try:
            return self.provider.upload(key, file_blob)
        except Exception as e:
            logger.warning(f"Storage provider upload error: {e}")
            raise ServiceException(f"Could not upload file {key}") from e
