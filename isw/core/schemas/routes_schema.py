from marshmallow import Schema, ValidationError, fields, validates_schema


class PaginationSchema(Schema):
    page = fields.Int(required=False, default=1)
    page_size = fields.Int(required=False, default=10)

    @validates_schema
    def validate_page(self, data, **kwargs):
        if data["page"] < 1:
            raise ValidationError("Page must be greater than 0")
        return data

    @validates_schema
    def validate_page_size(self, data, **kwargs):
        if data["page_size"] < 1 or data["page_size"] > 100:
            raise ValidationError("Page size must be greater than 0 and less than 100")
        return data


pagination_schema = PaginationSchema()
