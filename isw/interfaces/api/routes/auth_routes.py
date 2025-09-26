from flask import Blueprint, request

from ....core.controllers.auth_controller import AuthController
from ..decorators.auth import auth
from ..utils.response import Response

auth_controller = AuthController()
auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.get("/session")
@auth()
def validate_token():
    return Response.make("", Response.HTTP_NO_CONTENT)


@auth_routes.post("/session/refresh")
@auth()
def refresh_session_token():
    return Response.make(
        {
            "token": auth_controller.refresh_session_token(
                authorization=request.headers.get("Authorization"),
            ),
        },
        Response.HTTP_SUCCESS,
    )
