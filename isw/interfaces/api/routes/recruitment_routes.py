from flask import Blueprint, g, request

from isw.core.controllers.recruitment_controller import RecruitmentController
from isw.interfaces.api.decorators.auth import auth
from isw.interfaces.api.utils.response import Response

recruitment_controller = RecruitmentController()
recruitment_routes = Blueprint("recruitment_routes", __name__)


@recruitment_routes.post("/jobs")
@auth(role="admin")
def create_job():
    return Response.make(
        recruitment_controller.create_job(**request.json),
        Response.HTTP_CREATED,
    )


@recruitment_routes.delete("/jobs/<id>")
@auth(role="admin")
def remove_job(id):
    return Response.make(
        recruitment_controller.remove_job(id=id),
        Response.HTTP_NO_CONTENT,
    )


@recruitment_routes.get("/jobs")
@auth(role="admin")
def get_jobs():
    return Response.make(
        recruitment_controller.search_jobs(
            page=int(request.args.get("page", 1)),
            search_query=request.args.get("q", ""),
        ),
        Response.HTTP_SUCCESS,
    )


@recruitment_routes.get("/jobs/<id>")
@auth(role="admin")
def get_job_details(id):
    return Response.make(
        recruitment_controller.get_job_details(id=id),
        Response.HTTP_SUCCESS,
    )


@recruitment_routes.patch("/jobs/<id>")
@auth(role="admin")
def update_job(id):
    # note: force it via path params
    if "id" in request.json:
        del request.json["id"]

    return Response.make(
        recruitment_controller.update_job(id=id, **request.json),
        Response.HTTP_SUCCESS,
    )


@recruitment_routes.get("/submission-url")
@auth()
def get_upload_url():
    return Response.make(
        recruitment_controller.generate_technical_submission_request(
            application_id=g.user_details.get("application_id"),
            candidate_id=g.user_details.get("candidate_id"),
        ),
        Response.HTTP_SUCCESS,
    )
