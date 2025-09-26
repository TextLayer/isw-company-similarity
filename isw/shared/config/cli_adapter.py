from typing import Optional

from .base import BaseConfig


class CLIConfig(BaseConfig):
    """CLI-specific configuration that extends BaseConfig."""

    # Add any CLI-specific config attributes here
    # For now, it just inherits all base config
    pass


def get_cli_config(env_name: Optional[str] = None) -> CLIConfig:
    """Get CLI configuration.

    Args:
        env_name: Optional environment name override

    Returns:
        CLIConfig instance with values from environment
    """
    # For now, just create from environment
    # In the future, could add CLI-specific overrides
    return CLIConfig.from_env()
