from datetime import UTC, datetime, timedelta
from typing import Optional

import jwt
from isw.core.errors import ServiceException
from isw.core.utils.helpers import remove_keys
from isw.shared.config import config


class JWTService:
    algo: str
    secret: str

    def __init__(self):
        conf = config()
        self.algo = conf.jwt_algorithm
        self.secret = conf.jwt_secret

    @staticmethod
    def extract_from_bearer_token(bearer_token: str) -> Optional[str]:
        """Extract the token from a bearer token.

        Args:
            bearer_token (str): The bearer token to extract the token from.

        Returns:
            Optional[str]: The extracted token, or None if the bearer token format is invalid.
        """
        parts = bearer_token.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

        return None

    def generate_token(
        self,
        subject: str,
        data: Optional[dict] = None,
        expires_in: Optional[int] = None,
        issued_at: Optional[datetime] = None,
    ) -> str:
        """Generate a JWT token.

        Args:
            subject (str): The subject of the token.
            data (dict, optional): The data to encode in the token. Defaults to an empty dict.
            expires_in (int, optional): The number of seconds until the token expires. Defaults to 24 hours.
            issued_at (datetime, optional): The datetime the token was issued. Defaults to the current datetime.

        Returns:
            str: The generated JWT token.
        """
        data = data or {}
        expires_in = expires_in or 24 * 60 * 60  # one day
        issued_at = issued_at or datetime.now(UTC)
        expire_at = issued_at + timedelta(seconds=expires_in)

        return jwt.encode(
            {
                "sub": subject,
                "iat": int(issued_at.timestamp()),
                "exp": int(expire_at.timestamp()),
                **data,
            },
            self.secret,
            algorithm=self.algo,
        )

    def refresh_token(self, token: str) -> str:
        """Refresh a JWT token.

        Args:
            token (str): The JWT token to refresh.

        Returns:
            str: The refreshed JWT token.
        """
        try:
            decoded = jwt.decode(
                token, self.secret, algorithms=[self.algo], options={"verify_signature": True, "verify_exp": False}
            )

            return self.generate_token(
                data=decoded,
                subject=decoded["sub"],
            )
        except Exception as e:
            raise ServiceException("An error occurred while refreshing this token") from e

    def validate_token(self, token: str) -> dict:
        """Validate a JWT token and return decoded data.

        Args:
            token (str): The JWT token to validate.

        Returns:
            dict: The decoded value.

        Raises:
            ValidationException: If token is expired, invalid, or verification fails.
        """
        try:
            decoded = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algo],
            )

            return remove_keys(decoded, ["iat", "sub"])
        except jwt.ExpiredSignatureError as e:
            raise ServiceException("This token has expired") from e
        except jwt.InvalidTokenError as e:
            raise ServiceException("This token is invalid") from e
        except Exception as e:
            raise ServiceException("An error occurred while verifying this token") from e
