from dataclasses import dataclass
from typing import Optional

from .base import BaseConfig


@dataclass
class FlaskConfigAdapter(BaseConfig):
    """Extends base config with Flask-specific values"""

    # Flask-only values
    flask_secret_key: str
    flask_config: str
    preferred_url_scheme: str = "https"

    @classmethod
    def from_env(cls):
        """Create Flask config from environment variables"""
        # Get base config values
        base = BaseConfig.from_env()

        # Add Flask-specific values
        return cls(
            **base.__dict__,
            flask_secret_key=cls.get_env("SECRET_KEY", default="dev-secret-key-change-in-production"),
            flask_config=cls.get_env("FLASK_CONFIG", default="DEV"),
        )

    def to_flask_dict(self) -> dict:
        """Convert to Flask's expected format"""
        return {
            "SECRET_KEY": self.flask_secret_key,
            "DEBUG": self.debug,
            "TESTING": self.testing,
            "PREFERRED_URL_SCHEME": self.preferred_url_scheme,
        }


# Environment-specific Flask configs
class DevelopmentFlaskConfig(FlaskConfigAdapter):
    @classmethod
    def from_env(cls):
        config = FlaskConfigAdapter.from_env()
        config.flask_config = "DEV"
        config.testing = False
        config.debug = True
        return config


class TestingFlaskConfig(FlaskConfigAdapter):
    @classmethod
    def from_env(cls):
        config = FlaskConfigAdapter.from_env()
        config.flask_config = "TEST"
        config.testing = True
        config.debug = True
        return config


class StagingFlaskConfig(FlaskConfigAdapter):
    @classmethod
    def from_env(cls):
        config = FlaskConfigAdapter.from_env()
        config.flask_config = "STAGING"
        config.testing = False
        config.debug = False
        return config


class ProductionFlaskConfig(FlaskConfigAdapter):
    @classmethod
    def from_env(cls):
        config = FlaskConfigAdapter.from_env()
        config.flask_config = "PROD"
        config.testing = False
        config.debug = False
        return config


# Environment-based config selection
flask_config_map = {
    "DEV": DevelopmentFlaskConfig,
    "TEST": TestingFlaskConfig,
    "STAGING": StagingFlaskConfig,
    "PROD": ProductionFlaskConfig,
}


def get_flask_config(config_name: Optional[str] = None) -> FlaskConfigAdapter:
    """Get the appropriate Flask config based on environment or explicit config name

    Args:
        config_name: Optional config name to use. If not provided, reads from FLASK_CONFIG env var
    """
    env = config_name or BaseConfig.get_env("FLASK_CONFIG", default="DEV")
    config_class = flask_config_map.get(env, DevelopmentFlaskConfig)
    return config_class.from_env()
