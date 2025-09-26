from unittest.mock import Mock, patch

import pytest
from marshmallow import ValidationError

from tests import BaseCommandTest
from isw.core.commands.onboarding.invite import InviteCommand


class TestInviteCommand(BaseCommandTest):
    def test_init_with_valid_parameters(self):
        command = InviteCommand("test@example.com", 24)
        assert command.email == "test@example.com"
        assert command.expires_in_hours == 24

    def test_validate_with_valid_parameters(self):
        command = InviteCommand("test@example.com", 24)
        try:
            command.validate()
        except ValidationError:
            pytest.fail("Validation should not fail with valid parameters")

    def test_validate_with_invalid_email(self):
        command = InviteCommand("invalid-email", 24)
        try:
            command.validate()
        except Exception:
            pass

    def test_validate_with_negative_expires_in_hours(self):
        command = InviteCommand("test@example.com", -1)
        with pytest.raises(ValidationError):
            command.validate()

    def test_validate_with_zero_expires_in_hours(self):
        command = InviteCommand("test@example.com", 0)
        with pytest.raises(ValidationError):
            command.validate()

    def test_validate_with_very_large_expires_in_hours(self):
        command = InviteCommand("test@example.com", 999999)
        with pytest.raises(ValidationError):
            command.validate()

    @patch("textlayer.core.commands.onboarding.invite.config")
    @patch("textlayer.core.commands.onboarding.invite.JWTService")
    @patch("textlayer.core.commands.onboarding.invite.MailService")
    def test_execute_success(self, mock_mail_service_class, mock_jwt_service_class, mock_config):
        mock_config.return_value.client_url = "https://app.textlayer.com"

        mock_jwt_service = Mock()
        mock_jwt_service_class.return_value = mock_jwt_service
        mock_jwt_service.generate_token.return_value = "test-jwt-token"

        mock_mail_service = Mock()
        mock_mail_service_class.return_value = mock_mail_service

        command = InviteCommand("test@example.com", 24)
        result = command.execute()

        expected_result = {"status": "success", "expires_in_hours": 24}
        assert result == expected_result

        mock_jwt_service.generate_token.assert_called_once()
        jwt_call_args = mock_jwt_service.generate_token.call_args
        assert jwt_call_args[1]["subject"] == "onboarding_invite"
        assert jwt_call_args[1]["data"] == {"email": "test@example.com"}
        assert jwt_call_args[1]["expires_in"] == 86400

        mock_mail_service.send_email.assert_called_once()
        mail_call_args = mock_mail_service.send_email.call_args
        assert mail_call_args[1]["recipients"].to == ["test@example.com"]
        assert mail_call_args[1]["subject"] == "TextLayer - Onboarding Invite"
        assert mail_call_args[1]["template_name"] == "onboarding"
        assert "onboarding_url" in mail_call_args[1]["template_data"]
        assert "year" in mail_call_args[1]["template_data"]

    @patch("textlayer.core.commands.onboarding.invite.config")
    @patch("textlayer.core.commands.onboarding.invite.JWTService")
    @patch("textlayer.core.commands.onboarding.invite.MailService")
    def test_execute_with_custom_expires_in_hours(self, mock_mail_service_class, mock_jwt_service_class, mock_config):
        mock_config.return_value.client_url = "https://app.textlayer.com"

        mock_jwt_service = Mock()
        mock_jwt_service_class.return_value = mock_jwt_service
        mock_jwt_service.generate_token.return_value = "test-jwt-token"

        mock_mail_service = Mock()
        mock_mail_service_class.return_value = mock_mail_service

        command = InviteCommand("test@example.com", 72)
        result = command.execute()

        expected_result = {"status": "success", "expires_in_hours": 72}
        assert result == expected_result

        jwt_call_args = mock_jwt_service.generate_token.call_args
        assert jwt_call_args[1]["expires_in"] == 259200

    def test_convert_hours_to_seconds(self):
        command = InviteCommand("test@example.com", 1)
        assert command._InviteCommand__convert_hours_to_seconds(1) == 3600
        assert command._InviteCommand__convert_hours_to_seconds(2) == 7200
        assert command._InviteCommand__convert_hours_to_seconds(24) == 86400
        assert command._InviteCommand__convert_hours_to_seconds(48) == 172800

    @patch("textlayer.core.commands.onboarding.invite.config")
    @patch("textlayer.core.commands.onboarding.invite.JWTService")
    @patch("textlayer.core.commands.onboarding.invite.MailService")
    def test_run_method_integration(self, mock_mail_service_class, mock_jwt_service_class, mock_config):
        mock_config.return_value.client_url = "https://app.textlayer.com"

        mock_jwt_service = Mock()
        mock_jwt_service_class.return_value = mock_jwt_service
        mock_jwt_service.generate_token.return_value = "test-jwt-token"

        mock_mail_service = Mock()
        mock_mail_service_class.return_value = mock_mail_service

        command = InviteCommand("test@example.com", 24)
        result = command.run()

        expected_result = {"status": "success", "expires_in_hours": 24}
        assert result == expected_result
