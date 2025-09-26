from enum import Enum
from functools import cached_property

from marshmallow import Schema, fields, post_load, pre_load

from isw.core.schemas.utils import is_between
from isw.core.utils.helpers import decode, flatten
from isw.shared.config import config


class InsightType(Enum):
    APPLICATIONS = "Applications"
    KEY_POINTS = "Key Points"
    LIMITATIONS = "Limitations"
    CONTRIBUTIONS = "Contributions"


class ResearchPaperInsightsSchema(Schema):
    id = fields.Str(required=True)
    insight = fields.Enum(InsightType, required=True, by_value=True)


class ResearchPapersQuerySchema(Schema):
    categories = fields.List(fields.Str(), required=False)
    index = fields.Str(required=True)
    page = fields.Int(required=False, validate=is_between(1, 100_000))
    results_per_page = fields.Int(required=False, validate=is_between(1, 250))
    search_query = fields.Str(required=False)

    @post_load
    def decode_query_params(self, data: dict, **kwargs):
        return {
            "categories": decode(data.get("categories")),
            "index": data.get("index"),
            "page": data.get("page"),
            "results_per_page": data.get("results_per_page"),
            "search_query": decode(data.get("search_query")),
        }


class ResearchPaperSchema(Schema):
    authors = fields.List(fields.Str(), required=True)
    categories = fields.List(fields.Str(), required=True)
    external_id = fields.Str(required=True)
    id = fields.Str(required=True)
    image_path = fields.Str(required=True)
    published_date = fields.Str(required=True)
    summary = fields.Str(required=True)
    title = fields.Str(required=True)

    @cached_property
    def base_image_url(self) -> str:
        return config().cdn_url

    @pre_load(pass_many=True)
    def transform_from_source(self, data: dict, **kwargs):
        return {
            "authors": data["authors"],
            "categories": flatten(
                [
                    data["l1_domains"],
                    data["l2_domains"],
                ]
            ),
            "external_id": data["external_id"],
            "id": data["id"],
            "image_path": f"{self.base_image_url}/{data['image_path']}",
            "published_date": data["published_date"],
            "summary": data["summary"],
            "title": data["title"],
        }


research_papers_query_schema = ResearchPapersQuerySchema()
research_paper_schema = ResearchPaperSchema(partial=True)
research_paper_insights_schema = ResearchPaperInsightsSchema()
