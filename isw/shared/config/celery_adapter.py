"""Worker-specific configuration adapter."""

from typing import Optional

from .base import BaseConfig


class WorkerConfig(BaseConfig):
    """Worker-specific configuration that extends BaseConfig."""

    # Add any worker-specific config attributes here
    # For example: task timeouts, queue names, etc.
    pass


def get_worker_config(env_name: Optional[str] = None) -> WorkerConfig:
    """Get Worker configuration.

    Args:
        env_name: Optional environment name override

    Returns:
        WorkerConfig instance with values from environment
    """
    # For now, just create from environment
    # In the future, could add worker-specific overrides
    return WorkerConfig.from_env()
