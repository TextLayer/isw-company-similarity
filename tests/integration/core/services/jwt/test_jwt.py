import os

import pytest

from isw.core.errors import ServiceException
from isw.core.services.jwt import JWTService
from tests import BaseTest


@pytest.fixture(scope="session")
def setup_jwt_env():
    os.environ["JWT_SECRET"] = "test-123"
    os.environ["JWT_ALGORITHM"] = "HS256"


class TestJWTService(BaseTest):
    def test_token_issuance(self, setup_jwt_env):
        jwt = JWTService()
        payload = {"foo": "bar"}

        token = jwt.generate_token("test", payload)
        assert token is not None

        decoded = jwt.validate_token(token)
        assert payload.items() <= decoded.items()

    def test_token_validation(self, setup_jwt_env):
        jwt = JWTService()
        token = jwt.generate_token("test", {"foo": "bar"})
        jwt.secret = "test-456"

        with pytest.raises(ServiceException):
            jwt.validate_token(token)
