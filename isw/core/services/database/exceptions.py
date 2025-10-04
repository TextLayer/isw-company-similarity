from typing import Any

from ...errors.base import BaseAPIException


class DatabaseError(BaseAPIException):
    """Base exception for database operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class DatabaseTransactionError(DatabaseError):
    """Exception raised when a database transaction fails."""
    pass


class DatabaseQueryError(DatabaseError):
    """Exception raised when a database query fails."""
    pass
