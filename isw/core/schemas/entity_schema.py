from marshmallow import Schema, ValidationError, fields, validates_schema


class SearchEntitiesSchema(Schema):
    similarity_threshold = fields.Float(load_default=0.7)
    max_results = fields.Int(load_default=10)
    filter_community = fields.Bool(load_default=False)

    @validates_schema
    def validate_threshold(self, data, **kwargs):
        if not 0 <= data.get("similarity_threshold", 0.7) <= 1:
            raise ValidationError("similarity_threshold must be between 0 and 1")

    @validates_schema
    def validate_max_results(self, data, **kwargs):
        if not 1 <= data.get("max_results", 10) <= 100:
            raise ValidationError("max_results must be between 1 and 100")


class AddEntitySchema(Schema):
    identifier = fields.String(required=True)
    identifier_type = fields.String(required=True)
    jurisdiction = fields.String(required=True)
    name = fields.String(required=True)


class UpdateEntitySchema(Schema):
    name = fields.String()
    description = fields.String()
    revenue_raw = fields.Float()
    revenue_currency = fields.String()
    revenue_usd = fields.Float()
    revenue_period_end = fields.String()


search_entities_schema = SearchEntitiesSchema()
add_entity_schema = AddEntitySchema()
update_entity_schema = UpdateEntitySchema()
