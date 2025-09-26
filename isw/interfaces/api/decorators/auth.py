from functools import wraps

from flask import g

from isw.core.errors import AuthenticationException, AuthorizationException


def auth(role: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not getattr(g, "authenticated", False):
                raise AuthenticationException("This endpoint requires authentication")

            if role:
                try:
                    # will also raise an exception if g.user_details is None
                    if g.user_details.get("role") != role:
                        raise Exception("Incorrect role")
                except Exception as e:
                    raise AuthorizationException("Insufficient permissions") from e

            return func(*args, **kwargs)

        return wrapper

    return decorator
