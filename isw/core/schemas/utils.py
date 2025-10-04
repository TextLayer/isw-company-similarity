from marshmallow import Schema, ValidationError


def is_between(min_value: int, max_value: int):
    def _validator(value):
        if not (min_value <= value <= max_value):
            raise ValidationError(f"Value must be between {min_value} and {max_value}")
        return value

    return _validator


def safe_load(schema: Schema, data: dict) -> dict | None:
    """
    Safely loads data into a schema (e.g. swallows errors).

    Args:
        schema: Schema to use to load the data
        data: Data to load into the schema

    Returns:
        Dictionary with the loaded data or None if the data is invalid
    """
    try:
        return schema.load(data)
    except Exception:
        return None
