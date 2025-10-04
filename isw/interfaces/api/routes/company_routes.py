from flask import Blueprint, g, request

from isw.core.controllers import company_controller

from ....core.controllers.company_controller import CompanyController
from ....core.schemas.routes_schema import pagination_schema
from ....core.schemas.company_schema import (
    company_reports_schema,
    similar_company_search_schema,
    report_anomalies_schema
)
from ..utils.response import Response


company_controller = CompanyController()
company_routes = Blueprint("company_routes", __name__)


@company_routes.get('/')
def get_companies():
    validated_request_data = pagination_schema.load(request.get_json())
    page = validated_request_data['page']
    page_size = validated_request_data['page_size']   
    companies = company_controller.get_companies(page=page, page_size=page_size)
    return Response.make(companies, Response.HTTP_SUCCESS)


@company_routes.get('/<string:cik>')
def get_company_by_cik(cik):
    company_data = company_controller.get_company_by_cik(cik=cik)
    return Response.make(company_data, Response.HTTP_SUCCESS)


@company_routes.get('/<string:cik>/similar')
def get_similar_companies(cik):
    validated_request_data = similar_company_search_schema.load(request.get_json())
    companies = company_controller.get_similar_companies(
        cik=cik, 
        similarity_threshold=validated_request_data['similarity_threshold'], 
        max_results=validated_request_data['max_results'],
         filter_community=validated_request_data['filter_community']
        )
    return Response.make(companies, Response.HTTP_SUCCESS)


@company_routes.get('/<string:cik>/reports')
def get_company_reports(cik):
    validated_request_data = company_reports_schema.load(request.get_json() or {})
    reports = company_controller.get_company_reports(
        cik=cik, 
        fiscal_year=validated_request_data.get('fiscal_year'),
        filing_period=validated_request_data.get('filing_period'),
        form_type=validated_request_data.get('form_type')
    )
    return Response.make(reports, Response.HTTP_SUCCESS)


@company_routes.get('/<string:cik>/reports/anomalies')
def get_report_anomalies(cik):
    validated_request_data = report_anomalies_schema.load(request.get_json())
    anomalies = company_controller.get_report_anomalies(
        cik=cik,
        **validated_request_data
    )
    return Response.make(anomalies, Response.HTTP_SUCCESS)