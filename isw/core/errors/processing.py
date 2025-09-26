from isw.core.errors.base import BaseAPIException


class ProcessingException(BaseAPIException):
    """
    Exception raised when an error occurs during data processing.

    This exception should be used when operations on data fail during processing,
    such as when transforming, analyzing, or otherwise manipulating data after
    it has been validated but before a response is generated.

    Example:
        try:
            processed_data = process_data(input_data)
        except Exception as e:
            raise ProcessingException(f"Failed to process data: {str(e)}")
    """

    def __init__(self, message, *args: object) -> None:
        """
        Initialize a new ProcessingException with the provided message.

        Args:
            message: The processing error message or messages.
                     Can be a string or a dictionary of processing errors.
            *args: Additional arguments to pass to the parent BaseAPIException class.
        """
        super().__init__(message, *args)
