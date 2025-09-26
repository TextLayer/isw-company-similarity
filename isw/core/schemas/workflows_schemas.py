from typing import Callable, TypedDict

from marshmallow import Schema, fields

from .base import TypedSchema


class EvalsWorkflowData(TypedDict):
    name: str
    description: str
    runner: str
    prompt: Callable[[str], str]


@TypedSchema.implements(EvalsWorkflowData)
class EvalsWorkflowSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    runner = fields.Str(required=True)
    prompt = fields.Function(required=True)


evals_workflow_schema = EvalsWorkflowSchema()
