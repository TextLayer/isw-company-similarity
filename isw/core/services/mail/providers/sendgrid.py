from typing import Optional, Union

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Bcc, Cc, Content, From, Mail, ReplyTo, Subject, To

from isw.core.services.mail.providers.base import MailProvider, MailProviderFactory
from isw.core.services.mail.types import EmailRecipients
from isw.shared.config import config
from isw.shared.logging.logger import logger


class SendGridMailProvider(MailProvider):
    """SendGrid implementation of mail provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_sender: Optional[str] = None,
        test_mode: bool = False,
    ):
        """Initialize SendGrid provider."""
        self.api_key = api_key or config().sendgrid_api_key
        self.default_sender = default_sender or config().sendgrid_default_sender
        self.test_mode = test_mode

        if not self.api_key and not self.test_mode:
            raise ValueError("SendGrid API key not provided")

        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def send(
        self,
        recipients: EmailRecipients,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        sender: Optional[Union[str, tuple]] = None,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            if self.test_mode:
                logger.info(f"[TEST MODE] Email to {recipients.to} (Subject: {subject}) not sent.")
                return True

            if not sender:
                sender = self.default_sender

            if isinstance(sender, tuple):
                from_email = From(sender[0], sender[1])
            else:
                from_email = From(sender)

            message = Mail(from_email=from_email)
            message.subject = Subject(subject)

            for to_email in recipients.to:
                message.add_to(To(to_email))

            if recipients.cc:
                for cc_email in recipients.cc:
                    message.add_cc(Cc(cc_email))

            if recipients.bcc:
                for bcc_email in recipients.bcc:
                    message.add_bcc(Bcc(bcc_email))

            if recipients.reply_to:
                message.reply_to = ReplyTo(recipients.reply_to)

            if text_content:
                message.add_content(Content("text/plain", text_content))

            if html_content:
                message.add_content(Content("text/html", html_content))

            response = self.client.send(message)

            if response.status_code < 300:
                logger.info(f"Email sent via SendGrid to {recipients.to}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "sendgrid"


MailProviderFactory.register("sendgrid", SendGridMailProvider)
