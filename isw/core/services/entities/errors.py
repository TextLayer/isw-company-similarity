class EntityError(Exception):
    """Base exception for all entity-related errors."""


class StorageError(EntityError):
    pass


class FilingNotFoundError(StorageError):
    pass


class RateLimitError(StorageError):
    pass


class RegistryError(EntityError):
    pass


class DownloadError(RegistryError):
    pass


class ParseError(RegistryError):
    pass


class DescriptionExtractionError(EntityError):
    pass
