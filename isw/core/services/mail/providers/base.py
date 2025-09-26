from abc import ABC, abstractmethod
from typing import Optional, Union

from isw.core.services.mail.types import EmailRecipients
from isw.core.utils.factory import GenericProviderFactory


class MailProvider(ABC):
    """Base interface for mail providers."""

    @abstractmethod
    def send(
        self,
        recipients: EmailRecipients,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        sender: Optional[Union[str, tuple]] = None,
    ) -> bool:
        """
        Send an email through the provider.

        Args:
            recipients: Email recipients
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            sender: Sender email or (email, name) tuple

        Returns:
            bool: True if sent successfully
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass


MailProviderFactory = GenericProviderFactory[MailProvider]("mail")
