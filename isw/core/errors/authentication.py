from isw.core.errors.base import BaseAPIException


class AuthenticationException(BaseAPIException):
    """
    Exception raised when a user must be authenticated to access a resource.

    Example:
        try:
            if not user.is_authenticated:
                raise AuthenticationException("Login required")
    """

    def __init__(self, message, *args: object) -> None:
        super().__init__(message, *args)
