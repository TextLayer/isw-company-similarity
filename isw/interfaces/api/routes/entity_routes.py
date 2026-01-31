from flask import Blueprint, request

from isw.core.controllers.entity_controller import EntityController
from isw.core.schemas.entity_schema import (
    add_entity_schema,
    search_entities_schema,
    update_entity_schema,
)
from isw.core.schemas.routes_schema import pagination_schema
from isw.core.services.entities import EntityRecord, IdentifierType, Jurisdiction

from ..utils.response import Response

entity_controller = EntityController()
entity_routes = Blueprint("entity_routes", __name__)


@entity_routes.get("/")
def get_entities():
    data = request.get_json() or {}
    validated = pagination_schema.load(data)
    result = entity_controller.get_entities(page=validated["page"], page_size=validated["page_size"])
    return Response.make(result, Response.HTTP_SUCCESS)


@entity_routes.post("/")
def add_entity():
    validated = add_entity_schema.load(request.get_json())
    record = EntityRecord(
        identifier=validated["identifier"],
        identifier_type=IdentifierType(validated["identifier_type"]),
        jurisdiction=Jurisdiction(validated["jurisdiction"]),
        name=validated["name"],
    )
    result = entity_controller.add_entity(record=record)
    status = Response.HTTP_CREATED if result.created else Response.HTTP_SUCCESS
    return Response.make({"identifier": result.identifier, "created": result.created}, status)


@entity_routes.get("/<string:identifier>")
def get_entity(identifier: str):
    result = entity_controller.get_entity(identifier=identifier)
    return Response.make(result, Response.HTTP_SUCCESS)


@entity_routes.patch("/<string:identifier>")
def update_entity(identifier: str):
    validated = update_entity_schema.load(request.get_json())
    result = entity_controller.update_entity(identifier=identifier, **validated)
    if result.not_found:
        return Response.make({"error": "Entity not found"}, Response.HTTP_NOT_FOUND)
    return Response.make({"identifier": result.identifier, "updated": result.updated}, Response.HTTP_SUCCESS)


@entity_routes.delete("/<string:identifier>")
def delete_entity(identifier: str):
    result = entity_controller.delete_entity(identifier=identifier)
    if result.not_found:
        return Response.make({"error": "Entity not found"}, Response.HTTP_NOT_FOUND)
    return Response.make({"identifier": result.identifier, "deleted": result.deleted}, Response.HTTP_SUCCESS)


@entity_routes.get("/<string:identifier>/search")
def search_entities(identifier: str):
    data = request.get_json() or {}
    validated = search_entities_schema.load(data)
    result = entity_controller.search_entities(identifier=identifier, **validated)
    return Response.make(result, Response.HTTP_SUCCESS)
