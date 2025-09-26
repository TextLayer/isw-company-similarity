from typing import Final, TypedDict


class MessageDict(TypedDict):
    """Type definition for message dictionaries."""

    message: str


class Error:
    """
    Standard error messages for API responses.

    These messages provide consistent error communication across the application.
    Use with appropriate HTTP status codes (4xx, 5xx).

    Example:
        >>> from isw.utils.response import Response
        >>> from isw.utils.messages import Error
        >>>
        >>> response = Response.make(
        ...     Error.NOT_FOUND,
        ...     Response.HTTP_NOT_FOUND
        ... )
    """

    # Client errors (4xx)
    BAD_REQUEST: Final[MessageDict] = {"message": "Bad Request"}
    UNAUTHORIZED: Final[MessageDict] = {"message": "Unauthorized"}
    FORBIDDEN: Final[MessageDict] = {"message": "Forbidden"}
    NOT_FOUND: Final[MessageDict] = {"message": "Not Found"}
    SCHEMA_VALIDATION_FAILED: Final[MessageDict] = {"message": "Failed to validate schema"}
    INVALID_SIGNATURE: Final[MessageDict] = {"message": "Invalid signature"}

    # Server errors (5xx)
    REQUEST_FAILED: Final[MessageDict] = {"message": "Request failed to complete"}

    @staticmethod
    def custom(message: str) -> MessageDict:
        """
        Create a custom error message.

        Args:
            message: The error message text

        Returns:
            MessageDict: A message dictionary with the custom message

        Example:
            >>> error = Error.custom("Invalid file format")
            >>> print(error["message"])
            'Invalid file format'
        """
        return {"message": message}

    @staticmethod
    def make_bad_request_error(error: Exception) -> MessageDict:
        bad_request_msg = Error.BAD_REQUEST.copy()
        bad_request_msg["reason"] = getattr(error, "messages", None)
        return bad_request_msg

    @staticmethod
    def make_validation_error(error: Exception) -> MessageDict:
        validation_msg = Error.SCHEMA_VALIDATION_FAILED.copy()
        validation_msg["errors"] = getattr(error, "messages", [])
        return validation_msg


class Info:
    """
    Standard informational messages for API responses.

    These messages provide consistent informational communication across the
    application. Use with appropriate HTTP status codes (2xx).

    Example:
        >>> from isw.utils.response import Response
        >>> from isw.utils.messages import Info
        >>>
        >>> response = Response.make(
        ...     Info.ACCEPTED,
        ...     Response.HTTP_ACCEPTED
        ... )
    """

    # Success messages (2xx)
    ACCEPTED: Final[MessageDict] = {"message": "accepted"}

    # Informational messages
    RECORD_NOT_FOUND: Final[MessageDict] = {"message": "Record not found"}
    NO_RECORDS_FOUND: Final[MessageDict] = {"message": "No records found"}
    CANNOT_PROCESS_ACTION: Final[MessageDict] = {"message": "Can't process webhook action"}

    @staticmethod
    def custom(message: str) -> MessageDict:
        """
        Create a custom informational message.

        Args:
            message: The informational message text

        Returns:
            MessageDict: A message dictionary with the custom message

        Example:
            >>> info = Info.custom("Processing completed successfully")
            >>> print(info["message"])
            'Processing completed successfully'
        """
        return {"message": message}


class Success:
    """
    Standard success messages for API responses.

    These messages provide consistent success communication across the
    application. Use with HTTP 200 status codes.

    Example:
        >>> from isw.utils.response import Response
        >>> from isw.utils.messages import Success
        >>>
        >>> response = Response.make(
        ...     Success.CREATED,
        ...     Response.HTTP_SUCCESS
        ... )
    """

    # Common success messages
    OK: Final[MessageDict] = {"message": "OK"}
    CREATED: Final[MessageDict] = {"message": "Resource created successfully"}
    UPDATED: Final[MessageDict] = {"message": "Resource updated successfully"}
    DELETED: Final[MessageDict] = {"message": "Resource deleted successfully"}

    @staticmethod
    def custom(message: str) -> MessageDict:
        """
        Create a custom success message.

        Args:
            message: The success message text

        Returns:
            MessageDict: A message dictionary with the custom message

        Example:
            >>> success = Success.custom("Data exported successfully")
            >>> print(success["message"])
            'Data exported successfully'
        """
        return {"message": message}
