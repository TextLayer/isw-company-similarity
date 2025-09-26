from datetime import datetime
from typing import TypedDict


class StorageObjectMetadata(TypedDict):
    key: str
    modified_at: datetime


class StorageUploadRequest(TypedDict):
    fields: dict
    url: str
