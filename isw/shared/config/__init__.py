from typing import Optional

from .base import BaseConfig

# Global registry that gets updated by whichever app is running
_current_config: Optional[BaseConfig] = None


def set_config(config: BaseConfig):
    """Called by each app to register its config"""
    global _current_config
    _current_config = config


def get_config() -> BaseConfig:
    """Used by core business logic to access current config"""
    if _current_config is None:
        raise RuntimeError("No config has been set. Make sure your app calls set_config()")
    return _current_config


def with_config(config_key: str):
    """Decorator to inject a required config value into a function"""

    def inject_config_into_func(func):
        def wrapper(*args, **kwargs):
            value = getattr(config(), config_key)
            if value is None:
                raise Exception(f"{config_key} doesn't exist in config")
            return func(*args, **kwargs, **{config_key: value})

        return wrapper

    return inject_config_into_func


# Convenience alias
config = get_config
