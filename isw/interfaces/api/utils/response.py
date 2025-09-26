import uuid

import flask
from flask import Response as FlaskResponse
from flask import make_response, stream_with_context

from isw.core.errors.classifier import ExceptionClassifier
from isw.interfaces.api.utils.messages import Error
from isw.interfaces.api.utils.request import get_header, get_request_id


def get_request_uid() -> str:
    """
    Returns the current request ID or a new one if there is none.
    Order of preference:
    * If already created and stored in flask.g, use that
    * If X-Request-Id header is present, use that
    * Otherwise, generate a new UUID
    """
    request_id = get_request_id()
    if not request_id:
        request_id = str(uuid.uuid4())

    flask.g.request_id = request_id

    return request_id


class Response:
    # HTTP status code constants for standardized API responses
    HTTP_SUCCESS = 200
    HTTP_CREATED = 201
    HTTP_ACCEPTED = 202
    HTTP_NO_CONTENT = 204
    HTTP_MOVED_PERMANENTLY = 301
    HTTP_BAD_REQUEST = 400
    HTTP_UNAUTHORIZED = 401
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404
    HTTP_UNPROCESSABLE = 422
    HTTP_ERROR = 500
    HTTP_NOT_IMPLEMENTED = 501
    HTTP_UNAVAILABLE = 503

    def __init__(self, data=None, status=None):
        """
        Initialize a Response object with optional data and status code.

        Args:
            data: The payload to include in the response.
            status: The HTTP status code for the response.
        """
        self.data = data
        self.status = status

    def build(self):
        """
        Build a Flask response object with a standardized JSON structure.

        Returns:
            A Flask response object containing status, payload, and correlation_id.
        """
        response = {
            "status": self.status,
            "payload": self.data,
            "correlation_id": get_request_uid(),
        }
        resp = make_response(response)
        return resp

    def build_error(self, error):
        """
        Build a Flask response object with a standardized JSON structure for errors.
        Validation errors are handled differently than other errors to provide more information to the client.

        Returns:
            A Flask response object containing status, payload, and correlation_id.
        """

        specs = [
            (ExceptionClassifier.is_authentication_error, Error.UNAUTHORIZED, self.HTTP_UNAUTHORIZED),
            (ExceptionClassifier.is_authorization_error, Error.FORBIDDEN, self.HTTP_FORBIDDEN),
            (ExceptionClassifier.is_bad_request, Error.make_bad_request_error(error), self.HTTP_BAD_REQUEST),
            (ExceptionClassifier.is_not_found_error, Error.NOT_FOUND, self.HTTP_NOT_FOUND),
            (ExceptionClassifier.is_validation_error, Error.make_validation_error(error), self.HTTP_UNPROCESSABLE),
            (ExceptionClassifier.is_service_error, Error.REQUEST_FAILED, self.HTTP_ERROR),
        ]

        for spec, response, status_code in specs:
            if spec(error):
                return make_response(response, status_code)

        return make_response(Error.REQUEST_FAILED, self.HTTP_ERROR)

    @staticmethod
    def make(data, status, deprecation_warning=False, deprecation_date=None):
        """
        Create a standardized Flask response with optional deprecation warning.

        Args:
            data: The payload to include in the response.
            status: The HTTP status code for the response.
            deprecation_warning: Boolean indicating if a deprecation warning should be included.
            deprecation_date: Optional date when the endpoint will be deprecated.

        Returns:
            A Flask response object containing status, payload, correlation_id, and optional deprecation warning.
        """
        response = {
            "status": status,
            "payload": data,
            "correlation_id": get_request_uid(),
        }
        if deprecation_warning:
            deprecation_message = "This endpoint is deprecated and will be removed in the future."
            if deprecation_date:
                deprecation_message += f" This endpoint will be removed on {deprecation_date}."
            response["deprecation_warning"] = deprecation_message
        resp = make_response(response, status)
        return resp

    @staticmethod
    def stream(generator, status=HTTP_SUCCESS, headers=None):
        """
        Create a streaming response for server-sent events (SSE) or Vercel AI SDK protocol.

        Supports two protocols:
        1. SSE (Server-Sent Events) - Traditional format with 'data: ...' prefix.
        2. Vercel AI SDK - Format with numeric/letter prefixes (0:, 9:, etc.).

        Args:
            generator: A generator that yields data to be streamed.
            status: HTTP status code (default: 200).
            headers: Optional dictionary of headers to add to the response.

        Returns:
            A Flask response object with streaming content.
        """
        # Determine the appropriate wire format based on the Accept header
        wants_sse = "text/event-stream" in get_header("Accept")
        mimetype = "text/event-stream" if wants_sse else "text/plain"

        def _to_wire(chunk: bytes | str) -> bytes:
            """
            Convert a chunk of data to the appropriate wire format for streaming.

            Args:
                chunk: The data chunk to be formatted.

            Returns:
                The formatted chunk as bytes.
            """
            if not isinstance(chunk, (bytes, bytearray)):
                chunk = str(chunk)
            if wants_sse:
                # Wrap non-SSE frames and ensure proper termination
                if not chunk.startswith("data:"):
                    chunk = f"data: {chunk}"
                if not chunk.endswith("\n\n"):
                    chunk += "\n\n"
                return chunk.encode("utf-8")
            return chunk.encode("utf-8")

        def _iter():
            """
            Generator function that yields formatted data chunks for streaming.
            """
            for part in generator:
                yield _to_wire(part)

        resp = FlaskResponse(
            stream_with_context(_iter()),
            status=status,
            mimetype=mimetype,
            direct_passthrough=True,
        )

        # Set minimal headers to support streaming and prevent buffering
        resp.headers.update(
            {
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
        if not wants_sse:
            # Add Vercel-specific header for AI SDK protocol
            resp.headers["x-vercel-ai-data-stream"] = "v1"

        if headers:
            resp.headers.update(headers)

        # Do not set Transfer-Encoding manually; Flask manages this automatically.
        return resp
