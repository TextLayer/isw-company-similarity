import pytest

from isw.core.errors import ValidationException
from isw.interfaces.api.utils.response import Response
from tests import BaseTest


def assert_error_response(exception, status_code):
    response = Response().build_error(exception)
    assert response.status_code is status_code


class TestRequestUtils(BaseTest):
    """Test request utility functions."""

    @pytest.mark.unit
    def test_generic_error(self):
        assert_error_response(Exception("test"), Response.HTTP_ERROR)

    @pytest.mark.unit
    def test_bad_request(self):
        assert_error_response(ValidationException("test"), Response.HTTP_BAD_REQUEST)
