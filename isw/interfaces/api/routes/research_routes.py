from flask import Blueprint, request

from ....core.controllers.research_controller import ResearchController
from ....core.errors import NotFoundException
from ..utils.response import Response

research_routes = Blueprint("research_routes", __name__)


@research_routes.get("/")
def search_research_papers():
    return Response.make(
        ResearchController().search_research_papers(
            categories=request.args.getlist("category[]"),
            page=int(request.args.get("page", 1)),
            search_query=request.args.get("q", ""),
        ),
        Response.HTTP_SUCCESS,
    )


@research_routes.post("/<string:id>/insights")
def generate_research_paper_insights(id: str):
    try:
        return Response.stream(
            ResearchController().generate_research_paper_insights(
                id=id,
                insight=request.json.get("type"),
            ),
        )
    except Exception as e:
        raise NotFoundException("Unknown research paper insight route") from e
