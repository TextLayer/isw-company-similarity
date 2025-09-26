from flask import Blueprint, request

from ....core.controllers.onboarding_controller import OnboardingController
from ....core.services.jwt.jwt import JWTService
from ..decorators.auth import auth
from ..utils.response import Response

onboarding_controller = OnboardingController()
onboarding_routes = Blueprint("onboarding_routes", __name__)


@onboarding_routes.get("/core")
@auth()
def get_textlayer_core():
    key = request.args.get("key")
    token = request.args.get("token")

    decoded = JWTService().validate_token(token)

    result = onboarding_controller.get_textlayer_core(token=decoded, key=key)
    return Response.make(result, Response.HTTP_SUCCESS)


@onboarding_routes.get("/core/versions")
@auth()
def list_textlayer_versions():
    repository_name = request.args.get("repository_name")

    result = onboarding_controller.list_textlayer_versions(repository_name=repository_name)
    return Response.make(result, Response.HTTP_SUCCESS)


@onboarding_routes.post("/invite")
@auth(role="admin")
def invite():
    result = onboarding_controller.invite(**request.json)

    return Response.make(result, Response.HTTP_SUCCESS)
