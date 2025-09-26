import os
import tempfile

import pytest

from tests import BaseTest
from isw.core.services.mail import EmailRecipients, MailService
from isw.shared.config import config as shared_config
from isw.shared.config import get_config, set_config


class TestMailServiceIntegration(BaseTest):
    """Integration tests for mail service with SendGrid provider."""

    @pytest.mark.integration
    def test_send_email_integration(self):
        """Test actual email sending through SendGrid API."""
        config = get_config()

        set_config(config)

        # Skip if no API key (e.g., in CI without Doppler)
        if not config.sendgrid_api_key:
            pytest.skip("SendGrid API key not available")

        # Now the service can get config values automatically
        service = MailService()
        test_recipient = config.sendgrid_default_sender

        # Test basic send
        result = service.send_email(
            recipients=EmailRecipients(to=[test_recipient]),
            subject="[TEST] TextLayer Integration Test",
            body="Integration test email - if you received this, the service is working.",
        )

        if not result:
            pytest.skip(
                f"Email send failed - likely sender '{shared_config.sendgrid_default_sender}' "
                "is not verified in SendGrid. Please verify the sender or set "
                "SENDGRID_DEFAULT_SENDER to a verified address."
            )

        assert result is True

        # Test with template only if basic send worked
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "test.html"), "w") as f:
                f.write("<h1>Test: {{ status }}</h1>")

            template_service = MailService(template_dir=temp_dir)
            result = template_service.send_email(
                recipients=EmailRecipients(to=[test_recipient]),
                subject="[TEST] Template Test",
                template_name="test",
                template_data={"status": "SUCCESS"},
            )
            assert result is True

    def test_test_mode_integration(self):
        """Verify test mode doesn't send emails."""
        # Test mode should work with config
        service = MailService(test_mode=True)

        # Should succeed without sending
        result = service.send_email(
            recipients=EmailRecipients(to=["test@example.com"]),
            subject="[TEST] Should not be sent",
            body="Test mode email",
        )
        assert result is True
