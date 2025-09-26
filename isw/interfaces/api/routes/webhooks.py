from flask import Blueprint, request

from ....core.controllers.webhooks_controller import WebhooksController
from ....core.utils.helpers import safe_get
from ...api.utils.response import Response
from ...worker.registry import task_registry

webhooks_controller = WebhooksController()
webhooks_routes = Blueprint("webhooks_routes", __name__)


@webhooks_routes.post("/recruitment/ashby")
def handle_recruiting_updates():
    if not webhooks_controller.validate(
        body=request.get_data(),
        provider_name="ashby",
        signature=request.headers.get("Ashby-Signature", ""),
    ):
        return Response("", Response.HTTP_UNAUTHORIZED).build()

    j = request.get_json()
    application_id = safe_get(j, "data", "application", "id")
    candidate_id = safe_get(j, "data", "application", "candidate", "id")

    if j.get("action") == "applicationSubmit" and candidate_id and application_id:
        task_registry.defer(
            "process_candidate",
            {
                "application_id": application_id,
                "candidate_id": candidate_id,
            },
        )
    elif j.get("action") == "candidateStageChange" and candidate_id and application_id:
        task_registry.defer(
            "candidate_stage_change",
            {
                "application_id": application_id,
                "candidate_id": candidate_id,
            },
        )

    return Response.make(
        "",
        Response.HTTP_NO_CONTENT,
    )


@webhooks_routes.post("/prompts/langfuse")
def handle_prompts_update():
    if not webhooks_controller.validate(
        body=request.get_data(as_text=True),
        provider_name="langfuse",
        signature=request.headers.get("X-Langfuse-Signature", ""),
    ):
        return Response("", Response.HTTP_UNAUTHORIZED).build()

    task_registry.defer(
        "handle_update_prompts",
        {
            "provider_name": "langfuse",
        },
    )

    return Response.make(
        "",
        Response.HTTP_NO_CONTENT,
    )
