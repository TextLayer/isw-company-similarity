from flask import make_response
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from ....shared.logging.logger import logger
from ...worker.registry import task_registry
from ..middleware.logger_middleware import log_request_info, log_response_info
from ..utils.messages import Error
from ..utils.response import Response
from .company_routes import company_routes


def stop(env, resp):
    resp("200 OK", [("Content-Type", "text/plain")])
    return [b"InsightSoftware Anomaly Detection API. Basepath /v1/"]


blueprints = {
    "/company_routes": company_routes,
}


def init_routes(app):
    app.wsgi_app = DispatcherMiddleware(stop, {"/v1": app.wsgi_app})

    app.before_request(log_request_info)
    app.after_request(log_response_info)

    for path in blueprints:
        app.register_blueprint(blueprints[path], url_prefix=path)

    @app.get("/")
    def index():
        return Response(
            {"api_version": "v1.0", "api_description": "TextLayer Core API"},
            Response.HTTP_SUCCESS,
        ).build()

    @app.get("/health")
    def health():
        return Response(
            {"status": "online", "worker_status": task_registry.conduct_health_check()}, Response.HTTP_SUCCESS
        ).build()

    @app.errorhandler(404)
    def handle_404(error):
        return make_response(Error.NOT_FOUND, Response.HTTP_NOT_FOUND)

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Global error handler to replace the @handle_exceptions decorator"""
        logger.debug(f"Exception reached router: {error}")
        return Response().build_error(error)
