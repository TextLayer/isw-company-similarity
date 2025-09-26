import json
from unittest.mock import Mock, patch

import pytest

from tests import BaseTest
from isw.core.services.jwt import JWTService
from isw.interfaces.api.utils.response import Response
from isw.shared.config import config


class TestOnboardingRoutes(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_each_test(self):
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": config().api_key,
        }

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    @patch("textlayer.interfaces.api.routes.onboarding_routes.JWTService")
    def test_get_textlayer_core_success(self, mock_jwt_service_class, mock_controller):
        mock_jwt_service = Mock()
        mock_jwt_service_class.return_value = mock_jwt_service
        mock_jwt_service.validate_token.return_value = {"exp": 1234567890}

        mock_controller.get_textlayer_core.return_value = {"url": "https://test-url.com/file.zip"}

        response = self.client.get(
            "/v1/onboarding/core?key=test-key&token=test-token",
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_SUCCESS
        data = json.loads(response.data)
        assert "payload" in data
        assert data["payload"]["url"] == "https://test-url.com/file.zip"

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_get_textlayer_core_missing_key(self, mock_controller):
        mock_controller.get_textlayer_core.side_effect = Exception("Missing key")

        token = JWTService().generate_token("test", {"exp": 1234567890})

        response = self.client.get(
            "/v1/onboarding/core?token=" + token,
            headers=self.headers,
        )

        assert response.status_code == 500

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_get_textlayer_core_missing_token(self, mock_controller):
        mock_controller.get_textlayer_core.side_effect = Exception("Missing token")

        response = self.client.get(
            "/v1/onboarding/core?key=test-key",
            headers=self.headers,
        )

        assert response.status_code == 500

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_get_textlayer_core_missing_both_params(self, mock_controller):
        mock_controller.get_textlayer_core.side_effect = Exception("Missing parameters")

        response = self.client.get(
            "/v1/onboarding/core",
            headers=self.headers,
        )

        assert response.status_code == 500

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_list_textlayer_versions_success(self, mock_controller):
        mock_controller.list_textlayer_versions.return_value = {"versions": ["2.1.0", "1.5.2", "1.0.0"]}

        response = self.client.get(
            "/v1/onboarding/core/versions?repository_name=test-repo",
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_SUCCESS
        data = json.loads(response.data)
        assert "payload" in data
        assert data["payload"]["versions"] == ["2.1.0", "1.5.2", "1.0.0"]

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_list_textlayer_versions_missing_repository_name(self, mock_controller):
        mock_controller.list_textlayer_versions.side_effect = Exception("Missing repository name")

        response = self.client.get(
            "/v1/onboarding/core/versions",
            headers=self.headers,
        )

        assert response.status_code == 500

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_invite_success(self, mock_controller):
        mock_controller.invite.return_value = {"status": "success", "expires_in_hours": 24}
        invite_data = {"email": "test@example.com", "expires_in_hours": 24}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_SUCCESS
        data = json.loads(response.data)
        assert "payload" in data
        assert data["payload"]["status"] == "success"

    @pytest.mark.integration
    @patch("textlayer.interfaces.api.routes.onboarding_routes.onboarding_controller")
    def test_invite_with_default_expires_in_hours(self, mock_controller):
        mock_controller.invite.return_value = {"status": "success", "expires_in_hours": 48}
        invite_data = {"email": "test@example.com", "expires_in_hours": 48}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_SUCCESS
        data = json.loads(response.data)
        assert "payload" in data
        assert data["payload"]["status"] == "success"

    @pytest.mark.integration
    def test_invite_missing_email(self):
        invite_data = {"expires_in_hours": 24}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_ERROR

    @pytest.mark.integration
    def test_invite_invalid_email(self):
        invite_data = {"email": "invalid-email", "expires_in_hours": 24}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_UNPROCESSABLE

    @pytest.mark.integration
    def test_invite_negative_expires_in_hours(self):
        invite_data = {"email": "test@example.com", "expires_in_hours": -1}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_UNPROCESSABLE

    @pytest.mark.integration
    def test_invite_zero_expires_in_hours(self):
        invite_data = {"email": "test@example.com", "expires_in_hours": 0}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
            headers=self.headers,
        )

        assert response.status_code == Response.HTTP_UNPROCESSABLE

    @pytest.mark.integration
    def test_invite_authentication_required(self):
        invite_data = {"email": "test@example.com", "expires_in_hours": 24}

        response = self.client.post(
            "/v1/onboarding/invite",
            json=invite_data,
        )

        assert response.status_code == Response.HTTP_UNAUTHORIZED

    @pytest.mark.integration
    def test_get_textlayer_core_authentication_required(self):
        response = self.client.get("/v1/onboarding/core?key=test-key&token=test-token")
        assert response.status_code == Response.HTTP_UNAUTHORIZED

    @pytest.mark.integration
    def test_list_textlayer_versions_authentication_required(self):
        response = self.client.get("/v1/onboarding/core/versions?repository_name=test-repo")
        assert response.status_code == Response.HTTP_UNAUTHORIZED
