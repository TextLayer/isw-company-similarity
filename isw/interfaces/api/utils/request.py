from typing import Dict, Optional

from flask import has_request_context, request


def get_headers() -> Dict[str, str]:
    """
    Get request headers as a lowercase dictionary.

    Returns:
        Dict[str, str]: Dictionary of headers with lowercase keys, empty dict if not in request context
    """
    if not has_request_context():
        return {}

    try:
        return {k.lower(): v for k, v in request.headers.items()}
    except Exception:
        return {}


def get_header(header_name: str) -> Optional[str]:
    """
    Get a specific header value (case-insensitive).

    Args:
        header_name: The header name to retrieve

    Returns:
        Optional[str]: The header value or None if not found
    """
    return get_headers().get(header_name.lower())


def get_auth_token() -> Optional[str]:
    """
    Get the Authorization header value.

    Returns:
        Optional[str]: The authorization token or None
    """
    return get_header("authorization")


def get_api_key() -> Optional[str]:
    """
    Get the API key from X-API-Key header or api_key query parameter.

    Returns:
        Optional[str]: The API key or None
    """
    if not has_request_context():
        return None

    return get_header("x-api-key") or request.args.get("api_key")


def get_request_id() -> Optional[str]:
    """
    Get the request ID from headers.

    Returns:
        Optional[str]: Request ID or None
    """
    return get_header("x-request-id")
