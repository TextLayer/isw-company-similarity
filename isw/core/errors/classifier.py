from marshmallow import ValidationError

from isw.core.errors.authentication import AuthenticationException
from isw.core.errors.authorization import AuthorizationException
from isw.core.errors.not_found import NotFoundException
from isw.core.errors.processing import ProcessingException
from isw.core.errors.service import ServiceException
from isw.core.errors.validation import ValidationException


class ExceptionClassifier:
    @staticmethod
    def is_authentication_error(error):
        return isinstance(error, AuthenticationException)

    @staticmethod
    def is_authorization_error(error):
        return isinstance(error, AuthorizationException)

    @staticmethod
    def is_bad_request(error):
        return any(
            isinstance(error, cls)
            for cls in [
                ValidationException,
                ProcessingException,
            ]
        )

    @staticmethod
    def is_not_found_error(error):
        return isinstance(error, NotFoundException)

    @staticmethod
    def is_service_error(error):
        return isinstance(error, ServiceException)

    @staticmethod
    def is_validation_error(error):
        return isinstance(error, ValidationError)
