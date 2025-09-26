import pytest

from isw.core.commands.base import ReadCommand, WriteCommand
from isw.core.controllers.base import Controller
from isw.core.errors.validation import ValidationException


class TestCommandControllerIntegration:
    """Test critical integration between commands and controllers"""

    def test_controller_command_execution_flow(self):
        """Verify controllers properly execute commands through the Executor"""

        class GetDataCommand(ReadCommand):
            def __init__(self, data_id: str):
                self.data_id = data_id

            def validate(self):
                if not self.data_id:
                    raise ValidationException("ID required")

            def execute(self):
                return {"id": self.data_id, "value": "test-data"}

        class DataController(Controller):
            def get_data(self, data_id: str):
                command = GetDataCommand(data_id)
                return self.executor.execute_read(command)

        controller = DataController()
        result = controller.get_data("123")

        assert result == {"id": "123", "value": "test-data"}

    def test_validation_error_propagation(self):
        """Verify validation errors propagate through the controller-command flow"""

        class ValidatedCommand(WriteCommand):
            def validate(self):
                raise ValidationException("Invalid data")

            def execute(self):
                pytest.fail("Should not execute")

        class TestController(Controller):
            def perform_action(self):
                command = ValidatedCommand()
                return self.executor.execute_write(command)

        controller = TestController()

        with pytest.raises(ValidationException, match="Invalid data"):
            controller.perform_action()

    def test_command_execution_type(self):
        """Verify read<>write compatibility"""

        class WriteCommandTest(WriteCommand):
            def validate(self):
                pass

            def execute(self):
                pass

        class TestController(Controller):
            def perform_action(self):
                command = WriteCommandTest()
                return self.executor.execute_read(command)

        controller = TestController()

        with pytest.raises(Exception, match="Incorrect executable used"):
            controller.perform_action()
