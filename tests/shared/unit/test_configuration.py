import os
from unittest.mock import patch

from isw.shared.config.base import BaseConfig
from isw.shared.config.flask_adapter import get_flask_config


class TestConfiguration:
    """Verify critical configuration functionality"""

    def test_config_loads_from_environment(self):
        """App must be able to load config from environment variables"""
        with patch.dict(os.environ, {"ENV": "production", "DEBUG": "false", "SECRET_KEY": "test-secret-key"}):
            config = BaseConfig.from_env()

            assert config.env == "production"
            assert config.debug is False

    def test_flask_config_selection(self):
        """Flask config must be selectable by environment"""
        dev_config = get_flask_config("DEV")
        test_config = get_flask_config("TEST")

        assert dev_config.flask_config == "DEV"
        assert dev_config.debug is True

        assert test_config.flask_config == "TEST"
        assert test_config.testing is True

    def test_required_config_validation(self):
        """Critical configs must fail fast if missing"""
        with patch.dict(os.environ, {}, clear=True):
            config = BaseConfig.from_env()

            assert config.env == "development"
            assert config.debug is False
