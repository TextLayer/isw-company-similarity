class BaseAPIException(Exception):
    """
    Base exception class for all API-related exceptions in the application.

    This class serves as the foundation for the application's exception hierarchy,
    providing a consistent interface for error handling and message retrieval.
    All specific API exceptions should inherit from this class.

    Attributes:
        message (None): Default message attribute, overridden in __init__
        messages: The error message(s) associated with this exception
    """

    message = None

    def __init__(self, message, *args: object) -> None:
        """
        Initialize a new BaseAPIException with the provided message.

        Args:
            message: The error message or messages to associate with this exception.
                     Can be a string or a dictionary of error details.
            *args: Additional arguments to pass to the parent Exception class.
        """
        super().__init__(*args)
        self.messages = message

    def __str__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            String representation of the error messages.
        """
        return str(self.messages)

    def get_message(self):
        """
        Retrieve the error message(s) associated with this exception.

        Returns:
            The error message(s) that were provided when the exception was created.
            This can be a string or a dictionary depending on how the exception was initialized.
        """
        return self.messages
