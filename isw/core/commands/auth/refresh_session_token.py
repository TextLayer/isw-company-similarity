from ...errors import ValidationException
from ...services.jwt import JWTService
from ..base import WriteCommand


class RefreshSessionTokenCommand(WriteCommand):
    def __init__(self, authorization: str):
        self.authorization = authorization
        self.token = ""

    def execute(self) -> str:
        """
        Refresh the session token.

        Args:
            None

        Returns:
            str: The refreshed token.
        """
        return JWTService().refresh_token(self.token)

    def validate(self) -> None:
        """
        Extract the token from the authorization header value

        Args
            None

        Returns:
            None
        """

        try:
            self.token = JWTService.extract_from_bearer_token(self.authorization)
        except Exception as e:
            raise ValidationException("Token not found") from e
