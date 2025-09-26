import logging

from flask import request

from isw.shared.logging.logger import logger


def log_request_info():
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(request.headers)
        logger.debug(request.get_json(silent=True))


def log_response_info(response):
    if logger.isEnabledFor(logging.DEBUG):
        # Check if it's a streaming response before trying to access data
        if hasattr(response, "direct_passthrough") and response.direct_passthrough:
            logger.debug("Streaming response (data not logged)")
        else:
            logger.debug(response.data)
    return response
