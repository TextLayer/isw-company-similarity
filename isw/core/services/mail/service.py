from typing import Any, Dict, Optional, Union

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from isw.core.services.mail.providers import MailProviderFactory
from isw.core.services.mail.types import EmailRecipients
from isw.shared.config import config
from isw.shared.logging.logger import logger


class MailService:
    """Mail service that delegates to configured provider."""

    def __init__(
        self,
        provider: Optional[str] = None,
        template_dir: Optional[str] = None,
        test_mode: Optional[bool] = None,
        **provider_kwargs,
    ):
        """
        Initialize mail service.

        Args:
            provider: Mail provider to use (defaults to config)
            template_dir: Directory containing email templates
            test_mode: Override test mode from config
            **provider_kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider or config().mail_provider
        self.test_mode = test_mode if test_mode is not None else config().mail_test_mode

        # Initialize the provider
        self.provider = MailProviderFactory.create(self.provider_name, test_mode=self.test_mode, **provider_kwargs)

        # Setup template engine
        if template_dir:
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        else:
            # Default to the templates directory
            self.jinja_env = Environment(loader=FileSystemLoader("textlayer/templates/emails"), autoescape=True)

    def send_email(
        self,
        recipients: EmailRecipients,
        subject: str,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        body: Optional[str] = None,
        sender: Optional[Union[str, tuple]] = None,
    ) -> bool:
        """
        Send an email using the configured provider.

        This method handles template rendering and delegates to the provider.
        """
        html_content = None
        text_content = None

        if template_name and self.jinja_env:
            template_data = template_data or {}
            if body:
                template_data["body"] = body

            # Render HTML template
            try:
                html_template = self.jinja_env.get_template(f"{template_name}.html")
                html_content = html_template.render(**template_data)
            except TemplateNotFound:
                logger.warning(f"HTML template {template_name}.html not found")

            # Render text template
            try:
                txt_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = txt_template.render(**template_data)
            except TemplateNotFound:
                logger.warning(f"Text template {template_name}.txt not found")
                text_content = body or "No content"
        else:
            text_content = body or "No content"

        # Send via provider
        return self.provider.send(
            recipients=recipients, subject=subject, html_content=html_content, text_content=text_content, sender=sender
        )

    def get_provider_name(self) -> str:
        """Get the name of the current provider."""
        return self.provider.get_provider_name()
