from isw.core.errors.base import BaseAPIException


class AuthorizationException(BaseAPIException):
    """
    Exception raised when a user cannot access a resource.

    Example:
        try:
            if not user.is_admin:
                raise AuthorizationException("Only admins can access this resource")
    """

    def __init__(self, message, *args: object) -> None:
        super().__init__(message, *args)
