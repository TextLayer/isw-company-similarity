from unittest.mock import Mock, patch

from flask import Flask, request

from isw.interfaces.api.utils.request import (
    get_api_key,
    get_auth_token,
    get_headers,
)


class TestRequestUtils:
    """Test request utility functions."""

    def test_functions_outside_request_context(self):
        """Test all functions return safe defaults outside request context."""
        assert get_headers() == {}
        assert get_auth_token() is None
        assert get_api_key() is None

    def test_header_extraction(self):
        """Test header extraction with case handling."""
        app = Flask(__name__)

        with app.test_request_context(
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "test-key",
                "Authorization": "Bearer token123",
            }
        ):
            headers = get_headers()
            assert all(k.islower() for k in headers.keys())
            assert headers["content-type"] == "application/json"

            assert get_auth_token() == "Bearer token123"
            assert get_api_key() == "test-key"

    def test_api_key_precedence(self):
        """Test API key header takes precedence over query param."""
        app = Flask(__name__)

        with app.test_request_context("/?api_key=query-key", headers={"X-API-Key": "header-key"}):
            assert get_api_key() == "header-key"

        # Test fallback to query param
        with app.test_request_context("/?api_key=query-key"):
            assert get_api_key() == "query-key"

    def test_exception_handling(self):
        """Test graceful exception handling."""
        app = Flask(__name__)

        with app.test_request_context():
            with patch.object(request, "headers", property(lambda self: Mock(side_effect=Exception()))):
                assert get_headers() == {}
                assert get_auth_token() is None
