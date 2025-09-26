import pytest

from isw.core.commands.base import BaseCommand, ReadCommand
from isw.core.commands.executor import Executor
from isw.core.controllers.base import Controller
from isw.core.errors.validation import ValidationException


class TestArchitecturalBoundaries:
    """Verify critical architectural patterns and boundaries"""

    def test_command_validation_execution_pattern(self):
        """The validation→execution pattern is the core of our business logic safety"""
        execution_order = []

        class TrackedCommand(BaseCommand):
            def validate(self):
                execution_order.append("validate")

            def execute(self):
                execution_order.append("execute")
                return "result"

        command = TrackedCommand()
        result = command.run()

        assert execution_order == ["validate", "execute"], "Validation MUST run before execution"
        assert result == "result"

    def test_validation_blocks_execution(self):
        """Failed validation must prevent execution to maintain data integrity"""

        class ValidatedCommand(BaseCommand):
            def validate(self):
                raise ValidationException("Invalid input")

            def execute(self):
                pytest.fail("Execute should never be called")

        command = ValidatedCommand()

        with pytest.raises(ValidationException):
            command.run()

    def test_controllers_use_executor_not_commands_directly(self):
        """Controllers must delegate to Executor to maintain separation of concerns"""

        class SampleController(Controller):
            def do_something(self):
                # This is the correct pattern
                command = type("TestCommand", (ReadCommand,), {"execute": lambda self: "controller result"})()
                return self.executor.execute_read(command)

        controller = SampleController()
        result = controller.do_something()

        assert result == "controller result"
        assert hasattr(controller, "executor"), "Controllers must have executor"
        assert isinstance(controller.executor, Executor), "Must be Executor instance"

    def test_executor_is_singleton(self):
        """Executor singleton ensures consistent command execution across the app"""
        executor1 = Executor.get_instance()
        executor2 = Executor.get_instance()

        controller1 = Controller()
        controller2 = Controller()

        assert executor1 is executor2, "Executor must be singleton"
        assert controller1.executor is controller2.executor, "All controllers share executor"
