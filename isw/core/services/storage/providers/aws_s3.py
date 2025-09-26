import io
from io import BufferedReader, BufferedWriter
from pathlib import Path
from typing import Iterator, Optional

import boto3

from .....shared.config import config
from .base import StorageProvider, StorageProviderFactory
from .types import StorageObjectMetadata, StorageUploadRequest


class AWSS3StorageProvider(StorageProvider):
    """
    AWS S3 implementation of the StorageProvider interface.

    This class provides methods to interact with AWS S3 for file storage operations
    including upload, download, listing, and deletion of objects. It uses boto3
    for AWS SDK operations and supports presigned URLs for secure access.

    Attributes:
        bucket_name (str): The S3 bucket name where objects are stored
        s3_client: The boto3 S3 client instance for AWS operations
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize the AWS S3 storage provider.

        Args:
            bucket_name (Optional[str]): The S3 bucket name. If not provided,
                uses the bucket name from configuration.
        """
        c = config()
        self.bucket_name = bucket_name or c.aws_bucket_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=c.aws_access_key_id,
            aws_secret_access_key=c.aws_secret_access_key,
            config=boto3.session.Config(signature_version="s3v4"),
            region_name=c.aws_region,
        )

    def extract(self, key: str) -> None:
        raise NotImplementedError("AWS S3 does not support extraction")

    def get_bucket_path(self) -> Path:
        return Path(self.bucket_name)

    def get_upload_request(self, key: str, expires_in: Optional[int] = 3600) -> StorageUploadRequest:
        """
        Generate a presigned POST request for uploading files to S3.

        This method creates a presigned POST request that allows clients to upload
        files directly to S3 without requiring AWS credentials. The request includes
        the necessary fields and URL for the upload operation.

        Args:
            key (str): The S3 object key (file path) where the file will be stored
            expires_in (Optional[int]): The expiration time in seconds for the presigned
                request. Defaults to 3600 seconds (1 hour).

        Returns:
            StorageUploadRequest: A dictionary containing 'fields' and 'url' for the
                presigned POST request.
        """
        return self.s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            ExpiresIn=expires_in,
            Key=key,
        )

    def get_download_url(self, key: str, expires_in: Optional[int] = 3600) -> str:
        """
        Generate a presigned URL for downloading files from S3.

        This method creates a presigned URL that allows temporary access to download
        a file from S3 without requiring AWS credentials. The URL expires after the
        specified time period.

        Args:
            key (str): The S3 object key (file path) of the file to download
            expires_in (Optional[int]): The expiration time in seconds for the presigned
                URL. Defaults to 3600 seconds (1 hour).

        Returns:
            str: A presigned URL that can be used to download the file.
        """
        return self.s3_client.generate_presigned_url(
            "get_object",
            ExpiresIn=expires_in,
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
            },
        )

    def has(self, key: str) -> bool:
        raise NotImplementedError("AWS S3 does not support has")

    def list(self, folder: Optional[str] = "") -> Iterator[StorageObjectMetadata]:
        """
        List all objects in the specified folder/prefix in S3.

        This method uses S3's pagination to efficiently list all objects under
        the specified folder prefix. It yields metadata for each object including
        the key and last modified timestamp.

        Args:
            folder (Optional[str]): The folder prefix to list objects from.
                Defaults to empty string (root of bucket).

        Yields:
            StorageObjectMetadata: Metadata for each object including 'key' and
                'modified_at' timestamp.
        """
        paginator = self.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=folder):
            for obj in page.get("Contents", []):
                yield StorageObjectMetadata(key=obj["Key"], modified_at=obj["LastModified"])

    def remove(self, key: str) -> bool:
        """
        Delete an object from S3.

        This method permanently deletes the specified object from the S3 bucket.
        The operation is irreversible.

        Args:
            key (str): The S3 object key (file path) of the object to delete

        Returns:
            bool: True if the deletion was successful (no exception raised)
        """
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        return True

    def remove_bucket(self) -> str:
        raise NotImplementedError("AWS S3 does not support bucket removal")

    def stream_read(self, key: str) -> BufferedReader:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"]

    def stream_write(self, key: str) -> BufferedWriter:
        raise NotImplementedError("AWS S3 does not support write streams")

    def upload(self, key: str, file_blob: bytes) -> bool:
        """
        Upload a file directly to S3 using the provided bytes.

        This method uploads file content directly to S3 using the upload_fileobj
        method. It's useful for uploading files that are already in memory as bytes.

        Args:
            key (str): The S3 object key (file path) where the file will be stored
            file_blob (bytes): The file content as bytes to upload

        Returns:
            bool: True if the upload was successful (no exception raised)
        """
        self.s3_client.upload_fileobj(io.BytesIO(file_blob), self.bucket_name, key)
        return True


StorageProviderFactory.register("aws_s3", AWSS3StorageProvider)
