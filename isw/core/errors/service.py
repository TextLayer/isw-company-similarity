from isw.core.errors.base import BaseAPIException


class ServiceException(BaseAPIException):
    """
    Exception raised when an error occurs during service operations.

    Example:
        try:
            service.do_something()
        except Exception as e:
            raise ServiceException(f"Failed to do something: {str(e)}")
    """

    def __init__(self, message, *args: object) -> None:
        """
        Initialize a new ServiceException with the provided message.

        Args:
            message: The service error message or messages.
                     Can be a string or a dictionary of processing errors.
            *args: Additional arguments to pass to the parent BaseAPIException class.
        """
        super().__init__(message, *args)
