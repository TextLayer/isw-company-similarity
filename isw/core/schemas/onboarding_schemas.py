from marshmallow import Schema, fields, validate


class InviteRequestSchema(Schema):
    email = fields.Str(required=True, validate=validate.Email())
    expires_in_hours = fields.Int(required=False, default=48, missing=48, validate=validate.Range(max=500, min=1))


invite_request_schema = InviteRequestSchema()
