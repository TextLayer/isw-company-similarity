from contextlib import contextmanager
from unittest.mock import Mock, patch

from isw.shared.config.base import BaseConfig


def create_mock_config(**overrides):
    """Create a mock config object with sensible defaults for mail testing."""
    mock_config = Mock(spec=BaseConfig)

    mock_config.mail_provider = "sendgrid"
    mock_config.mail_test_mode = True
    mock_config.sendgrid_api_key = "test-api-key"
    mock_config.sendgrid_default_sender = "default@example.com"

    for key, value in overrides.items():
        setattr(mock_config, key, value)

    return mock_config


@contextmanager
def mock_sendgrid_config(**config_overrides):
    """Context manager to mock SendGrid config in provider tests."""
    with patch("textlayer.core.services.mail.providers.sendgrid.config") as mock_config:
        mock_config.return_value = create_mock_config(**config_overrides)
        yield mock_config
