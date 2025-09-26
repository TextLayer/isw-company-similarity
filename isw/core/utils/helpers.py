import json
import re
from itertools import chain
from typing import Any, get_origin
from urllib.parse import unquote


def decode(value: list[str] | str) -> list[str] | str:
    """Decode a string or list of strings."""

    def __run_decode(value: str) -> str:
        return unquote(value) if value else ""

    if isinstance(value, list):
        return [__run_decode(v) for v in value]
    return __run_decode(value)


def flatten(list_of_lists: list[list]) -> list:
    """Flatten a list of lists into a single dimension list."""
    try:
        return list(chain(*list_of_lists))
    except TypeError:
        return list_of_lists


def from_json(data: str) -> dict[str, Any]:
    """Convert data from JSON."""
    try:
        return json.loads(data)
    except Exception:
        return data


def get_file_name_without_extension(file_name: str) -> str:
    """Get the file name without the extension."""
    return file_name.split(".")[0]


def get_header_value(header: str) -> str:
    """Get the value of a header key."""
    return header.split("=", 1)[1]


def is_dict_like(param_type: Any) -> bool:
    """
    Check if a parameter is a dictionary-like type (includes TypedDict)

    Args:
        param_type (Any): The type of the parameter

    Returns:
        bool: True if the parameter is a dictionary-like type, False otherwise
    """
    try:
        return (
            param_type is dict
            or get_origin(param_type) is dict
            or (hasattr(param_type, "__base__") and param_type.__base__ is dict)
            or (hasattr(param_type, "__origin__") and param_type.__origin__ is dict)
        )
    except Exception:
        return False


def remove_keys(data: dict, keys_to_remove: list[str]) -> dict:
    """Remove specified keys from dictionary"""
    return {k: v for k, v in data.items() if k not in keys_to_remove}


def safe_get(data: dict, *keys, default=None) -> Any:
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def to_snake_case(string: str) -> str:
    """Convert string to snake_case."""
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", string).lower()
