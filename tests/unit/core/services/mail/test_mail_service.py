import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from tests.unit.core.services.mail.utils import create_mock_config
from isw.core.services.mail.providers.base import (
    MailProvider,
    MailProviderFactory,
)
from isw.core.services.mail.service import MailService
from isw.core.services.mail.types import EmailRecipients


class TestMailService:
    """Test mail service core functionality."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock mail provider."""
        provider = Mock(spec=MailProvider)
        provider.get_provider_name.return_value = "mock"
        provider.send.return_value = True
        return provider

    @pytest.fixture
    def service(self, mock_provider):
        """Create mail service with mocked provider."""
        with patch.object(MailProviderFactory, "create", return_value=mock_provider):
            with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                mock_config_func.return_value = create_mock_config()
                return MailService(provider="mock")

    def test_initialization_default_provider(self, mock_provider):
        """Test service initialization with default provider."""
        with patch.object(MailProviderFactory, "create", return_value=mock_provider):
            with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                mock_config_func.return_value = create_mock_config()

                service = MailService(test_mode=True)
                assert service.provider_name == "sendgrid"
                assert service.test_mode is True

    def test_initialization_explicit_provider(self, mock_provider):
        """Test service initialization with explicit provider."""
        with patch.object(MailProviderFactory, "create", return_value=mock_provider):
            with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                mock_config_func.return_value = create_mock_config()
                service = MailService(provider="mock", test_mode=False)
                assert service.provider_name == "mock"
                assert service.test_mode is False

    def test_missing_api_key(self):
        with patch.object(
            MailProviderFactory,
            "create",
            side_effect=ValueError("API key not provided"),
        ):
            with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                mock_config_func.return_value = create_mock_config(sendgrid_api_key="")
                with pytest.raises(ValueError, match="API key not provided"):
                    MailService()

    def test_send_email_basic(self, service, mock_provider):
        """Test basic email sending."""
        recipients = EmailRecipients(to=["test@example.com"])
        result = service.send_email(recipients=recipients, subject="Test", body="Test body")

        assert result is True
        mock_provider.send.assert_called_once_with(
            recipients=recipients,
            subject="Test",
            html_content=None,
            text_content="Test body",
            sender=None,
        )

    def test_send_email_with_multiple_recipients(self, service, mock_provider):
        """Test sending email to multiple recipients."""
        recipients = EmailRecipients(
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        result = service.send_email(recipients=recipients, subject="Multi Recipient Test", body="Test body")

        assert result is True
        mock_provider.send.assert_called_once_with(
            recipients=recipients,
            subject="Multi Recipient Test",
            html_content=None,
            text_content="Test body",
            sender=None,
        )

    def test_send_email_with_template(self, mock_provider):
        """Test sending email with template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "test.html"), "w") as f:
                f.write("<h1>Hello {{ name }}!</h1>")
            with open(os.path.join(temp_dir, "test.txt"), "w") as f:
                f.write("Hello {{ name }}!")

            with patch.object(MailProviderFactory, "create", return_value=mock_provider):
                with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                    mock_config_func.return_value = create_mock_config()
                    service = MailService(template_dir=temp_dir)

            recipients = EmailRecipients(to=["test@example.com"])
            result = service.send_email(
                recipients=recipients,
                subject="Template Test",
                template_name="test",
                template_data={"name": "John"},
            )

            assert result is True
            mock_provider.send.assert_called_once()
            call_args = mock_provider.send.call_args.kwargs
            assert "<h1>Hello John!</h1>" in call_args["html_content"]
            assert "Hello John!" in call_args["text_content"]

    def test_send_email_failure(self, service, mock_provider):
        """Test email sending failure handling."""
        mock_provider.send.return_value = False

        recipients = EmailRecipients(to=["test@example.com"])
        result = service.send_email(recipients=recipients, subject="Test", body="Test")

        assert result is False

    def test_send_email_with_custom_sender(self, service, mock_provider):
        """Test email with custom sender."""
        recipients = EmailRecipients(to=["test@example.com"])
        custom_sender = ("sender@example.com", "Sender Name")

        result = service.send_email(
            recipients=recipients,
            subject="Test",
            body="Test body",
            sender=custom_sender,
        )

        assert result is True
        mock_provider.send.assert_called_once()
        call_args = mock_provider.send.call_args.kwargs
        assert call_args["sender"] == custom_sender

    def test_test_mode_behavior(self, mock_provider):
        """Test that test mode is passed to provider."""
        with patch.object(MailProviderFactory, "create", return_value=mock_provider) as mock_create:
            with patch("textlayer.core.services.mail.service.config") as mock_config_func:
                mock_config_func.return_value = create_mock_config()
                service = MailService(test_mode=True)

                mock_create.assert_called_with("sendgrid", test_mode=True)

                result = service.send_email(
                    recipients=EmailRecipients(to=["test@example.com"]),
                    subject="Test",
                    body="Test in test mode",
                )
                assert result is True
                mock_provider.send.assert_called_once()
