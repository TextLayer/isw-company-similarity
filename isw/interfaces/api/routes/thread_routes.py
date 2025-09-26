from flask import Blueprint, request

from ....core.controllers.thread_controller import ThreadController
from ..utils.response import Response

thread_routes = Blueprint("thread_routes", __name__)
thread_controller = ThreadController()


@thread_routes.get("/models")
def get_models():
    return Response.make(thread_controller.get_models(), Response.HTTP_SUCCESS)


@thread_routes.post("/chat")
def chat():
    response = thread_controller.process_chat_message(
        max_steps=int(request.json.get("maxSteps", 10)),
        messages=request.json.get("messages"),
        model=request.json.get("model"),
        stream=False,
    )

    return Response.make(response, Response.HTTP_SUCCESS)


@thread_routes.post("/chat/stream")
def chat_stream():
    return Response.stream(
        thread_controller.process_chat_message(
            max_steps=int(request.json.get("maxSteps", 10)),
            messages=request.json.get("messages"),
            model=request.json.get("model"),
            stream=True,
        )
    )
