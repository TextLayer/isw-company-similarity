from unittest.mock import Mock, patch

import pytest

from tests.unit.core.services.mail.utils import (
    mock_sendgrid_config,
)
from isw.core.services.mail.providers import SendGridMailProvider
from isw.core.services.mail.types import EmailRecipients


class TestSendGridMailProvider:
    """Unit tests for SendGrid mail provider."""

    @pytest.fixture
    def mock_sendgrid_client(self):
        """Create mock SendGrid client."""
        with patch("textlayer.core.services.mail.providers.sendgrid.SendGridAPIClient") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def provider(self, mock_sendgrid_client):
        """Create SendGrid provider with mocked client."""
        with mock_sendgrid_config():
            provider = SendGridMailProvider(api_key="test_key")
            provider.client = mock_sendgrid_client
            return provider

    def test_init_requires_api_key(self):
        """Test initialization fails without API key."""
        with mock_sendgrid_config(sendgrid_api_key=None):
            with pytest.raises(ValueError, match="SendGrid API key not provided"):
                SendGridMailProvider()

    def test_send_email_success(self, provider, mock_sendgrid_client):
        """Test successful email sending."""
        mock_response = Mock(status_code=202)
        mock_sendgrid_client.send.return_value = mock_response

        recipients = EmailRecipients(to=["test@example.com"])
        result = provider.send(recipients, "Test Subject", html_content="<p>Test</p>")

        assert result is True
        mock_sendgrid_client.send.assert_called_once()

    def test_send_email_with_multiple_recipients(self, provider, mock_sendgrid_client):
        """Test email with cc and bcc recipients."""
        mock_response = Mock(status_code=202)
        mock_sendgrid_client.send.return_value = mock_response

        recipients = EmailRecipients(to=["to@example.com"], cc=["cc@example.com"], bcc=["bcc@example.com"])
        result = provider.send(recipients, "Test", text_content="Test content")

        assert result is True
        mock_sendgrid_client.send.assert_called_once()

    def test_send_email_handles_errors(self, provider, mock_sendgrid_client):
        """Test error handling during send."""
        mock_sendgrid_client.send.side_effect = Exception("API Error")

        recipients = EmailRecipients(to=["test@example.com"])
        result = provider.send(recipients, "Test", html_content="<p>Test</p>")

        assert result is False

    def test_test_mode_skips_sending(self):
        """Test that test mode doesn't send emails."""
        with mock_sendgrid_config():
            provider = SendGridMailProvider(api_key="test_key", test_mode=True)

            recipients = EmailRecipients(to=["test@example.com"])
            result = provider.send(recipients, "Test", text_content="Test")

            assert result is True

    def test_get_provider_name(self, provider):
        """Test provider name."""
        assert provider.get_provider_name() == "sendgrid"
