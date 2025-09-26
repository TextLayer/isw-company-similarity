import os

# initialize celery in memory for testing (before test setup)
os.environ["CELERY_BROKER_URL"] = "memory://localhost/"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "True"
os.environ["CELERY_TASK_IGNORE_RESULT"] = "False"

import pytest
import werkzeug

from isw.interfaces.api import create_app
from isw.shared.logging.logger import logger


class BaseTest:
    """Base class for all tests with common setup and teardown"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment before each test and tear down after"""
        logger.info(f"Setting up {self.__class__.__name__}")

        os.environ["FLASK_CONFIG"] = "TEST"
        os.environ["TESTING"] = "true"
        os.environ["API_KEY"] = "test-api-key-for-testing"

        self.app = create_app("TEST")
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Work around werkzeug version issue
        if not hasattr(werkzeug, "__version__"):
            werkzeug.__version__ = "2.0.0"  # Set a dummy version

        self.client = self.app.test_client()

        yield

        logger.info(f"Tearing down {self.__class__.__name__}")
        self.ctx.pop()


class BaseCommandTest:
    """Base class for command pattern tests"""

    def assert_validation_fails(self, command, expected_error_message=None):
        """Helper to assert that command validation fails"""
        from isw.core.errors.validation import ValidationException

        with pytest.raises(ValidationException) as exc_info:
            command.run()

        if expected_error_message:
            assert expected_error_message in str(exc_info.value)

    def assert_command_succeeds(self, command):
        """Helper to assert that command execution succeeds"""
        try:
            result = command.run()
            return result
        except Exception as e:
            pytest.fail(f"Command execution failed unexpectedly: {str(e)}")
