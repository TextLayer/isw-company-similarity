from abc import ABC, abstractmethod
from io import BufferedReader, BufferedWriter
from pathlib import Path
from typing import Iterator, Optional

from isw.core.services.storage.providers.types import StorageObjectMetadata, StorageUploadRequest
from isw.core.utils.factory import GenericProviderFactory


class StorageProvider(ABC):
    """Base interface for storage providers."""

    @abstractmethod
    def __init__(self, bucket_name: Optional[str], use_temp_dir: Optional[bool]):
        pass

    @abstractmethod
    def get_bucket_path(self) -> Path:
        pass

    @abstractmethod
    def get_upload_request(self, key: str, expires_in: Optional[int]) -> StorageUploadRequest:
        pass

    @abstractmethod
    def get_download_url(self, key: str, expires_in: Optional[int]) -> str:
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        pass

    @abstractmethod
    def extract(self, key: str) -> str:
        pass

    @abstractmethod
    def list(self, folder: Optional[str]) -> Iterator[StorageObjectMetadata]:
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        pass

    @abstractmethod
    def remove_bucket(self) -> str:
        pass

    @abstractmethod
    def stream_read(self, key: str) -> BufferedReader:
        pass

    @abstractmethod
    def stream_write(self, key: str) -> BufferedWriter:
        pass

    @abstractmethod
    def upload(self, key: str, file_blob: bytes) -> bool:
        pass


StorageProviderFactory = GenericProviderFactory[StorageProvider]("storage")
