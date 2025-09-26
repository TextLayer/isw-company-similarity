from isw.core.errors.base import BaseAPIException


class NotFoundException(BaseAPIException):
    """
    Exception raised when a resource is not found.

    Example:
      if not candidate:
        raise NotFoundException("Candidate not found")

    """

    def __init__(self, message, *args: object) -> None:
        """
        Initialize a new NotFoundException with the provided message.

        Args:
            message: The not found error message or messages.
                     Can be a string or a dictionary of not found errors.
            *args: Additional arguments to pass to the parent BaseAPIException class.
        """
        super().__init__(message, *args)
