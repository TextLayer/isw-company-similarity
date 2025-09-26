from typing import Type, TypeVar

from marshmallow import Schema, fields

T = TypeVar("T")


class IDSchema(Schema):
    id = fields.Str(required=True)


class TypedSchema(Schema):
    """Base schema that indicates it implements a TypedDict"""

    _typed_dict: Type[T] = None

    @staticmethod
    def implements(typed_dict: Type[T]):
        """Decorator to indicate this schema implements a TypedDict"""

        def decorator(cls):
            cls._typed_dict = typed_dict
            return cls

        return decorator


id_schema = IDSchema()
