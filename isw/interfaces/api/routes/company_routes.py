from flask import Blueprint, request

from ....core.controllers.company_controller import CompanyController
from ....core.schemas.company_schema import similar_company_search_schema
from ....core.schemas.routes_schema import pagination_schema
from ..utils.response import Response

company_controller = CompanyController()
company_routes = Blueprint("company_routes", __name__)


@company_routes.get("/")
def get_companies():
    validated_request_data = pagination_schema.load(request.get_json())
    page = validated_request_data["page"]
    page_size = validated_request_data["page_size"]
    companies = company_controller.get_companies(page=page, page_size=page_size)
    return Response.make(companies, Response.HTTP_SUCCESS)


@company_routes.get("/<string:identifier>")
def get_company_by_identifier(identifier):
    company_data = company_controller.get_company_by_identifier(identifier=identifier)
    return Response.make(company_data, Response.HTTP_SUCCESS)


@company_routes.get("/<string:identifier>/similar")
def get_similar_companies(identifier):
    validated_request_data = similar_company_search_schema.load(request.get_json())
    companies = company_controller.get_similar_companies(
        identifier=identifier,
        similarity_threshold=validated_request_data["similarity_threshold"],
        max_results=validated_request_data["max_results"],
        filter_community=validated_request_data["filter_community"],
    )
    return Response.make(companies, Response.HTTP_SUCCESS)
