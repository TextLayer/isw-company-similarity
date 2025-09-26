from marshmallow import ValidationError

from isw.core.errors import (
    AuthenticationException,
    AuthorizationException,
    ExceptionClassifier,
    ProcessingException,
    ValidationException,
)


class TestErrorPipeline:
    """Verify error classification and handling pipeline"""

    def test_authentication_errors_map_to_401(self):
        """Auth errors must return 401 for proper client handling"""
        error = AuthenticationException("Invalid token")

        assert ExceptionClassifier.is_authentication_error(error)
        assert not ExceptionClassifier.is_authorization_error(error)
        assert not ExceptionClassifier.is_bad_request(error)

    def test_authorization_errors_map_to_403(self):
        """Authz errors must return 403 for proper client handling"""
        error = AuthorizationException("Insufficient permissions")

        assert ExceptionClassifier.is_authorization_error(error)
        assert not ExceptionClassifier.is_authentication_error(error)
        assert not ExceptionClassifier.is_bad_request(error)

    def test_validation_errors_map_to_400(self):
        """Validation errors must return 400 as bad requests"""
        error = ValidationException("Invalid input")

        assert ExceptionClassifier.is_bad_request(error)
        assert not ExceptionClassifier.is_authentication_error(error)
        assert not ExceptionClassifier.is_authorization_error(error)

    def test_processing_errors_map_to_400(self):
        """Processing errors are also bad requests"""
        error = ProcessingException("Cannot process")

        assert ExceptionClassifier.is_bad_request(error)

    def test_validation_errors_map_to_422(self):
        """Validation errors (marshmallow) are unprocessable"""
        error = ValidationError("Invalid input", field_name="field_name")
        assert ExceptionClassifier.is_validation_error(error)

    def test_unknown_errors_are_not_classified(self):
        """Unknown errors should not be misclassified"""
        error = Exception("Unknown error")

        assert not ExceptionClassifier.is_authentication_error(error)
        assert not ExceptionClassifier.is_authorization_error(error)
        assert not ExceptionClassifier.is_bad_request(error)
