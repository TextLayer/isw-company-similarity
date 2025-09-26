from unittest.mock import Mock

import pytest

from isw.core.services.mail.providers import MailProviderFactory


class TestMailProviderFactory:
    """Unit tests for mail provider factory."""

    def test_register_and_create_provider(self):
        """Test registering and creating a provider."""
        mock_provider_class = Mock()
        mock_instance = Mock()
        mock_provider_class.return_value = mock_instance

        MailProviderFactory.register("test", mock_provider_class)

        provider = MailProviderFactory.create("test", api_key="test_key")

        assert provider == mock_instance
        mock_provider_class.assert_called_once_with(api_key="test_key")

    def test_create_unknown_provider_raises(self):
        """Test creating unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mail provider: unknown"):
            MailProviderFactory.create("unknown")

    def test_available_providers(self):
        """Test available_providers returns registered providers."""
        MailProviderFactory._providers.clear()
        MailProviderFactory.register("provider1", Mock())
        MailProviderFactory.register("provider2", Mock())

        providers = MailProviderFactory.available_providers()

        assert set(providers) == {"provider1", "provider2"}
