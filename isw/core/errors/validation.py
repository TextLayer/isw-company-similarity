from isw.core.errors.base import BaseAPIException


class ValidationException(BaseAPIException):
    """
    Exception raised when validation of input data fails.

    This exception should be used when request data, parameters, or other inputs
    fail validation checks. It inherits from BaseAPIException to maintain
    consistent error handling throughout the application.

    Example:
        if not valid_email(email):
            raise ValidationException("Invalid email format")
    """

    def __init__(self, message, *args: object) -> None:
        """
        Initialize a new ValidationException with the provided message.

        Args:
            message: The validation error message or messages.
                     Can be a string or a dictionary of validation errors.
            *args: Additional arguments to pass to the parent BaseAPIException class.
        """
        super().__init__(message, *args)
