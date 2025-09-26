import inspect

from ...shared.logging.logger import logger


class BaseCommand:
    """
    Abstract base class for all commands in the command pattern.

    Provides the template method pattern with automatic validation flow.
    """

    def scope(self):
        """Check if the command is being executed in the correct scope."""
        out_of_scope = False

        try:
            # some gnarly checks going on, but it's assuming we're always using Controller>Command as we should
            parent_class = self.__class__.__bases__[0]
            executor_name = inspect.stack()[2].function

            if (
                executor_name.startswith("execute_")
                and executor_name.split("_").pop().capitalize() not in parent_class.__name__
            ):
                logger.warning(f"Incorrect executable used: {executor_name}")
                out_of_scope = True

        # in case our inspect fails, we'll just keep track of scoping via a flag
        except Exception:
            logger.warning(f"Couldn't scope {self.__class__.__name__}")
            pass

        if out_of_scope:
            raise Exception("Incorrect executable used")

    def run(self):
        """
        Template method for checking and debugging command lifecycle.

        Returns:
            The result of the command execution.
        """
        id = self.__class__.__name__

        logger.debug(f"Scoping {id}")
        self.scope()

        logger.debug(f"Validating {id}")
        self.validate()

        logger.debug(f"Executing {id}")
        return self.execute()

    def validate(self):
        """
        Override this method to add validation logic.

        This method is called before execute() and should raise
        ValidationException if validation fails.
        Default implementation does nothing (no validation required).
        """
        pass

    def execute(self):
        """
        Implement your business logic here.

        This method must be implemented by all concrete command classes.

        Returns:
            The result of the command execution.

        Raises:
            NotImplementedError: If not implemented by concrete class.
        """
        raise NotImplementedError


class ReadCommand(BaseCommand):
    """
    Abstract base class for read-only operations in the command pattern.

    ReadCommand is part of the application's command processing architecture,
    specifically for operations that retrieve data without modifying the system state.
    This pattern provides a clean separation of concerns by isolating business logic
    from request handling.

    Example:
        class GetUserCommand(ReadCommand):
            def __init__(self, user_id):
                self.user_id = user_id

            def validate(self):
                if not self.user_id:
                    raise ValidationException("Missing user_id")

            def execute(self):
                return {"id": self.user_id, "name": "Example User"}
    """

    pass


class WriteCommand(BaseCommand):
    """
    Abstract base class for write operations in the command pattern.

    WriteCommand is part of the application's command processing architecture,
    specifically for operations that modify the system state. This pattern ensures
    a clean separation of concerns, with business logic organized in command handlers
    separate from API controllers.

    Example:
        class CreateUserCommand(WriteCommand):
            def __init__(self, user_data):
                self.user_data = user_data

            def validate(self):
                if not self.user_data.get('email'):
                    raise ValidationException("Missing email")

            def execute(self):
                return {"id": "new_id", "status": "created"}
    """

    pass
