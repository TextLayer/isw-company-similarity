from marshmallow import Schema, ValidationError, fields, validates_schema


class SimilarCompanySearchSchema(Schema):
    similarity_threshold = fields.Float(required=False, default=0.7)
    max_results = fields.Int(required=False, default=10)
    filter_community = fields.Bool(required=False, default=True)

    @validates_schema
    def validate_similarity_threshold(self, data, **kwargs):
        if data["similarity_threshold"] < 0 or data["similarity_threshold"] > 1:
            raise ValidationError("Similarity threshold must be between 0 and 1")
        return data

    @validates_schema
    def validate_max_results(self, data, **kwargs):
        if data["max_results"] < 1 or data["max_results"] > 100:
            raise ValidationError("Max results must be between 1 and 100")
        return data

    @validates_schema
    def validate_filter_community(self, data, **kwargs):
        if data["filter_community"] not in [True, False]:
            raise ValidationError("Filter community must be a boolean")
        return data


similar_company_search_schema = SimilarCompanySearchSchema()
