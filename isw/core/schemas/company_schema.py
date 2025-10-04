from enum import Enum

from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow_enum import EnumField


class ReportType(Enum):
    """SEC report filing types."""
    TEN_K = "10-K"
    TEN_Q = "10-Q"


class CompanyReportsSchema(Schema):
    """Schema for filtering company financial reports."""
    fiscal_year = fields.String(required=False, allow_none=True, load_default=None)
    filing_period = fields.String(required=False, allow_none=True, load_default=None)
    form_type = fields.String(required=False, allow_none=True, load_default=None)

    @validates_schema
    def validate_filing_period(self, data, **kwargs):
        valid_periods = ['Q1', 'Q2', 'Q3', 'FY', None]
        if data.get('filing_period') and data.get('filing_period') not in valid_periods:
            raise ValidationError("Filing period must be Q1, Q2, Q3, or FY")
        return data
    
    @validates_schema
    def validate_form_type(self, data, **kwargs):
        valid_forms = ['10-K', '10-Q', None]
        if data.get('form_type') and data.get('form_type') not in valid_forms:
            raise ValidationError("Form type must be 10-K or 10-Q")
        return data


class ReportTypeSchema(Schema):
    report_type = EnumField(ReportType, required=True)
    
    
class SimilarCompanySearchSchema(Schema):
    similarity_threshold = fields.Float(required=False, default=0.7)
    max_results = fields.Int(required=False, default=10)
    filter_community = fields.Bool(required=False, default=True)

    @validates_schema
    def validate_similarity_threshold(self, data, **kwargs):
        if data['similarity_threshold'] < 0 or data['similarity_threshold'] > 1:
            raise ValidationError("Similarity threshold must be between 0 and 1")
        return data

    @validates_schema
    def validate_max_results(self, data, **kwargs):
        if data['max_results'] < 1 or data['max_results'] > 100:
            raise ValidationError("Max results must be between 1 and 100")
        return data

    @validates_schema
    def validate_filter_community(self, data, **kwargs):
        if data['filter_community'] not in [True, False]:
            raise ValidationError("Filter community must be a boolean")
        return data


class ReportAnomaliesSchema(Schema):
    """Schema for XBRL tag anomaly detection. Defaults come from AnomalyDetectionConfig."""
    form_type = fields.String(required=True)
    fiscal_year = fields.String(required=False)
    filing_period = fields.String(required=False)
    n_peers = fields.Int(required=False)
    similarity_threshold = fields.Float(required=False)
    filter_community = fields.Bool(required=False)
    common_threshold = fields.Float(required=False)
    rare_threshold = fields.Float(required=False)

    @validates_schema
    def validate_form_type(self, data, **kwargs):
        if data['form_type'] not in ['10-K', '10-Q']:
            raise ValidationError("Form type must be 10-K or 10-Q")
        return data
    
    @validates_schema
    def validate_thresholds(self, data, **kwargs):
        if data.get('common_threshold', 0.8) < 0 or data.get('common_threshold', 0.8) > 1:
            raise ValidationError("Common threshold must be between 0 and 1")
        if data.get('rare_threshold', 0.1) < 0 or data.get('rare_threshold', 0.1) > 1:
            raise ValidationError("Rare threshold must be between 0 and 1")
        return data


company_reports_schema = CompanyReportsSchema()
report_anomalies_schema = ReportAnomaliesSchema()
report_type_schema = ReportTypeSchema()
similar_company_search_schema = SimilarCompanySearchSchema()
