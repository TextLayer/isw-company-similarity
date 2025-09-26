import pytest
from flask import g

from isw.core.errors import AuthenticationException, AuthorizationException
from isw.interfaces.api.decorators.auth import auth
from tests import BaseTest


class TestSessionDecorators(BaseTest):
    def test_authentication_without_g_authenticated_state(self):
        @auth()
        def test_function():
            return ""

        g.authenticated = False
        g.user_details = None

        with pytest.raises(AuthenticationException):
            test_function()

    def test_authentication_with_g_authenticated_state(self):
        @auth()
        def test_function():
            return ""

        g.authenticated = True
        g.user_details = None
        test_function()

    def test_authorization_without_g_user_details(self):
        @auth(role="admin")
        def test_function():
            return ""

        g.authenticated = True
        g.user_details = None
        with pytest.raises(AuthorizationException):
            test_function()

    def test_authorization_with_g_user_details(self):
        @auth(role="admin")
        def test_function():
            return ""

        g.authenticated = True
        g.user_details = {"id": "123", "role": "admin"}
        test_function()
