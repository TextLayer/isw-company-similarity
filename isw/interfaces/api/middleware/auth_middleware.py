from flask import g

from isw.core.services.jwt.jwt import JWTService
from isw.interfaces.api.utils.request import get_api_key, get_auth_token
from isw.shared.config import config
from isw.shared.logging.logger import logger


def authenticate_request():
    """Intercept request headers to inform flask of authentication status."""
    try:
        api_key = get_api_key()
        bearer_token = get_auth_token()

        # default session state
        g.authenticated = False
        g.user_details = None

        if api_key == config().api_key:
            g.authenticated = True
            g.user_details = {
                "role": "admin",
            }

        if bearer_token:
            try:
                token = JWTService.extract_from_bearer_token(bearer_token)
                if token:
                    user = JWTService().validate_token(token)
                    g.authenticated = True
                    g.user_details = user
            except Exception as e:
                logger.debug(f"Error validating token: {e}")

    except Exception as e:
        logger.error(f"Authentication middleware encountered an error: {e}")
